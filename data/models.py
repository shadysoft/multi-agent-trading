"""Pydantic data models for the trading system."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class SignalDirection(str, Enum):
    """Trade signal direction."""
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


class MarketType(str, Enum):
    """Market type enumeration."""
    FOREX = "forex"
    GOLD = "gold"
    STOCKS = "stocks"
    CRYPTO = "crypto"


class TradeStatus(str, Enum):
    """Trade status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class AgentSignal(BaseModel):
    """Signal from an individual agent."""
    agent_name: str
    symbol: str
    direction: SignalDirection
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class TradeSignal(BaseModel):
    """Aggregated trade signal from meta-agent."""
    symbol: str
    market_type: MarketType
    direction: SignalDirection
    confidence: float = Field(..., ge=0.0, le=1.0)
    agent_signals: List[AgentSignal]
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.now)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None


class Trade(BaseModel):
    """Trading position information."""
    id: Optional[int] = None
    symbol: str
    market_type: MarketType
    direction: SignalDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    entry_time: datetime = Field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    status: TradeStatus = TradeStatus.PENDING
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    metadata: Optional[Dict[str, Any]] = None

    @property
    def is_winner(self) -> Optional[bool]:
        """Check if trade is a winner."""
        if self.profit_loss is None:
            return None
        return self.profit_loss > 0

    @property
    def risk_reward_ratio(self) -> Optional[float]:
        """Calculate risk-reward ratio."""
        if self.entry_price == 0 or self.stop_loss == 0 or self.take_profit == 0:
            return None
        
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)
        
        if risk == 0:
            return None
        
        return reward / risk


class MarketData(BaseModel):
    """Market price data."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    timeframe: str = "H1"


class PerformanceMetrics(BaseModel):
    """Agent or system performance metrics."""
    agent_name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    average_rr: float = 0.0
    total_profit: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

    @property
    def loss_rate(self) -> float:
        """Calculate loss rate."""
        if self.total_trades == 0:
            return 0.0
        return self.losing_trades / self.total_trades

    def update_metrics(self, trade: Trade) -> None:
        """Update metrics with new trade."""
        if trade.status != TradeStatus.CLOSED or trade.profit_loss is None:
            return
        
        self.total_trades += 1
        
        if trade.is_winner:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0.0
        self.total_profit += trade.profit_loss
        self.last_updated = datetime.now()


class AgentWeight(BaseModel):
    """Agent weight for meta-agent calculations."""
    agent_name: str
    weight: float = Field(..., ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.now)

    @validator('weight')
    def validate_weight(cls, v):
        """Ensure weight is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Weight must be between 0.0 and 1.0')
        return v
