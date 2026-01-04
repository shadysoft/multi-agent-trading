//+------------------------------------------------------------------+
//|                                            TradingExecutor.mq5   |
//|                        Multi-Agent Trading System Executor        |
//|                                                                    |
//+------------------------------------------------------------------+
#property copyright "ShadySoft"
#property link      "https://github.com/shadysoft/multi-agent-trading"
#property version   "1.00"
#property description "Expert Advisor for safe order execution from Python"
#property strict

//--- Input Parameters
input int      MagicNumber = 234000;        // Magic number for orders
input string   CommentPrefix = "MultiAgent"; // Comment prefix
input bool     EnableTrailing = true;        // Enable trailing stop
input double   TrailingStop = 50.0;          // Trailing stop in points
input double   TrailingStep = 10.0;          // Trailing step in points

//--- Global Variables
bool tradingAllowed = true;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("Multi-Agent Trading Executor initialized");
   Print("Magic Number: ", MagicNumber);
   Print("Trailing Stop: ", EnableTrailing ? "Enabled" : "Disabled");
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("Multi-Agent Trading Executor stopped");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check if trading is allowed
   if(!tradingAllowed)
      return;
   
   // Update trailing stops if enabled
   if(EnableTrailing)
      UpdateTrailingStops();
   
   // Monitor open positions
   MonitorPositions();
}

//+------------------------------------------------------------------+
//| Update trailing stops for open positions                          |
//+------------------------------------------------------------------+
void UpdateTrailingStops()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            string symbol = PositionGetString(POSITION_SYMBOL);
            double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
            double currentPrice = PositionGetDouble(POSITION_PRICE_CURRENT);
            double stopLoss = PositionGetDouble(POSITION_SL);
            long posType = PositionGetInteger(POSITION_TYPE);
            
            double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
            double trailingStopPoints = TrailingStop * point;
            double trailingStepPoints = TrailingStep * point;
            
            // For Buy positions
            if(posType == POSITION_TYPE_BUY)
            {
               double newSL = NormalizeDouble(currentPrice - trailingStopPoints, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
               
               if(newSL > stopLoss + trailingStepPoints || stopLoss == 0)
               {
                  ModifyPosition(PositionGetTicket(i), newSL, PositionGetDouble(POSITION_TP));
               }
            }
            // For Sell positions
            else if(posType == POSITION_TYPE_SELL)
            {
               double newSL = NormalizeDouble(currentPrice + trailingStopPoints, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
               
               if((newSL < stopLoss || stopLoss == 0) && newSL > 0)
               {
                  ModifyPosition(PositionGetTicket(i), newSL, PositionGetDouble(POSITION_TP));
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Modify position SL/TP                                             |
//+------------------------------------------------------------------+
bool ModifyPosition(ulong ticket, double sl, double tp)
{
   MqlTradeRequest request;
   MqlTradeResult result;
   
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_SLTP;
   request.position = ticket;
   request.sl = sl;
   request.tp = tp;
   request.magic = MagicNumber;
   
   if(!OrderSend(request, result))
   {
      Print("Error modifying position: ", GetLastError());
      return false;
   }
   
   if(result.retcode == TRADE_RETCODE_DONE)
   {
      Print("Position ", ticket, " modified successfully. SL: ", sl, ", TP: ", tp);
      return true;
   }
   else
   {
      Print("Position modification failed. Return code: ", result.retcode);
      return false;
   }
}

//+------------------------------------------------------------------+
//| Monitor open positions                                            |
//+------------------------------------------------------------------+
void MonitorPositions()
{
   static datetime lastCheck = 0;
   datetime currentTime = TimeCurrent();
   
   // Check every minute
   if(currentTime - lastCheck < 60)
      return;
   
   lastCheck = currentTime;
   
   int totalPositions = 0;
   double totalProfit = 0.0;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            totalPositions++;
            totalProfit += PositionGetDouble(POSITION_PROFIT);
         }
      }
   }
   
   if(totalPositions > 0)
   {
      Comment(StringFormat("Multi-Agent Trading System\n" +
                          "Open Positions: %d\n" +
                          "Total Profit: %.2f %s",
                          totalPositions,
                          totalProfit,
                          AccountInfoString(ACCOUNT_CURRENCY)));
   }
   else
   {
      Comment("Multi-Agent Trading System\nNo open positions");
   }
}

//+------------------------------------------------------------------+
//| Send order function                                               |
//+------------------------------------------------------------------+
bool SendOrder(string symbol, ENUM_ORDER_TYPE orderType, double volume, 
               double price, double sl, double tp, string comment)
{
   MqlTradeRequest request;
   MqlTradeResult result;
   
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = symbol;
   request.volume = volume;
   request.type = orderType;
   request.price = price;
   request.sl = sl;
   request.tp = tp;
   request.deviation = 20;
   request.magic = MagicNumber;
   request.comment = CommentPrefix + ": " + comment;
   request.type_time = ORDER_TIME_GTC;
   request.type_filling = ORDER_FILLING_IOC;
   
   if(!OrderSend(request, result))
   {
      Print("Error sending order: ", GetLastError());
      return false;
   }
   
   if(result.retcode == TRADE_RETCODE_DONE)
   {
      Print("Order executed successfully. Ticket: ", result.order, 
            ", Volume: ", result.volume, ", Price: ", result.price);
      return true;
   }
   else
   {
      Print("Order failed. Return code: ", result.retcode, 
            ", Comment: ", result.comment);
      return false;
   }
}

//+------------------------------------------------------------------+
//| Close position function                                           |
//+------------------------------------------------------------------+
bool ClosePosition(ulong ticket)
{
   if(!PositionSelectByTicket(ticket))
   {
      Print("Position ", ticket, " not found");
      return false;
   }
   
   string symbol = PositionGetString(POSITION_SYMBOL);
   long posType = PositionGetInteger(POSITION_TYPE);
   double volume = PositionGetDouble(POSITION_VOLUME);
   
   ENUM_ORDER_TYPE closeType;
   double closePrice;
   
   if(posType == POSITION_TYPE_BUY)
   {
      closeType = ORDER_TYPE_SELL;
      closePrice = SymbolInfoDouble(symbol, SYMBOL_BID);
   }
   else
   {
      closeType = ORDER_TYPE_BUY;
      closePrice = SymbolInfoDouble(symbol, SYMBOL_ASK);
   }
   
   MqlTradeRequest request;
   MqlTradeResult result;
   
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = symbol;
   request.volume = volume;
   request.type = closeType;
   request.position = ticket;
   request.price = closePrice;
   request.deviation = 20;
   request.magic = MagicNumber;
   request.comment = CommentPrefix + ": Close";
   request.type_time = ORDER_TIME_GTC;
   request.type_filling = ORDER_FILLING_IOC;
   
   if(!OrderSend(request, result))
   {
      Print("Error closing position: ", GetLastError());
      return false;
   }
   
   if(result.retcode == TRADE_RETCODE_DONE)
   {
      Print("Position ", ticket, " closed successfully");
      return true;
   }
   else
   {
      Print("Position close failed. Return code: ", result.retcode);
      return false;
   }
}

//+------------------------------------------------------------------+
//| Get account information                                           |
//+------------------------------------------------------------------+
string GetAccountInfo()
{
   return StringFormat("Balance: %.2f, Equity: %.2f, Margin: %.2f, Free Margin: %.2f",
                      AccountInfoDouble(ACCOUNT_BALANCE),
                      AccountInfoDouble(ACCOUNT_EQUITY),
                      AccountInfoDouble(ACCOUNT_MARGIN),
                      AccountInfoDouble(ACCOUNT_MARGIN_FREE));
}

//+------------------------------------------------------------------+
