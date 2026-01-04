//+------------------------------------------------------------------+
//|                                                MultiAgentEA.mq5 |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property link      "https://github.com/shadysoft/multi-agent-trading"
#property version   "1.00"
#property description "Multi-Agent AI Trading System for Forex, Gold, Stocks & Crypto"
#property strict

// Include all required files
#include "Config/Settings.mqh"
#include "Utils/Helpers.mqh"
#include "Utils/RiskManager.mqh"
#include "Utils/TradeManager.mqh"
#include "Utils/SignalAggregator.mqh"
#include "Agents/TrendAgent.mqh"
#include "Agents/SMCAgent.mqh"
#include "Agents/WaveAgent.mqh"
#include "Agents/StatisticalAgent.mqh"

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
CRiskManager* g_risk_manager = NULL;
CTradeManager* g_trade_manager = NULL;
CSignalAggregator* g_signal_aggregator = NULL;
CTrendAgent* g_trend_agent = NULL;
CSMCAgent* g_smc_agent = NULL;
CWaveAgent* g_wave_agent = NULL;
CStatisticalAgent* g_stats_agent = NULL;

datetime g_last_bar_time = 0;
bool g_is_initialized = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   LogMessage("========================================");
   LogMessage("Multi-Agent EA v1.0 - Initializing...");
   LogMessage("========================================");
   
   // Initialize settings
   InitSettings();
   
   // Create manager instances
   g_risk_manager = new CRiskManager();
   g_trade_manager = new CTradeManager();
   g_signal_aggregator = new CSignalAggregator();
   
   // Create agent instances
   g_trend_agent = new CTrendAgent();
   g_smc_agent = new CSMCAgent();
   g_wave_agent = new CWaveAgent();
   g_stats_agent = new CStatisticalAgent();
   
   // Validate initialization
   if(g_risk_manager == NULL || g_trade_manager == NULL || 
      g_signal_aggregator == NULL || g_trend_agent == NULL ||
      g_smc_agent == NULL || g_wave_agent == NULL || g_stats_agent == NULL)
   {
      LogMessage("ERROR: Failed to initialize managers or agents");
      return INIT_FAILED;
   }
   
   // Initialize trend agent indicators
   if(!g_trend_agent.Initialize())
   {
      LogMessage("ERROR: Failed to initialize Trend Agent");
      return INIT_FAILED;
   }
   
   g_is_initialized = true;
   
   LogMessage("Symbol: " + _Symbol);
   LogMessage("Timeframe: " + EnumToString(PERIOD_CURRENT));
   LogMessage("Magic Number: " + IntegerToString(MagicNumber));
   LogMessage("Risk per trade: " + FormatDouble(RiskPercent, 2) + "%");
   LogMessage("Risk/Reward Ratio: " + FormatDouble(RiskRewardRatio, 2));
   LogMessage("========================================");
   LogMessage("EA Initialized Successfully!");
   LogMessage("========================================");
   
   // Create dashboard
   if(ShowDashboard)
      CreateDashboard();
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   LogMessage("========================================");
   LogMessage("Multi-Agent EA - Shutting down...");
   LogMessage("Reason: " + IntegerToString(reason));
   LogMessage("========================================");
   
   // Delete dashboard
   if(ShowDashboard)
      DeleteDashboard();
   
   // Clean up instances
   if(g_risk_manager != NULL)
      delete g_risk_manager;
   if(g_trade_manager != NULL)
      delete g_trade_manager;
   if(g_signal_aggregator != NULL)
      delete g_signal_aggregator;
   if(g_trend_agent != NULL)
      delete g_trend_agent;
   if(g_smc_agent != NULL)
      delete g_smc_agent;
   if(g_wave_agent != NULL)
      delete g_wave_agent;
   if(g_stats_agent != NULL)
      delete g_stats_agent;
   
   g_is_initialized = false;
   
   LogMessage("EA Shutdown Complete");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!g_is_initialized)
      return;
   
   // Check for new bar
   datetime current_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(current_bar == g_last_bar_time)
   {
      // Manage existing positions on every tick
      g_trade_manager.ManageTrailingStop();
      g_trade_manager.ManageBreakEven();
      
      // Update dashboard
      if(ShowDashboard)
         UpdateDashboard();
      
      return;
   }
   
   g_last_bar_time = current_bar;
   
   // New bar - Run analysis
   LogMessage("========================================");
   LogMessage("New Bar - Running Analysis...");
   
   // Step 1: Validate trading conditions with Statistical Agent
   int stats_decision = g_stats_agent.Validate(g_risk_manager);
   
   if(stats_decision == BLOCK_TRADE)
   {
      LogMessage("Statistical Agent BLOCKED trading: " + g_stats_agent.GetBlockReason());
      if(ShowDashboard)
         UpdateDashboard();
      return;
   }
   
   // Step 2: Get signals from all analysis agents
   g_signal_aggregator.ClearSignals();
   
   // Trend Agent
   int trend_signal = SIGNAL_NEUTRAL;
   double trend_confidence = 0;
   g_trend_agent.Analyze(trend_signal, trend_confidence);
   g_signal_aggregator.AddSignal("Trend", trend_signal, trend_confidence, TrendAgentWeight);
   
   // SMC Agent
   int smc_signal = SIGNAL_NEUTRAL;
   double smc_confidence = 0;
   g_smc_agent.Analyze(smc_signal, smc_confidence);
   g_signal_aggregator.AddSignal("SMC", smc_signal, smc_confidence, SMCAgentWeight);
   
   // Wave Agent
   int wave_signal = SIGNAL_NEUTRAL;
   double wave_confidence = 0;
   g_wave_agent.Analyze(wave_signal, wave_confidence);
   g_signal_aggregator.AddSignal("Wave", wave_signal, wave_confidence, WaveAgentWeight);
   
   // Step 3: Aggregate signals
   double final_confidence = 0;
   int final_signal = g_signal_aggregator.AggregateSignals(final_confidence);
   
   // Step 4: Execute trade if signal is valid
   if(final_signal != SIGNAL_NEUTRAL)
   {
      ExecuteTrade(final_signal, final_confidence);
   }
   else
   {
      LogMessage("No valid trading signal - Waiting...");
   }
   
   // Update dashboard
   if(ShowDashboard)
      UpdateDashboard();
   
   LogMessage("========================================");
}

//+------------------------------------------------------------------+
//| Execute trade based on signal                                    |
//+------------------------------------------------------------------+
void ExecuteTrade(int signal, double confidence)
{
   // Calculate stop loss and take profit
   double sl_points = g_risk_manager.CalculateStopLoss();
   double tp_points = g_risk_manager.CalculateTakeProfit(sl_points);
   
   // Calculate lot size
   double lot_size = g_risk_manager.CalculateLotSize(sl_points);
   
   if(lot_size <= 0)
   {
      LogMessage("Invalid lot size calculated - Trade aborted");
      return;
   }
   
   // Check margin
   ENUM_ORDER_TYPE order_type = (signal == SIGNAL_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!g_risk_manager.CheckMargin(lot_size, order_type))
   {
      LogMessage("Insufficient margin - Trade aborted");
      return;
   }
   
   // Execute trade
   bool result = false;
   if(signal == SIGNAL_BUY)
   {
      LogMessage("Opening BUY position with confidence: " + FormatDouble(confidence, 1) + "%");
      result = g_trade_manager.OpenBuy(lot_size, sl_points, tp_points, 
                                       EA_Name + " BUY (" + FormatDouble(confidence, 0) + "%)");
   }
   else if(signal == SIGNAL_SELL)
   {
      LogMessage("Opening SELL position with confidence: " + FormatDouble(confidence, 1) + "%");
      result = g_trade_manager.OpenSell(lot_size, sl_points, tp_points,
                                        EA_Name + " SELL (" + FormatDouble(confidence, 0) + "%)");
   }
   
   if(result)
   {
      LogMessage("Trade executed successfully!");
   }
   else
   {
      LogMessage("Trade execution failed!");
   }
}

//+------------------------------------------------------------------+
//| Create dashboard on chart                                        |
//+------------------------------------------------------------------+
void CreateDashboard()
{
   int x = 10;
   int y = 20;
   int width = 280;
   int line_height = 18;
   
   // Background panel
   ObjectCreate(0, "Dashboard_BG", OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "Dashboard_BG", OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, "Dashboard_BG", OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, "Dashboard_BG", OBJPROP_XSIZE, width);
   ObjectSetInteger(0, "Dashboard_BG", OBJPROP_YSIZE, 280);
   ObjectSetInteger(0, "Dashboard_BG", OBJPROP_BGCOLOR, clrBlack);
   ObjectSetInteger(0, "Dashboard_BG", OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, "Dashboard_BG", OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, "Dashboard_BG", OBJPROP_BACK, true);
   ObjectSetInteger(0, "Dashboard_BG", OBJPROP_SELECTABLE, false);
   
   // Create labels
   CreateLabel("Dashboard_Title", x + 10, y + 10, EA_Name, clrWhite, 10, "Arial Bold");
   CreateLabel("Dashboard_Status", x + 10, y + 30, "Status: RUNNING", clrLime, Dashboard_FontSize);
   CreateLabel("Dashboard_Symbol", x + 10, y + 50, "Symbol: " + _Symbol, clrWhite, Dashboard_FontSize);
   CreateLabel("Dashboard_Spread", x + 10, y + 70, "Spread: 0.0 pips", clrWhite, Dashboard_FontSize);
   
   CreateLabel("Dashboard_AgentTitle", x + 10, y + 95, "AGENTS:", clrYellow, Dashboard_FontSize, "Arial Bold");
   CreateLabel("Dashboard_Trend", x + 10, y + 115, "├─ Trend:    WAIT", clrGray, Dashboard_FontSize);
   CreateLabel("Dashboard_SMC", x + 10, y + 135, "├─ SMC:      WAIT", clrGray, Dashboard_FontSize);
   CreateLabel("Dashboard_Wave", x + 10, y + 155, "├─ Wave:     WAIT", clrGray, Dashboard_FontSize);
   CreateLabel("Dashboard_Stats", x + 10, y + 175, "└─ Stats:    ALLOW", clrLime, Dashboard_FontSize);
   
   CreateLabel("Dashboard_Final", x + 10, y + 200, "Final: WAIT | Confidence: 0%", clrWhite, Dashboard_FontSize);
   
   CreateLabel("Dashboard_Positions", x + 10, y + 225, "Open Trades: 0/3", clrWhite, Dashboard_FontSize);
   CreateLabel("Dashboard_PL", x + 10, y + 245, "Today P/L: +0.00 USD", clrWhite, Dashboard_FontSize);
   CreateLabel("Dashboard_DD", x + 10, y + 265, "Drawdown: 0.0%", clrWhite, Dashboard_FontSize);
   
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Create label helper                                              |
//+------------------------------------------------------------------+
void CreateLabel(string name, int x, int y, string text, color clr, int font_size = 9, string font = "Consolas")
{
   ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, font_size);
   ObjectSetString(0, name, OBJPROP_FONT, font);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
}

//+------------------------------------------------------------------+
//| Update dashboard                                                 |
//+------------------------------------------------------------------+
void UpdateDashboard()
{
   if(!ShowDashboard)
      return;
   
   // Update spread
   double spread = GetSpreadPoints();
   double spread_pips = spread / 10.0;
   string spread_text = "Spread: " + FormatDouble(spread_pips, 1) + " pips";
   if(spread > MaxSpreadPoints)
      spread_text += " ✗";
   else
      spread_text += " ✓";
   ObjectSetString(0, "Dashboard_Spread", OBJPROP_TEXT, spread_text);
   ObjectSetInteger(0, "Dashboard_Spread", OBJPROP_COLOR, 
                    spread > MaxSpreadPoints ? clrRed : clrLime);
   
   // Update agent signals
   int signal_count = g_signal_aggregator.GetSignalCount();
   
   for(int i = 0; i < signal_count; i++)
   {
      string agent_name;
      int signal;
      double confidence;
      g_signal_aggregator.GetAgentSignal(i, agent_name, signal, confidence);
      
      string signal_text = (signal == SIGNAL_BUY) ? "BUY" : 
                          (signal == SIGNAL_SELL) ? "SELL" : "NEUTRAL";
      color signal_color = (signal == SIGNAL_BUY) ? BuyColor : 
                          (signal == SIGNAL_SELL) ? SellColor : NeutralColor;
      
      string symbol_indicator = (signal != SIGNAL_NEUTRAL) ? "●" : "○";
      
      string display_text = "";
      if(agent_name == "Trend")
         display_text = "├─ Trend:    " + signal_text + "  (" + FormatDouble(confidence, 0) + "%)  " + symbol_indicator;
      else if(agent_name == "SMC")
         display_text = "├─ SMC:      " + signal_text + "  (" + FormatDouble(confidence, 0) + "%)  " + symbol_indicator;
      else if(agent_name == "Wave")
         display_text = "├─ Wave:     " + signal_text + "  (" + FormatDouble(confidence, 0) + "%)  " + symbol_indicator;
      
      if(agent_name == "Trend")
      {
         ObjectSetString(0, "Dashboard_Trend", OBJPROP_TEXT, display_text);
         ObjectSetInteger(0, "Dashboard_Trend", OBJPROP_COLOR, signal_color);
      }
      else if(agent_name == "SMC")
      {
         ObjectSetString(0, "Dashboard_SMC", OBJPROP_TEXT, display_text);
         ObjectSetInteger(0, "Dashboard_SMC", OBJPROP_COLOR, signal_color);
      }
      else if(agent_name == "Wave")
      {
         ObjectSetString(0, "Dashboard_Wave", OBJPROP_TEXT, display_text);
         ObjectSetInteger(0, "Dashboard_Wave", OBJPROP_COLOR, signal_color);
      }
   }
   
   // Update stats agent
   string stats_status = g_stats_agent.GetStatusString();
   ObjectSetString(0, "Dashboard_Stats", OBJPROP_TEXT, "└─ Stats:    " + stats_status);
   ObjectSetInteger(0, "Dashboard_Stats", OBJPROP_COLOR, 
                    StringFind(stats_status, "ALLOW") >= 0 ? clrLime : clrRed);
   
   // Update final decision
   double final_confidence = 0;
   int final_signal = g_signal_aggregator.AggregateSignals(final_confidence);
   string final_text = (final_signal == SIGNAL_BUY) ? "BUY" : 
                      (final_signal == SIGNAL_SELL) ? "SELL" : "WAIT";
   color final_color = (final_signal == SIGNAL_BUY) ? BuyColor : 
                      (final_signal == SIGNAL_SELL) ? SellColor : NeutralColor;
   
   ObjectSetString(0, "Dashboard_Final", OBJPROP_TEXT, 
                  "Final: " + final_text + " | Confidence: " + FormatDouble(final_confidence, 0) + "%");
   ObjectSetInteger(0, "Dashboard_Final", OBJPROP_COLOR, final_color);
   
   // Update positions
   int open_positions = g_risk_manager.CountOpenPositions();
   ObjectSetString(0, "Dashboard_Positions", OBJPROP_TEXT, 
                  "Open Trades: " + IntegerToString(open_positions) + "/" + IntegerToString(MaxOpenTrades));
   
   // Update P/L
   double today_pl = g_trade_manager.GetTodayProfitLoss();
   string pl_text = "Today P/L: " + (today_pl >= 0 ? "+" : "") + FormatDouble(today_pl, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY);
   ObjectSetString(0, "Dashboard_PL", OBJPROP_TEXT, pl_text);
   ObjectSetInteger(0, "Dashboard_PL", OBJPROP_COLOR, today_pl >= 0 ? clrLime : clrRed);
   
   // Update drawdown
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   
   // Calculate current floating drawdown
   double dd = 0;
   if(balance > 0.0001 && equity < balance)
   {
      dd = ((balance - equity) / balance) * 100.0;
   }
   
   ObjectSetString(0, "Dashboard_DD", OBJPROP_TEXT, "Drawdown: " + FormatDouble(dd, 1) + "%");
   ObjectSetInteger(0, "Dashboard_DD", OBJPROP_COLOR, dd < 5.0 ? clrLime : (dd < 8.0 ? clrYellow : clrRed));
   
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Delete dashboard                                                 |
//+------------------------------------------------------------------+
void DeleteDashboard()
{
   ObjectDelete(0, "Dashboard_BG");
   ObjectDelete(0, "Dashboard_Title");
   ObjectDelete(0, "Dashboard_Status");
   ObjectDelete(0, "Dashboard_Symbol");
   ObjectDelete(0, "Dashboard_Spread");
   ObjectDelete(0, "Dashboard_AgentTitle");
   ObjectDelete(0, "Dashboard_Trend");
   ObjectDelete(0, "Dashboard_SMC");
   ObjectDelete(0, "Dashboard_Wave");
   ObjectDelete(0, "Dashboard_Stats");
   ObjectDelete(0, "Dashboard_Final");
   ObjectDelete(0, "Dashboard_Positions");
   ObjectDelete(0, "Dashboard_PL");
   ObjectDelete(0, "Dashboard_DD");
   
   ChartRedraw();
}
