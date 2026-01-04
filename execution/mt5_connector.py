"""MetaTrader 5 Connector for Python-MT5 communication."""

import MetaTrader5 as mt5
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class MT5Connector:
    """Handles connection and communication with MetaTrader 5."""

    def __init__(self):
        """Initialize MT5 Connector."""
        self.initialized = False
        self.account_info = None

    def initialize(
        self,
        login: Optional[int] = None,
        password: Optional[str] = None,
        server: Optional[str] = None
    ) -> bool:
        """
        Initialize MT5 connection.
        
        Args:
            login: MT5 account number
            password: MT5 password
            server: MT5 server
            
        Returns:
            True if successful
        """
        try:
            # Get credentials from environment if not provided
            if login is None:
                login = int(os.getenv('MT5_LOGIN', '0'))
            if password is None:
                password = os.getenv('MT5_PASSWORD', '')
            if server is None:
                server = os.getenv('MT5_SERVER', '')
            
            # Initialize MT5
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Login if credentials provided
            if login and password and server:
                if not mt5.login(login, password, server):
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
            
            # Get account info
            self.account_info = mt5.account_info()
            if self.account_info is None:
                logger.warning("Could not get account info")
            else:
                logger.info(f"Connected to MT5 - Account: {self.account_info.login}, Balance: ${self.account_info.balance}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False

    def shutdown(self) -> None:
        """Shutdown MT5 connection."""
        if self.initialized:
            mt5.shutdown()
            self.initialized = False
            logger.info("MT5 connection closed")

    def get_account_info(self) -> Optional[Dict]:
        """
        Get account information.
        
        Returns:
            Dictionary with account info
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return None
        
        info = mt5.account_info()
        if info is None:
            logger.error(f"Failed to get account info: {mt5.last_error()}")
            return None
        
        return {
            'login': info.login,
            'balance': info.balance,
            'equity': info.equity,
            'margin': info.margin,
            'margin_free': info.margin_free,
            'margin_level': info.margin_level,
            'profit': info.profit,
            'currency': info.currency,
            'leverage': info.leverage
        }

    def send_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        deviation: int = 20,
        comment: str = ""
    ) -> Optional[Dict]:
        """
        Send order to MT5.
        
        Args:
            symbol: Trading symbol
            order_type: Order type (BUY, SELL)
            volume: Position size in lots
            price: Order price (None for market orders)
            sl: Stop loss price
            tp: Take profit price
            deviation: Maximum price deviation in points
            comment: Order comment
            
        Returns:
            Order result dictionary
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return None
        
        try:
            # Determine order type constant
            if order_type == "BUY":
                trade_type = mt5.ORDER_TYPE_BUY
                if price is None:
                    price = mt5.symbol_info_tick(symbol).ask
            elif order_type == "SELL":
                trade_type = mt5.ORDER_TYPE_SELL
                if price is None:
                    price = mt5.symbol_info_tick(symbol).bid
            else:
                logger.error(f"Invalid order type: {order_type}")
                return None
            
            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": trade_type,
                "price": price,
                "deviation": deviation,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add SL/TP if provided
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                logger.error(f"Order send failed: {mt5.last_error()}")
                return None
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.retcode} - {result.comment}")
                return {
                    'success': False,
                    'retcode': result.retcode,
                    'comment': result.comment
                }
            
            logger.info(f"Order executed: {symbol} {order_type} {volume} lots at {result.price}")
            
            return {
                'success': True,
                'order': result.order,
                'volume': result.volume,
                'price': result.price,
                'bid': result.bid,
                'ask': result.ask,
                'comment': result.comment
            }
            
        except Exception as e:
            logger.error(f"Error sending order: {e}")
            return None

    def close_position(self, ticket: int) -> bool:
        """
        Close position by ticket.
        
        Args:
            ticket: Position ticket number
            
        Returns:
            True if successful
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return False
        
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                logger.error(f"Position {ticket} not found")
                return False
            
            position = position[0]
            
            # Determine close order type
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Position closed",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Failed to close position {ticket}")
                return False
            
            logger.info(f"Position {ticket} closed at {result.price}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    def modify_position(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> bool:
        """
        Modify position SL/TP.
        
        Args:
            ticket: Position ticket number
            sl: New stop loss (None to keep current)
            tp: New take profit (None to keep current)
            
        Returns:
            True if successful
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return False
        
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                logger.error(f"Position {ticket} not found")
                return False
            
            position = position[0]
            
            # Use current values if not provided
            if sl is None:
                sl = position.sl
            if tp is None:
                tp = position.tp
            
            # Prepare modification request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": sl,
                "tp": tp,
                "magic": 234000,
            }
            
            # Send modification
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Failed to modify position {ticket}")
                return False
            
            logger.info(f"Position {ticket} modified - SL: {sl}, TP: {tp}")
            return True
            
        except Exception as e:
            logger.error(f"Error modifying position: {e}")
            return False

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open positions.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of positions
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return []
        
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'comment': pos.comment
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get pending orders.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of orders
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return []
        
        try:
            if symbol:
                orders = mt5.orders_get(symbol=symbol)
            else:
                orders = mt5.orders_get()
            
            if orders is None:
                return []
            
            result = []
            for order in orders:
                result.append({
                    'ticket': order.ticket,
                    'symbol': order.symbol,
                    'type': order.type,
                    'volume': order.volume,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'comment': order.comment
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
