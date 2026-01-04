//+------------------------------------------------------------------+
//|                                            StatisticalAgent.mqh |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property version   "1.00"
#property strict

#include "../Config/Settings.mqh"
#include "../Utils/Helpers.mqh"

//+------------------------------------------------------------------+
//| Statistical Agent (Gatekeeper) Class                            |
//+------------------------------------------------------------------+
class CStatisticalAgent
{
private:
   string m_block_reason;
   
public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   CStatisticalAgent()
   {
      m_block_reason = "";
   }
   
   //+------------------------------------------------------------------+
   //| Get block reason                                                 |
   //+------------------------------------------------------------------+
   string GetBlockReason()
   {
      return m_block_reason;
   }
   
   //+------------------------------------------------------------------+
   //| Check ATR filter (volatility)                                   |
   //+------------------------------------------------------------------+
   bool CheckATRFilter()
   {
      double atr = GetATR(Stats_ATRPeriod, 1);
      
      if(atr < ATR_MinValue)
      {
         m_block_reason = "ATR too low (" + FormatDouble(atr, 5) + ")";
         return false;
      }
      
      if(ATR_MaxValue > 0 && atr > ATR_MaxValue)
      {
         m_block_reason = "ATR too high (" + FormatDouble(atr, 5) + ")";
         return false;
      }
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Check spread validation                                         |
   //+------------------------------------------------------------------+
   bool CheckSpread()
   {
      double spread = GetSpreadPoints();
      
      if(spread > MaxSpreadPoints)
      {
         m_block_reason = "Spread too high (" + FormatDouble(spread, 1) + " points)";
         return false;
      }
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Check time filter                                               |
   //+------------------------------------------------------------------+
   bool CheckTimeFilter()
   {
      if(!UseTimeFilter)
         return true;
      
      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      
      // Check if weekend
      if(dt.day_of_week == 0 || dt.day_of_week == 6)
      {
         m_block_reason = "Weekend - Market closed";
         return false;
      }
      
      // Check trading hours
      if(dt.hour < TradingStartHour || dt.hour >= TradingEndHour)
      {
         m_block_reason = "Outside trading hours (" + IntegerToString(dt.hour) + ":00)";
         return false;
      }
      
      // Check Friday late trading
      if(AvoidFriday && dt.day_of_week == 5 && dt.hour >= FridayStopHour)
      {
         m_block_reason = "Friday late hours";
         return false;
      }
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Check if market is open                                         |
   //+------------------------------------------------------------------+
   bool CheckMarketOpen()
   {
      if(!IsMarketOpen())
      {
         m_block_reason = "Market is closed";
         return false;
      }
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Check trading conditions (wrapper for risk manager checks)      |
   //+------------------------------------------------------------------+
   bool CheckTradingConditions(CRiskManager* risk_manager)
   {
      if(risk_manager == NULL)
         return false;
      
      // Check drawdown
      if(risk_manager.IsDrawdownExceeded())
      {
         m_block_reason = "Max drawdown exceeded";
         return false;
      }
      
      // Check daily loss
      if(risk_manager.IsDailyLossExceeded())
      {
         m_block_reason = "Daily loss limit exceeded";
         return false;
      }
      
      // Check max positions
      if(risk_manager.IsMaxPositionsReached())
      {
         m_block_reason = "Max positions reached";
         return false;
      }
      
      // Check max positions per symbol
      if(risk_manager.IsMaxPositionsPerSymbolReached())
      {
         m_block_reason = "Max positions per symbol reached";
         return false;
      }
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Check news filter (basic time-based)                            |
   //+------------------------------------------------------------------+
   bool CheckNewsFilter()
   {
      // This is a basic implementation
      // In a production system, you would integrate with a news calendar
      
      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      
      // Avoid trading during typical high-impact news hours
      // (This is a simplified approach - customize based on your needs)
      
      // Check if it's a major news hour (example: 8:30 AM, 10:00 AM, 2:00 PM EST)
      int news_hours[] = {8, 10, 14, 15};
      
      for(int i = 0; i < ArraySize(news_hours); i++)
      {
         if(dt.hour == news_hours[i] && dt.min < 30)
         {
            m_block_reason = "Potential news hour (" + IntegerToString(dt.hour) + ":00)";
            return false;
         }
      }
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Validate symbol characteristics                                 |
   //+------------------------------------------------------------------+
   bool CheckSymbolCharacteristics()
   {
      // Check if symbol allows trading
      if(!SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE))
      {
         m_block_reason = "Symbol trading is disabled";
         return false;
      }
      
      // Check if we're in trading session
      if(SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE) == SYMBOL_TRADE_MODE_DISABLED)
      {
         m_block_reason = "Symbol trading session closed";
         return false;
      }
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Main validation function                                         |
   //+------------------------------------------------------------------+
   int Validate(CRiskManager* risk_manager)
   {
      m_block_reason = "";
      
      // Check all conditions
      if(!CheckMarketOpen())
      {
         LogMessage("StatisticalAgent: BLOCK - " + m_block_reason);
         return BLOCK_TRADE;
      }
      
      if(!CheckTimeFilter())
      {
         LogMessage("StatisticalAgent: BLOCK - " + m_block_reason);
         return BLOCK_TRADE;
      }
      
      if(!CheckSpread())
      {
         LogMessage("StatisticalAgent: BLOCK - " + m_block_reason);
         return BLOCK_TRADE;
      }
      
      if(!CheckATRFilter())
      {
         LogMessage("StatisticalAgent: BLOCK - " + m_block_reason);
         return BLOCK_TRADE;
      }
      
      if(!CheckSymbolCharacteristics())
      {
         LogMessage("StatisticalAgent: BLOCK - " + m_block_reason);
         return BLOCK_TRADE;
      }
      
      if(!CheckTradingConditions(risk_manager))
      {
         LogMessage("StatisticalAgent: BLOCK - " + m_block_reason);
         return BLOCK_TRADE;
      }
      
      // All checks passed
      LogMessage("StatisticalAgent: ALLOW - All conditions met");
      return ALLOW_TRADE;
   }
   
   //+------------------------------------------------------------------+
   //| Get validation status string                                    |
   //+------------------------------------------------------------------+
   string GetStatusString()
   {
      if(m_block_reason == "")
         return "ALLOW";
      else
         return "BLOCK: " + m_block_reason;
   }
   
   //+------------------------------------------------------------------+
   //| Get comprehensive statistics                                    |
   //+------------------------------------------------------------------+
   string GetStatistics()
   {
      string stats = "";
      
      // Spread
      double spread = GetSpreadPoints();
      stats += "Spread: " + FormatDouble(spread, 1) + " pts | ";
      
      // ATR
      double atr = GetATR(Stats_ATRPeriod, 1);
      stats += "ATR: " + FormatDouble(atr, 5) + " | ";
      
      // Time
      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      stats += "Hour: " + IntegerToString(dt.hour) + ":00 | ";
      
      // Market status
      stats += "Market: " + (IsMarketOpen() ? "OPEN" : "CLOSED");
      
      return stats;
   }
};
