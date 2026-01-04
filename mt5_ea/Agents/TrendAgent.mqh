//+------------------------------------------------------------------+
//|                                                   TrendAgent.mqh |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property version   "1.00"
#property strict

#include "../Config/Settings.mqh"
#include "../Utils/Helpers.mqh"

//+------------------------------------------------------------------+
//| Trend Agent Class                                                |
//+------------------------------------------------------------------+
class CTrendAgent
{
private:
   int m_ema_fast_handle;
   int m_ema_medium_handle;
   int m_ema_slow_handle;
   int m_adx_handle;
   
public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   CTrendAgent()
   {
      m_ema_fast_handle = INVALID_HANDLE;
      m_ema_medium_handle = INVALID_HANDLE;
      m_ema_slow_handle = INVALID_HANDLE;
      m_adx_handle = INVALID_HANDLE;
      
      Initialize();
   }
   
   //+------------------------------------------------------------------+
   //| Destructor                                                       |
   //+------------------------------------------------------------------+
   ~CTrendAgent()
   {
      if(m_ema_fast_handle != INVALID_HANDLE)
         IndicatorRelease(m_ema_fast_handle);
      if(m_ema_medium_handle != INVALID_HANDLE)
         IndicatorRelease(m_ema_medium_handle);
      if(m_ema_slow_handle != INVALID_HANDLE)
         IndicatorRelease(m_ema_slow_handle);
      if(m_adx_handle != INVALID_HANDLE)
         IndicatorRelease(m_adx_handle);
   }
   
   //+------------------------------------------------------------------+
   //| Initialize indicators                                            |
   //+------------------------------------------------------------------+
   bool Initialize()
   {
      m_ema_fast_handle = iMA(_Symbol, PERIOD_CURRENT, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
      m_ema_medium_handle = iMA(_Symbol, PERIOD_CURRENT, EMA_Medium, 0, MODE_EMA, PRICE_CLOSE);
      m_ema_slow_handle = iMA(_Symbol, PERIOD_CURRENT, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
      m_adx_handle = iADX(_Symbol, PERIOD_CURRENT, ADX_Period);
      
      if(m_ema_fast_handle == INVALID_HANDLE || m_ema_medium_handle == INVALID_HANDLE ||
         m_ema_slow_handle == INVALID_HANDLE || m_adx_handle == INVALID_HANDLE)
      {
         LogMessage("TrendAgent: Failed to initialize indicators");
         return false;
      }
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Get EMA values                                                   |
   //+------------------------------------------------------------------+
   bool GetEMAValues(double &fast[], double &medium[], double &slow[], int count = 3)
   {
      ArraySetAsSeries(fast, true);
      ArraySetAsSeries(medium, true);
      ArraySetAsSeries(slow, true);
      
      if(CopyBuffer(m_ema_fast_handle, 0, 0, count, fast) <= 0)
         return false;
      if(CopyBuffer(m_ema_medium_handle, 0, 0, count, medium) <= 0)
         return false;
      if(CopyBuffer(m_ema_slow_handle, 0, 0, count, slow) <= 0)
         return false;
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Get ADX value                                                    |
   //+------------------------------------------------------------------+
   double GetADXValue(int shift = 0)
   {
      double adx[];
      ArraySetAsSeries(adx, true);
      
      if(CopyBuffer(m_adx_handle, 0, shift, 1, adx) <= 0)
         return 0;
      
      return adx[0];
   }
   
   //+------------------------------------------------------------------+
   //| Analyze trend using EMA crossovers                              |
   //+------------------------------------------------------------------+
   int AnalyzeEMACrossover()
   {
      double ema_fast[3], ema_medium[3], ema_slow[3];
      
      if(!GetEMAValues(ema_fast, ema_medium, ema_slow, 3))
         return SIGNAL_NEUTRAL;
      
      // Check EMA alignment for bullish trend
      if(ema_fast[0] > ema_medium[0] && ema_medium[0] > ema_slow[0])
      {
         // Check for recent crossover (more reliable)
         if(ema_fast[1] <= ema_medium[1])
            return SIGNAL_BUY;
         
         // Already in trend
         if(ema_fast[0] > ema_slow[0])
            return SIGNAL_BUY;
      }
      
      // Check EMA alignment for bearish trend
      if(ema_fast[0] < ema_medium[0] && ema_medium[0] < ema_slow[0])
      {
         // Check for recent crossover
         if(ema_fast[1] >= ema_medium[1])
            return SIGNAL_SELL;
         
         // Already in trend
         if(ema_fast[0] < ema_slow[0])
            return SIGNAL_SELL;
      }
      
      return SIGNAL_NEUTRAL;
   }
   
   //+------------------------------------------------------------------+
   //| Analyze price structure (Higher Highs/Lower Lows)               |
   //+------------------------------------------------------------------+
   int AnalyzePriceStructure()
   {
      // Look back at last 10 bars to identify structure
      int lookback = 10;
      int higher_highs = 0;
      int higher_lows = 0;
      int lower_highs = 0;
      int lower_lows = 0;
      
      for(int i = 1; i < lookback; i++)
      {
         double high_current = iHigh(_Symbol, PERIOD_CURRENT, i);
         double high_prev = iHigh(_Symbol, PERIOD_CURRENT, i + 1);
         double low_current = iLow(_Symbol, PERIOD_CURRENT, i);
         double low_prev = iLow(_Symbol, PERIOD_CURRENT, i + 1);
         
         if(high_current > high_prev) higher_highs++;
         if(high_current < high_prev) lower_highs++;
         if(low_current > low_prev) higher_lows++;
         if(low_current < low_prev) lower_lows++;
      }
      
      // Bullish structure: Higher Highs and Higher Lows
      if(higher_highs > lower_highs && higher_lows > lower_lows)
         return SIGNAL_BUY;
      
      // Bearish structure: Lower Highs and Lower Lows
      if(lower_highs > higher_highs && lower_lows > higher_lows)
         return SIGNAL_SELL;
      
      return SIGNAL_NEUTRAL;
   }
   
   //+------------------------------------------------------------------+
   //| Calculate confidence based on trend strength                    |
   //+------------------------------------------------------------------+
   double CalculateConfidence(int signal)
   {
      double confidence = 0;
      
      if(signal == SIGNAL_NEUTRAL)
         return 0;
      
      // Base confidence
      confidence = 50;
      
      // ADX strength bonus (0-25 points)
      double adx = GetADXValue(0);
      if(adx > ADX_Threshold)
      {
         double adx_bonus = MathMin((adx - ADX_Threshold) * 0.5, 25);
         confidence += adx_bonus;
      }
      
      // EMA alignment bonus (0-15 points)
      double ema_fast[2], ema_medium[2], ema_slow[2];
      if(GetEMAValues(ema_fast, ema_medium, ema_slow, 2))
      {
         double fast_distance = MathAbs(ema_fast[0] - ema_medium[0]) / _Point;
         double medium_distance = MathAbs(ema_medium[0] - ema_slow[0]) / _Point;
         
         if(fast_distance > 50 && medium_distance > 50)
            confidence += 15;
         else if(fast_distance > 20 && medium_distance > 20)
            confidence += 10;
      }
      
      // Price structure confirmation bonus (0-10 points)
      int structure_signal = AnalyzePriceStructure();
      if(structure_signal == signal)
         confidence += 10;
      
      // Ensure confidence is within 0-100
      if(confidence > 100) confidence = 100;
      if(confidence < 0) confidence = 0;
      
      return confidence;
   }
   
   //+------------------------------------------------------------------+
   //| Main analysis function                                           |
   //+------------------------------------------------------------------+
   void Analyze(int &signal, double &confidence)
   {
      signal = SIGNAL_NEUTRAL;
      confidence = 0;
      
      // Get EMA crossover signal
      int ema_signal = AnalyzeEMACrossover();
      
      // Check ADX for trend strength
      double adx = GetADXValue(0);
      
      // Only consider signals when ADX shows trend strength
      if(adx < ADX_Threshold)
      {
         signal = SIGNAL_NEUTRAL;
         confidence = 0;
         return;
      }
      
      // Get price structure confirmation
      int structure_signal = AnalyzePriceStructure();
      
      // Combine signals
      if(ema_signal == structure_signal && ema_signal != SIGNAL_NEUTRAL)
      {
         signal = ema_signal;
      }
      else if(ema_signal != SIGNAL_NEUTRAL)
      {
         // EMA signal only, lower confidence
         signal = ema_signal;
      }
      else
      {
         signal = SIGNAL_NEUTRAL;
      }
      
      // Calculate confidence
      confidence = CalculateConfidence(signal);
      
      LogMessage("TrendAgent: Signal=" + IntegerToString(signal) + 
                " Confidence=" + FormatDouble(confidence, 1) + 
                "% ADX=" + FormatDouble(adx, 1));
   }
};
