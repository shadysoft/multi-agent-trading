//+------------------------------------------------------------------+
//|                                                  RiskManager.mqh |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property version   "1.00"
#property strict

#include "../Config/Settings.mqh"
#include "Helpers.mqh"

//+------------------------------------------------------------------+
//| Risk Manager Class                                               |
//+------------------------------------------------------------------+
class CRiskManager
{
private:
   double m_starting_balance;
   double m_daily_starting_balance;
   datetime m_last_reset_date;
   
public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   CRiskManager()
   {
      m_starting_balance = AccountInfoDouble(ACCOUNT_BALANCE);
      m_daily_starting_balance = m_starting_balance;
      m_last_reset_date = TimeCurrent();
   }
   
   //+------------------------------------------------------------------+
   //| Calculate lot size based on risk percentage                     |
   //+------------------------------------------------------------------+
   double CalculateLotSize(double stop_loss_points)
   {
      if(stop_loss_points <= 0)
      {
         LogMessage("Invalid stop loss points for lot calculation");
         return 0;
      }
      
      double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double risk_amount = account_balance * (RiskPercent / 100.0);
      
      // Get tick value
      double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      
      if(tick_value == 0 || tick_size == 0)
      {
         LogMessage("Invalid tick value or tick size");
         return 0;
      }
      
      // Calculate lot size
      double sl_in_price = stop_loss_points * _Point;
      double lot_size = risk_amount / (sl_in_price / tick_size * tick_value);
      
      // Normalize lot size
      lot_size = NormalizeLot(lot_size);
      
      LogMessage("Calculated lot size: " + FormatDouble(lot_size, 2) + 
                " for SL: " + FormatDouble(stop_loss_points, 0) + " points");
      
      return lot_size;
   }
   
   //+------------------------------------------------------------------+
   //| Check if current drawdown exceeds maximum allowed               |
   //+------------------------------------------------------------------+
   bool IsDrawdownExceeded()
   {
      double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double account_equity = AccountInfoDouble(ACCOUNT_EQUITY);
      
      if(m_starting_balance <= 0.0001)
      {
         LogMessage("Invalid starting balance");
         return false;
      }
      
      double drawdown = ((m_starting_balance - account_equity) / m_starting_balance) * 100.0;
      
      if(drawdown >= MaxDrawdownPercent)
      {
         LogMessage("Max drawdown exceeded: " + FormatDouble(drawdown, 2) + "%");
         return true;
      }
      
      return false;
   }
   
   //+------------------------------------------------------------------+
   //| Check if daily loss limit is exceeded                           |
   //+------------------------------------------------------------------+
   bool IsDailyLossExceeded()
   {
      // Reset daily balance if new day
      ResetDailyBalanceIfNeeded();
      
      double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
      
      if(m_daily_starting_balance <= 0.0001)
      {
         LogMessage("Invalid daily starting balance");
         return false;
      }
      
      double daily_loss = ((m_daily_starting_balance - account_balance) / m_daily_starting_balance) * 100.0;
      
      if(daily_loss >= MaxDailyLossPercent)
      {
         LogMessage("Daily loss limit exceeded: " + FormatDouble(daily_loss, 2) + "%");
         return true;
      }
      
      return false;
   }
   
   //+------------------------------------------------------------------+
   //| Reset daily balance if new day                                  |
   //+------------------------------------------------------------------+
   void ResetDailyBalanceIfNeeded()
   {
      MqlDateTime current_dt, last_dt;
      TimeToStruct(TimeCurrent(), current_dt);
      TimeToStruct(m_last_reset_date, last_dt);
      
      if(current_dt.day != last_dt.day || current_dt.mon != last_dt.mon || current_dt.year != last_dt.year)
      {
         m_daily_starting_balance = AccountInfoDouble(ACCOUNT_BALANCE);
         m_last_reset_date = TimeCurrent();
         LogMessage("Daily balance reset to: " + FormatDouble(m_daily_starting_balance, 2));
      }
   }
   
   //+------------------------------------------------------------------+
   //| Check if margin is sufficient for trade                         |
   //+------------------------------------------------------------------+
   bool CheckMargin(double lot_size, ENUM_ORDER_TYPE order_type)
   {
      double free_margin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      double margin_required = 0;
      
      if(!OrderCalcMargin(order_type, _Symbol, lot_size, 
                         SymbolInfoDouble(_Symbol, SYMBOL_ASK), margin_required))
      {
         LogMessage("Failed to calculate required margin");
         return false;
      }
      
      if(margin_required > free_margin)
      {
         LogMessage("Insufficient margin. Required: " + FormatDouble(margin_required, 2) + 
                   ", Available: " + FormatDouble(free_margin, 2));
         return false;
      }
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Count open positions                                            |
   //+------------------------------------------------------------------+
   int CountOpenPositions(string symbol = "")
   {
      int count = 0;
      
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;
         
         if(PositionGetInteger(POSITION_MAGIC) != MagicNumber)
            continue;
         
         if(symbol != "" && PositionGetString(POSITION_SYMBOL) != symbol)
            continue;
         
         count++;
      }
      
      return count;
   }
   
   //+------------------------------------------------------------------+
   //| Check if max positions limit is reached                         |
   //+------------------------------------------------------------------+
   bool IsMaxPositionsReached()
   {
      int total_positions = CountOpenPositions();
      
      if(total_positions >= MaxOpenTrades)
      {
         LogMessage("Max open positions reached: " + IntegerToString(total_positions));
         return true;
      }
      
      return false;
   }
   
   //+------------------------------------------------------------------+
   //| Check if max positions per symbol is reached                    |
   //+------------------------------------------------------------------+
   bool IsMaxPositionsPerSymbolReached()
   {
      int symbol_positions = CountOpenPositions(_Symbol);
      
      if(symbol_positions >= MaxTradesPerSymbol)
      {
         LogMessage("Max positions per symbol reached: " + IntegerToString(symbol_positions));
         return true;
      }
      
      return false;
   }
   
   //+------------------------------------------------------------------+
   //| Validate all risk conditions                                    |
   //+------------------------------------------------------------------+
   bool ValidateRiskConditions()
   {
      if(IsDrawdownExceeded())
         return false;
      
      if(IsDailyLossExceeded())
         return false;
      
      if(IsMaxPositionsReached())
         return false;
      
      if(IsMaxPositionsPerSymbolReached())
         return false;
      
      return true;
   }
   
   //+------------------------------------------------------------------+
   //| Get current account statistics                                  |
   //+------------------------------------------------------------------+
   string GetAccountStats()
   {
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      
      double drawdown = 0;
      if(m_starting_balance > 0.0001)
      {
         drawdown = ((m_starting_balance - equity) / m_starting_balance) * 100.0;
      }
      
      ResetDailyBalanceIfNeeded();
      double daily_pl = balance - m_daily_starting_balance;
      
      string stats = "Balance: " + FormatDouble(balance, 2) + 
                    " | Equity: " + FormatDouble(equity, 2) +
                    " | DD: " + FormatDouble(drawdown, 2) + "%" +
                    " | Daily P/L: " + FormatDouble(daily_pl, 2);
      
      return stats;
   }
   
   //+------------------------------------------------------------------+
   //| Calculate stop loss in points                                   |
   //+------------------------------------------------------------------+
   double CalculateStopLoss()
   {
      double sl_points = 0;
      
      if(UseATRForSL)
      {
         double atr = GetATR(ATRPeriod, 1);
         if(atr > 0)
         {
            sl_points = (atr / _Point) * ATRMultiplier;
         }
         else
         {
            sl_points = FixedSLPoints;
         }
      }
      else
      {
         sl_points = FixedSLPoints;
      }
      
      // Ensure minimum stop loss level
      int min_stop_level = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
      if(sl_points < min_stop_level)
         sl_points = min_stop_level + 10;
      
      return sl_points;
   }
   
   //+------------------------------------------------------------------+
   //| Calculate take profit in points                                 |
   //+------------------------------------------------------------------+
   double CalculateTakeProfit(double stop_loss_points)
   {
      return stop_loss_points * RiskRewardRatio;
   }
};
