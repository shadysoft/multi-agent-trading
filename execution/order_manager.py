"""Order Manager for handling order execution and management (SL, TP, BE, Trailing)."""

import logging
from typing import Optional, Dict
from datetime import datetime
import time

from .mt5_connector import MT5Connector
from data.models import TradeSignal, Trade, TradeStatus, MarketType
from data.database import DatabaseHandler
from risk.risk_manager import RiskManager

logger = logging.getLogger(__name__)


class OrderManager:
    """Manages order execution and position management."""

    def __init__(
        self,
        mt5_connector: MT5Connector,
        risk_manager: RiskManager,
        db_handler: DatabaseHandler
    ):
        """
        Initialize Order Manager.
        
        Args:
            mt5_connector: MT5 connector instance
            risk_manager: Risk manager instance
            db_handler: Database handler instance
        """
        self.mt5 = mt5_connector
        self.risk_manager = risk_manager
        self.db_handler = db_handler
        logger.info("OrderManager initialized")

    def execute_trade(self, trade_signal: TradeSignal, config: Dict) -> Optional[Trade]:
        """
        Execute a trade based on signal.
        
        Args:
            trade_signal: Trade signal from meta-agent
            config: Market configuration
            
        Returns:
            Trade object if successful
        """
        try:
            # Validate trade with risk manager
            validation = self.risk_manager.validate_trade(trade_signal)
            if not validation['is_valid']:
                logger.warning(f"Trade validation failed: {validation['message']}")
                return None
            
            # Get current price from MT5
            symbol = trade_signal.symbol
            tick_info = self.mt5.mt5_connector.get_current_price(symbol) if hasattr(self.mt5, 'mt5_connector') else None
            
            # For now, use signal entry price if available
            if trade_signal.entry_price:
                entry_price = trade_signal.entry_price
            else:
                # Would get from MT5 tick
                logger.warning("No entry price in signal")
                return None
            
            # Calculate SL/TP if not provided in signal
            if trade_signal.stop_loss is None or trade_signal.take_profit is None:
                # Get ATR from market data (simplified here)
                atr = 0.001  # Placeholder - should calculate from actual data
                
                position_config = config.get('position_management', {})
                sl_multiplier = position_config.get('sl_atr_multiplier', 2.0)
                tp_multiplier = position_config.get('tp_atr_multiplier', 3.0)
                
                sl_tp = self.risk_manager.calculate_stop_loss_take_profit(
                    entry_price,
                    trade_signal.direction.value,
                    atr,
                    sl_multiplier,
                    tp_multiplier
                )
                
                stop_loss = sl_tp['stop_loss']
                take_profit = sl_tp['take_profit']
            else:
                stop_loss = trade_signal.stop_loss
                take_profit = trade_signal.take_profit
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                symbol,
                entry_price,
                stop_loss
            )
            
            # Send order to MT5
            order_result = self.mt5.send_order(
                symbol=symbol,
                order_type=trade_signal.direction.value,
                volume=position_size,
                price=entry_price,
                sl=stop_loss,
                tp=take_profit,
                comment=f"Multi-Agent System: {trade_signal.confidence:.2%}"
            )
            
            if order_result is None or not order_result.get('success'):
                logger.error(f"Failed to send order for {symbol}")
                return None
            
            # Create Trade object
            trade = Trade(
                symbol=symbol,
                market_type=trade_signal.market_type,
                direction=trade_signal.direction,
                entry_price=order_result['price'],
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                entry_time=datetime.now(),
                status=TradeStatus.OPEN,
                confidence=trade_signal.confidence,
                reasoning=trade_signal.reasoning,
                metadata={
                    'order_ticket': order_result.get('order'),
                    'agent_signals': [s.dict() for s in trade_signal.agent_signals]
                }
            )
            
            # Save to database
            self.db_handler.save_trade(trade)
            
            logger.info(f"Trade executed: {symbol} {trade_signal.direction.value} {position_size} lots")
            return trade
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None

    def manage_positions(self, config: Dict) -> None:
        """
        Manage open positions (breakeven, trailing stop, etc.).
        
        Args:
            config: Market configuration
        """
        try:
            # Get open positions from MT5
            positions = self.mt5.get_positions()
            
            for position in positions:
                try:
                    self._manage_single_position(position, config)
                except Exception as e:
                    logger.error(f"Error managing position {position['ticket']}: {e}")
            
        except Exception as e:
            logger.error(f"Error managing positions: {e}")

    def _manage_single_position(self, position: Dict, config: Dict) -> None:
        """
        Manage a single position.
        
        Args:
            position: Position data from MT5
            config: Market configuration
        """
        position_config = config.get('position_management', {})
        
        # Check for breakeven
        if position_config.get('enable_breakeven', False):
            self._check_breakeven(position, position_config)
        
        # Check for trailing stop
        if position_config.get('enable_trailing_stop', False):
            self._check_trailing_stop(position, position_config)

    def _check_breakeven(self, position: Dict, config: Dict) -> None:
        """
        Check and move SL to breakeven if conditions met.
        
        Args:
            position: Position data
            config: Position management config
        """
        try:
            entry_price = position['price_open']
            current_price = position['price_current']
            current_sl = position['sl']
            
            # Calculate ATR (placeholder - should get from market data)
            atr = abs(entry_price - current_sl) / config.get('sl_atr_multiplier', 2.0)
            
            breakeven_trigger = atr * config.get('breakeven_trigger_atr', 1.0)
            
            # Check if price has moved enough
            if position['type'] == 'BUY':
                if current_price >= entry_price + breakeven_trigger:
                    # Move SL to breakeven (entry + small buffer)
                    new_sl = entry_price + (atr * 0.1)  # Small buffer
                    if new_sl > current_sl:
                        self.mt5.modify_position(position['ticket'], sl=new_sl)
                        logger.info(f"Position {position['ticket']} moved to breakeven")
            else:  # SELL
                if current_price <= entry_price - breakeven_trigger:
                    # Move SL to breakeven
                    new_sl = entry_price - (atr * 0.1)
                    if new_sl < current_sl:
                        self.mt5.modify_position(position['ticket'], sl=new_sl)
                        logger.info(f"Position {position['ticket']} moved to breakeven")
        
        except Exception as e:
            logger.error(f"Error checking breakeven: {e}")

    def _check_trailing_stop(self, position: Dict, config: Dict) -> None:
        """
        Check and update trailing stop if needed.
        
        Args:
            position: Position data
            config: Position management config
        """
        try:
            entry_price = position['price_open']
            current_price = position['price_current']
            current_sl = position['sl']
            
            # Calculate ATR (placeholder)
            atr = abs(entry_price - current_sl) / config.get('sl_atr_multiplier', 2.0)
            
            trailing_distance = atr * config.get('trailing_stop_atr', 1.5)
            
            # Update trailing stop
            if position['type'] == 'BUY':
                new_sl = current_price - trailing_distance
                if new_sl > current_sl:
                    self.mt5.modify_position(position['ticket'], sl=new_sl)
                    logger.info(f"Trailing stop updated for position {position['ticket']}")
            else:  # SELL
                new_sl = current_price + trailing_distance
                if new_sl < current_sl or current_sl == 0:
                    self.mt5.modify_position(position['ticket'], sl=new_sl)
                    logger.info(f"Trailing stop updated for position {position['ticket']}")
        
        except Exception as e:
            logger.error(f"Error checking trailing stop: {e}")

    def close_trade(self, trade: Trade) -> bool:
        """
        Close a trade.
        
        Args:
            trade: Trade to close
            
        Returns:
            True if successful
        """
        try:
            if trade.metadata and 'order_ticket' in trade.metadata:
                ticket = trade.metadata['order_ticket']
                
                if self.mt5.close_position(ticket):
                    # Update trade in database
                    trade.status = TradeStatus.CLOSED
                    trade.exit_time = datetime.now()
                    
                    # Get final position info to calculate P&L
                    # This is simplified - would get actual exit price from MT5
                    trade.exit_price = trade.take_profit  # Placeholder
                    
                    # Calculate P&L (simplified)
                    if trade.direction.value == 'BUY':
                        trade.profit_loss = (trade.exit_price - trade.entry_price) * trade.position_size * 100000
                    else:
                        trade.profit_loss = (trade.entry_price - trade.exit_price) * trade.position_size * 100000
                    
                    self.db_handler.update_trade(trade)
                    logger.info(f"Trade {trade.id} closed with P&L: ${trade.profit_loss:.2f}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error closing trade: {e}")
            return False

    def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """
        Close all open positions.
        
        Args:
            symbol: Close only positions for this symbol (optional)
            
        Returns:
            Number of positions closed
        """
        try:
            positions = self.mt5.get_positions(symbol)
            closed_count = 0
            
            for position in positions:
                if self.mt5.close_position(position['ticket']):
                    closed_count += 1
            
            logger.info(f"Closed {closed_count} positions")
            return closed_count
            
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            return 0

    def sync_positions_with_database(self) -> None:
        """Synchronize MT5 positions with database."""
        try:
            # Get all open positions from MT5
            mt5_positions = self.mt5.get_positions()
            mt5_tickets = {pos['ticket'] for pos in mt5_positions}
            
            # Get all open trades from database
            db_trades = self.db_handler.get_trades(status=TradeStatus.OPEN)
            
            # Check for trades that are closed in MT5 but still open in DB
            for trade in db_trades:
                if trade.metadata and 'order_ticket' in trade.metadata:
                    ticket = trade.metadata['order_ticket']
                    
                    if ticket not in mt5_tickets:
                        # Position was closed in MT5, update database
                        logger.info(f"Syncing closed position {ticket}")
                        # This would need to fetch historical data to get exit price
                        # For now, just mark as closed
                        trade.status = TradeStatus.CLOSED
                        trade.exit_time = datetime.now()
                        self.db_handler.update_trade(trade)
            
            logger.info("Position synchronization complete")
            
        except Exception as e:
            logger.error(f"Error syncing positions: {e}")
