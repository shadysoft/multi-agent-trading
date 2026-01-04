"""Smart Money Concepts Agent for detecting liquidity zones, order blocks, and FVGs."""

import pandas as pd
from typing import List, Dict, Optional
import logging

from .base_agent import BaseAgent
from data.models import AgentSignal, SignalDirection

logger = logging.getLogger(__name__)


class SMCAgent(BaseAgent):
    """Smart Money Concepts agent for institutional trading patterns."""

    def __init__(
        self,
        symbol: str,
        timeframe: str = "H1",
        weight: float = 0.25,
        min_order_block_touches: int = 2,
        fvg_min_size_pips: float = 5.0,
        liquidity_zone_lookback: int = 50
    ):
        """
        Initialize SMC Agent.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            weight: Agent weight
            min_order_block_touches: Minimum touches for valid order block
            fvg_min_size_pips: Minimum size for Fair Value Gap in pips
            liquidity_zone_lookback: Lookback period for liquidity zones
        """
        super().__init__("SMCAgent", symbol, timeframe, weight)
        self.min_order_block_touches = min_order_block_touches
        self.fvg_min_size_pips = fvg_min_size_pips
        self.liquidity_zone_lookback = liquidity_zone_lookback

    def analyze(self, data: pd.DataFrame) -> AgentSignal:
        """
        Analyze using Smart Money Concepts.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            AgentSignal with direction, confidence, and reasoning
        """
        # Validate data
        if not self.validate_data(data, min_bars=self.liquidity_zone_lookback + 20):
            return self.create_signal(
                SignalDirection.WAIT,
                0.0,
                "Insufficient data for analysis"
            )

        try:
            # Identify liquidity zones
            liquidity_zones = self._identify_liquidity_zones(data)
            
            # Identify order blocks
            order_blocks = self._identify_order_blocks(data)
            
            # Identify Fair Value Gaps
            fvgs = self._identify_fvgs(data)
            
            # Analyze current price in relation to these zones
            current_price = data['close'].iloc[-1]
            
            direction = SignalDirection.WAIT
            confidence = 0.0
            reasoning_parts = []
            
            # Check proximity to bullish order blocks
            bullish_ob_nearby = any(
                ob['type'] == 'bullish' and abs(current_price - ob['low']) < (current_price * 0.002)
                for ob in order_blocks[-5:]  # Check last 5 order blocks
            )
            
            # Check proximity to bearish order blocks
            bearish_ob_nearby = any(
                ob['type'] == 'bearish' and abs(current_price - ob['high']) < (current_price * 0.002)
                for ob in order_blocks[-5:]
            )
            
            # Check for unfilled FVGs
            unfilled_bullish_fvg = any(
                fvg['type'] == 'bullish' and not fvg['filled']
                for fvg in fvgs[-5:]
            )
            
            unfilled_bearish_fvg = any(
                fvg['type'] == 'bearish' and not fvg['filled']
                for fvg in fvgs[-5:]
            )
            
            # Determine signal
            if bullish_ob_nearby and unfilled_bullish_fvg:
                direction = SignalDirection.BUY
                confidence = 0.8
                reasoning_parts.append("Price near bullish order block with unfilled FVG")
            elif bullish_ob_nearby:
                direction = SignalDirection.BUY
                confidence = 0.6
                reasoning_parts.append("Price near bullish order block")
            elif unfilled_bullish_fvg:
                direction = SignalDirection.BUY
                confidence = 0.5
                reasoning_parts.append("Unfilled bullish FVG present")
            elif bearish_ob_nearby and unfilled_bearish_fvg:
                direction = SignalDirection.SELL
                confidence = 0.8
                reasoning_parts.append("Price near bearish order block with unfilled FVG")
            elif bearish_ob_nearby:
                direction = SignalDirection.SELL
                confidence = 0.6
                reasoning_parts.append("Price near bearish order block")
            elif unfilled_bearish_fvg:
                direction = SignalDirection.SELL
                confidence = 0.5
                reasoning_parts.append("Unfilled bearish FVG present")
            else:
                reasoning_parts.append("No clear SMC setup")
            
            # Check liquidity zones
            if liquidity_zones:
                reasoning_parts.append(f"Found {len(liquidity_zones)} liquidity zones")
                if direction != SignalDirection.WAIT:
                    confidence = min(confidence + 0.1, 1.0)
            
            reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No SMC signals"
            
            metadata = {
                'order_blocks_count': len(order_blocks),
                'fvgs_count': len(fvgs),
                'liquidity_zones_count': len(liquidity_zones),
                'bullish_ob_nearby': bullish_ob_nearby,
                'bearish_ob_nearby': bearish_ob_nearby
            }
            
            return self.create_signal(direction, confidence, reasoning, metadata)
            
        except Exception as e:
            logger.error(f"Error in SMCAgent analysis: {e}")
            return self.create_signal(
                SignalDirection.WAIT,
                0.0,
                f"Analysis error: {str(e)}"
            )

    def _identify_liquidity_zones(self, data: pd.DataFrame) -> List[Dict]:
        """
        Identify liquidity zones (swing highs/lows).
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            List of liquidity zones
        """
        zones = []
        lookback = min(self.liquidity_zone_lookback, len(data) - 1)
        recent_data = data.iloc[-lookback:]
        
        # Find swing highs (liquidity above)
        for i in range(2, len(recent_data) - 2):
            if (recent_data['high'].iloc[i] > recent_data['high'].iloc[i-1] and
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i-2] and
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i+1] and
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i+2]):
                zones.append({
                    'type': 'resistance',
                    'price': recent_data['high'].iloc[i],
                    'index': i
                })
        
        # Find swing lows (liquidity below)
        for i in range(2, len(recent_data) - 2):
            if (recent_data['low'].iloc[i] < recent_data['low'].iloc[i-1] and
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i-2] and
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i+1] and
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i+2]):
                zones.append({
                    'type': 'support',
                    'price': recent_data['low'].iloc[i],
                    'index': i
                })
        
        return zones

    def _identify_order_blocks(self, data: pd.DataFrame) -> List[Dict]:
        """
        Identify order blocks (last down candle before up move and vice versa).
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            List of order blocks
        """
        order_blocks = []
        
        for i in range(3, len(data) - 1):
            # Bullish order block: down candle before strong up move
            if (data['close'].iloc[i] < data['open'].iloc[i] and  # Down candle
                data['close'].iloc[i+1] > data['open'].iloc[i+1] and  # Up candle
                data['close'].iloc[i+1] > data['high'].iloc[i]):  # Strong move up
                order_blocks.append({
                    'type': 'bullish',
                    'high': data['high'].iloc[i],
                    'low': data['low'].iloc[i],
                    'index': i
                })
            
            # Bearish order block: up candle before strong down move
            if (data['close'].iloc[i] > data['open'].iloc[i] and  # Up candle
                data['close'].iloc[i+1] < data['open'].iloc[i+1] and  # Down candle
                data['close'].iloc[i+1] < data['low'].iloc[i]):  # Strong move down
                order_blocks.append({
                    'type': 'bearish',
                    'high': data['high'].iloc[i],
                    'low': data['low'].iloc[i],
                    'index': i
                })
        
        return order_blocks

    def _identify_fvgs(self, data: pd.DataFrame) -> List[Dict]:
        """
        Identify Fair Value Gaps.
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            List of FVGs
        """
        fvgs = []
        current_price = data['close'].iloc[-1]
        
        for i in range(1, len(data) - 1):
            # Bullish FVG: gap between bar i-1 high and bar i+1 low
            if data['low'].iloc[i+1] > data['high'].iloc[i-1]:
                gap_size = data['low'].iloc[i+1] - data['high'].iloc[i-1]
                # Check if filled
                filled = current_price < data['low'].iloc[i+1]
                fvgs.append({
                    'type': 'bullish',
                    'top': data['low'].iloc[i+1],
                    'bottom': data['high'].iloc[i-1],
                    'size': gap_size,
                    'filled': filled,
                    'index': i
                })
            
            # Bearish FVG: gap between bar i-1 low and bar i+1 high
            if data['high'].iloc[i+1] < data['low'].iloc[i-1]:
                gap_size = data['low'].iloc[i-1] - data['high'].iloc[i+1]
                # Check if filled
                filled = current_price > data['high'].iloc[i+1]
                fvgs.append({
                    'type': 'bearish',
                    'top': data['low'].iloc[i-1],
                    'bottom': data['high'].iloc[i+1],
                    'size': gap_size,
                    'filled': filled,
                    'index': i
                })
        
        return fvgs
