"""Abstract base class for all trading agents."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import pandas as pd
import logging

from data.models import AgentSignal, SignalDirection

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all trading agents."""

    def __init__(self, name: str, symbol: str, timeframe: str = "H1", weight: float = 0.2):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            weight: Agent weight in meta-agent calculations
        """
        self.name = name
        self.symbol = symbol
        self.timeframe = timeframe
        self.weight = weight
        logger.info(f"Initialized {name} for {symbol} on {timeframe}")

    @abstractmethod
    def analyze(self, data: pd.DataFrame) -> AgentSignal:
        """
        Analyze market data and generate a trading signal.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            AgentSignal with direction, confidence, and reasoning
        """
        pass

    def create_signal(
        self,
        direction: SignalDirection,
        confidence: float,
        reasoning: str,
        metadata: Optional[dict] = None
    ) -> AgentSignal:
        """
        Create an agent signal.
        
        Args:
            direction: Signal direction (BUY, SELL, WAIT)
            confidence: Confidence level (0.0 to 1.0)
            reasoning: Explanation for the signal
            metadata: Additional metadata
            
        Returns:
            AgentSignal object
        """
        return AgentSignal(
            agent_name=self.name,
            symbol=self.symbol,
            direction=direction,
            confidence=confidence,
            reasoning=reasoning,
            timestamp=datetime.now(),
            metadata=metadata
        )

    def calculate_ema(self, data: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            data: DataFrame with price data
            period: EMA period
            column: Column to calculate EMA on
            
        Returns:
            Series with EMA values
        """
        return data[column].ewm(span=period, adjust=False).mean()

    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range.
        
        Args:
            data: DataFrame with OHLC data
            period: ATR period
            
        Returns:
            Series with ATR values
        """
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr

    def calculate_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average Directional Index.
        
        Args:
            data: DataFrame with OHLC data
            period: ADX period
            
        Returns:
            Series with ADX values
        """
        # Calculate +DM and -DM
        high_diff = data['high'].diff()
        low_diff = -data['low'].diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        # Calculate ATR
        atr = self.calculate_atr(data, period)
        
        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx

    def calculate_rsi(self, data: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """
        Calculate Relative Strength Index.
        
        Args:
            data: DataFrame with price data
            period: RSI period
            column: Column to calculate RSI on
            
        Returns:
            Series with RSI values
        """
        delta = data[column].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    def validate_data(self, data: pd.DataFrame, min_bars: int = 200) -> bool:
        """
        Validate that we have sufficient data for analysis.
        
        Args:
            data: DataFrame to validate
            min_bars: Minimum number of bars required
            
        Returns:
            True if data is valid
        """
        if data is None or len(data) < min_bars:
            logger.warning(f"{self.name}: Insufficient data ({len(data) if data is not None else 0} bars)")
            return False
        
        required_columns = {'open', 'high', 'low', 'close'}
        if not required_columns.issubset(data.columns):
            logger.warning(f"{self.name}: Missing required columns")
            return False
        
        return True
