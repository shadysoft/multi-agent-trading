"""Statistical Agent - Gatekeeper for trade validation."""

import pandas as pd
from typing import Optional
import logging

from .base_agent import BaseAgent
from data.models import AgentSignal, SignalDirection

logger = logging.getLogger(__name__)


class StatisticalAgent(BaseAgent):
    """Statistical gatekeeper agent that validates trading conditions."""

    def __init__(
        self,
        symbol: str,
        timeframe: str = "H1",
        weight: float = 0.20,
        max_spread_pips: float = 2.0,
        min_atr_pips: float = 10.0,
        atr_period: int = 14,
        max_open_positions: int = 5
    ):
        """
        Initialize Statistical Agent.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            weight: Agent weight
            max_spread_pips: Maximum allowed spread in pips
            min_atr_pips: Minimum ATR required in pips
            atr_period: ATR calculation period
            max_open_positions: Maximum allowed open positions
        """
        super().__init__("StatisticalAgent", symbol, timeframe, weight)
        self.max_spread_pips = max_spread_pips
        self.min_atr_pips = min_atr_pips
        self.atr_period = atr_period
        self.max_open_positions = max_open_positions

    def analyze(self, data: pd.DataFrame, current_spread: float = 0.0, open_positions: int = 0) -> AgentSignal:
        """
        Validate trading conditions.
        
        Args:
            data: DataFrame with OHLCV data
            current_spread: Current spread in pips
            open_positions: Number of open positions
            
        Returns:
            AgentSignal with direction, confidence, and reasoning
        """
        # Validate data
        if not self.validate_data(data, min_bars=self.atr_period + 10):
            return self.create_signal(
                SignalDirection.WAIT,
                0.0,
                "Insufficient data for analysis"
            )

        try:
            # Calculate ATR
            atr = self.calculate_atr(data, self.atr_period)
            current_atr = atr.iloc[-1]
            
            # Convert ATR to pips (assuming 4-digit or 5-digit broker)
            # This is a simplified conversion - should be adjusted based on symbol
            point = 0.0001 if 'JPY' not in self.symbol else 0.01
            atr_pips = current_atr / point
            
            reasoning_parts = []
            violations = []
            confidence = 1.0  # Start with full confidence, reduce for violations
            
            # Check spread
            if current_spread > self.max_spread_pips:
                violations.append(f"Spread too high ({current_spread:.1f} pips > {self.max_spread_pips} pips)")
                confidence -= 0.4
            else:
                reasoning_parts.append(f"Spread acceptable ({current_spread:.1f} pips)")
            
            # Check ATR
            if atr_pips < self.min_atr_pips:
                violations.append(f"ATR too low ({atr_pips:.1f} pips < {self.min_atr_pips} pips)")
                confidence -= 0.4
            else:
                reasoning_parts.append(f"ATR acceptable ({atr_pips:.1f} pips)")
            
            # Check open positions
            if open_positions >= self.max_open_positions:
                violations.append(f"Too many open positions ({open_positions} >= {self.max_open_positions})")
                confidence -= 0.3
            else:
                reasoning_parts.append(f"Position count OK ({open_positions}/{self.max_open_positions})")
            
            # Calculate volatility (price change percentage)
            if len(data) >= 20:
                recent_high = data['high'].iloc[-20:].max()
                recent_low = data['low'].iloc[-20:].min()
                volatility_pct = ((recent_high - recent_low) / recent_low) * 100
                
                reasoning_parts.append(f"20-bar volatility: {volatility_pct:.2f}%")
                
                # Check for extreme volatility
                if volatility_pct > 10.0:
                    violations.append(f"Extreme volatility ({volatility_pct:.2f}%)")
                    confidence -= 0.2
            
            # Ensure confidence is in valid range
            confidence = max(0.0, min(1.0, confidence))
            
            # Determine direction based on whether conditions are met
            if confidence >= 0.6:
                direction = SignalDirection.BUY  # Neutral positive signal - allows trading
                reasoning = "Trading conditions acceptable: " + "; ".join(reasoning_parts)
            else:
                direction = SignalDirection.WAIT
                reasoning = "Trading conditions not met: " + "; ".join(violations)
            
            metadata = {
                'atr_pips': float(atr_pips),
                'spread_pips': float(current_spread),
                'open_positions': open_positions,
                'violations': violations
            }
            
            return self.create_signal(direction, confidence, reasoning, metadata)
            
        except Exception as e:
            logger.error(f"Error in StatisticalAgent analysis: {e}")
            return self.create_signal(
                SignalDirection.WAIT,
                0.0,
                f"Analysis error: {str(e)}"
            )

    def check_correlation(self, symbol1_data: pd.DataFrame, symbol2_data: pd.DataFrame, window: int = 20) -> float:
        """
        Check correlation between two symbols.
        
        Args:
            symbol1_data: DataFrame for first symbol
            symbol2_data: DataFrame for second symbol
            window: Rolling window for correlation
            
        Returns:
            Correlation coefficient
        """
        if len(symbol1_data) < window or len(symbol2_data) < window:
            return 0.0
        
        # Align data by index
        combined = pd.DataFrame({
            'symbol1': symbol1_data['close'],
            'symbol2': symbol2_data['close']
        }).dropna()
        
        if len(combined) < window:
            return 0.0
        
        correlation = combined['symbol1'].tail(window).corr(combined['symbol2'].tail(window))
        return correlation

    def calculate_risk_metrics(self, data: pd.DataFrame) -> dict:
        """
        Calculate various risk metrics.
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            Dictionary with risk metrics
        """
        if len(data) < 20:
            return {}
        
        # Calculate ATR
        atr = self.calculate_atr(data, self.atr_period)
        
        # Calculate volatility
        returns = data['close'].pct_change().dropna()
        volatility = returns.std() * 100  # Percentage
        
        # Calculate average candle size
        candle_sizes = (data['high'] - data['low']).tail(20)
        avg_candle_size = candle_sizes.mean()
        
        return {
            'atr': float(atr.iloc[-1]),
            'volatility_pct': float(volatility),
            'avg_candle_size': float(avg_candle_size),
            'current_price': float(data['close'].iloc[-1])
        }
