//+------------------------------------------------------------------+
//|                                                     Settings.mqh |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| Enumerations                                                     |
//+------------------------------------------------------------------+
enum ENUM_SIGNAL_TYPE
{
   SIGNAL_BUY = 1,
   SIGNAL_SELL = -1,
   SIGNAL_NEUTRAL = 0
};

enum ENUM_TRADE_DECISION
{
   ALLOW_TRADE = 1,
   BLOCK_TRADE = 0
};

//+------------------------------------------------------------------+
//| General Settings                                                 |
//+------------------------------------------------------------------+
input group "=== General Settings ==="
input string EA_Name = "Multi-Agent EA v1.0";        // EA Name
input int MagicNumber = 123456;                      // Magic Number
input ENUM_TIMEFRAMES Timeframe = PERIOD_H1;         // Analysis Timeframe

//+------------------------------------------------------------------+
//| Risk Management Settings                                         |
//+------------------------------------------------------------------+
input group "=== Risk Management ==="
input double RiskPercent = 1.0;                      // Risk per trade (%)
input double MaxDrawdownPercent = 10.0;              // Max drawdown before stop (%)
input int MaxOpenTrades = 3;                         // Max concurrent trades
input int MaxTradesPerSymbol = 1;                    // Max trades per symbol
input double MaxSpreadPoints = 30;                   // Max allowed spread (points)
input double MaxDailyLossPercent = 3.0;              // Max daily loss (%)

//+------------------------------------------------------------------+
//| Take Profit & Stop Loss Settings                                |
//+------------------------------------------------------------------+
input group "=== Take Profit & Stop Loss ==="
input double RiskRewardRatio = 2.0;                  // TP = SL * RR
input bool UseATRForSL = true;                       // Use ATR for SL calculation
input double ATRMultiplier = 1.5;                    // SL = ATR * Multiplier
input int ATRPeriod = 14;                            // ATR Period
input int FixedSLPoints = 500;                       // Fixed SL if not using ATR (points)

//+------------------------------------------------------------------+
//| Trailing Stop Settings                                           |
//+------------------------------------------------------------------+
input group "=== Trailing Stop ==="
input bool UseTrailingStop = true;                   // Enable trailing stop
input double TrailingStartRR = 1.0;                  // Start trailing at profit (R)
input double TrailingStepPoints = 50;                // Trailing step (points)

//+------------------------------------------------------------------+
//| Break Even Settings                                              |
//+------------------------------------------------------------------+
input group "=== Break Even ==="
input bool UseBreakEven = true;                      // Enable break even
input double BreakEvenAtRR = 0.5;                    // Move to BE at profit (R)
input double BreakEvenPlusPoints = 10;               // Extra points above BE

//+------------------------------------------------------------------+
//| Agent Weights                                                    |
//+------------------------------------------------------------------+
input group "=== Agent Weights ==="
input double TrendAgentWeight = 1.0;                 // Trend Agent Weight
input double SMCAgentWeight = 1.0;                   // SMC Agent Weight
input double WaveAgentWeight = 0.8;                  // Wave Agent Weight

//+------------------------------------------------------------------+
//| Confidence Thresholds                                            |
//+------------------------------------------------------------------+
input group "=== Confidence Thresholds ==="
input double MinConfidenceForex = 75.0;              // Min confidence for Forex (%)
input double MinConfidenceGold = 80.0;               // Min confidence for Gold (%)
input double MinConfidenceCrypto = 70.0;             // Min confidence for Crypto (%)
input double MinConfidenceDefault = 75.0;            // Min confidence for other (%)

//+------------------------------------------------------------------+
//| Time Filter Settings                                             |
//+------------------------------------------------------------------+
input group "=== Time Filter ==="
input bool UseTimeFilter = true;                     // Enable time filter
input int TradingStartHour = 8;                      // Trading start hour
input int TradingEndHour = 20;                       // Trading end hour
input bool AvoidFriday = true;                       // Avoid Friday late trading
input int FridayStopHour = 18;                       // Stop trading on Friday at

//+------------------------------------------------------------------+
//| Trend Agent Settings                                             |
//+------------------------------------------------------------------+
input group "=== Trend Agent Settings ==="
input int EMA_Fast = 20;                             // Fast EMA Period
input int EMA_Medium = 50;                           // Medium EMA Period
input int EMA_Slow = 200;                            // Slow EMA Period
input int ADX_Period = 14;                           // ADX Period
input double ADX_Threshold = 25.0;                   // ADX Threshold

//+------------------------------------------------------------------+
//| SMC Agent Settings                                               |
//+------------------------------------------------------------------+
input group "=== SMC Agent Settings ==="
input int OrderBlock_Lookback = 20;                  // Order Block Lookback
input int FVG_MinGapPoints = 50;                     // Min FVG Gap (points)
input int LiquidityZone_Touches = 3;                 // Liquidity Zone Min Touches

//+------------------------------------------------------------------+
//| Wave Agent Settings                                              |
//+------------------------------------------------------------------+
input group "=== Wave Agent Settings ==="
input int Wave_ZigZagDepth = 12;                     // ZigZag Depth
input int Wave_ZigZagDeviation = 5;                  // ZigZag Deviation
input int Wave_ZigZagBackstep = 3;                   // ZigZag Backstep
input int Wave_MinSwingPoints = 100;                 // Min Swing Size (points)

//+------------------------------------------------------------------+
//| Statistical Agent Settings                                       |
//+------------------------------------------------------------------+
input group "=== Statistical Agent Settings ==="
input double ATR_MinValue = 0.0001;                  // Min ATR Value
input double ATR_MaxValue = 0.01;                    // Max ATR Value (0 = no limit)
input int Stats_ATRPeriod = 14;                      // Statistical ATR Period

//+------------------------------------------------------------------+
//| Display Settings                                                 |
//+------------------------------------------------------------------+
input group "=== Display Settings ==="
input bool ShowDashboard = true;                     // Show Dashboard
input color BuyColor = clrLime;                      // Buy Signal Color
input color SellColor = clrRed;                      // Sell Signal Color
input color NeutralColor = clrGray;                  // Neutral Color
input int Dashboard_FontSize = 9;                    // Dashboard Font Size
input string Dashboard_Font = "Consolas";            // Dashboard Font

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
string g_symbol;
double g_point;
double g_tick_size;
double g_tick_value;
int g_digits;

//+------------------------------------------------------------------+
//| Initialize global variables                                      |
//+------------------------------------------------------------------+
void InitSettings()
{
   g_symbol = _Symbol;
   g_point = _Point;
   g_tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   g_tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   g_digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
}
