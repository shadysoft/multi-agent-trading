# Multi-Agent Trading System Architecture

## Overview

The Multi-Agent Trading System is a sophisticated automated trading platform that leverages multiple AI agents to analyze markets and make trading decisions. The system is designed to trade across multiple asset classes: Forex, Gold/Commodities, Stocks, and Cryptocurrency.

## System Components

### 1. Data Layer (`data/`)

The data layer handles all data management, storage, and retrieval:

- **models.py**: Pydantic data models for type safety and validation
  - `AgentSignal`: Individual agent trading signals
  - `TradeSignal`: Aggregated trading signal from meta-agent
  - `Trade`: Complete trade information
  - `MarketData`: OHLCV price data
  - `PerformanceMetrics`: Agent and system performance tracking

- **market_data.py**: Interface with MetaTrader 5 for market data
  - Real-time price fetching
  - Historical data retrieval
  - Symbol information

- **database.py**: SQLAlchemy-based data persistence
  - Trade history storage
  - Agent performance metrics
  - Agent weight management

### 2. Agent Layer (`agents/`)

Five specialized trading agents analyze markets independently:

#### BaseAgent (`base_agent.py`)
- Abstract base class for all agents
- Common indicator calculations (EMA, ATR, ADX, RSI)
- Data validation utilities

#### TrendAgent (`trend_agent.py`)
- **Purpose**: Identify and follow market trends
- **Methods**:
  - EMA crossovers (20, 50, 200 periods)
  - ADX for trend strength measurement
  - Price structure analysis (Higher Highs/Lower Lows)
- **Weight**: 25% (default)

#### SMCAgent (`smc_agent.py`)
- **Purpose**: Smart Money Concepts analysis
- **Methods**:
  - Liquidity zone identification
  - Order block detection
  - Fair Value Gap (FVG) analysis
- **Weight**: 25% (default)

#### StatisticalAgent (`statistical_agent.py`)
- **Purpose**: Gatekeeper for trade validation
- **Methods**:
  - ATR-based volatility checks
  - Spread validation
  - Position count monitoring
  - Correlation analysis
- **Weight**: 20% (default)

#### WaveAgent (`wave_agent.py`)
- **Purpose**: Wave structure analysis
- **Methods**:
  - Impulse vs correction wave identification
  - Momentum analysis
  - Swing point detection
- **Weight**: 20% (default)

#### LearningAgent (`learning_agent.py`)
- **Purpose**: Adaptive learning and weight adjustment
- **Methods**:
  - Performance tracking
  - Weight adjustment recommendations
  - Losing streak detection
- **Weight**: 10% (default)

### 3. Meta-Agent Layer (`meta/`)

#### MetaAgent (`meta_agent.py`)
- **Purpose**: Aggregate agent signals and make final decisions
- **Process**:
  1. Collect signals from all agents
  2. Calculate weighted confidence scores
  3. Apply market-specific thresholds
  4. Validate statistical gate
  5. Generate final trade signal

- **Thresholds**:
  - Forex: 75%
  - Gold: 80%
  - Stocks: 75%
  - Crypto: 80%

### 4. Strategy Layer (`strategies/`)

#### ConfidenceCalculator (`confidence_calculator.py`)
- Aggregates confidence scores
- Calculates signal strength
- Applies time decay
- Risk-adjusted confidence calculation

### 5. Risk Management Layer (`risk/`)

#### RiskManager (`risk_manager.py`)
- **Functions**:
  - Position sizing based on account risk
  - Daily loss limit enforcement
  - Drawdown protection
  - Maximum concurrent trades management
  - SL/TP calculation

#### CorrelationMatrix (`correlation_matrix.py`)
- **Functions**:
  - Inter-symbol correlation analysis
  - Portfolio diversification scoring
  - Position validation based on correlation

### 6. Execution Layer (`execution/`)

#### MT5Connector (`mt5_connector.py`)
- **Functions**:
  - MT5 connection management
  - Order placement
  - Position modification
  - Account information retrieval

#### OrderManager (`order_manager.py`)
- **Functions**:
  - Trade execution from signals
  - Position management (breakeven, trailing stops)
  - Position synchronization with database

### 7. Dashboard (`dashboard/`)

Web-based Streamlit dashboard for monitoring and control:

- **Overview**: System-wide metrics and equity curve
- **Market Tabs**: Individual market performance
- **Alerts**: Real-time notifications and warnings
- **Settings**: Configuration management

### 8. MT5 Expert Advisor (`mt5_ea/`)

#### TradingExecutor.mq5
- Runs on MetaTrader 5 terminal
- Executes orders safely
- Manages trailing stops
- Monitors positions

## Data Flow

```
1. Market Data → MarketDataFetcher → Agents
2. Agents → Individual Analysis → AgentSignals
3. AgentSignals → MetaAgent → TradeSignal
4. TradeSignal → RiskManager → Validation
5. Validated Signal → OrderManager → MT5Connector
6. MT5Connector → MetaTrader 5 → Order Execution
7. Execution Result → Database → Dashboard
8. Performance Data → LearningAgent → Weight Adjustment
```

## Decision Making Process

### 1. Signal Generation Phase
- Each agent analyzes current market data independently
- Agents generate signals with:
  - Direction (BUY/SELL/WAIT)
  - Confidence (0.0 to 1.0)
  - Reasoning

### 2. Meta-Agent Aggregation
- Collects all agent signals
- Validates minimum agent count
- Separates signals by direction
- Calculates weighted confidence

### 3. Statistical Gate
- StatisticalAgent must approve (confidence ≥ 60%)
- Checks spread, ATR, position count
- Acts as final gatekeeper

### 4. Risk Validation
- Checks daily loss limits
- Validates position count
- Checks correlation with open positions
- Verifies drawdown limits

### 5. Execution
- Calculate position size
- Set SL/TP levels
- Send order to MT5
- Store trade in database

### 6. Position Management
- Monitor for breakeven trigger
- Update trailing stops
- Check for exit conditions

### 7. Learning Phase
- Record trade results
- Update agent performance metrics
- Adjust agent weights (±1% per 100 trades)
- Pause learning during losing streaks

## Configuration

### Market-Specific Configs
- **forex_config.yaml**: Forex pairs, thresholds
- **gold_config.yaml**: Precious metals, commodities
- **stocks_config.yaml**: Stock symbols, market hours
- **crypto_config.yaml**: Cryptocurrencies, 24/7 trading

### General Settings
- **settings.yaml**: System-wide configuration
  - Agent weights
  - Risk parameters
  - Database settings
  - Logging configuration

## Security Features

1. **Risk Controls**:
   - Maximum daily loss limits
   - Position size limits
   - Drawdown protection
   - Maximum concurrent trades

2. **Validation Layers**:
   - Statistical gatekeeper
   - Risk manager validation
   - Correlation checks

3. **Safe Execution**:
   - MT5 Expert Advisor for order safety
   - Database transaction management
   - Error handling and logging

## Scalability

The system is designed to scale:
- **Horizontal**: Add new agents for different strategies
- **Vertical**: Increase analysis complexity per agent
- **Markets**: Easily add new asset classes
- **Symbols**: Configure any tradeable symbol

## Performance Monitoring

1. **Real-time Dashboard**: Live metrics and alerts
2. **Database Logging**: Complete trade history
3. **Agent Performance**: Individual agent tracking
4. **Adaptive Learning**: Automatic weight adjustment

## Technology Stack

- **Language**: Python 3.9+
- **Trading Platform**: MetaTrader 5
- **Database**: SQLite/PostgreSQL
- **Dashboard**: Streamlit
- **Data Validation**: Pydantic
- **Testing**: Pytest
- **Visualization**: Plotly
