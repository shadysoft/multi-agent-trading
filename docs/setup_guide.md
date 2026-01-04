# Setup Guide - Multi-Agent Trading System

## Prerequisites

### System Requirements
- Python 3.9 or higher
- MetaTrader 5 terminal (Windows, Linux via Wine, or Mac via CrossOver)
- 4GB RAM minimum (8GB recommended)
- Stable internet connection

### Required Accounts
- MetaTrader 5 broker account (demo or live)
- Optional: Telegram account (for alerts)
- Optional: Email account (for notifications)

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/shadysoft/multi-agent-trading.git
cd multi-agent-trading
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If `ta-lib` installation fails, you may need to install TA-Lib separately:

**Windows**:
1. Download TA-Lib from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
2. Install: `pip install TA_Lib‑0.4.XX‑cpXX‑cpXX‑winXX.whl`

**Linux**:
```bash
sudo apt-get install ta-lib
pip install ta-lib
```

**Mac**:
```bash
brew install ta-lib
pip install ta-lib
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

**Required Settings in .env**:
```env
# MetaTrader 5 Configuration
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# Database Configuration
DATABASE_URL=sqlite:///./trading.db

# Trading Configuration
ENABLE_LIVE_TRADING=False
ENABLE_PAPER_TRADING=True

# Risk Management
MAX_DAILY_LOSS_PERCENT=2.0
MAX_POSITION_SIZE_PERCENT=1.0
MAX_CONCURRENT_TRADES=5
```

### 5. Install MetaTrader 5 Expert Advisor

1. Copy `mt5_ea/TradingExecutor.mq5` to your MT5 experts folder:
   - **Windows**: `C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\`
   - **Where XXXXX** is your terminal ID

2. Open MetaTrader 5
3. Go to **Tools → Options → Expert Advisors**
4. Enable:
   - ✅ Allow algorithmic trading
   - ✅ Allow DLL imports
   - ✅ Allow external experts imports

5. Compile the EA:
   - Open MetaEditor (F4 in MT5)
   - Open TradingExecutor.mq5
   - Click Compile (F7)

6. Attach EA to chart:
   - Open any chart
   - Drag TradingExecutor from Navigator to chart
   - Click OK on settings dialog

---

## Configuration

### Market Configuration Files

Edit configuration files in `config/` directory:

#### General Settings (`config/settings.yaml`)
```yaml
trading:
  enable_live_trading: false
  enable_paper_trading: true
  default_timeframe: "H1"

risk_management:
  max_daily_loss_percent: 2.0
  max_position_size_percent: 1.0
  max_concurrent_trades: 5

agent_weights:
  trend_agent: 0.25
  smc_agent: 0.25
  statistical_agent: 0.20
  wave_agent: 0.20
  learning_agent: 0.10
```

#### Market-Specific Configs
- `forex_config.yaml`: Configure Forex pairs to trade
- `gold_config.yaml`: Configure gold and commodities
- `stocks_config.yaml`: Configure stock symbols
- `crypto_config.yaml`: Configure cryptocurrencies

**Example - Adding a new Forex pair**:
```yaml
# In forex_config.yaml
active_symbols:
  - "EURUSD"
  - "GBPUSD"
  - "USDJPY"
  - "AUDUSD"
  - "NZDUSD"  # Add new pair here
```

---

## Running the System

### 1. Start MetaTrader 5
- Launch MT5 terminal
- Ensure TradingExecutor EA is running on a chart
- Verify connection to broker server

### 2. Initialize Database

```bash
python -c "from data.database import DatabaseHandler; db = DatabaseHandler(); print('Database initialized')"
```

### 3. Run the Trading System

```bash
python main.py
```

The system will:
1. Initialize MT5 connection
2. Load configurations
3. Initialize all agents
4. Start analyzing markets
5. Generate and execute signals

### 4. Launch Dashboard (Optional)

In a separate terminal:

```bash
streamlit run dashboard/app.py
```

Access dashboard at: http://localhost:8501

---

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Paper Trading (Recommended First Step)

1. Set in `.env`:
```env
ENABLE_LIVE_TRADING=False
ENABLE_PAPER_TRADING=True
```

2. Run for at least 1-2 weeks
3. Review performance metrics
4. Adjust configurations as needed

### Backtesting

Use the Jupyter notebook:
```bash
jupyter notebook notebooks/backtesting_analysis.ipynb
```

---

## Going Live

⚠️ **IMPORTANT**: Only proceed after successful paper trading!

### Pre-Live Checklist

- [ ] Successfully paper traded for 2+ weeks
- [ ] Win rate meets expectations (>50%)
- [ ] Drawdown stays within limits (<5%)
- [ ] All agents performing consistently
- [ ] Risk parameters properly configured
- [ ] Sufficient account balance
- [ ] Emergency stop procedures understood

### Enable Live Trading

1. Update `.env`:
```env
ENABLE_LIVE_TRADING=True
ENABLE_PAPER_TRADING=False
```

2. Start with minimum position sizes
3. Monitor closely for first week
4. Gradually increase position sizes

---

## Monitoring & Maintenance

### Daily Tasks
1. Check dashboard for alerts
2. Review overnight trades
3. Verify MT5 connection
4. Check log files for errors

### Weekly Tasks
1. Review performance metrics
2. Analyze agent performance
3. Check correlation matrix
4. Review risk metrics
5. Backup database

### Monthly Tasks
1. Comprehensive performance review
2. Adjust agent weights if needed
3. Review and update configurations
4. System optimization

---

## Troubleshooting

### MT5 Connection Issues

**Problem**: "MT5 initialization failed"
```bash
# Solution 1: Check MT5 credentials in .env
# Solution 2: Ensure MT5 terminal is running
# Solution 3: Check MT5 logs in: Terminal/Logs/
```

**Problem**: "Order send failed"
```bash
# Check:
# 1. Algorithmic trading is enabled in MT5
# 2. Sufficient margin in account
# 3. Market is open for trading
# 4. Symbol is available
```

### Database Issues

**Problem**: "Database locked"
```bash
# Solution: Close any other processes accessing the database
# If persists, delete trading.db and reinitialize
```

### Agent Issues

**Problem**: "Agents always return WAIT"
```bash
# Check:
# 1. Sufficient historical data available (200+ bars)
# 2. Market is not ranging (ADX > 25)
# 3. Spread is within limits
# 4. Confidence thresholds not too high
```

### Performance Issues

**Problem**: "System running slow"
```bash
# Solutions:
# 1. Reduce number of active symbols
# 2. Increase analysis interval
# 3. Optimize database queries
# 4. Add more RAM
```

---

## Security Best Practices

### Credentials
- Never commit `.env` file to git
- Use strong passwords
- Enable 2FA on broker account
- Rotate API keys regularly

### Risk Management
- Start with small position sizes
- Set appropriate stop losses
- Monitor daily loss limits
- Use demo account first

### System Security
- Keep Python and dependencies updated
- Regular backups of database
- Monitor system logs
- Use firewall for external connections

---

## Getting Help

### Documentation
- [Architecture Guide](architecture.md)
- [Agent Guide](agents_guide.md)
- System logs: `logs/trading.log`

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share experiences

### Logs
Always check logs when troubleshooting:
```bash
tail -f logs/trading.log
```

---

## Updating the System

### Update Code

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Update Configuration

After updates, check for new configuration options:
```bash
# Compare your config with examples
diff config/settings.yaml config/settings.yaml.example
```

### Database Migrations

If database schema changes:
```bash
# Backup current database
cp trading.db trading.db.backup

# Run migrations (if provided)
python scripts/migrate_database.py
```

---

## Advanced Configuration

### Custom Agents

To add a custom agent:

1. Create file in `agents/custom_agent.py`
2. Extend `BaseAgent` class
3. Implement `analyze()` method
4. Add to `main.py` initialization
5. Update configuration with weight

### Custom Indicators

Add custom indicators in `BaseAgent`:
```python
def calculate_custom_indicator(self, data, period):
    # Your calculation
    return result
```

### Database Optimization

For PostgreSQL (production):

```env
DATABASE_URL=postgresql://user:password@localhost/trading_db
```

Benefits:
- Better performance
- Concurrent access
- Advanced features
- Better for multiple instances

---

## Performance Optimization

### 1. Reduce Timeframe Analysis
- Use H4 or D1 instead of M15
- Less frequent signal generation
- Lower CPU usage

### 2. Limit Active Symbols
- Start with 2-3 pairs
- Add more as system stabilizes
- Monitor resource usage

### 3. Optimize Database
```bash
# For SQLite
sqlite3 trading.db "VACUUM;"

# For PostgreSQL
psql -d trading_db -c "VACUUM ANALYZE;"
```

---

## Backup and Recovery

### Automated Backups

Create backup script:
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
cp trading.db backups/trading_$DATE.db
cp config/*.yaml backups/config_$DATE/
```

### Manual Backup
```bash
# Backup database
cp trading.db trading.db.backup

# Backup configs
tar -czf configs_backup.tar.gz config/
```

### Recovery
```bash
# Restore database
cp trading.db.backup trading.db

# Restore configs
tar -xzf configs_backup.tar.gz
```

---

## Next Steps

After successful setup:

1. ✅ Run paper trading
2. ✅ Monitor dashboard daily
3. ✅ Review agent performance weekly
4. ✅ Optimize configurations
5. ✅ Document your changes
6. ✅ Consider going live (after testing)

Good luck with your automated trading! 🚀
