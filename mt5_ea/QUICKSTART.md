# Multi-Agent EA - Quick Start Guide

## ⚡ Quick Installation (5 Minutes)

### Step 1: Download Files
1. Download all files from the `mt5_ea` folder
2. Keep the folder structure intact

### Step 2: Copy to MT5
1. Open MetaTrader 5
2. Press `F4` or click **Tools → MetaQuotes Language Editor**
3. In MetaEditor, click **File → Open Data Folder**
4. Navigate to `MQL5/Experts/`
5. Copy the entire `mt5_ea` folder here
6. Your path should be: `MQL5/Experts/mt5_ea/`

### Step 3: Compile
1. In MetaEditor, navigate to **Experts → mt5_ea → MultiAgentEA.mq5**
2. Double-click to open the file
3. Click **Compile** button (F7)
4. Check for "0 error(s), 0 warning(s)" message
5. Close MetaEditor

### Step 4: Attach to Chart
1. In MT5, open a chart (EURUSD H1 recommended for testing)
2. In **Navigator** panel (Ctrl+N), expand **Expert Advisors**
3. Find **MultiAgentEA** and drag it onto the chart
4. Click **OK** on the settings dialog (use defaults for now)
5. Enable **AutoTrading** (Ctrl+E or click the button in toolbar)

### Step 5: Verify
✅ Green smiley face appears in top-right of chart  
✅ Dashboard appears in top-left corner  
✅ Experts tab shows "Multi-Agent EA v1.0 - Initializing..."  
✅ Status shows "RUNNING"

## 🎯 Recommended First-Time Settings

```
Symbol: EURUSD
Timeframe: H1
Account Type: DEMO (always test first!)

Risk Settings:
├─ RiskPercent: 0.5%          (start low!)
├─ MaxOpenTrades: 1            (one at a time)
├─ MaxSpreadPoints: 20
└─ MaxDrawdownPercent: 5%      (conservative)

Other Settings:
├─ UseATRForSL: true
├─ RiskRewardRatio: 2.0
├─ UseTrailingStop: true
├─ UseBreakEven: true
└─ ShowDashboard: true
```

## 📊 What to Monitor

### First 24 Hours
- [ ] Check that dashboard updates on each new bar
- [ ] Verify spread checking works (spread should show ✓)
- [ ] Monitor agent signals (should change based on market)
- [ ] Watch for "Statistical Agent: ALLOW" messages

### First Week
- [ ] Monitor if trades are being opened
- [ ] Check if SL/TP levels are appropriate
- [ ] Verify trailing stop activates when in profit
- [ ] Review daily P/L accuracy
- [ ] Check drawdown calculation

### First Month
- [ ] Analyze win rate and average R multiple
- [ ] Review which agents give best signals
- [ ] Optimize agent weights if needed
- [ ] Test on different symbols

## 🚨 Troubleshooting

### No Dashboard?
- Set `ShowDashboard = true`
- Remove EA and re-attach
- Press Ctrl+H to show hidden objects

### Spread Too High Error?
- Increase `MaxSpreadPoints` (try 30-50)
- Trade during active hours (8am-8pm broker time)

### No Trades Opening?
- Check "Statistical Agent" shows "ALLOW"
- Lower `MinConfidenceForex` from 75 to 65
- Check account has sufficient margin
- Ensure market is open

### Compilation Errors?
- Verify all files are in correct folders
- Check MT5 version (needs Build 3000+)
- Update MT5 to latest version

## 🎓 Learning Path

### Week 1: Observation
- Run on DEMO only
- Don't modify settings
- Learn what each agent does
- Watch dashboard changes

### Week 2: Understanding
- Review the logs
- Understand why trades opened/didn't open
- Learn the signal aggregation logic
- Read agent descriptions

### Week 3: Optimization
- Adjust agent weights
- Test different confidence thresholds
- Try different symbols
- Fine-tune risk settings

### Week 4: Advanced
- Optimize for specific market conditions
- Create custom settings per symbol
- Analyze performance metrics
- Consider live testing (small account)

## 💡 Pro Tips

1. **Start Conservative**: Use 0.5% risk, max 1 trade
2. **Use DEMO First**: Test for minimum 2 weeks
3. **One Symbol**: Master one symbol before expanding
4. **Monitor Daily**: Check dashboard and logs daily
5. **Keep Logs**: Save performance data for analysis
6. **Update Settings**: Market conditions change, adjust accordingly
7. **Respect the Gatekeeper**: If Statistical Agent blocks, don't override
8. **Trust the Process**: Agents need data to work effectively

## 📈 Expected Behavior

### Normal Operation
```
✅ Dashboard updates every new bar
✅ Agents show different signals
✅ Statistical Agent mostly shows ALLOW
✅ Some bars have no trading signal (this is normal!)
✅ Trades have proper SL/TP
✅ Trailing stop activates in profit
```

### Warning Signs
```
⚠️ Dashboard not updating
⚠️ All agents always NEUTRAL
⚠️ Statistical Agent always BLOCK
⚠️ No trades after 1 week
⚠️ Trades without SL/TP
⚠️ Excessive losing streak
```

## 📞 Getting Help

1. **Check Logs**: Experts tab has detailed info
2. **Read README**: Full documentation available
3. **Review Settings**: Verify all parameters
4. **Test on DEMO**: Never skip demo testing
5. **GitHub Issues**: Report bugs with logs

## ⚡ Performance Expectations

### Realistic Goals (DEMO Testing)
- **Trade Frequency**: 2-5 trades per week (depends on market)
- **Win Rate**: 50-60% (with 2:1 RR, this is profitable)
- **Max Drawdown**: Should stay under 10%
- **Monthly Return**: 3-8% (varies by risk settings)

### Remember
- Past performance ≠ future results
- Demo results ≠ live results
- Always risk only what you can afford to lose
- This is a tool, not a guarantee

---

**Good Luck! Trade Responsibly! 🚀**

*Last Updated: 2026-01-04*
