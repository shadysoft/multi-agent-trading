//+------------------------------------------------------------------+
//|                                                 TradeManager.mqh |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property version   "1.00"
#property strict

#include "../Config/Settings.mqh"
#include "Helpers.mqh"
#include <Trade/Trade.mqh>

//+------------------------------------------------------------------+
//| Trade Manager Class                                              |
//+------------------------------------------------------------------+
class CTradeManager
{
private:
   CTrade m_trade;
   
   struct TradeInfo
   {
      ulong ticket;
      double entry_price;
      double sl_price;
      double tp_price;
      double sl_points;
   };
   
public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   CTradeManager()
   {
      m_trade.SetExpertMagicNumber(MagicNumber);
      m_trade.SetDeviationInPoints(50);
      m_trade.SetTypeFilling(ORDER_FILLING_FOK);
      m_trade.SetAsyncMode(false);
   }
   
   //+------------------------------------------------------------------+
   //| Open Buy position                                                |
   //+------------------------------------------------------------------+
   bool OpenBuy(double lot_size, double sl_points, double tp_points, string comment = "")
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double sl = NormalizePrice(ask - PointsToPrice(sl_points));
      double tp = NormalizePrice(ask + PointsToPrice(tp_points));
      
      if(comment == "")
         comment = EA_Name + " Buy";
      
      LogMessage("Opening BUY: Lot=" + FormatDouble(lot_size, 2) + 
                " SL=" + FormatDouble(sl_points, 0) + 
                " TP=" + FormatDouble(tp_points, 0));
      
      bool result = m_trade.Buy(lot_size, _Symbol, ask, sl, tp, comment);
      
      if(result)
      {
         LogMessage("BUY order opened successfully. Ticket: " + IntegerToString(m_trade.ResultOrder()));
         return true;
      }
      else
      {
         LogMessage("Failed to open BUY order. Error: " + IntegerToString(m_trade.ResultRetcode()));
         return false;
      }
   }
   
   //+------------------------------------------------------------------+
   //| Open Sell position                                              |
   //+------------------------------------------------------------------+
   bool OpenSell(double lot_size, double sl_points, double tp_points, string comment = "")
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double sl = NormalizePrice(bid + PointsToPrice(sl_points));
      double tp = NormalizePrice(bid - PointsToPrice(tp_points));
      
      if(comment == "")
         comment = EA_Name + " Sell";
      
      LogMessage("Opening SELL: Lot=" + FormatDouble(lot_size, 2) + 
                " SL=" + FormatDouble(sl_points, 0) + 
                " TP=" + FormatDouble(tp_points, 0));
      
      bool result = m_trade.Sell(lot_size, _Symbol, bid, sl, tp, comment);
      
      if(result)
      {
         LogMessage("SELL order opened successfully. Ticket: " + IntegerToString(m_trade.ResultOrder()));
         return true;
      }
      else
      {
         LogMessage("Failed to open SELL order. Error: " + IntegerToString(m_trade.ResultRetcode()));
         return false;
      }
   }
   
   //+------------------------------------------------------------------+
   //| Manage trailing stop for all positions                          |
   //+------------------------------------------------------------------+
   void ManageTrailingStop()
   {
      if(!UseTrailingStop)
         return;
      
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;
         
         if(PositionGetInteger(POSITION_MAGIC) != MagicNumber)
            continue;
         
         if(PositionGetString(POSITION_SYMBOL) != _Symbol)
            continue;
         
         TrailPosition(ticket);
      }
   }
   
   //+------------------------------------------------------------------+
   //| Trail individual position                                        |
   //+------------------------------------------------------------------+
   void TrailPosition(ulong ticket)
   {
      if(!PositionSelectByTicket(ticket))
         return;
      
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double current_sl = PositionGetDouble(POSITION_SL);
      double current_tp = PositionGetDouble(POSITION_TP);
      ENUM_POSITION_TYPE pos_type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      
      double sl_distance = 0;
      if(pos_type == POSITION_TYPE_BUY)
      {
         sl_distance = DistanceInPoints(open_price, current_sl);
      }
      else
      {
         sl_distance = DistanceInPoints(current_sl, open_price);
      }
      
      // Check if profit reached trailing start level
      double current_profit_points = 0;
      if(pos_type == POSITION_TYPE_BUY)
      {
         current_profit_points = DistanceInPoints(SymbolInfoDouble(_Symbol, SYMBOL_BID), open_price);
      }
      else
      {
         current_profit_points = DistanceInPoints(open_price, SymbolInfoDouble(_Symbol, SYMBOL_ASK));
      }
      
      double start_trail_points = sl_distance * TrailingStartRR;
      
      if(current_profit_points < start_trail_points)
         return;
      
      // Calculate new stop loss
      double new_sl = 0;
      if(pos_type == POSITION_TYPE_BUY)
      {
         double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         new_sl = NormalizePrice(bid - PointsToPrice(TrailingStepPoints));
         
         if(new_sl > current_sl && new_sl < bid)
         {
            m_trade.PositionModify(ticket, new_sl, current_tp);
            LogMessage("Trailing stop updated for ticket " + IntegerToString(ticket));
         }
      }
      else // SELL
      {
         double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         new_sl = NormalizePrice(ask + PointsToPrice(TrailingStepPoints));
         
         if(new_sl < current_sl && new_sl > ask)
         {
            m_trade.PositionModify(ticket, new_sl, current_tp);
            LogMessage("Trailing stop updated for ticket " + IntegerToString(ticket));
         }
      }
   }
   
   //+------------------------------------------------------------------+
   //| Move position to break even                                     |
   //+------------------------------------------------------------------+
   void ManageBreakEven()
   {
      if(!UseBreakEven)
         return;
      
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;
         
         if(PositionGetInteger(POSITION_MAGIC) != MagicNumber)
            continue;
         
         if(PositionGetString(POSITION_SYMBOL) != _Symbol)
            continue;
         
         MoveToBreakEven(ticket);
      }
   }
   
   //+------------------------------------------------------------------+
   //| Move individual position to break even                          |
   //+------------------------------------------------------------------+
   void MoveToBreakEven(ulong ticket)
   {
      if(!PositionSelectByTicket(ticket))
         return;
      
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double current_sl = PositionGetDouble(POSITION_SL);
      double current_tp = PositionGetDouble(POSITION_TP);
      ENUM_POSITION_TYPE pos_type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      
      // Calculate SL distance
      double sl_distance = 0;
      if(pos_type == POSITION_TYPE_BUY)
      {
         sl_distance = DistanceInPoints(open_price, current_sl);
      }
      else
      {
         sl_distance = DistanceInPoints(current_sl, open_price);
      }
      
      // Check if profit reached break even level
      double current_profit_points = 0;
      if(pos_type == POSITION_TYPE_BUY)
      {
         current_profit_points = DistanceInPoints(SymbolInfoDouble(_Symbol, SYMBOL_BID), open_price);
         
         // Check if already at break even
         if(current_sl >= open_price)
            return;
      }
      else
      {
         current_profit_points = DistanceInPoints(open_price, SymbolInfoDouble(_Symbol, SYMBOL_ASK));
         
         // Check if already at break even
         if(current_sl <= open_price)
            return;
      }
      
      double be_trigger_points = sl_distance * BreakEvenAtRR;
      
      if(current_profit_points < be_trigger_points)
         return;
      
      // Move to break even plus some points
      double new_sl = 0;
      if(pos_type == POSITION_TYPE_BUY)
      {
         new_sl = NormalizePrice(open_price + PointsToPrice(BreakEvenPlusPoints));
      }
      else
      {
         new_sl = NormalizePrice(open_price - PointsToPrice(BreakEvenPlusPoints));
      }
      
      m_trade.PositionModify(ticket, new_sl, current_tp);
      LogMessage("Position moved to break even. Ticket: " + IntegerToString(ticket));
   }
   
   //+------------------------------------------------------------------+
   //| Close position by ticket                                        |
   //+------------------------------------------------------------------+
   bool ClosePosition(ulong ticket)
   {
      if(!PositionSelectByTicket(ticket))
         return false;
      
      bool result = m_trade.PositionClose(ticket);
      
      if(result)
      {
         LogMessage("Position closed. Ticket: " + IntegerToString(ticket));
         return true;
      }
      else
      {
         LogMessage("Failed to close position. Ticket: " + IntegerToString(ticket) + 
                   " Error: " + IntegerToString(m_trade.ResultRetcode()));
         return false;
      }
   }
   
   //+------------------------------------------------------------------+
   //| Close all positions                                             |
   //+------------------------------------------------------------------+
   void CloseAllPositions()
   {
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;
         
         if(PositionGetInteger(POSITION_MAGIC) != MagicNumber)
            continue;
         
         ClosePosition(ticket);
      }
      
      LogMessage("All positions closed");
   }
   
   //+------------------------------------------------------------------+
   //| Get today's profit/loss                                         |
   //+------------------------------------------------------------------+
   double GetTodayProfitLoss()
   {
      double profit = 0;
      datetime today_start = iTime(_Symbol, PERIOD_D1, 0);
      
      // Get profit from closed deals today
      HistorySelect(today_start, TimeCurrent());
      
      for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = HistoryDealGetTicket(i);
         if(ticket <= 0) continue;
         
         if(HistoryDealGetInteger(ticket, DEAL_MAGIC) != MagicNumber)
            continue;
         
         if(HistoryDealGetString(ticket, DEAL_SYMBOL) != _Symbol)
            continue;
         
         profit += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         profit += HistoryDealGetDouble(ticket, DEAL_SWAP);
         profit += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      }
      
      // Add profit from open positions
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;
         
         if(PositionGetInteger(POSITION_MAGIC) != MagicNumber)
            continue;
         
         if(PositionGetString(POSITION_SYMBOL) != _Symbol)
            continue;
         
         profit += PositionGetDouble(POSITION_PROFIT);
         profit += PositionGetDouble(POSITION_SWAP);
      }
      
      return profit;
   }
};
