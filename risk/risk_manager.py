"""Risk Manager for position sizing and risk control."""

from typing import Optional, Dict, List
import logging
import yaml
from datetime import datetime, timedelta

from data.models import Trade, TradeSignal, TradeStatus
from data.database import DatabaseHandler

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages risk, position sizing, and drawdown protection."""

    def __init__(
        self,
        account_balance: float,
        config_path: str = "config/settings.yaml"
    ):
        """
        Initialize Risk Manager.
        
        Args:
            account_balance: Current account balance
            config_path: Path to configuration file
        """
        self.account_balance = account_balance
        self.config = self._load_config(config_path)
        self.db_handler = DatabaseHandler()
        
        # Get risk parameters from config
        risk_config = self.config.get('risk_management', {})
        self.max_daily_loss_percent = risk_config.get('max_daily_loss_percent', 2.0)
        self.max_position_size_percent = risk_config.get('max_position_size_percent', 1.0)
        self.max_concurrent_trades = risk_config.get('max_concurrent_trades', 5)
        self.max_correlation = risk_config.get('max_correlation', 0.7)
        self.enable_drawdown_protection = risk_config.get('enable_drawdown_protection', True)
        self.max_drawdown_percent = risk_config.get('max_drawdown_percent', 10.0)
        
        logger.info(f"RiskManager initialized with balance ${account_balance}")

    def _load_config(self, config_path: str) -> dict:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        risk_percent: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_percent: Risk percentage (overrides default)
            
        Returns:
            Position size in lots
        """
        if risk_percent is None:
            risk_percent = self.max_position_size_percent
        
        # Calculate risk amount in account currency
        risk_amount = self.account_balance * (risk_percent / 100)
        
        # Calculate distance to stop loss
        price_difference = abs(entry_price - stop_loss)
        
        if price_difference == 0:
            logger.warning("Stop loss equals entry price, returning minimum position size")
            return 0.01
        
        # Calculate position size
        # This is simplified - should be adjusted based on symbol specifications
        pip_value = self._get_pip_value(symbol)
        position_size = risk_amount / (price_difference / pip_value)
        
        # Round to appropriate lot size
        position_size = round(position_size, 2)
        
        # Apply minimum and maximum limits
        position_size = max(0.01, min(position_size, 100.0))
        
        logger.info(f"Calculated position size for {symbol}: {position_size} lots")
        return position_size

    def _get_pip_value(self, symbol: str) -> float:
        """
        Get pip value for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Pip value
        """
        # Simplified pip value calculation
        if 'JPY' in symbol:
            return 0.01
        else:
            return 0.0001

    def validate_trade(
        self,
        trade_signal: TradeSignal,
        current_spread: float = 0.0
    ) -> Dict[str, any]:
        """
        Validate if trade meets risk management criteria.
        
        Args:
            trade_signal: Trade signal to validate
            current_spread: Current spread in pips
            
        Returns:
            Dictionary with validation result
        """
        violations = []
        
        # Check daily loss limit
        if self._check_daily_loss_limit():
            violations.append("Daily loss limit reached")
        
        # Check concurrent trades limit
        open_trades = self._get_open_trades_count()
        if open_trades >= self.max_concurrent_trades:
            violations.append(f"Max concurrent trades reached ({open_trades}/{self.max_concurrent_trades})")
        
        # Check if symbol already has open position
        if self._has_open_position(trade_signal.symbol):
            violations.append(f"Symbol {trade_signal.symbol} already has open position")
        
        # Check drawdown protection
        if self.enable_drawdown_protection and self._check_drawdown_limit():
            violations.append("Drawdown limit reached")
        
        # Check spread (if provided)
        # This would need market-specific limits from config
        
        is_valid = len(violations) == 0
        
        return {
            'is_valid': is_valid,
            'violations': violations,
            'open_trades_count': open_trades,
            'message': ' | '.join(violations) if violations else 'Trade validated'
        }

    def _check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been reached.
        
        Returns:
            True if limit reached
        """
        try:
            # Get today's trades
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            all_trades = self.db_handler.get_trades(status=TradeStatus.CLOSED)
            
            today_trades = [
                t for t in all_trades
                if t.exit_time and t.exit_time >= today_start
            ]
            
            # Calculate today's P&L
            today_pnl = sum(t.profit_loss for t in today_trades if t.profit_loss is not None)
            
            # Calculate loss percentage
            loss_percent = abs(today_pnl / self.account_balance * 100) if today_pnl < 0 else 0.0
            
            if loss_percent >= self.max_daily_loss_percent:
                logger.warning(f"Daily loss limit reached: {loss_percent:.2f}%")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            return False

    def _check_drawdown_limit(self) -> bool:
        """
        Check if drawdown limit has been reached.
        
        Returns:
            True if limit reached
        """
        try:
            # Get all closed trades
            all_trades = self.db_handler.get_trades(status=TradeStatus.CLOSED)
            
            if not all_trades:
                return False
            
            # Calculate cumulative P&L and max drawdown
            cumulative_pnl = 0.0
            peak = 0.0
            max_drawdown = 0.0
            
            for trade in all_trades:
                if trade.profit_loss is not None:
                    cumulative_pnl += trade.profit_loss
                    peak = max(peak, cumulative_pnl)
                    drawdown = peak - cumulative_pnl
                    max_drawdown = max(max_drawdown, drawdown)
            
            # Calculate drawdown percentage
            drawdown_percent = (max_drawdown / self.account_balance) * 100
            
            if drawdown_percent >= self.max_drawdown_percent:
                logger.warning(f"Drawdown limit reached: {drawdown_percent:.2f}%")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking drawdown limit: {e}")
            return False

    def _get_open_trades_count(self) -> int:
        """
        Get count of open trades.
        
        Returns:
            Number of open trades
        """
        try:
            open_trades = self.db_handler.get_trades(status=TradeStatus.OPEN)
            return len(open_trades)
        except Exception as e:
            logger.error(f"Error getting open trades count: {e}")
            return 0

    def _has_open_position(self, symbol: str) -> bool:
        """
        Check if symbol already has an open position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if open position exists
        """
        try:
            open_trades = self.db_handler.get_trades(symbol=symbol, status=TradeStatus.OPEN)
            return len(open_trades) > 0
        except Exception as e:
            logger.error(f"Error checking open position: {e}")
            return False

    def calculate_stop_loss_take_profit(
        self,
        entry_price: float,
        direction: str,
        atr: float,
        sl_multiplier: float = 2.0,
        tp_multiplier: float = 3.0
    ) -> Dict[str, float]:
        """
        Calculate stop loss and take profit levels.
        
        Args:
            entry_price: Entry price
            direction: Trade direction (BUY/SELL)
            atr: Average True Range value
            sl_multiplier: Stop loss ATR multiplier
            tp_multiplier: Take profit ATR multiplier
            
        Returns:
            Dictionary with stop_loss and take_profit
        """
        sl_distance = atr * sl_multiplier
        tp_distance = atr * tp_multiplier
        
        if direction == "BUY":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:  # SELL
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance
        
        return {
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'risk_reward_ratio': tp_multiplier / sl_multiplier
        }

    def update_account_balance(self, new_balance: float) -> None:
        """
        Update account balance.
        
        Args:
            new_balance: New account balance
        """
        old_balance = self.account_balance
        self.account_balance = new_balance
        logger.info(f"Account balance updated: ${old_balance:.2f} -> ${new_balance:.2f}")

    def get_risk_metrics(self) -> Dict:
        """
        Get current risk metrics.
        
        Returns:
            Dictionary with risk metrics
        """
        try:
            all_trades = self.db_handler.get_trades(status=TradeStatus.CLOSED)
            
            total_trades = len(all_trades)
            winning_trades = len([t for t in all_trades if t.is_winner])
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            
            # Calculate total P&L
            total_pnl = sum(t.profit_loss for t in all_trades if t.profit_loss is not None)
            
            # Calculate max drawdown
            cumulative_pnl = 0.0
            peak = 0.0
            max_drawdown = 0.0
            
            for trade in all_trades:
                if trade.profit_loss is not None:
                    cumulative_pnl += trade.profit_loss
                    peak = max(peak, cumulative_pnl)
                    drawdown = peak - cumulative_pnl
                    max_drawdown = max(max_drawdown, drawdown)
            
            return {
                'account_balance': self.account_balance,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'max_drawdown': max_drawdown,
                'max_drawdown_percent': (max_drawdown / self.account_balance * 100) if self.account_balance > 0 else 0.0,
                'open_trades': self._get_open_trades_count(),
                'daily_loss_limit': self.max_daily_loss_percent,
                'max_concurrent_trades': self.max_concurrent_trades
            }
        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return {}
