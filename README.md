# 🤖 Multi-Agent AI Trading System

**[English](#english) | [العربية](#arabic)**

---

<a name="english"></a>
## 📊 Overview

A sophisticated automated trading system powered by multiple AI agents that analyze Forex, Gold, Stocks, and Cryptocurrency markets. The system uses intelligent agent collaboration and adaptive learning to generate high-confidence trading signals.

### ✨ Key Features

- **🤖 5 Specialized AI Agents**: Trend, Smart Money Concepts, Statistical, Wave, and Learning agents
- **📈 Multi-Market Support**: Forex, Gold/Commodities, Stocks, and Crypto
- **🎯 Meta-Agent Decision Making**: Aggregates signals with weighted confidence scoring
- **🛡️ Advanced Risk Management**: Position sizing, drawdown protection, correlation analysis
- **📊 Real-time Dashboard**: Streamlit-based web interface with performance metrics
- **🔄 Adaptive Learning**: Automatically adjusts agent weights based on performance
- **⚙️ MetaTrader 5 Integration**: Direct execution through MT5 platform
- **📱 Alerts & Notifications**: Real-time alerts for critical events

### 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Market Data (MT5)                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Trading Agents Layer                       │
│  ┌────────┐ ┌─────┐ ┌──────────┐ ┌──────┐ ┌──────────┐    │
│  │ Trend  │ │ SMC │ │Statistical│ │ Wave │ │ Learning │    │
│  │ Agent  │ │Agent│ │  Agent    │ │Agent │ │  Agent   │    │
│  └────────┘ └─────┘ └──────────┘ └──────┘ └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               Meta-Agent (Signal Aggregation)                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Risk Management Layer                      │
│         ┌─────────────┐  ┌──────────────────┐              │
│         │Risk Manager │  │Correlation Matrix│              │
│         └─────────────┘  └──────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Execution Layer (MT5)                       │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- MetaTrader 5 terminal
- Broker account (demo or live)

### Installation

```bash
# Clone repository
git clone https://github.com/shadysoft/multi-agent-trading.git
cd multi-agent-trading

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MT5 credentials
```

### Configuration

Edit configuration files in `config/` directory:

- `settings.yaml` - General system settings
- `forex_config.yaml` - Forex trading parameters
- `gold_config.yaml` - Gold/Commodities settings
- `stocks_config.yaml` - Stock trading settings
- `crypto_config.yaml` - Cryptocurrency settings

### Running the System

```bash
# Start the trading system
python main.py

# Launch dashboard (in separate terminal)
streamlit run dashboard/app.py
```

## 📖 Documentation

- [Architecture Guide](docs/architecture.md) - System design and components
- [Agent Guide](docs/agents_guide.md) - Detailed agent documentation
- [Setup Guide](docs/setup_guide.md) - Complete setup instructions

## 🤖 Trading Agents

### 1. **Trend Agent** (25% weight)
- EMA crossovers (20, 50, 200)
- ADX trend strength
- Price structure analysis

### 2. **SMC Agent** (25% weight)
- Liquidity zones
- Order blocks
- Fair Value Gaps (FVG)

### 3. **Statistical Agent** (20% weight)
- Spread validation
- ATR volatility checks
- Position count monitoring

### 4. **Wave Agent** (20% weight)
- Impulse vs correction waves
- Momentum analysis
- Wave counting

### 5. **Learning Agent** (10% weight)
- Performance tracking
- Adaptive weight adjustment
- Losing streak detection

## 📊 Dashboard

Access the web dashboard at `http://localhost:8501` after launching:

- **Overview**: System-wide metrics, equity curve, P&L
- **Markets**: Individual market performance (Forex, Gold, Stocks, Crypto)
- **Alerts**: Real-time notifications and warnings
- **Settings**: Configuration management

## 🛡️ Risk Management

- **Position Sizing**: Automatic calculation based on account risk
- **Daily Loss Limit**: Maximum 2% daily loss (configurable)
- **Drawdown Protection**: Stops trading at 10% drawdown
- **Correlation Control**: Maximum 70% correlation between positions
- **Max Concurrent Trades**: Limit to 5 simultaneous positions

## 🔧 Configuration Example

```yaml
# config/forex_config.yaml
active_symbols:
  - "EURUSD"
  - "GBPUSD"
  - "USDJPY"

meta_agent:
  confidence_threshold: 0.75  # 75% for forex

risk:
  max_spread_pips: 2.0
  min_atr_pips: 10.0
  risk_per_trade_percent: 1.0
```

## 📈 Performance Metrics

The system tracks:
- Win Rate
- Profit Factor
- Maximum Drawdown
- Average R:R Ratio
- Sharpe Ratio
- Individual Agent Performance

## ⚠️ Important Notes

1. **Paper Trading First**: Always test with paper trading before going live
2. **Risk Management**: Never risk more than you can afford to lose
3. **Monitoring**: Regularly check system logs and dashboard
4. **Broker Selection**: Choose a reputable MT5 broker
5. **Internet Stability**: Ensure stable internet connection

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions welcome! Please read contributing guidelines before submitting PRs.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/shadysoft/multi-agent-trading/issues)
- **Documentation**: [Wiki](https://github.com/shadysoft/multi-agent-trading/wiki)

## ⚖️ Disclaimer

This software is for educational purposes only. Trading involves risk. Past performance does not guarantee future results. Always do your own research and consult with financial advisors before trading.

---

<a name="arabic"></a>
# 🤖 نظام التداول الذكي متعدد الوكلاء

## 📊 نظرة عامة

نظام تداول آلي متطور يعمل بواسطة وكلاء ذكاء اصطناعي متعددين لتحليل أسواق الفوركس والذهب والأسهم والعملات الرقمية. يستخدم النظام التعاون الذكي بين الوكلاء والتعلم التكيفي لتوليد إشارات تداول عالية الثقة.

### ✨ المميزات الرئيسية

- **🤖 5 وكلاء ذكاء اصطناعي متخصصين**: وكلاء الاتجاه، مفاهيم الأموال الذكية، الإحصائي، الموجات، والتعلم
- **📈 دعم أسواق متعددة**: الفوركس، الذهب/السلع، الأسهم، والعملات الرقمية
- **🎯 اتخاذ القرار بواسطة الوكيل الرئيسي**: تجميع الإشارات مع نظام تسجيل الثقة الموزون
- **🛡️ إدارة مخاطر متقدمة**: تحجيم المراكز، حماية من الانخفاض، تحليل الارتباط
- **📊 لوحة تحكم فورية**: واجهة ويب قائمة على Streamlit مع مقاييس الأداء
- **🔄 التعلم التكيفي**: ضبط تلقائي لأوزان الوكلاء بناءً على الأداء
- **⚙️ تكامل مع MetaTrader 5**: تنفيذ مباشر عبر منصة MT5
- **📱 تنبيهات وإشعارات**: تنبيهات فورية للأحداث الحرجة

### 🏗️ بنية النظام

النظام يتكون من طبقات متعددة تعمل بتناغم:

1. **طبقة البيانات**: جلب البيانات من MT5 وإدارة قاعدة البيانات
2. **طبقة الوكلاء**: 5 وكلاء متخصصين للتحليل المستقل
3. **الوكيل الرئيسي**: تجميع الإشارات واتخاذ القرار النهائي
4. **إدارة المخاطر**: التحقق من صحة الصفقات وحساب حجم المركز
5. **طبقة التنفيذ**: إرسال الأوامر إلى MT5

## 🚀 البدء السريع

### المتطلبات الأساسية

- Python 3.9 أو أحدث
- منصة MetaTrader 5
- حساب وسيط (تجريبي أو حقيقي)

### التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/shadysoft/multi-agent-trading.git
cd multi-agent-trading

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # على Windows: venv\Scripts\activate

# تثبيت المكتبات
pip install -r requirements.txt

# إعداد البيئة
cp .env.example .env
# قم بتحرير .env بإضافة بيانات اعتماد MT5 الخاصة بك
```

### التكوين

قم بتحرير ملفات التكوين في مجلد `config/`:

- `settings.yaml` - إعدادات النظام العامة
- `forex_config.yaml` - معاملات تداول الفوركس
- `gold_config.yaml` - إعدادات الذهب/السلع
- `stocks_config.yaml` - إعدادات تداول الأسهم
- `crypto_config.yaml` - إعدادات العملات الرقمية

### تشغيل النظام

```bash
# بدء نظام التداول
python main.py

# تشغيل لوحة التحكم (في نافذة طرفية منفصلة)
streamlit run dashboard/app.py
```

## 📖 التوثيق

- [دليل البنية](docs/architecture.md) - تصميم النظام والمكونات
- [دليل الوكلاء](docs/agents_guide.md) - توثيق تفصيلي للوكلاء
- [دليل الإعداد](docs/setup_guide.md) - تعليمات الإعداد الكاملة

## 🤖 وكلاء التداول

### 1. **وكيل الاتجاه** (وزن 25%)
- تقاطعات المتوسطات المتحركة (20، 50، 200)
- قوة الاتجاه ADX
- تحليل هيكل السعر

### 2. **وكيل مفاهيم الأموال الذكية** (وزن 25%)
- مناطق السيولة
- كتل الطلبات
- فجوات القيمة العادلة (FVG)

### 3. **الوكيل الإحصائي** (وزن 20%)
- التحقق من السبريد
- فحوصات التقلب ATR
- مراقبة عدد المراكز

### 4. **وكيل الموجات** (وزن 20%)
- موجات الدفع مقابل التصحيح
- تحليل الزخم
- عد الموجات

### 5. **وكيل التعلم** (وزن 10%)
- تتبع الأداء
- التعديل التكيفي للأوزان
- كشف سلسلة الخسائر

## 📊 لوحة التحكم

يمكن الوصول إلى لوحة تحكم الويب على `http://localhost:8501`:

- **نظرة عامة**: مقاييس النظام، منحنى رأس المال، الربح والخسارة
- **الأسواق**: أداء الأسواق الفردية (الفوركس، الذهب، الأسهم، العملات الرقمية)
- **التنبيهات**: إشعارات وتحذيرات فورية
- **الإعدادات**: إدارة التكوين

## 🛡️ إدارة المخاطر

- **تحجيم المركز**: حساب تلقائي بناءً على مخاطر الحساب
- **حد الخسارة اليومي**: حد أقصى 2% خسارة يومية (قابل للتكوين)
- **حماية الانخفاض**: إيقاف التداول عند انخفاض 10%
- **التحكم في الارتباط**: حد أقصى 70% ارتباط بين المراكز
- **الحد الأقصى للصفقات المتزامنة**: حد 5 مراكز في وقت واحد

## ⚠️ ملاحظات مهمة

1. **التداول الورقي أولاً**: اختبر دائماً بالتداول الورقي قبل التداول الحقيقي
2. **إدارة المخاطر**: لا تخاطر أبداً بأكثر مما يمكنك تحمل خسارته
3. **المراقبة**: تحقق بانتظام من سجلات النظام ولوحة التحكم
4. **اختيار الوسيط**: اختر وسيط MT5 موثوق
5. **استقرار الإنترنت**: تأكد من اتصال إنترنت مستقر

## 🧪 الاختبار

```bash
# تشغيل جميع الاختبارات
pytest

# تشغيل مع التغطية
pytest --cov=. --cov-report=html
```

## 📝 الترخيص

ترخيص MIT - انظر ملف [LICENSE](LICENSE) للتفاصيل

## ⚖️ إخلاء المسؤولية

هذا البرنامج لأغراض تعليمية فقط. التداول ينطوي على مخاطر. الأداء السابق لا يضمن النتائج المستقبلية. قم دائماً بإجراء بحثك الخاص واستشر المستشارين الماليين قبل التداول.

---

**Made with ❤️ by ShadySoft**
