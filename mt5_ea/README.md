# Multi-Agent Trading Expert Advisor for MetaTrader 5

## 📋 Overview

The Multi-Agent EA is a sophisticated trading system that combines multiple AI agents to analyze market conditions and make intelligent trading decisions. Each agent specializes in a different aspect of market analysis, and their signals are aggregated to produce high-confidence trading opportunities.

## 🤖 Agent Architecture

### 1. **Trend Agent** (TrendAgent.mqh)
- **Purpose**: Identifies and confirms market trends
- **Methods**:
  - EMA 20, 50, 200 crossover analysis
  - ADX for trend strength validation (threshold: 25)
  - Price structure analysis (Higher Highs/Higher Lows)
- **Output**: BUY/SELL/NEUTRAL signal with 0-100% confidence

### 2. **Smart Money Concepts Agent** (SMCAgent.mqh)
- **Purpose**: Identifies institutional trading patterns
- **Methods**:
  - Order Block detection (last opposite candle before impulse)
  - Fair Value Gap (FVG) identification
  - Liquidity zone detection (equal highs/lows)
  - Break of Structure (BOS) recognition
- **Output**: BUY/SELL/NEUTRAL signal with 0-100% confidence

### 3. **Wave Agent** (WaveAgent.mqh)
- **Purpose**: Analyzes wave patterns and market cycles
- **Methods**:
  - Swing point identification
  - Impulse wave detection (strong trend moves)
  - Correction wave analysis (pullbacks with Fibonacci levels)
  - Wave momentum calculation
- **Output**: BUY/SELL/NEUTRAL signal with 0-100% confidence

### 4. **Statistical Agent** (StatisticalAgent.mqh)
- **Purpose**: Acts as a gatekeeper to validate trading conditions
- **Validations**:
  - ATR filter (volatility check)
  - Spread validation (max spread limit)
  - Time filter (trading hours, avoid weekends)
  - Market status check
  - Account drawdown protection
  - Daily loss limit monitoring
  - Position limit enforcement
- **Output**: ALLOW_TRADE or BLOCK_TRADE with reason

## 📊 Signal Aggregation

The **SignalAggregator** combines all agent signals using a weighted voting system:

1. Collects signals from all analysis agents
2. Calculates weighted confidence scores
3. Checks for direction consensus (at least 2 agents must agree)
4. Applies market-specific confidence thresholds
5. Returns final decision: BUY, SELL, or WAIT

## ⚙️ Installation

### Step 1: Copy Files to MT5

1. Open MetaTrader 5
2. Click **File** → **Open Data Folder**
3. Navigate to `MQL5/Experts/`
4. Create a new folder called `MultiAgentEA`
5. Copy all files maintaining the directory structure:
   ```
   MQL5/Experts/MultiAgentEA/
   ├── MultiAgentEA.mq5
   ├── Agents/
   │   ├── TrendAgent.mqh
   │   ├── SMCAgent.mqh
   │   ├── StatisticalAgent.mqh
   │   └── WaveAgent.mqh
   ├── Utils/
   │   ├── RiskManager.mqh
   │   ├── TradeManager.mqh
   │   ├── SignalAggregator.mqh
   │   └── Helpers.mqh
   └── Config/
       └── Settings.mqh
   ```

### Step 2: Compile the EA

1. Open **MetaEditor** (F4 in MT5)
2. Navigate to `Experts/MultiAgentEA/MultiAgentEA.mq5`
3. Click **Compile** (F7) or the compile button
4. Check for any errors in the **Errors** tab
5. Successful compilation will show "0 error(s), 0 warning(s)"

### Step 3: Attach to Chart

1. In MT5, open the chart for your desired symbol (e.g., EURUSD, XAUUSD)
2. Go to **Navigator** → **Expert Advisors**
3. Find **MultiAgentEA** and drag it onto the chart
4. Configure input parameters (see Configuration section)
5. Enable **AutoTrading** (Ctrl+E or click the AutoTrading button)

## 🔧 Configuration

### Essential Parameters

#### Risk Management
```
RiskPercent = 1.0              // Risk 1% of account per trade
MaxDrawdownPercent = 10.0      // Stop trading if drawdown exceeds 10%
MaxOpenTrades = 3              // Maximum 3 concurrent positions
MaxTradesPerSymbol = 1         // Maximum 1 trade per symbol
MaxSpreadPoints = 30           // Maximum allowed spread in points
```

#### Stop Loss & Take Profit
```
RiskRewardRatio = 2.0          // TP is 2x the SL
UseATRForSL = true             // Use ATR for dynamic SL
ATRMultiplier = 1.5            // SL = ATR × 1.5
FixedSLPoints = 500            // Fixed SL if ATR is disabled (50 pips for 5-digit)
```

#### Trailing Stop
```
UseTrailingStop = true         // Enable trailing stop
TrailingStartRR = 1.0          // Start trailing when profit = 1R
TrailingStepPoints = 50        // Trail by 5 pips (for 5-digit)
```

#### Break Even
```
UseBreakEven = true            // Enable break even
BreakEvenAtRR = 0.5            // Move to BE when profit = 0.5R
BreakEvenPlusPoints = 10       // Add 1 pip above BE
```

#### Agent Weights
```
TrendAgentWeight = 1.0         // Standard weight
SMCAgentWeight = 1.0           // Standard weight
WaveAgentWeight = 0.8          // Slightly lower weight
```

#### Confidence Thresholds
```
MinConfidenceForex = 75.0      // Minimum 75% for Forex pairs
MinConfidenceGold = 80.0       // Minimum 80% for Gold (more volatile)
MinConfidenceCrypto = 70.0     // Minimum 70% for Crypto
```

### Recommended Settings by Market

#### EURUSD, GBPUSD (Forex Majors)
```
RiskPercent = 1.0
MaxSpreadPoints = 20
MinConfidenceForex = 75.0
UseATRForSL = true
ATRMultiplier = 1.5
RiskRewardRatio = 2.0
```

#### XAUUSD (Gold)
```
RiskPercent = 0.5              // Lower risk due to volatility
MaxSpreadPoints = 50           // Gold has wider spreads
MinConfidenceGold = 80.0       // Higher confidence required
UseATRForSL = true
ATRMultiplier = 2.0            // Wider SL for gold
RiskRewardRatio = 2.5
```

#### BTCUSD (Crypto)
```
RiskPercent = 0.5
MaxSpreadPoints = 100          // Crypto spreads can be wide
MinConfidenceCrypto = 70.0
UseATRForSL = true
ATRMultiplier = 2.0
RiskRewardRatio = 3.0          // Higher RR for crypto
```

## 📱 Dashboard

When `ShowDashboard = true`, the EA displays a real-time dashboard on the chart:

```
┌─────────────────────────────────────┐
│     Multi-Agent EA v1.0             │
├─────────────────────────────────────┤
│ Status: RUNNING                     │
│ Symbol: EURUSD                      │
│ Spread: 1.2 pips ✓                  │
├─────────────────────────────────────┤
│ AGENTS:                             │
│ ├─ Trend:    BUY  (85%)  ●          │
│ ├─ SMC:      BUY  (72%)  ●          │
│ ├─ Wave:     NEUTRAL     ○          │
│ └─ Stats:    ALLOW       ✓          │
├─────────────────────────────────────┤
│ Final: BUY | Confidence: 78%        │
├─────────────────────────────────────┤
│ Open Trades: 1/3                    │
│ Today P/L: +125.50 USD              │
│ Drawdown: 2.3%                      │
└─────────────────────────────────────┘
```

### Dashboard Elements

- **Status**: EA running status
- **Symbol**: Current trading symbol
- **Spread**: Current spread with validation indicator
- **Agent Signals**: Individual agent decisions and confidence
- **Final Decision**: Aggregated signal and confidence
- **Position Info**: Current positions and P/L
- **Risk Metrics**: Daily P/L and drawdown percentage

## 🛡️ Safety Features

### 1. Risk Management
- **Position Sizing**: Automatic lot calculation based on risk percentage
- **Drawdown Protection**: Stops trading when max drawdown is reached
- **Daily Loss Limit**: Prevents excessive daily losses
- **Margin Check**: Validates sufficient margin before opening trades

### 2. Trade Validation
- **Spread Filter**: Blocks trades when spread is too wide
- **Time Filter**: Avoids trading during off-hours and weekends
- **ATR Filter**: Ensures adequate volatility for trading
- **Market Status**: Checks if market is open

### 3. Position Management
- **Max Positions**: Limits total concurrent positions
- **Symbol Limit**: Limits positions per symbol
- **Trailing Stop**: Locks in profits as trade moves favorably
- **Break Even**: Protects capital by moving SL to entry

### 4. Error Handling
- **Magic Number**: Uniquely identifies EA's trades
- **Retry Logic**: Handles temporary connection issues
- **Logging**: Comprehensive logging for debugging

## 📝 Usage Guide

### Starting the EA

1. **Choose Your Symbol**: Select a chart (H1 or H4 recommended)
2. **Attach EA**: Drag MultiAgentEA onto the chart
3. **Configure**: Set your risk parameters
4. **Enable AutoTrading**: Click the AutoTrading button in MT5
5. **Monitor**: Watch the dashboard for signals and trades

### Monitoring Performance

- **Check Daily**: Review the dashboard daily for P/L and drawdown
- **Review Logs**: Check the **Experts** tab for detailed logs
- **Adjust Parameters**: Fine-tune based on performance
- **Backtest**: Use Strategy Tester to validate settings

### Best Practices

1. **Start Small**: Begin with minimum risk (0.5-1%)
2. **One Symbol**: Test on one symbol before expanding
3. **Monitor First Week**: Watch closely during the first week
4. **Keep Logs**: Save logs for performance analysis
5. **Update Settings**: Adjust based on market conditions

## 🔍 Troubleshooting

### EA Not Trading

**Check:**
- ✅ AutoTrading is enabled (Ctrl+E)
- ✅ EA shows "RUNNING" status in dashboard
- ✅ Statistical Agent shows "ALLOW" (not BLOCK)
- ✅ Spread is within limits
- ✅ Trading hours are correct
- ✅ Account has sufficient margin

### High Spread Error

**Solution:**
- Increase `MaxSpreadPoints` parameter
- Trade during active market hours
- Check broker spread conditions

### No Signals Generated

**Possible Reasons:**
- Market conditions don't meet criteria
- Confidence below threshold
- No agent consensus (< 2 agents agree)
- Time filter blocking trades

**Solution:**
- Lower confidence thresholds slightly
- Adjust agent weights
- Review time filter settings

### Compilation Errors

**Common Issues:**
1. **Missing Files**: Ensure all .mqh files are in correct folders
2. **Path Issues**: Check that #include paths match your directory structure
3. **MT5 Version**: Ensure MT5 build 3000+ is installed

**Fix:**
- Reinstall files in correct structure
- Update MT5 to latest version
- Check MetaEditor errors tab for specific issues

### Dashboard Not Showing

**Fix:**
- Set `ShowDashboard = true` in inputs
- Remove EA and re-attach to chart
- Check if objects are hidden (Ctrl+H)

## 📊 Performance Optimization

### For Ranging Markets
```
TrendAgentWeight = 0.5         // Reduce trend agent influence
SMCAgentWeight = 1.5           // Increase SMC agent weight
MinConfidence = 80.0           // Require higher confidence
```

### For Trending Markets
```
TrendAgentWeight = 1.5         // Increase trend agent influence
WaveAgentWeight = 1.2          // Increase wave agent weight
TrailingStartRR = 0.5          // Start trailing earlier
```

### For Volatile Markets (Gold, Crypto)
```
ATRMultiplier = 2.0            // Wider stop loss
RiskPercent = 0.5              // Lower risk per trade
MaxSpreadPoints = 100          // Allow wider spreads
MinConfidence = 85.0           // Higher confidence required
```

## 🌐 Multi-Language Support

### English Documentation
This README provides complete English documentation.

### Arabic Documentation (الوثائق العربية)

#### التثبيت
1. افتح ميتاتريدر 5
2. اذهب إلى ملف → فتح مجلد البيانات
3. انتقل إلى MQL5/Experts/
4. انسخ جميع ملفات EA مع الحفاظ على الهيكل

#### الإعدادات الموصى بها
- **المخاطرة لكل صفقة**: 1٪
- **نسبة المخاطرة/المكافأة**: 2.0
- **الحد الأقصى للسبريد**: 30 نقطة
- **استخدام ATR للإيقاف**: نعم

#### الأمان
- حماية السحب الأقصى: 10٪
- حد الخسارة اليومية: 3٪
- الحد الأقصى للصفقات: 3

## 🔄 Version History

### v1.0 (Current)
- Initial release
- 4 specialized agents (Trend, SMC, Wave, Statistical)
- Complete risk management system
- Real-time dashboard
- Multi-market support (Forex, Gold, Crypto)
- Comprehensive safety features

## 📞 Support

For issues, questions, or suggestions:
- **GitHub**: https://github.com/shadysoft/multi-agent-trading
- **Issues**: Report bugs via GitHub Issues

## ⚠️ Disclaimer

**IMPORTANT**: Trading forex, gold, and cryptocurrencies carries a high level of risk and may not be suitable for all investors. Past performance is not indicative of future results. This EA is provided for educational purposes. Always test thoroughly on a demo account before using real money.

## 📄 License

Copyright © 2024 Multi-Agent Trading System
All rights reserved.

---

**Happy Trading! 🚀**
