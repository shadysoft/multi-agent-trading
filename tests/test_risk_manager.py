"""Tests for Risk Manager."""

import pytest
from datetime import datetime

from risk.risk_manager import RiskManager
from data.models import TradeSignal, SignalDirection, MarketType


@pytest.fixture
def risk_manager():
    """Create a risk manager instance for testing."""
    return RiskManager(account_balance=10000.0)


class TestRiskManager:
    """Test cases for RiskManager."""
    
    def test_initialization(self, risk_manager):
        """Test risk manager initialization."""
        assert risk_manager.account_balance == 10000.0
        assert risk_manager.max_daily_loss_percent > 0
        assert risk_manager.max_concurrent_trades > 0
    
    def test_calculate_position_size(self, risk_manager):
        """Test position size calculation."""
        position_size = risk_manager.calculate_position_size(
            symbol="EURUSD",
            entry_price=1.1000,
            stop_loss=1.0980,
            risk_percent=1.0
        )
        
        assert position_size > 0
        assert position_size >= 0.01  # Minimum lot size
    
    def test_calculate_position_size_zero_distance(self, risk_manager):
        """Test position size with zero SL distance."""
        position_size = risk_manager.calculate_position_size(
            symbol="EURUSD",
            entry_price=1.1000,
            stop_loss=1.1000,  # Same as entry
            risk_percent=1.0
        )
        
        # Should return minimum position size
        assert position_size == 0.01
    
    def test_validate_trade_success(self, risk_manager):
        """Test trade validation with valid conditions."""
        trade_signal = TradeSignal(
            symbol="EURUSD",
            market_type=MarketType.FOREX,
            direction=SignalDirection.BUY,
            confidence=0.8,
            agent_signals=[],
            reasoning="Test signal"
        )
        
        validation = risk_manager.validate_trade(trade_signal, current_spread=1.5)
        
        # Should pass validation with default conditions
        assert 'is_valid' in validation
        assert 'violations' in validation
    
    def test_calculate_stop_loss_take_profit_buy(self, risk_manager):
        """Test SL/TP calculation for BUY order."""
        result = risk_manager.calculate_stop_loss_take_profit(
            entry_price=1.1000,
            direction="BUY",
            atr=0.0020,
            sl_multiplier=2.0,
            tp_multiplier=3.0
        )
        
        assert 'stop_loss' in result
        assert 'take_profit' in result
        assert 'risk_reward_ratio' in result
        
        # For BUY: SL should be below entry, TP should be above
        assert result['stop_loss'] < 1.1000
        assert result['take_profit'] > 1.1000
        assert result['risk_reward_ratio'] == 1.5  # 3.0 / 2.0
    
    def test_calculate_stop_loss_take_profit_sell(self, risk_manager):
        """Test SL/TP calculation for SELL order."""
        result = risk_manager.calculate_stop_loss_take_profit(
            entry_price=1.1000,
            direction="SELL",
            atr=0.0020,
            sl_multiplier=2.0,
            tp_multiplier=3.0
        )
        
        # For SELL: SL should be above entry, TP should be below
        assert result['stop_loss'] > 1.1000
        assert result['take_profit'] < 1.1000
    
    def test_update_account_balance(self, risk_manager):
        """Test account balance update."""
        risk_manager.update_account_balance(12000.0)
        assert risk_manager.account_balance == 12000.0
    
    def test_get_risk_metrics(self, risk_manager):
        """Test getting risk metrics."""
        metrics = risk_manager.get_risk_metrics()
        
        assert 'account_balance' in metrics
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics
        assert metrics['account_balance'] == 10000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
