"""Wave Analysis Agent for identifying impulse and correction waves."""

import pandas as pd
import numpy as np
from typing import Optional, Dict
import logging

from .base_agent import BaseAgent
from data.models import AgentSignal, SignalDirection

logger = logging.getLogger(__name__)


class WaveAgent(BaseAgent):
    """Wave analysis agent for identifying impulse and correction phases."""

    def __init__(
        self,
        symbol: str,
        timeframe: str = "H1",
        weight: float = 0.20,
        min_impulse_bars: int = 5,
        min_correction_bars: int = 3,
        impulse_threshold: float = 0.6
    ):
        """
        Initialize Wave Agent.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            weight: Agent weight
            min_impulse_bars: Minimum bars for impulse wave
            min_correction_bars: Minimum bars for correction wave
            impulse_threshold: Threshold for impulse strength (0-1)
        """
        super().__init__("WaveAgent", symbol, timeframe, weight)
        self.min_impulse_bars = min_impulse_bars
        self.min_correction_bars = min_correction_bars
        self.impulse_threshold = impulse_threshold

    def analyze(self, data: pd.DataFrame) -> AgentSignal:
        """
        Analyze wave structure to identify impulse/correction phases.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            AgentSignal with direction, confidence, and reasoning
        """
        # Validate data
        if not self.validate_data(data, min_bars=50):
            return self.create_signal(
                SignalDirection.WAIT,
                0.0,
                "Insufficient data for analysis"
            )

        try:
            # Identify current wave phase
            wave_analysis = self._analyze_wave_structure(data)
            
            direction = SignalDirection.WAIT
            confidence = 0.0
            reasoning_parts = []
            
            current_phase = wave_analysis['current_phase']
            impulse_strength = wave_analysis['impulse_strength']
            
            # Determine signal based on wave analysis
            if current_phase == 'bullish_impulse':
                direction = SignalDirection.BUY
                confidence = min(impulse_strength, 0.9)
                reasoning_parts.append(f"Bullish impulse wave (strength: {impulse_strength:.2f})")
            elif current_phase == 'bearish_impulse':
                direction = SignalDirection.SELL
                confidence = min(impulse_strength, 0.9)
                reasoning_parts.append(f"Bearish impulse wave (strength: {impulse_strength:.2f})")
            elif current_phase == 'bullish_correction':
                # Correction phase - potential continuation after retracement
                direction = SignalDirection.BUY
                confidence = 0.5
                reasoning_parts.append("Bullish correction - potential continuation setup")
            elif current_phase == 'bearish_correction':
                direction = SignalDirection.SELL
                confidence = 0.5
                reasoning_parts.append("Bearish correction - potential continuation setup")
            else:
                reasoning_parts.append("No clear wave structure")
            
            # Adjust confidence based on wave count and consistency
            wave_count = wave_analysis.get('wave_count', 0)
            if wave_count >= 3:
                reasoning_parts.append(f"Multiple waves detected ({wave_count})")
                confidence = min(confidence + 0.1, 1.0)
            
            reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No wave signal"
            
            metadata = {
                'current_phase': current_phase,
                'impulse_strength': float(impulse_strength),
                'wave_count': wave_count,
                'wave_duration': wave_analysis.get('wave_duration', 0)
            }
            
            return self.create_signal(direction, confidence, reasoning, metadata)
            
        except Exception as e:
            logger.error(f"Error in WaveAgent analysis: {e}")
            return self.create_signal(
                SignalDirection.WAIT,
                0.0,
                f"Analysis error: {str(e)}"
            )

    def _analyze_wave_structure(self, data: pd.DataFrame, lookback: int = 30) -> Dict:
        """
        Analyze wave structure to identify impulse and correction phases.
        
        Args:
            data: DataFrame with OHLC data
            lookback: Number of bars to analyze
            
        Returns:
            Dictionary with wave analysis
        """
        if len(data) < lookback:
            lookback = len(data)
        
        recent_data = data.iloc[-lookback:]
        
        # Calculate price momentum
        close_prices = recent_data['close'].values
        price_change = close_prices[-1] - close_prices[0]
        price_change_pct = (price_change / close_prices[0]) * 100
        
        # Calculate average candle body size
        bodies = abs(recent_data['close'] - recent_data['open']).values
        avg_body = np.mean(bodies)
        
        # Calculate directional movement
        up_moves = 0
        down_moves = 0
        for i in range(1, len(close_prices)):
            if close_prices[i] > close_prices[i-1]:
                up_moves += 1
            elif close_prices[i] < close_prices[i-1]:
                down_moves += 1
        
        total_moves = up_moves + down_moves
        if total_moves == 0:
            return {
                'current_phase': 'sideways',
                'impulse_strength': 0.0,
                'wave_count': 0,
                'wave_duration': 0
            }
        
        # Calculate directional ratio
        up_ratio = up_moves / total_moves
        down_ratio = down_moves / total_moves
        
        # Determine wave phase
        current_phase = 'sideways'
        impulse_strength = 0.0
        
        # Strong upward movement
        if up_ratio >= self.impulse_threshold and price_change_pct > 0.5:
            if len(recent_data) >= self.min_impulse_bars:
                current_phase = 'bullish_impulse'
                impulse_strength = up_ratio
            else:
                current_phase = 'bullish_correction'
                impulse_strength = up_ratio * 0.7
        # Strong downward movement
        elif down_ratio >= self.impulse_threshold and price_change_pct < -0.5:
            if len(recent_data) >= self.min_impulse_bars:
                current_phase = 'bearish_impulse'
                impulse_strength = down_ratio
            else:
                current_phase = 'bearish_correction'
                impulse_strength = down_ratio * 0.7
        # Weak upward movement (correction in downtrend)
        elif up_ratio > 0.5 and abs(price_change_pct) < 0.5:
            current_phase = 'bearish_correction'
            impulse_strength = 0.4
        # Weak downward movement (correction in uptrend)
        elif down_ratio > 0.5 and abs(price_change_pct) < 0.5:
            current_phase = 'bullish_correction'
            impulse_strength = 0.4
        
        # Count waves (simplified - count direction changes)
        wave_count = 0
        direction = 0  # 1 for up, -1 for down
        for i in range(1, len(close_prices)):
            if close_prices[i] > close_prices[i-1] and direction != 1:
                wave_count += 1
                direction = 1
            elif close_prices[i] < close_prices[i-1] and direction != -1:
                wave_count += 1
                direction = -1
        
        return {
            'current_phase': current_phase,
            'impulse_strength': impulse_strength,
            'wave_count': wave_count,
            'wave_duration': lookback,
            'price_change_pct': price_change_pct,
            'up_ratio': up_ratio,
            'down_ratio': down_ratio
        }

    def _identify_swing_points(self, data: pd.DataFrame, window: int = 5) -> Dict:
        """
        Identify swing high and low points.
        
        Args:
            data: DataFrame with OHLC data
            window: Window size for swing detection
            
        Returns:
            Dictionary with swing points
        """
        swing_highs = []
        swing_lows = []
        
        for i in range(window, len(data) - window):
            # Check for swing high
            if data['high'].iloc[i] == data['high'].iloc[i-window:i+window+1].max():
                swing_highs.append({
                    'index': i,
                    'price': data['high'].iloc[i],
                    'time': data.index[i]
                })
            
            # Check for swing low
            if data['low'].iloc[i] == data['low'].iloc[i-window:i+window+1].min():
                swing_lows.append({
                    'index': i,
                    'price': data['low'].iloc[i],
                    'time': data.index[i]
                })
        
        return {
            'swing_highs': swing_highs,
            'swing_lows': swing_lows
        }
