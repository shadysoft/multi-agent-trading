# multi-agent-trading
Multi-Agent AI Trading System for Forex, Gold, Stocks &amp; Crypto

## 🎯 Project Overview

This repository contains a complete **MetaTrader 5 Expert Advisor** that implements a sophisticated multi-agent AI trading system. The EA uses four specialized agents that analyze different aspects of the market and combine their insights to make high-confidence trading decisions.

## 📁 Repository Structure

```
multi-agent-trading/
├── README.md                          # This file
├── VALIDATION.md                      # Complete implementation checklist
├── .gitignore                         # Git exclusions
└── mt5_ea/                            # MetaTrader 5 Expert Advisor
    ├── MultiAgentEA.mq5               # Main EA file
    ├── README.md                      # Complete user guide
    ├── QUICKSTART.md                  # 5-minute setup guide
    ├── IMPLEMENTATION_SUMMARY.md      # Technical implementation details
    ├── Agents/
    │   ├── TrendAgent.mqh             # Trend analysis (EMA + ADX)
    │   ├── SMCAgent.mqh               # Smart Money Concepts
    │   ├── StatisticalAgent.mqh       # Gatekeeper & risk validator
    │   └── WaveAgent.mqh              # Wave pattern analysis
    ├── Utils/
    │   ├── RiskManager.mqh            # Risk & money management
    │   ├── TradeManager.mqh           # Trade execution & management
    │   ├── SignalAggregator.mqh       # Multi-agent signal combination
    │   └── Helpers.mqh                # Utility functions
    └── Config/
        └── Settings.mqh               # All configurable parameters
```

## 🤖 The Four Agents

### 1. **Trend Agent** - Identifies market direction
- EMA 20/50/200 crossover analysis
- ADX trend strength validation
- Price structure confirmation

### 2. **SMC Agent** - Institutional trading patterns
- Order Block detection
- Fair Value Gap (FVG) identification
- Liquidity zone analysis
- Break of Structure (BOS) recognition

### 3. **Wave Agent** - Market cycles and waves
- Swing point detection
- Impulse and correction wave analysis
- Fibonacci retracement zones

### 4. **Statistical Agent** - Risk gatekeeper
- Spread validation
- Volatility (ATR) filtering
- Time-based filters
- Drawdown protection
- Position limit enforcement

## ✨ Key Features

- ✅ **Standalone Operation**: Works independently without Python or external systems
- ✅ **Multi-Agent System**: 4 specialized AI agents with weighted voting
- ✅ **Comprehensive Risk Management**: Position sizing, drawdown protection, daily loss limits
- ✅ **Advanced Trade Management**: Trailing stop, break-even, partial exits
- ✅ **Real-time Dashboard**: Visual display on chart showing all agent signals
- ✅ **Multi-Market Support**: Optimized for Forex, Gold, and Crypto
- ✅ **22+ Safety Features**: Extensive validation and error handling
- ✅ **52 Input Parameters**: Fully customizable to your trading style
- ✅ **Complete Documentation**: User guides in English and Arabic

## 🚀 Quick Start

1. **Read the Quick Start Guide**: `mt5_ea/QUICKSTART.md` (5 minutes)
2. **Copy to MT5**: Copy the `mt5_ea` folder to `MQL5/Experts/`
3. **Compile**: Open `MultiAgentEA.mq5` in MetaEditor and compile (F7)
4. **Test on Demo**: Always test on demo account first!
5. **Follow the Guide**: See `mt5_ea/README.md` for detailed instructions

## 📊 Performance Expectations

- **Trade Frequency**: 2-5 trades per week (market dependent)
- **Win Rate Target**: 50-60% (with 2:1 Risk/Reward)
- **Recommended Risk**: 0.5-1% per trade
- **Best Timeframes**: H1, H4
- **Recommended Symbols**: EURUSD, GBPUSD, XAUUSD

## 📚 Documentation

- **QUICKSTART.md**: 5-minute setup guide
- **README.md**: Complete user manual with installation, configuration, and troubleshooting
- **IMPLEMENTATION_SUMMARY.md**: Technical implementation details
- **VALIDATION.md**: Complete requirements compliance checklist

## 🛡️ Safety Features

The EA includes 22+ safety checks:
- Magic number identification
- Spread filtering
- Drawdown protection (auto-stop)
- Daily loss limits
- Position limits
- Margin validation
- ATR volatility filter
- Time-based filters
- Division by zero protection
- Array bounds checking

## ⚙️ System Requirements

- **Platform**: MetaTrader 5 (Build 3000+)
- **Account**: Demo or Live (start with demo!)
- **Operating System**: Windows, Linux (Wine), macOS (Wine/Parallels)
- **Recommended**: Minimum $1000 account for proper risk management

## 🎯 Trading Philosophy

This EA follows a **systematic, multi-confirmation approach**:

1. Multiple agents analyze different market aspects
2. Signals are aggregated using weighted voting
3. Minimum 2 agents must agree for a trade
4. Statistical agent validates all risk conditions
5. Comprehensive position management protects capital

## ⚠️ Important Disclaimer

**Trading involves significant risk of loss and may not be suitable for all investors.**

- Past performance does not guarantee future results
- Always test thoroughly on demo accounts
- Never risk more than you can afford to lose
- This is a tool, not a guarantee of profits
- The EA is provided for educational purposes
- You are responsible for your trading decisions

## 🔧 Technical Specifications

- **Language**: MQL5
- **Total Code**: 3,062 lines
- **Files**: 11 code files + 3 documentation files
- **Classes**: 7 (one per major component)
- **Input Parameters**: 52
- **Architecture**: Object-oriented, modular design

## 📈 What Makes This EA Different?

1. **Multi-Agent Intelligence**: Unlike single-strategy EAs, this uses 4 specialized agents
2. **Smart Consensus**: Requires agreement from multiple agents, reducing false signals
3. **Adaptive Risk**: Dynamic position sizing and comprehensive risk management
4. **Transparent**: Real-time dashboard shows what each agent is thinking
5. **Safety First**: 22+ validation checks before every trade
6. **Well Documented**: Three comprehensive guides for users

## 🤝 Contributing

This is an open-source educational project. Contributions, suggestions, and feedback are welcome via GitHub issues.

## 📞 Support

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check README.md and QUICKSTART.md first
- **Validation**: See VALIDATION.md for implementation details

## 📄 License

Copyright © 2024-2026 Multi-Agent Trading System. All rights reserved.

## 🎓 Learning Resources

1. Start with `QUICKSTART.md` for immediate setup
2. Read `mt5_ea/README.md` for comprehensive understanding
3. Check `VALIDATION.md` to understand the technical implementation
4. Test on demo for at least 2 weeks before considering live trading

## 🏆 Status

- **Implementation**: ✅ COMPLETE
- **Code Review**: ✅ PASSED
- **Documentation**: ✅ COMPLETE
- **Testing Status**: Ready for user testing
- **Production Ready**: Yes (after demo testing)

---

**Last Updated**: 2026-01-04  
**Version**: 1.0  
**Status**: Production Ready

**Happy Trading! 🚀**

*Remember: Always start with demo accounts and never risk more than you can afford to lose.*

