//+------------------------------------------------------------------+
//|                                                     SMCAgent.mqh |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property version   "1.00"
#property strict

#include "../Config/Settings.mqh"
#include "../Utils/Helpers.mqh"

//+------------------------------------------------------------------+
//| Smart Money Concepts Agent Class                                 |
//+------------------------------------------------------------------+
class CSMCAgent
{
private:
   struct OrderBlock
   {
      datetime time;
      double high;
      double low;
      int type; // 1 for bullish, -1 for bearish
   };
   
   struct FVG
   {
      datetime time;
      double upper;
      double lower;
      int type; // 1 for bullish, -1 for bearish
   };
   
   OrderBlock m_last_order_block;
   FVG m_last_fvg;
   
public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   CSMCAgent()
   {
      m_last_order_block.time = 0;
      m_last_fvg.time = 0;
   }
   
   //+------------------------------------------------------------------+
   //| Identify Order Blocks                                           |
   //+------------------------------------------------------------------+
   bool FindOrderBlock(OrderBlock &ob)
   {
      // Look for the last opposite candle before a strong impulse move
      for(int i = 2; i < OrderBlock_Lookback; i++)
      {
         double close_curr = iClose(_Symbol, PERIOD_CURRENT, i);
         double open_curr = iOpen(_Symbol, PERIOD_CURRENT, i);
         double close_next = iClose(_Symbol, PERIOD_CURRENT, i - 1);
         double open_next = iOpen(_Symbol, PERIOD_CURRENT, i - 1);
         
         double body_curr = MathAbs(close_curr - open_curr);
         double body_next = MathAbs(close_next - open_next);
         
         // Bullish Order Block: Bearish candle followed by strong bullish move
         if(close_curr < open_curr && close_next > open_next && body_next > body_curr * 2)
         {
            ob.time = iTime(_Symbol, PERIOD_CURRENT, i);
            ob.high = iHigh(_Symbol, PERIOD_CURRENT, i);
            ob.low = iLow(_Symbol, PERIOD_CURRENT, i);
            ob.type = SIGNAL_BUY;
            return true;
         }
         
         // Bearish Order Block: Bullish candle followed by strong bearish move
         if(close_curr > open_curr && close_next < open_next && body_next > body_curr * 2)
         {
            ob.time = iTime(_Symbol, PERIOD_CURRENT, i);
            ob.high = iHigh(_Symbol, PERIOD_CURRENT, i);
            ob.low = iLow(_Symbol, PERIOD_CURRENT, i);
            ob.type = SIGNAL_SELL;
            return true;
         }
      }
      
      return false;
   }
   
   //+------------------------------------------------------------------+
   //| Identify Fair Value Gaps (FVG)                                  |
   //+------------------------------------------------------------------+
   bool FindFVG(FVG &fvg)
   {
      // FVG occurs when there's a gap between candle 1 and candle 3
      for(int i = 1; i < 10; i++)
      {
         double high_1 = iHigh(_Symbol, PERIOD_CURRENT, i + 1);
         double low_1 = iLow(_Symbol, PERIOD_CURRENT, i + 1);
         double high_2 = iHigh(_Symbol, PERIOD_CURRENT, i);
         double low_2 = iLow(_Symbol, PERIOD_CURRENT, i);
         double high_3 = iHigh(_Symbol, PERIOD_CURRENT, i - 1);
         double low_3 = iLow(_Symbol, PERIOD_CURRENT, i - 1);
         
         // Bullish FVG: Gap between low of candle 3 and high of candle 1
         if(low_3 > high_1)
         {
            double gap_size = (low_3 - high_1) / _Point;
            if(gap_size >= FVG_MinGapPoints)
            {
               fvg.time = iTime(_Symbol, PERIOD_CURRENT, i);
               fvg.upper = low_3;
               fvg.lower = high_1;
               fvg.type = SIGNAL_BUY;
               return true;
            }
         }
         
         // Bearish FVG: Gap between high of candle 3 and low of candle 1
         if(high_3 < low_1)
         {
            double gap_size = (low_1 - high_3) / _Point;
            if(gap_size >= FVG_MinGapPoints)
            {
               fvg.time = iTime(_Symbol, PERIOD_CURRENT, i);
               fvg.upper = low_1;
               fvg.lower = high_3;
               fvg.type = SIGNAL_SELL;
               return true;
            }
         }
      }
      
      return false;
   }
   
   //+------------------------------------------------------------------+
   //| Detect liquidity zones (equal highs/lows)                       |
   //+------------------------------------------------------------------+
   int FindLiquidityZones()
   {
      double tolerance = 20 * _Point; // 20 points tolerance for "equal" levels
      int lookback = 20;
      
      // Check for equal highs (resistance/liquidity)
      int equal_highs = 0;
      double ref_high = iHigh(_Symbol, PERIOD_CURRENT, 1);
      
      for(int i = 2; i <= lookback; i++)
      {
         double high = iHigh(_Symbol, PERIOD_CURRENT, i);
         if(MathAbs(high - ref_high) <= tolerance)
            equal_highs++;
      }
      
      // Check for equal lows (support/liquidity)
      int equal_lows = 0;
      double ref_low = iLow(_Symbol, PERIOD_CURRENT, 1);
      
      for(int i = 2; i <= lookback; i++)
      {
         double low = iLow(_Symbol, PERIOD_CURRENT, i);
         if(MathAbs(low - ref_low) <= tolerance)
            equal_lows++;
      }
      
      // If price is near equal lows, expect bounce (bullish)
      double current_price = iClose(_Symbol, PERIOD_CURRENT, 0);
      if(equal_lows >= LiquidityZone_Touches && MathAbs(current_price - ref_low) <= tolerance * 2)
         return SIGNAL_BUY;
      
      // If price is near equal highs, expect rejection (bearish)
      if(equal_highs >= LiquidityZone_Touches && MathAbs(current_price - ref_high) <= tolerance * 2)
         return SIGNAL_SELL;
      
      return SIGNAL_NEUTRAL;
   }
   
   //+------------------------------------------------------------------+
   //| Detect Break of Structure (BOS)                                 |
   //+------------------------------------------------------------------+
   int DetectBOS()
   {
      // Find recent swing high and low
      double swing_high = iHigh(_Symbol, PERIOD_CURRENT, iHighest(_Symbol, PERIOD_CURRENT, MODE_HIGH, 10, 1));
      double swing_low = iLow(_Symbol, PERIOD_CURRENT, iLowest(_Symbol, PERIOD_CURRENT, MODE_LOW, 10, 1));
      
      double current_close = iClose(_Symbol, PERIOD_CURRENT, 0);
      double prev_close = iClose(_Symbol, PERIOD_CURRENT, 1);
      
      // Bullish BOS: Price breaks above recent swing high
      if(current_close > swing_high && prev_close <= swing_high)
         return SIGNAL_BUY;
      
      // Bearish BOS: Price breaks below recent swing low
      if(current_close < swing_low && prev_close >= swing_low)
         return SIGNAL_SELL;
      
      return SIGNAL_NEUTRAL;
   }
   
   //+------------------------------------------------------------------+
   //| Check if price is at order block zone                           |
   //+------------------------------------------------------------------+
   bool IsPriceAtOrderBlock(OrderBlock &ob)
   {
      double current_price = iClose(_Symbol, PERIOD_CURRENT, 0);
      
      // Check if price is within order block zone
      if(current_price >= ob.low && current_price <= ob.high)
         return true;
      
      return false;
   }
   
   //+------------------------------------------------------------------+
   //| Check if price is at FVG zone                                   |
   //+------------------------------------------------------------------+
   bool IsPriceAtFVG(FVG &fvg)
   {
      double current_price = iClose(_Symbol, PERIOD_CURRENT, 0);
      
      // Check if price is within FVG zone
      if(current_price >= fvg.lower && current_price <= fvg.upper)
         return true;
      
      return false;
   }
   
   //+------------------------------------------------------------------+
   //| Calculate confidence                                             |
   //+------------------------------------------------------------------+
   double CalculateConfidence(int signal, bool has_ob, bool has_fvg, bool has_liq, bool has_bos)
   {
      if(signal == SIGNAL_NEUTRAL)
         return 0;
      
      double confidence = 40; // Base confidence
      
      // Order block confirmation
      if(has_ob) confidence += 20;
      
      // FVG confirmation
      if(has_fvg) confidence += 15;
      
      // Liquidity zone confirmation
      if(has_liq) confidence += 15;
      
      // Break of structure confirmation
      if(has_bos) confidence += 10;
      
      if(confidence > 100) confidence = 100;
      
      return confidence;
   }
   
   //+------------------------------------------------------------------+
   //| Main analysis function                                           |
   //+------------------------------------------------------------------+
   void Analyze(int &signal, double &confidence)
   {
      signal = SIGNAL_NEUTRAL;
      confidence = 0;
      
      // Find order blocks
      OrderBlock ob;
      bool has_ob = FindOrderBlock(ob);
      bool price_at_ob = false;
      int ob_signal = SIGNAL_NEUTRAL;
      
      if(has_ob)
      {
         m_last_order_block = ob;
         price_at_ob = IsPriceAtOrderBlock(ob);
         if(price_at_ob)
            ob_signal = ob.type;
      }
      
      // Find FVG
      FVG fvg;
      bool has_fvg = FindFVG(fvg);
      bool price_at_fvg = false;
      int fvg_signal = SIGNAL_NEUTRAL;
      
      if(has_fvg)
      {
         m_last_fvg = fvg;
         price_at_fvg = IsPriceAtFVG(fvg);
         if(price_at_fvg)
            fvg_signal = fvg.type;
      }
      
      // Find liquidity zones
      int liq_signal = FindLiquidityZones();
      
      // Detect BOS
      int bos_signal = DetectBOS();
      
      // Combine signals
      int signals[] = {ob_signal, fvg_signal, liq_signal, bos_signal};
      int buy_count = 0, sell_count = 0;
      
      for(int i = 0; i < 4; i++)
      {
         if(signals[i] == SIGNAL_BUY) buy_count++;
         if(signals[i] == SIGNAL_SELL) sell_count++;
      }
      
      // Determine final signal
      if(buy_count > sell_count && buy_count >= 2)
         signal = SIGNAL_BUY;
      else if(sell_count > buy_count && sell_count >= 2)
         signal = SIGNAL_SELL;
      else
         signal = SIGNAL_NEUTRAL;
      
      // Calculate confidence
      confidence = CalculateConfidence(signal, price_at_ob, price_at_fvg, 
                                       liq_signal != SIGNAL_NEUTRAL, 
                                       bos_signal != SIGNAL_NEUTRAL);
      
      LogMessage("SMCAgent: Signal=" + IntegerToString(signal) + 
                " Confidence=" + FormatDouble(confidence, 1) + 
                "% OB=" + (has_ob ? "Y" : "N") +
                " FVG=" + (has_fvg ? "Y" : "N") +
                " BOS=" + (bos_signal != 0 ? "Y" : "N"));
   }
};
