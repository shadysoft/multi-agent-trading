# Agent Guide - Multi-Agent Trading System

This guide provides detailed information about each trading agent in the system.

## Agent Overview

The system uses five specialized agents that work together to generate trading signals. Each agent has a specific role and uses different analysis methods.

## 1. TrendAgent 🔄

### Purpose
Identifies and follows market trends using moving averages and directional indicators.

### Analysis Methods

#### Exponential Moving Averages (EMA)
- **Fast EMA**: 20-period (short-term trend)
- **Medium EMA**: 50-period (medium-term trend)
- **Slow EMA**: 200-period (long-term trend)

**Bullish Alignment**: Fast > Medium > Slow
**Bearish Alignment**: Fast < Medium < Slow

#### Average Directional Index (ADX)
- Measures trend strength
- Threshold: 25 (Forex), 30 (Gold)
- Above threshold = strong trend
- Below threshold = weak/ranging market

#### Price Structure
- **Higher Highs + Higher Lows** = Uptrend
- **Lower Highs + Lower Lows** = Downtrend
- Mixed structure = Ranging/consolidation

### Signal Generation

**BUY Signal** when:
- Bullish EMA alignment
- ADX > threshold
- Higher highs and higher lows

**SELL Signal** when:
- Bearish EMA alignment
- ADX > threshold
- Lower highs and lower lows

**Confidence Calculation**:
- EMA alignment: +30%
- Strong ADX: +30%
- Price structure: +40%
- Maximum: 100%

### Configuration
```yaml
indicators:
  ema_periods: [20, 50, 200]
  adx_period: 14
  adx_threshold: 25
```

---

## 2. SMCAgent 💎

### Purpose
Identifies institutional trading patterns using Smart Money Concepts.

### Analysis Methods

#### Liquidity Zones
- **Swing Highs**: Areas where price reversed down (resistance)
- **Swing Lows**: Areas where price reversed up (support)
- Institutions target these areas to trigger stop losses

#### Order Blocks
- **Bullish Order Block**: Last down candle before strong up move
- **Bearish Order Block**: Last up candle before strong down move
- Represents where institutions placed large orders

#### Fair Value Gaps (FVG)
- **Bullish FVG**: Gap between bar i-1 high and bar i+1 low
- **Bearish FVG**: Gap between bar i-1 low and bar i+1 high
- Price often returns to "fill" these gaps

### Signal Generation

**BUY Signal** when:
- Price near bullish order block
- Unfilled bullish FVG present
- Support liquidity zone nearby

**SELL Signal** when:
- Price near bearish order block
- Unfilled bearish FVG present
- Resistance liquidity zone nearby

**Confidence Levels**:
- Order block + FVG: 80%
- Order block only: 60%
- FVG only: 50%

### Configuration
```yaml
smc:
  min_order_block_touches: 2
  fvg_min_size_pips: 5
  liquidity_zone_lookback: 50
```

---

## 3. StatisticalAgent 🛡️

### Purpose
Acts as a gatekeeper to validate trading conditions before allowing trades.

### Validation Checks

#### Spread Check
- Ensures spread is within acceptable limits
- High spread = higher trading costs
- Violation: Reduces confidence by 40%

#### ATR (Volatility) Check
- Ensures sufficient market movement
- Too low ATR = not enough opportunity
- Violation: Reduces confidence by 40%

#### Position Count Check
- Ensures max concurrent trades not exceeded
- Prevents over-exposure
- Violation: Reduces confidence by 30%

#### Volatility Filter
- Checks for extreme market conditions
- 20-bar volatility percentage
- Extreme volatility: Reduces confidence by 20%

### Signal Generation

**Approval (BUY signal)** when:
- Spread acceptable
- ATR sufficient
- Position count OK
- Volatility normal
- Confidence ≥ 60%

**Rejection (WAIT signal)** when:
- Any violation exists
- Confidence < 60%

### Configuration
```yaml
risk:
  max_spread_pips: 2.0
  min_atr_pips: 10.0
  max_position_size_percent: 1.0
```

---

## 4. WaveAgent 🌊

### Purpose
Identifies market wave structure to determine impulse and correction phases.

### Analysis Methods

#### Wave Classification
- **Impulse Wave**: Strong directional movement
- **Correction Wave**: Retracement/consolidation
- Analyzes directional ratio and price change

#### Momentum Analysis
- Counts up vs down bars
- Calculates directional ratio
- Threshold: 60% for impulse classification

#### Wave Counting
- Counts direction changes
- Multiple waves = stronger trend
- Helps identify trend maturity

### Signal Generation

**BUY Signal** when:
- Bullish impulse wave (high confidence 0.6-0.9)
- Bullish correction (medium confidence 0.5)

**SELL Signal** when:
- Bearish impulse wave (high confidence 0.6-0.9)
- Bearish correction (medium confidence 0.5)

**Confidence Factors**:
- Impulse strength (directional ratio)
- Wave count (+10% for 3+ waves)
- Price change magnitude

### Configuration
```yaml
wave:
  min_impulse_bars: 5
  min_correction_bars: 3
  impulse_threshold: 0.6
```

---

## 5. LearningAgent 🧠

### Purpose
Monitors system performance and adaptively adjusts agent weights.

### Learning Process

#### Performance Tracking
- Win rate calculation
- Average risk-reward ratio
- Total profit/loss
- Maximum drawdown
- Losing/winning streaks

#### Weight Adjustment
- Evaluates every 100 trades (configurable)
- Adjusts weights by ±1%
- Based on individual agent performance
- Gradual changes to avoid instability

#### Safety Mechanisms
- **Losing Streak Detection**: Pauses learning after 5 consecutive losses
- **Minimum Trades**: Requires 20 trades before learning
- **Weight Limits**: Keeps weights between 5% and 50%

### Signal Generation

The LearningAgent doesn't generate trading signals directly. Instead, it:

1. Provides performance assessment
2. Recommends weight adjustments
3. Signals when to pause trading (losing streaks)

**Confidence Interpretation**:
- High (0.8): Strong performance, increase weights
- Medium (0.6): Adequate performance, maintain
- Low (0.4): Underperformance, decrease weights

### Configuration
```yaml
learning:
  learning_rate: 0.01  # 1% adjustment
  evaluation_window: 100
  min_trades_for_learning: 20
```

---

## Agent Weight System

### Default Weights
- TrendAgent: 25%
- SMCAgent: 25%
- StatisticalAgent: 20%
- WaveAgent: 20%
- LearningAgent: 10%

### Weight Adjustment
- Performed by LearningAgent
- Based on individual agent contribution to wins/losses
- Gradual adjustments (±1% per evaluation)
- Requires minimum trade history

### Weight Constraints
- Minimum: 5% (agent still contributes)
- Maximum: 50% (prevents over-reliance)
- Sum doesn't need to equal 100% (normalized during calculation)

---

## How Agents Work Together

### 1. Independent Analysis
Each agent analyzes market data independently:
```python
trend_signal = trend_agent.analyze(data)
smc_signal = smc_agent.analyze(data)
stat_signal = statistical_agent.analyze(data, spread, positions)
wave_signal = wave_agent.analyze(data)
```

### 2. Meta-Agent Aggregation
Signals are combined using weighted confidence:
```
Weighted Confidence = Σ(agent_confidence × agent_weight) / Σ(agent_weight)
```

### 3. Threshold Validation
Final signal must meet market-specific threshold:
- Forex: 75%
- Gold: 80%
- Stocks: 75%
- Crypto: 80%

### 4. Statistical Gate
StatisticalAgent must approve (confidence ≥ 60%)

### 5. Final Decision
- All conditions met → Execute trade
- Any condition fails → WAIT

---

## Best Practices

### For Developers
1. **Don't modify agent logic without testing**
2. **Maintain agent independence** (no cross-dependencies)
3. **Add new agents by extending BaseAgent**
4. **Test agents individually before integration**

### For Traders
1. **Monitor agent performance** via dashboard
2. **Understand each agent's role** before adjusting weights
3. **Let LearningAgent adapt** before manual intervention
4. **Review reasoning** in agent signals to understand decisions

### For System Operators
1. **Start with default weights** for new markets
2. **Allow 100+ trades** before evaluating performance
3. **Check for agent failures** in logs
4. **Backup weight configurations** before major changes

---

## Troubleshooting

### Agent Returns WAIT Constantly
- Check data availability and quality
- Verify indicator calculations
- Review threshold settings
- Check for sufficient volatility

### Low Confidence Signals
- Normal in ranging markets
- StatisticalAgent may be blocking
- Check individual agent reasonings
- Verify market conditions match agent strengths

### Agent Performance Declining
- Market regime may have changed
- Review recent trades
- Check agent parameters
- Consider re-calibration

---

## Extending the System

### Adding a New Agent

1. **Create agent class** extending BaseAgent
2. **Implement analyze() method**
3. **Add to agent initialization** in main.py
4. **Update configuration** with agent weight
5. **Add tests** in tests/test_agents.py
6. **Document** agent behavior and parameters

Example:
```python
class VolumeAgent(BaseAgent):
    def __init__(self, symbol, timeframe="H1", weight=0.15):
        super().__init__("VolumeAgent", symbol, timeframe, weight)
    
    def analyze(self, data):
        # Your analysis logic
        return self.create_signal(direction, confidence, reasoning)
```
