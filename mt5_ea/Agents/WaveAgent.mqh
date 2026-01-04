//+------------------------------------------------------------------+
//|                                                    WaveAgent.mqh |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property version   "1.00"
#property strict

#include "../Config/Settings.mqh"
#include "../Utils/Helpers.mqh"

//+------------------------------------------------------------------+
//| Wave Agent Class                                                 |
//+------------------------------------------------------------------+
class CWaveAgent
{
private:
   struct SwingPoint
   {
      datetime time;
      double price;
      int type; // 1 for high, -1 for low
      int bar_index;
   };
   
   SwingPoint m_swings[];
   int m_swing_count;
   
public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   CWaveAgent()
   {
      m_swing_count = 0;
      ArrayResize(m_swings, 50);
   }
   
   //+------------------------------------------------------------------+
   //| Find swing highs and lows                                       |
   //+------------------------------------------------------------------+
   void FindSwingPoints()
   {
      m_swing_count = 0;
      int lookback = 50;
      int swing_period = 5; // Bars before and after to confirm swing
      
      for(int i = swing_period; i < lookback - swing_period; i++)
      {
         double high_curr = iHigh(_Symbol, PERIOD_CURRENT, i);
         double low_curr = iLow(_Symbol, PERIOD_CURRENT, i);
         
         // Check for swing high
         bool is_swing_high = true;
         for(int j = 1; j <= swing_period; j++)
         {
            if(iHigh(_Symbol, PERIOD_CURRENT, i - j) >= high_curr ||
               iHigh(_Symbol, PERIOD_CURRENT, i + j) >= high_curr)
            {
               is_swing_high = false;
               break;
            }
         }
         
         if(is_swing_high)
         {
            SwingPoint sp;
            sp.time = iTime(_Symbol, PERIOD_CURRENT, i);
            sp.price = high_curr;
            sp.type = 1;
            sp.bar_index = i;
            m_swings[m_swing_count++] = sp;
         }
         
         // Check for swing low
         bool is_swing_low = true;
         for(int j = 1; j <= swing_period; j++)
         {
            if(iLow(_Symbol, PERIOD_CURRENT, i - j) <= low_curr ||
               iLow(_Symbol, PERIOD_CURRENT, i + j) <= low_curr)
            {
               is_swing_low = false;
               break;
            }
         }
         
         if(is_swing_low)
         {
            SwingPoint sp;
            sp.time = iTime(_Symbol, PERIOD_CURRENT, i);
            sp.price = low_curr;
            sp.type = -1;
            sp.bar_index = i;
            m_swings[m_swing_count++] = sp;
         }
         
         if(m_swing_count >= 45) break; // Limit swing points
      }
   }
   
   //+------------------------------------------------------------------+
   //| Identify impulse waves (strong trend moves)                     |
   //+------------------------------------------------------------------+
   int IdentifyImpulseWave()
   {
      if(m_swing_count < 4)
         return SIGNAL_NEUTRAL;
      
      // Sort swings by bar index (most recent first)
      for(int i = 0; i < m_swing_count - 1; i++)
      {
         for(int j = i + 1; j < m_swing_count; j++)
         {
            if(m_swings[j].bar_index < m_swings[i].bar_index)
            {
               SwingPoint temp = m_swings[i];
               m_swings[i] = m_swings[j];
               m_swings[j] = temp;
            }
         }
      }
      
      // Look at last 4 swings to identify wave pattern
      for(int i = 0; i < MathMin(m_swing_count - 3, 5); i++)
      {
         // Bullish impulse: Low -> High -> Higher Low -> Higher High
         if(m_swings[i].type == -1 && m_swings[i + 1].type == 1 &&
            m_swings[i + 2].type == -1 && m_swings[i + 3].type == 1)
         {
            if(m_swings[i + 2].price > m_swings[i].price &&
               m_swings[i + 3].price > m_swings[i + 1].price)
            {
               double impulse_size = (m_swings[i + 3].price - m_swings[i + 2].price) / _Point;
               if(impulse_size >= Wave_MinSwingPoints)
                  return SIGNAL_BUY;
            }
         }
         
         // Bearish impulse: High -> Low -> Lower High -> Lower Low
         if(m_swings[i].type == 1 && m_swings[i + 1].type == -1 &&
            m_swings[i + 2].type == 1 && m_swings[i + 3].type == -1)
         {
            if(m_swings[i + 2].price < m_swings[i].price &&
               m_swings[i + 3].price < m_swings[i + 1].price)
            {
               double impulse_size = (m_swings[i + 2].price - m_swings[i + 3].price) / _Point;
               if(impulse_size >= Wave_MinSwingPoints)
                  return SIGNAL_SELL;
            }
         }
      }
      
      return SIGNAL_NEUTRAL;
   }
   
   //+------------------------------------------------------------------+
   //| Identify correction waves (pullbacks)                           |
   //+------------------------------------------------------------------+
   int IdentifyCorrectionWave()
   {
      if(m_swing_count < 3)
         return SIGNAL_NEUTRAL;
      
      // Look for pullback patterns
      for(int i = 0; i < MathMin(m_swing_count - 2, 5); i++)
      {
         // Bullish correction: After uptrend, looking for pullback completion
         if(m_swings[i].type == 1 && m_swings[i + 1].type == -1)
         {
            double retracement = (m_swings[i].price - m_swings[i + 1].price) / _Point;
            
            if(i > 0 && m_swings[i - 1].type == -1)
            {
               double previous_wave = (m_swings[i].price - m_swings[i - 1].price) / _Point;
               double retrace_percent = (retracement / previous_wave) * 100;
               
               // 38.2% to 61.8% Fibonacci retracement
               if(retrace_percent >= 38 && retrace_percent <= 62)
               {
                  double current_price = iClose(_Symbol, PERIOD_CURRENT, 0);
                  // If price is near the pullback low, signal buy
                  if(MathAbs(current_price - m_swings[i + 1].price) < 50 * _Point)
                     return SIGNAL_BUY;
               }
            }
         }
         
         // Bearish correction: After downtrend, looking for pullback completion
         if(m_swings[i].type == -1 && m_swings[i + 1].type == 1)
         {
            double retracement = (m_swings[i + 1].price - m_swings[i].price) / _Point;
            
            if(i > 0 && m_swings[i - 1].type == 1)
            {
               double previous_wave = (m_swings[i - 1].price - m_swings[i].price) / _Point;
               double retrace_percent = (retracement / previous_wave) * 100;
               
               // 38.2% to 61.8% Fibonacci retracement
               if(retrace_percent >= 38 && retrace_percent <= 62)
               {
                  double current_price = iClose(_Symbol, PERIOD_CURRENT, 0);
                  // If price is near the pullback high, signal sell
                  if(MathAbs(current_price - m_swings[i + 1].price) < 50 * _Point)
                     return SIGNAL_SELL;
               }
            }
         }
      }
      
      return SIGNAL_NEUTRAL;
   }
   
   //+------------------------------------------------------------------+
   //| Calculate wave momentum                                          |
   //+------------------------------------------------------------------+
   double CalculateWaveMomentum()
   {
      if(m_swing_count < 2)
         return 0;
      
      // Calculate momentum based on recent swing sizes
      double total_momentum = 0;
      int count = 0;
      
      for(int i = 0; i < MathMin(m_swing_count - 1, 3); i++)
      {
         double swing_size = MathAbs(m_swings[i + 1].price - m_swings[i].price) / _Point;
         int bars_duration = MathAbs(m_swings[i + 1].bar_index - m_swings[i].bar_index);
         
         if(bars_duration > 0)
         {
            double momentum = swing_size / bars_duration;
            total_momentum += momentum;
            count++;
         }
      }
      
      if(count > 0)
         return total_momentum / count;
      
      return 0;
   }
   
   //+------------------------------------------------------------------+
   //| Calculate confidence                                             |
   //+------------------------------------------------------------------+
   double CalculateConfidence(int signal, bool has_impulse, bool has_correction)
   {
      if(signal == SIGNAL_NEUTRAL)
         return 0;
      
      double confidence = 45; // Base confidence
      
      // Impulse wave bonus
      if(has_impulse) confidence += 25;
      
      // Correction wave bonus
      if(has_correction) confidence += 15;
      
      // Momentum bonus
      double momentum = CalculateWaveMomentum();
      if(momentum > 2.0) confidence += 15;
      else if(momentum > 1.0) confidence += 10;
      
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
      
      // Find swing points
      FindSwingPoints();
      
      if(m_swing_count < 3)
      {
         LogMessage("WaveAgent: Insufficient swing points");
         return;
      }
      
      // Identify impulse and correction waves
      int impulse_signal = IdentifyImpulseWave();
      int correction_signal = IdentifyCorrectionWave();
      
      // Combine signals
      if(impulse_signal != SIGNAL_NEUTRAL && correction_signal != SIGNAL_NEUTRAL)
      {
         // Both agree
         if(impulse_signal == correction_signal)
            signal = impulse_signal;
         else
            signal = impulse_signal; // Impulse has priority
      }
      else if(impulse_signal != SIGNAL_NEUTRAL)
      {
         signal = impulse_signal;
      }
      else if(correction_signal != SIGNAL_NEUTRAL)
      {
         signal = correction_signal;
      }
      
      // Calculate confidence
      confidence = CalculateConfidence(signal, 
                                       impulse_signal != SIGNAL_NEUTRAL,
                                       correction_signal != SIGNAL_NEUTRAL);
      
      LogMessage("WaveAgent: Signal=" + IntegerToString(signal) + 
                " Confidence=" + FormatDouble(confidence, 1) + 
                "% Swings=" + IntegerToString(m_swing_count) +
                " Momentum=" + FormatDouble(CalculateWaveMomentum(), 2));
   }
};
