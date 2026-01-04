"""Market data fetcher for retrieving price data from MT5."""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from .models import MarketData

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """Fetches market data from MetaTrader 5."""

    def __init__(self):
        """Initialize the market data fetcher."""
        self.initialized = False

    def initialize(self) -> bool:
        """Initialize MT5 connection."""
        if not mt5.initialize():
            logger.error(f"MT5 initialization failed: {mt5.last_error()}")
            return False
        
        self.initialized = True
        logger.info("MT5 initialized successfully")
        return True

    def shutdown(self) -> None:
        """Shutdown MT5 connection."""
        if self.initialized:
            mt5.shutdown()
            self.initialized = False
            logger.info("MT5 shutdown complete")

    def get_current_price(self, symbol: str) -> Optional[dict]:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with bid, ask, spread, etc.
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return None

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Failed to get tick for {symbol}: {mt5.last_error()}")
            return None

        return {
            'symbol': symbol,
            'bid': tick.bid,
            'ask': tick.ask,
            'spread': tick.ask - tick.bid,
            'time': datetime.fromtimestamp(tick.time),
            'volume': tick.volume
        }

    def get_bars(
        self,
        symbol: str,
        timeframe: str = "H1",
        count: int = 500,
        start_pos: int = 0
    ) -> Optional[pd.DataFrame]:
        """
        Get historical bars for a symbol.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M15, M30, H1, H4, D1)
            count: Number of bars to retrieve
            start_pos: Starting position
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return None

        # Map timeframe string to MT5 constant
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }

        tf = timeframe_map.get(timeframe)
        if tf is None:
            logger.error(f"Invalid timeframe: {timeframe}")
            return None

        # Get bars
        rates = mt5.copy_rates_from_pos(symbol, tf, start_pos, count)
        if rates is None or len(rates) == 0:
            logger.error(f"Failed to get bars for {symbol}: {mt5.last_error()}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        return df

    def get_bars_range(
        self,
        symbol: str,
        timeframe: str = "H1",
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Optional[pd.DataFrame]:
        """
        Get historical bars for a date range.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M15, M30, H1, H4, D1)
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return None

        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        # Map timeframe string to MT5 constant
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }

        tf = timeframe_map.get(timeframe)
        if tf is None:
            logger.error(f"Invalid timeframe: {timeframe}")
            return None

        # Get bars
        rates = mt5.copy_rates_range(symbol, tf, start_date, end_date)
        if rates is None or len(rates) == 0:
            logger.error(f"Failed to get bars for {symbol}: {mt5.last_error()}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        return df

    def get_symbols(self) -> List[str]:
        """
        Get list of available symbols.
        
        Returns:
            List of symbol names
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return []

        symbols = mt5.symbols_get()
        if symbols is None:
            logger.error(f"Failed to get symbols: {mt5.last_error()}")
            return []

        return [s.name for s in symbols]

    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """
        Get symbol information.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with symbol info
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return None

        info = mt5.symbol_info(symbol)
        if info is None:
            logger.error(f"Failed to get symbol info for {symbol}: {mt5.last_error()}")
            return None

        return {
            'name': info.name,
            'description': info.description,
            'point': info.point,
            'digits': info.digits,
            'spread': info.spread,
            'trade_contract_size': info.trade_contract_size,
            'volume_min': info.volume_min,
            'volume_max': info.volume_max,
            'volume_step': info.volume_step
        }
