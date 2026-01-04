//+------------------------------------------------------------------+
//|                                                      Helpers.mqh |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| Helper Functions                                                 |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Normalize price to valid tick size                              |
//+------------------------------------------------------------------+
double NormalizePrice(double price)
{
   double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   return NormalizeDouble(MathRound(price / tick_size) * tick_size, _Digits);
}

//+------------------------------------------------------------------+
//| Normalize lot size                                              |
//+------------------------------------------------------------------+
double NormalizeLot(double lot)
{
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   if(lot < min_lot) lot = min_lot;
   if(lot > max_lot) lot = max_lot;
   
   lot = NormalizeDouble(MathRound(lot / lot_step) * lot_step, 2);
   
   return lot;
}

//+------------------------------------------------------------------+
//| Convert points to price                                         |
//+------------------------------------------------------------------+
double PointsToPrice(double points)
{
   return points * _Point;
}

//+------------------------------------------------------------------+
//| Convert price to points                                         |
//+------------------------------------------------------------------+
double PriceToPoints(double price)
{
   return price / _Point;
}

//+------------------------------------------------------------------+
//| Get current spread in points                                    |
//+------------------------------------------------------------------+
double GetSpreadPoints()
{
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   return (ask - bid) / _Point;
}

//+------------------------------------------------------------------+
//| Check if market is open                                         |
//+------------------------------------------------------------------+
bool IsMarketOpen()
{
   datetime servertime = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(servertime, dt);
   
   // Check if it's weekend
   if(dt.day_of_week == 0 || dt.day_of_week == 6)
      return false;
      
   return true;
}

//+------------------------------------------------------------------+
//| Get symbol type                                                  |
//+------------------------------------------------------------------+
string GetSymbolType()
{
   string symbol = _Symbol;
   
   // Check for major forex pairs
   if(StringFind(symbol, "EUR") >= 0 || StringFind(symbol, "GBP") >= 0 || 
      StringFind(symbol, "USD") >= 0 || StringFind(symbol, "JPY") >= 0 ||
      StringFind(symbol, "AUD") >= 0 || StringFind(symbol, "NZD") >= 0 ||
      StringFind(symbol, "CAD") >= 0 || StringFind(symbol, "CHF") >= 0)
      return "FOREX";
   
   // Check for gold
   if(StringFind(symbol, "XAU") >= 0 || StringFind(symbol, "GOLD") >= 0)
      return "GOLD";
   
   // Check for crypto
   if(StringFind(symbol, "BTC") >= 0 || StringFind(symbol, "ETH") >= 0 ||
      StringFind(symbol, "XRP") >= 0 || StringFind(symbol, "LTC") >= 0)
      return "CRYPTO";
   
   return "OTHER";
}

//+------------------------------------------------------------------+
//| Count digits after decimal point                                |
//+------------------------------------------------------------------+
int GetDigits()
{
   return (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
}

//+------------------------------------------------------------------+
//| Check if new bar has formed                                     |
//+------------------------------------------------------------------+
bool IsNewBar()
{
   static datetime lastbar_time = 0;
   datetime current_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
   
   if(lastbar_time != current_bar)
   {
      lastbar_time = current_bar;
      return true;
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Get ATR value                                                    |
//+------------------------------------------------------------------+
double GetATR(int period, int shift = 0)
{
   double atr_array[];
   ArraySetAsSeries(atr_array, true);
   
   int atr_handle = iATR(_Symbol, PERIOD_CURRENT, period);
   if(atr_handle == INVALID_HANDLE)
   {
      Print("Failed to create ATR indicator");
      return 0;
   }
   
   if(CopyBuffer(atr_handle, 0, shift, 1, atr_array) <= 0)
   {
      Print("Failed to copy ATR buffer");
      IndicatorRelease(atr_handle);
      return 0;
   }
   
   double atr = atr_array[0];
   IndicatorRelease(atr_handle);
   
   return atr;
}

//+------------------------------------------------------------------+
//| Get EMA value                                                    |
//+------------------------------------------------------------------+
double GetEMA(int period, int shift = 0)
{
   double ema_array[];
   ArraySetAsSeries(ema_array, true);
   
   int ema_handle = iMA(_Symbol, PERIOD_CURRENT, period, 0, MODE_EMA, PRICE_CLOSE);
   if(ema_handle == INVALID_HANDLE)
   {
      Print("Failed to create EMA indicator");
      return 0;
   }
   
   if(CopyBuffer(ema_handle, 0, shift, 1, ema_array) <= 0)
   {
      Print("Failed to copy EMA buffer");
      IndicatorRelease(ema_handle);
      return 0;
   }
   
   double ema = ema_array[0];
   IndicatorRelease(ema_handle);
   
   return ema;
}

//+------------------------------------------------------------------+
//| Get ADX value                                                    |
//+------------------------------------------------------------------+
double GetADX(int period, int shift = 0)
{
   double adx_array[];
   ArraySetAsSeries(adx_array, true);
   
   int adx_handle = iADX(_Symbol, PERIOD_CURRENT, period);
   if(adx_handle == INVALID_HANDLE)
   {
      Print("Failed to create ADX indicator");
      return 0;
   }
   
   if(CopyBuffer(adx_handle, 0, shift, 1, adx_array) <= 0)
   {
      Print("Failed to copy ADX buffer");
      IndicatorRelease(adx_handle);
      return 0;
   }
   
   double adx = adx_array[0];
   IndicatorRelease(adx_handle);
   
   return adx;
}

//+------------------------------------------------------------------+
//| Format double to string with specific decimals                  |
//+------------------------------------------------------------------+
string FormatDouble(double value, int decimals)
{
   return DoubleToString(value, decimals);
}

//+------------------------------------------------------------------+
//| Log message with timestamp                                      |
//+------------------------------------------------------------------+
void LogMessage(string message)
{
   Print(TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS), " - ", message);
}

//+------------------------------------------------------------------+
//| Check if value is within range                                  |
//+------------------------------------------------------------------+
bool IsInRange(double value, double min_val, double max_val)
{
   return (value >= min_val && value <= max_val);
}

//+------------------------------------------------------------------+
//| Get higher high/lower low status                                |
//+------------------------------------------------------------------+
bool IsHigherHigh(int shift1, int shift2)
{
   double high1 = iHigh(_Symbol, PERIOD_CURRENT, shift1);
   double high2 = iHigh(_Symbol, PERIOD_CURRENT, shift2);
   return high1 > high2;
}

bool IsLowerLow(int shift1, int shift2)
{
   double low1 = iLow(_Symbol, PERIOD_CURRENT, shift1);
   double low2 = iLow(_Symbol, PERIOD_CURRENT, shift2);
   return low1 < low2;
}

//+------------------------------------------------------------------+
//| Calculate distance in points between two prices                 |
//+------------------------------------------------------------------+
double DistanceInPoints(double price1, double price2)
{
   return MathAbs(price1 - price2) / _Point;
}
