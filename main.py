"""Main application entry point for Multi-Agent Trading System."""

import logging
import time
import yaml
import sys
import argparse
from datetime import datetime
from typing import List, Dict
import os
from dotenv import load_dotenv

from data.market_data import MarketDataFetcher
from data.database import DatabaseHandler
from data.models import MarketType, TradeStatus

from agents.trend_agent import TrendAgent
from agents.smc_agent import SMCAgent
from agents.statistical_agent import StatisticalAgent
from agents.wave_agent import WaveAgent
from agents.learning_agent import LearningAgent

from meta.meta_agent import MetaAgent
from risk.risk_manager import RiskManager
from risk.correlation_matrix import CorrelationMatrix
from execution.mt5_connector import MT5Connector
from execution.order_manager import OrderManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TradingSystem:
    """Main trading system orchestrator."""

    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize the trading system.
        
        Args:
            config_path: Path to general configuration file
        """
        logger.info("=" * 80)
        logger.info("Multi-Agent Trading System Starting...")
        logger.info("=" * 80)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.db_handler = DatabaseHandler()
        self.market_data_fetcher = MarketDataFetcher()
        self.mt5_connector = MT5Connector()
        
        # Initialize risk management
        initial_balance = float(os.getenv('INITIAL_BALANCE', '10000.0'))
        self.risk_manager = RiskManager(account_balance=initial_balance)
        self.correlation_matrix = CorrelationMatrix()
        
        # Initialize order manager
        self.order_manager = OrderManager(
            self.mt5_connector,
            self.risk_manager,
            self.db_handler
        )
        
        # Market configurations
        self.market_configs = {
            MarketType.FOREX: self._load_config("config/forex_config.yaml"),
            MarketType.GOLD: self._load_config("config/gold_config.yaml"),
            MarketType.STOCKS: self._load_config("config/stocks_config.yaml"),
            MarketType.CRYPTO: self._load_config("config/crypto_config.yaml")
        }
        
        # Initialize meta-agents for each market
        self.meta_agents: Dict[MarketType, MetaAgent] = {}
        for market_type in [MarketType.FOREX, MarketType.GOLD, MarketType.STOCKS, MarketType.CRYPTO]:
            self.meta_agents[market_type] = MetaAgent(market_type)
        
        # Initialize agents dictionary
        self.agents = {}
        
        # Trading control flags
        self.enable_live_trading = os.getenv('ENABLE_LIVE_TRADING', 'False').lower() == 'true'
        self.enable_paper_trading = os.getenv('ENABLE_PAPER_TRADING', 'True').lower() == 'true'
        self.running = False
        
        logger.info(f"Live Trading: {'ENABLED' if self.enable_live_trading else 'DISABLED'}")
        logger.info(f"Paper Trading: {'ENABLED' if self.enable_paper_trading else 'DISABLED'}")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return {}

    def initialize(self) -> bool:
        """Initialize all system components."""
        try:
            logger.info("Initializing system components...")
            
            # Initialize MT5 connection
            if not self.market_data_fetcher.initialize():
                logger.error("Failed to initialize MT5 market data fetcher")
                return False
            
            if not self.mt5_connector.initialize():
                logger.error("Failed to initialize MT5 connector")
                return False
            
            # Get account info
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                self.risk_manager.update_account_balance(account_info['balance'])
                logger.info(f"Account Balance: ${account_info['balance']:.2f}")
            
            # Initialize agents for each active symbol
            self._initialize_agents()
            
            logger.info("System initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False

    def _initialize_agents(self):
        """Initialize trading agents for all active symbols."""
        logger.info("Initializing trading agents...")
        
        # Get all active symbols from all market configs
        all_symbols = []
        for market_type, config in self.market_configs.items():
            symbols = config.get('active_symbols', [])
            for symbol in symbols:
                all_symbols.append((symbol, market_type))
        
        # Initialize agents for each symbol
        for symbol, market_type in all_symbols:
            self.agents[symbol] = {
                'market_type': market_type,
                'trend': TrendAgent(symbol),
                'smc': SMCAgent(symbol),
                'statistical': StatisticalAgent(symbol),
                'wave': WaveAgent(symbol),
                'learning': LearningAgent(symbol)
            }
            logger.info(f"Initialized agents for {symbol} ({market_type.value})")

    def analyze_symbol(self, symbol: str, market_type: MarketType) -> None:
        """
        Analyze a symbol and generate trading signals.
        
        Args:
            symbol: Trading symbol
            market_type: Type of market
        """
        try:
            # Get market data
            data = self.market_data_fetcher.get_bars(symbol, timeframe="H1", count=500)
            
            if data is None or len(data) < 200:
                logger.warning(f"{symbol}: Insufficient data")
                return
            
            # Get agents for this symbol
            symbol_agents = self.agents.get(symbol)
            if not symbol_agents:
                logger.warning(f"{symbol}: No agents initialized")
                return
            
            # Generate signals from each agent
            signals = []
            
            trend_signal = symbol_agents['trend'].analyze(data)
            signals.append(trend_signal)
            
            smc_signal = symbol_agents['smc'].analyze(data)
            signals.append(smc_signal)
            
            # Get current spread and open positions for statistical agent
            current_price = self.market_data_fetcher.get_current_price(symbol)
            spread_pips = current_price['spread'] / 0.0001 if current_price else 0
            open_positions = len(self.db_handler.get_trades(symbol=symbol, status=TradeStatus.OPEN))
            
            stat_signal = symbol_agents['statistical'].analyze(data, spread_pips, open_positions)
            signals.append(stat_signal)
            
            wave_signal = symbol_agents['wave'].analyze(data)
            signals.append(wave_signal)
            
            # Aggregate signals with meta-agent
            meta_agent = self.meta_agents[market_type]
            trade_signal = meta_agent.aggregate_signals(signals, symbol)
            
            # Log the decision
            logger.info(f"{symbol}: {trade_signal.direction.value} "
                       f"(Confidence: {trade_signal.confidence:.1%}) - {trade_signal.reasoning}")
            
            # Execute trade if conditions are met
            if trade_signal.direction.value in ['BUY', 'SELL']:
                if self.enable_live_trading or self.enable_paper_trading:
                    self._execute_trade(trade_signal, market_type)
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")

    def _execute_trade(self, trade_signal, market_type: MarketType):
        """
        Execute a trade based on signal.
        
        Args:
            trade_signal: Trade signal from meta-agent
            market_type: Type of market
        """
        try:
            # Get market configuration
            market_config = self.market_configs.get(market_type, {})
            
            # Validate with risk manager
            validation = self.risk_manager.validate_trade(trade_signal)
            
            if not validation['is_valid']:
                logger.warning(f"Trade validation failed: {validation['message']}")
                return
            
            # Check correlation if there are open positions
            open_trades = self.db_handler.get_trades(status=TradeStatus.OPEN)
            if open_trades:
                open_symbols = [t.symbol for t in open_trades]
                correlation_check = self.correlation_matrix.validate_new_position(
                    trade_signal.symbol,
                    open_symbols
                )
                
                if not correlation_check['is_valid']:
                    logger.warning(f"Correlation check failed: {correlation_check['message']}")
                    return
            
            # Execute trade (only in live mode, paper trading logs but doesn't execute)
            if self.enable_live_trading:
                trade = self.order_manager.execute_trade(trade_signal, market_config)
                if trade:
                    logger.info(f"Trade executed: {trade.symbol} {trade.direction.value} "
                               f"{trade.position_size} lots at {trade.entry_price}")
            else:
                logger.info(f"[PAPER TRADE] Would execute: {trade_signal.symbol} "
                           f"{trade_signal.direction.value} (Confidence: {trade_signal.confidence:.1%})")
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")

    def manage_positions(self):
        """Manage open positions (breakeven, trailing stops, etc.)."""
        try:
            # Manage positions for each market
            for market_type, config in self.market_configs.items():
                if self.enable_live_trading:
                    self.order_manager.manage_positions(config)
            
            # Sync positions with database
            if self.enable_live_trading:
                self.order_manager.sync_positions_with_database()
            
        except Exception as e:
            logger.error(f"Error managing positions: {e}")

    def run(self, interval: int = 300):
        """
        Run the trading system main loop.
        
        Args:
            interval: Analysis interval in seconds (default: 300 = 5 minutes)
        """
        logger.info("Starting trading system main loop...")
        logger.info(f"Analysis interval: {interval} seconds")
        
        self.running = True
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                logger.info(f"--- Iteration {iteration} - {datetime.now()} ---")
                
                # Analyze all active symbols
                for symbol, agent_info in self.agents.items():
                    market_type = agent_info['market_type']
                    self.analyze_symbol(symbol, market_type)
                
                # Manage open positions
                self.manage_positions()
                
                # Log system status
                metrics = self.risk_manager.get_risk_metrics()
                logger.info(f"System Status - Balance: ${metrics.get('account_balance', 0):.2f}, "
                           f"Open Trades: {metrics.get('open_trades', 0)}, "
                           f"Win Rate: {metrics.get('win_rate', 0):.1%}")
                
                # Wait for next iteration
                logger.info(f"Waiting {interval} seconds for next analysis...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
            self.shutdown()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.shutdown()

    def shutdown(self):
        """Shutdown the trading system gracefully."""
        logger.info("Shutting down trading system...")
        
        self.running = False
        
        # Close MT5 connections
        self.market_data_fetcher.shutdown()
        self.mt5_connector.shutdown()
        
        logger.info("Trading system stopped")
        logger.info("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Multi-Agent Trading System')
    parser.add_argument('--interval', type=int, default=300, help='Analysis interval in seconds')
    parser.add_argument('--config', type=str, default='config/settings.yaml', help='Path to config file')
    
    args = parser.parse_args()
    
    # Create and initialize system
    system = TradingSystem(config_path=args.config)
    
    if not system.initialize():
        logger.error("Failed to initialize trading system")
        sys.exit(1)
    
    # Run the system
    system.run(interval=args.interval)


if __name__ == "__main__":
    main()
