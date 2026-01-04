"""Database handler for storing trading data."""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional, List
import logging
import os
from dotenv import load_dotenv

from .models import Trade, TradeStatus, SignalDirection, MarketType, PerformanceMetrics

load_dotenv()
logger = logging.getLogger(__name__)

Base = declarative_base()


class TradeRecord(Base):
    """SQLAlchemy model for trades."""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    market_type = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    position_size = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    profit_loss = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(String(500), nullable=True)
    metadata = Column(JSON, nullable=True)


class AgentPerformanceRecord(Base):
    """SQLAlchemy model for agent performance."""
    __tablename__ = 'agent_performance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(50), nullable=False, unique=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    average_rr = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.now)
    metadata = Column(JSON, nullable=True)


class AgentWeightRecord(Base):
    """SQLAlchemy model for agent weights."""
    __tablename__ = 'agent_weights'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(50), nullable=False, unique=True)
    weight = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.now)


class DatabaseHandler:
    """Handles database operations for the trading system."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database handler.
        
        Args:
            database_url: Database URL (defaults to env variable or SQLite)
        """
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///./trading.db')
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized: {database_url}")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def save_trade(self, trade: Trade) -> Trade:
        """
        Save a trade to the database.
        
        Args:
            trade: Trade object
            
        Returns:
            Trade object with ID
        """
        session = self.get_session()
        try:
            trade_record = TradeRecord(
                symbol=trade.symbol,
                market_type=trade.market_type.value,
                direction=trade.direction.value,
                entry_price=trade.entry_price,
                stop_loss=trade.stop_loss,
                take_profit=trade.take_profit,
                position_size=trade.position_size,
                entry_time=trade.entry_time,
                exit_time=trade.exit_time,
                exit_price=trade.exit_price,
                profit_loss=trade.profit_loss,
                status=trade.status.value,
                confidence=trade.confidence,
                reasoning=trade.reasoning,
                metadata=trade.metadata
            )
            session.add(trade_record)
            session.commit()
            session.refresh(trade_record)
            trade.id = trade_record.id
            logger.info(f"Trade saved: {trade.id}")
            return trade
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving trade: {e}")
            raise
        finally:
            session.close()

    def update_trade(self, trade: Trade) -> None:
        """
        Update a trade in the database.
        
        Args:
            trade: Trade object with ID
        """
        if trade.id is None:
            raise ValueError("Trade must have an ID to update")
        
        session = self.get_session()
        try:
            trade_record = session.query(TradeRecord).filter_by(id=trade.id).first()
            if trade_record is None:
                raise ValueError(f"Trade {trade.id} not found")
            
            trade_record.exit_time = trade.exit_time
            trade_record.exit_price = trade.exit_price
            trade_record.profit_loss = trade.profit_loss
            trade_record.status = trade.status.value
            trade_record.metadata = trade.metadata
            
            session.commit()
            logger.info(f"Trade updated: {trade.id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating trade: {e}")
            raise
        finally:
            session.close()

    def get_trades(
        self,
        symbol: Optional[str] = None,
        status: Optional[TradeStatus] = None,
        limit: Optional[int] = None
    ) -> List[Trade]:
        """
        Get trades from the database.
        
        Args:
            symbol: Filter by symbol
            status: Filter by status
            limit: Limit number of results
            
        Returns:
            List of Trade objects
        """
        session = self.get_session()
        try:
            query = session.query(TradeRecord)
            
            if symbol:
                query = query.filter_by(symbol=symbol)
            if status:
                query = query.filter_by(status=status.value)
            
            query = query.order_by(TradeRecord.entry_time.desc())
            
            if limit:
                query = query.limit(limit)
            
            trade_records = query.all()
            
            trades = []
            for record in trade_records:
                trade = Trade(
                    id=record.id,
                    symbol=record.symbol,
                    market_type=MarketType(record.market_type),
                    direction=SignalDirection(record.direction),
                    entry_price=record.entry_price,
                    stop_loss=record.stop_loss,
                    take_profit=record.take_profit,
                    position_size=record.position_size,
                    entry_time=record.entry_time,
                    exit_time=record.exit_time,
                    exit_price=record.exit_price,
                    profit_loss=record.profit_loss,
                    status=TradeStatus(record.status),
                    confidence=record.confidence,
                    reasoning=record.reasoning or "",
                    metadata=record.metadata
                )
                trades.append(trade)
            
            return trades
        finally:
            session.close()

    def save_agent_performance(self, metrics: PerformanceMetrics) -> None:
        """
        Save agent performance metrics.
        
        Args:
            metrics: PerformanceMetrics object
        """
        session = self.get_session()
        try:
            record = session.query(AgentPerformanceRecord).filter_by(
                agent_name=metrics.agent_name
            ).first()
            
            if record is None:
                record = AgentPerformanceRecord(agent_name=metrics.agent_name)
                session.add(record)
            
            record.total_trades = metrics.total_trades
            record.winning_trades = metrics.winning_trades
            record.losing_trades = metrics.losing_trades
            record.win_rate = metrics.win_rate
            record.average_rr = metrics.average_rr
            record.total_profit = metrics.total_profit
            record.max_drawdown = metrics.max_drawdown
            record.sharpe_ratio = metrics.sharpe_ratio
            record.last_updated = metrics.last_updated
            record.metadata = metrics.metadata
            
            session.commit()
            logger.info(f"Performance saved for {metrics.agent_name}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving performance: {e}")
            raise
        finally:
            session.close()

    def get_agent_performance(self, agent_name: str) -> Optional[PerformanceMetrics]:
        """
        Get agent performance metrics.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            PerformanceMetrics object or None
        """
        session = self.get_session()
        try:
            record = session.query(AgentPerformanceRecord).filter_by(
                agent_name=agent_name
            ).first()
            
            if record is None:
                return None
            
            return PerformanceMetrics(
                agent_name=record.agent_name,
                total_trades=record.total_trades,
                winning_trades=record.winning_trades,
                losing_trades=record.losing_trades,
                win_rate=record.win_rate,
                average_rr=record.average_rr,
                total_profit=record.total_profit,
                max_drawdown=record.max_drawdown,
                sharpe_ratio=record.sharpe_ratio,
                last_updated=record.last_updated,
                metadata=record.metadata
            )
        finally:
            session.close()

    def save_agent_weight(self, agent_name: str, weight: float) -> None:
        """
        Save agent weight.
        
        Args:
            agent_name: Name of the agent
            weight: Weight value (0.0 to 1.0)
        """
        session = self.get_session()
        try:
            record = session.query(AgentWeightRecord).filter_by(
                agent_name=agent_name
            ).first()
            
            if record is None:
                record = AgentWeightRecord(agent_name=agent_name)
                session.add(record)
            
            record.weight = weight
            record.last_updated = datetime.now()
            
            session.commit()
            logger.info(f"Weight saved for {agent_name}: {weight}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving weight: {e}")
            raise
        finally:
            session.close()

    def get_agent_weights(self) -> dict:
        """
        Get all agent weights.
        
        Returns:
            Dictionary of agent_name: weight
        """
        session = self.get_session()
        try:
            records = session.query(AgentWeightRecord).all()
            return {record.agent_name: record.weight for record in records}
        finally:
            session.close()
