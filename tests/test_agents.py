"""Tests for trading agents."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.trend_agent import TrendAgent
from agents.smc_agent import SMCAgent
from agents.statistical_agent import StatisticalAgent
from agents.wave_agent import WaveAgent
from data.models import SignalDirection


@pytest.fixture
def sample_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=250, freq='H')
    
    # Generate realistic price data
    np.random.seed(42)
    close = 1.1000 + np.cumsum(np.random.randn(250) * 0.0001)
    
    data = pd.DataFrame({
        'open': close + np.random.randn(250) * 0.0001,
        'high': close + abs(np.random.randn(250) * 0.0002),
        'low': close - abs(np.random.randn(250) * 0.0002),
        'close': close,
        'volume': np.random.randint(1000, 10000, 250)
    }, index=dates)
    
    return data


class TestTrendAgent:
    """Test cases for TrendAgent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = TrendAgent(symbol="EURUSD", timeframe="H1")
        assert agent.name == "TrendAgent"
        assert agent.symbol == "EURUSD"
        assert agent.timeframe == "H1"
    
    def test_analyze_with_valid_data(self, sample_data):
        """Test analysis with valid data."""
        agent = TrendAgent(symbol="EURUSD", timeframe="H1")
        signal = agent.analyze(sample_data)
        
        assert signal is not None
        assert signal.agent_name == "TrendAgent"
        assert signal.symbol == "EURUSD"
        assert signal.direction in [SignalDirection.BUY, SignalDirection.SELL, SignalDirection.WAIT]
        assert 0.0 <= signal.confidence <= 1.0
    
    def test_analyze_with_insufficient_data(self):
        """Test analysis with insufficient data."""
        agent = TrendAgent(symbol="EURUSD", timeframe="H1")
        insufficient_data = pd.DataFrame({
            'open': [1.1],
            'high': [1.1001],
            'low': [1.0999],
            'close': [1.1]
        })
        
        signal = agent.analyze(insufficient_data)
        assert signal.direction == SignalDirection.WAIT
        assert signal.confidence == 0.0


class TestSMCAgent:
    """Test cases for SMCAgent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = SMCAgent(symbol="EURUSD", timeframe="H1")
        assert agent.name == "SMCAgent"
        assert agent.symbol == "EURUSD"
    
    def test_analyze_with_valid_data(self, sample_data):
        """Test analysis with valid data."""
        agent = SMCAgent(symbol="EURUSD", timeframe="H1")
        signal = agent.analyze(sample_data)
        
        assert signal is not None
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.metadata is not None


class TestStatisticalAgent:
    """Test cases for StatisticalAgent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = StatisticalAgent(symbol="EURUSD", timeframe="H1")
        assert agent.name == "StatisticalAgent"
    
    def test_analyze_with_valid_conditions(self, sample_data):
        """Test analysis with valid trading conditions."""
        agent = StatisticalAgent(symbol="EURUSD", timeframe="H1")
        signal = agent.analyze(sample_data, current_spread=1.5, open_positions=2)
        
        assert signal is not None
        assert 0.0 <= signal.confidence <= 1.0
    
    def test_analyze_with_high_spread(self, sample_data):
        """Test analysis with high spread."""
        agent = StatisticalAgent(symbol="EURUSD", timeframe="H1", max_spread_pips=2.0)
        signal = agent.analyze(sample_data, current_spread=3.0, open_positions=0)
        
        # Should have lower confidence or WAIT signal
        assert signal.confidence < 1.0


class TestWaveAgent:
    """Test cases for WaveAgent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = WaveAgent(symbol="EURUSD", timeframe="H1")
        assert agent.name == "WaveAgent"
    
    def test_analyze_with_valid_data(self, sample_data):
        """Test analysis with valid data."""
        agent = WaveAgent(symbol="EURUSD", timeframe="H1")
        signal = agent.analyze(sample_data)
        
        assert signal is not None
        assert 0.0 <= signal.confidence <= 1.0
        assert 'current_phase' in signal.metadata


class TestBaseAgent:
    """Test cases for BaseAgent helper methods."""
    
    def test_calculate_ema(self, sample_data):
        """Test EMA calculation."""
        agent = TrendAgent(symbol="EURUSD", timeframe="H1")
        ema = agent.calculate_ema(sample_data, period=20)
        
        assert len(ema) == len(sample_data)
        assert not ema.isna().all()
    
    def test_calculate_atr(self, sample_data):
        """Test ATR calculation."""
        agent = TrendAgent(symbol="EURUSD", timeframe="H1")
        atr = agent.calculate_atr(sample_data, period=14)
        
        assert len(atr) == len(sample_data)
        assert atr.iloc[-1] > 0
    
    def test_calculate_rsi(self, sample_data):
        """Test RSI calculation."""
        agent = TrendAgent(symbol="EURUSD", timeframe="H1")
        rsi = agent.calculate_rsi(sample_data, period=14)
        
        assert len(rsi) == len(sample_data)
        # RSI should be between 0 and 100
        assert (rsi.dropna() >= 0).all() and (rsi.dropna() <= 100).all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
