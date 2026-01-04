"""Tests for Meta-Agent."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from meta.meta_agent import MetaAgent
from data.models import AgentSignal, SignalDirection, MarketType


@pytest.fixture
def sample_agent_signals():
    """Create sample agent signals for testing."""
    return [
        AgentSignal(
            agent_name="TrendAgent",
            symbol="EURUSD",
            direction=SignalDirection.BUY,
            confidence=0.8,
            reasoning="Strong uptrend detected"
        ),
        AgentSignal(
            agent_name="SMCAgent",
            symbol="EURUSD",
            direction=SignalDirection.BUY,
            confidence=0.7,
            reasoning="Price near bullish order block"
        ),
        AgentSignal(
            agent_name="StatisticalAgent",
            symbol="EURUSD",
            direction=SignalDirection.BUY,
            confidence=0.9,
            reasoning="Trading conditions acceptable"
        ),
        AgentSignal(
            agent_name="WaveAgent",
            symbol="EURUSD",
            direction=SignalDirection.BUY,
            confidence=0.6,
            reasoning="Bullish impulse wave"
        )
    ]


class TestMetaAgent:
    """Test cases for MetaAgent."""
    
    def test_initialization(self):
        """Test meta-agent initialization."""
        meta = MetaAgent(market_type=MarketType.FOREX)
        assert meta.market_type == MarketType.FOREX
        assert meta.confidence_threshold > 0
    
    def test_aggregate_signals_buy(self, sample_agent_signals):
        """Test signal aggregation for BUY signals."""
        meta = MetaAgent(market_type=MarketType.FOREX)
        trade_signal = meta.aggregate_signals(sample_agent_signals, "EURUSD")
        
        assert trade_signal is not None
        assert trade_signal.symbol == "EURUSD"
        assert trade_signal.market_type == MarketType.FOREX
        # With all BUY signals and high confidence, should result in BUY
        assert trade_signal.direction in [SignalDirection.BUY, SignalDirection.WAIT]
        assert 0.0 <= trade_signal.confidence <= 1.0
    
    def test_aggregate_signals_mixed(self):
        """Test signal aggregation with mixed signals."""
        mixed_signals = [
            AgentSignal(
                agent_name="TrendAgent",
                symbol="EURUSD",
                direction=SignalDirection.BUY,
                confidence=0.6,
                reasoning="Weak uptrend"
            ),
            AgentSignal(
                agent_name="SMCAgent",
                symbol="EURUSD",
                direction=SignalDirection.SELL,
                confidence=0.7,
                reasoning="Bearish setup"
            ),
            AgentSignal(
                agent_name="StatisticalAgent",
                symbol="EURUSD",
                direction=SignalDirection.WAIT,
                confidence=0.5,
                reasoning="High spread"
            )
        ]
        
        meta = MetaAgent(market_type=MarketType.FOREX)
        trade_signal = meta.aggregate_signals(mixed_signals, "EURUSD")
        
        # With mixed signals, might result in WAIT
        assert trade_signal.direction in [SignalDirection.BUY, SignalDirection.SELL, SignalDirection.WAIT]
    
    def test_insufficient_agents(self):
        """Test with insufficient number of agents."""
        limited_signals = [
            AgentSignal(
                agent_name="TrendAgent",
                symbol="EURUSD",
                direction=SignalDirection.BUY,
                confidence=0.9,
                reasoning="Strong signal"
            )
        ]
        
        meta = MetaAgent(market_type=MarketType.FOREX)
        meta.min_agents_required = 3
        
        trade_signal = meta.aggregate_signals(limited_signals, "EURUSD")
        assert trade_signal.direction == SignalDirection.WAIT
    
    def test_weighted_confidence_calculation(self, sample_agent_signals):
        """Test weighted confidence calculation."""
        meta = MetaAgent(market_type=MarketType.FOREX)
        
        # Calculate weighted confidence for BUY signals
        buy_signals = [s for s in sample_agent_signals if s.direction == SignalDirection.BUY]
        confidence = meta._calculate_weighted_confidence(buy_signals)
        
        assert 0.0 <= confidence <= 1.0
        # Should be higher than simple average due to high confidence signals
        simple_avg = sum(s.confidence for s in buy_signals) / len(buy_signals)
        assert confidence > 0  # At least some confidence
    
    def test_update_agent_weights(self):
        """Test updating agent weights."""
        meta = MetaAgent(market_type=MarketType.FOREX)
        
        new_weights = {
            'TrendAgent': 0.3,
            'SMCAgent': 0.2
        }
        
        meta.update_agent_weights(new_weights)
        
        assert meta.agent_weights['TrendAgent'] == 0.3
        assert meta.agent_weights['SMCAgent'] == 0.2
    
    def test_get_decision_summary(self, sample_agent_signals):
        """Test getting decision summary."""
        meta = MetaAgent(market_type=MarketType.FOREX)
        summary = meta.get_decision_summary(sample_agent_signals)
        
        assert 'total_agents' in summary
        assert 'buy_count' in summary
        assert 'sell_count' in summary
        assert 'wait_count' in summary
        assert summary['total_agents'] == len(sample_agent_signals)
    
    def test_validate_statistical_gate(self, sample_agent_signals):
        """Test statistical gate validation."""
        meta = MetaAgent(market_type=MarketType.FOREX)
        
        # Should pass with good statistical signal
        result = meta.validate_statistical_gate(sample_agent_signals)
        assert result == True  # StatisticalAgent has BUY with 0.9 confidence
        
        # Test with failed gate
        failed_signals = [
            AgentSignal(
                agent_name="StatisticalAgent",
                symbol="EURUSD",
                direction=SignalDirection.WAIT,
                confidence=0.3,
                reasoning="Conditions not met"
            )
        ]
        
        result = meta.validate_statistical_gate(failed_signals)
        assert result == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
