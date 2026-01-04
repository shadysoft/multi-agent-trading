"""Trend Analysis Agent using EMA, ADX, and Price Structure."""

import pandas as pd
from typing import Optional
import logging

from .base_agent import BaseAgent
from data.models import AgentSignal, SignalDirection

logger = logging.getLogger(__name__)


class TrendAgent(BaseAgent):
    """Trend analysis agent using EMA crossovers, ADX, and price structure."""

    def __init__(
        self,
        symbol: str,
        timeframe: str = "H1",
        weight: float = 0.25,
        ema_periods: list = None,
        adx_period: int = 14,
        adx_threshold: float = 25.0
    ):
        """
        Initialize Trend Agent.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            weight: Agent weight
            ema_periods: EMA periods [fast, medium, slow]
            adx_period: ADX period
            adx_threshold: Minimum ADX value for strong trend
        """
        super().__init__("TrendAgent", symbol, timeframe, weight)
        self.ema_periods = ema_periods or [20, 50, 200]
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold

    def analyze(self, data: pd.DataFrame) -> AgentSignal:
        """
        Analyze trend using EMA, ADX, and price structure.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            AgentSignal with direction, confidence, and reasoning
        """
        # Validate data
        if not self.validate_data(data, min_bars=max(self.ema_periods) + 50):
            return self.create_signal(
                SignalDirection.WAIT,
                0.0,
                "Insufficient data for analysis"
            )

        try:
            # Calculate EMAs
            ema_fast = self.calculate_ema(data, self.ema_periods[0])
            ema_medium = self.calculate_ema(data, self.ema_periods[1])
            ema_slow = self.calculate_ema(data, self.ema_periods[2])
            
            # Calculate ADX
            adx = self.calculate_adx(data, self.adx_period)
            
            # Get current values
            current_price = data['close'].iloc[-1]
            current_ema_fast = ema_fast.iloc[-1]
            current_ema_medium = ema_medium.iloc[-1]
            current_ema_slow = ema_slow.iloc[-1]
            current_adx = adx.iloc[-1]
            
            # Analyze price structure
            price_structure = self._analyze_price_structure(data)
            
            # Determine trend direction
            direction = SignalDirection.WAIT
            confidence = 0.0
            reasoning_parts = []
            
            # Check EMA alignment
            bullish_emas = (current_ema_fast > current_ema_medium > current_ema_slow)
            bearish_emas = (current_ema_fast < current_ema_medium < current_ema_slow)
            
            if bullish_emas:
                direction = SignalDirection.BUY
                reasoning_parts.append("Bullish EMA alignment")
                confidence += 0.3
            elif bearish_emas:
                direction = SignalDirection.SELL
                reasoning_parts.append("Bearish EMA alignment")
                confidence += 0.3
            else:
                reasoning_parts.append("No clear EMA alignment")
            
            # Check ADX for trend strength
            if current_adx >= self.adx_threshold:
                reasoning_parts.append(f"Strong trend (ADX={current_adx:.1f})")
                confidence += 0.3
            else:
                reasoning_parts.append(f"Weak trend (ADX={current_adx:.1f})")
                confidence += 0.1
            
            # Check price structure
            if price_structure['higher_highs'] and price_structure['higher_lows']:
                if direction == SignalDirection.BUY:
                    reasoning_parts.append("Higher highs and higher lows")
                    confidence += 0.4
                elif direction == SignalDirection.WAIT:
                    direction = SignalDirection.BUY
                    reasoning_parts.append("Higher highs and higher lows")
                    confidence += 0.2
            elif price_structure['lower_highs'] and price_structure['lower_lows']:
                if direction == SignalDirection.SELL:
                    reasoning_parts.append("Lower highs and lower lows")
                    confidence += 0.4
                elif direction == SignalDirection.WAIT:
                    direction = SignalDirection.SELL
                    reasoning_parts.append("Lower highs and lower lows")
                    confidence += 0.2
            else:
                reasoning_parts.append("Mixed price structure")
            
            # Normalize confidence to 0-1 range
            confidence = min(confidence, 1.0)
            
            reasoning = "; ".join(reasoning_parts)
            
            metadata = {
                'ema_fast': float(current_ema_fast),
                'ema_medium': float(current_ema_medium),
                'ema_slow': float(current_ema_slow),
                'adx': float(current_adx),
                'price_structure': price_structure
            }
            
            return self.create_signal(direction, confidence, reasoning, metadata)
            
        except Exception as e:
            logger.error(f"Error in TrendAgent analysis: {e}")
            return self.create_signal(
                SignalDirection.WAIT,
                0.0,
                f"Analysis error: {str(e)}"
            )

    def _analyze_price_structure(self, data: pd.DataFrame, lookback: int = 20) -> dict:
        """
        Analyze price structure (Higher Highs/Lows, Lower Highs/Lows).
        
        Args:
            data: DataFrame with OHLC data
            lookback: Number of bars to analyze
            
        Returns:
            Dictionary with price structure analysis
        """
        if len(data) < lookback + 1:
            return {
                'higher_highs': False,
                'higher_lows': False,
                'lower_highs': False,
                'lower_lows': False
            }
        
        recent_data = data.iloc[-lookback:]
        
        # Find swing highs and lows
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        
        # Simple approach: compare recent highs and lows
        mid_point = len(highs) // 2
        
        first_half_high = max(highs[:mid_point])
        second_half_high = max(highs[mid_point:])
        
        first_half_low = min(lows[:mid_point])
        second_half_low = min(lows[mid_point:])
        
        higher_highs = second_half_high > first_half_high
        higher_lows = second_half_low > first_half_low
        lower_highs = second_half_high < first_half_high
        lower_lows = second_half_low < first_half_low
        
        return {
            'higher_highs': higher_highs,
            'higher_lows': higher_lows,
            'lower_highs': lower_highs,
            'lower_lows': lower_lows
        }
