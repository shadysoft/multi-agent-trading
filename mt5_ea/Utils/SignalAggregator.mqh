//+------------------------------------------------------------------+
//|                                           SignalAggregator.mqh |
//|                                          Multi-Agent Trading EA |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Multi-Agent Trading System"
#property version   "1.00"
#property strict

#include "../Config/Settings.mqh"
#include "../Utils/Helpers.mqh"

//+------------------------------------------------------------------+
//| Signal Aggregator Class                                          |
//+------------------------------------------------------------------+
class CSignalAggregator
{
private:
   struct AgentSignal
   {
      string name;
      int signal;
      double confidence;
      double weight;
   };
   
   AgentSignal m_signals[];
   int m_signal_count;
   
public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   CSignalAggregator()
   {
      ArrayResize(m_signals, 10);
      m_signal_count = 0;
   }
   
   //+------------------------------------------------------------------+
   //| Add agent signal                                                 |
   //+------------------------------------------------------------------+
   void AddSignal(string agent_name, int signal, double confidence, double weight)
   {
      if(m_signal_count >= ArraySize(m_signals))
      {
         ArrayResize(m_signals, m_signal_count + 5);
      }
      
      m_signals[m_signal_count].name = agent_name;
      m_signals[m_signal_count].signal = signal;
      m_signals[m_signal_count].confidence = confidence;
      m_signals[m_signal_count].weight = weight;
      m_signal_count++;
   }
   
   //+------------------------------------------------------------------+
   //| Clear all signals                                                |
   //+------------------------------------------------------------------+
   void ClearSignals()
   {
      m_signal_count = 0;
   }
   
   //+------------------------------------------------------------------+
   //| Get minimum confidence threshold based on symbol type           |
   //+------------------------------------------------------------------+
   double GetMinConfidenceThreshold()
   {
      string symbol_type = GetSymbolType();
      
      if(symbol_type == "FOREX")
         return MinConfidenceForex;
      else if(symbol_type == "GOLD")
         return MinConfidenceGold;
      else if(symbol_type == "CRYPTO")
         return MinConfidenceCrypto;
      else
         return MinConfidenceDefault;
   }
   
   //+------------------------------------------------------------------+
   //| Calculate weighted confidence for a direction                    |
   //+------------------------------------------------------------------+
   double CalculateWeightedConfidence(int direction)
   {
      double total_weighted_confidence = 0;
      double total_weight = 0;
      
      for(int i = 0; i < m_signal_count; i++)
      {
         if(m_signals[i].signal == direction)
         {
            total_weighted_confidence += m_signals[i].confidence * m_signals[i].weight;
            total_weight += m_signals[i].weight;
         }
      }
      
      if(total_weight > 0)
         return total_weighted_confidence / total_weight;
      
      return 0;
   }
   
   //+------------------------------------------------------------------+
   //| Count signals for each direction                                 |
   //+------------------------------------------------------------------+
   void CountSignals(int &buy_count, int &sell_count, int &neutral_count)
   {
      buy_count = 0;
      sell_count = 0;
      neutral_count = 0;
      
      for(int i = 0; i < m_signal_count; i++)
      {
         if(m_signals[i].signal == SIGNAL_BUY)
            buy_count++;
         else if(m_signals[i].signal == SIGNAL_SELL)
            sell_count++;
         else
            neutral_count++;
      }
   }
   
   //+------------------------------------------------------------------+
   //| Check direction consensus                                        |
   //+------------------------------------------------------------------+
   bool HasConsensus(int direction)
   {
      int buy_count, sell_count, neutral_count;
      CountSignals(buy_count, sell_count, neutral_count);
      
      if(direction == SIGNAL_BUY)
      {
         // At least 2 agents agree and no opposing signals
         return (buy_count >= 2 && sell_count == 0);
      }
      else if(direction == SIGNAL_SELL)
      {
         // At least 2 agents agree and no opposing signals
         return (sell_count >= 2 && buy_count == 0);
      }
      
      return false;
   }
   
   //+------------------------------------------------------------------+
   //| Aggregate signals and make final decision                        |
   //+------------------------------------------------------------------+
   int AggregateSignals(double &final_confidence)
   {
      final_confidence = 0;
      
      if(m_signal_count == 0)
      {
         LogMessage("SignalAggregator: No signals to aggregate");
         return SIGNAL_NEUTRAL;
      }
      
      // Count signals by direction
      int buy_count, sell_count, neutral_count;
      CountSignals(buy_count, sell_count, neutral_count);
      
      // Calculate weighted confidence for each direction
      double buy_confidence = CalculateWeightedConfidence(SIGNAL_BUY);
      double sell_confidence = CalculateWeightedConfidence(SIGNAL_SELL);
      
      // Determine final signal based on voting and confidence
      int final_signal = SIGNAL_NEUTRAL;
      
      if(buy_count > sell_count && buy_count > neutral_count)
      {
         final_signal = SIGNAL_BUY;
         final_confidence = buy_confidence;
      }
      else if(sell_count > buy_count && sell_count > neutral_count)
      {
         final_signal = SIGNAL_SELL;
         final_confidence = sell_confidence;
      }
      else if(buy_count == sell_count && buy_count > 0)
      {
         // Tie-breaker: Use confidence
         if(buy_confidence > sell_confidence)
         {
            final_signal = SIGNAL_BUY;
            final_confidence = buy_confidence;
         }
         else if(sell_confidence > buy_confidence)
         {
            final_signal = SIGNAL_SELL;
            final_confidence = sell_confidence;
         }
         else
         {
            final_signal = SIGNAL_NEUTRAL;
            final_confidence = 0;
         }
      }
      
      // Check if confidence meets minimum threshold
      double min_threshold = GetMinConfidenceThreshold();
      
      if(final_confidence < min_threshold)
      {
         LogMessage("SignalAggregator: Confidence " + FormatDouble(final_confidence, 1) + 
                   "% below threshold " + FormatDouble(min_threshold, 1) + "%");
         return SIGNAL_NEUTRAL;
      }
      
      // Check for consensus (at least 2 agents agree)
      if(!HasConsensus(final_signal))
      {
         LogMessage("SignalAggregator: No consensus among agents");
         // Reduce confidence if no consensus (using configurable penalty)
         final_confidence *= NoConsensusPenalty;
         
         // Re-check threshold after reduction
         if(final_confidence < min_threshold)
            return SIGNAL_NEUTRAL;
      }
      
      // Log final decision
      string signal_str = (final_signal == SIGNAL_BUY) ? "BUY" : 
                         (final_signal == SIGNAL_SELL) ? "SELL" : "NEUTRAL";
      
      LogMessage("SignalAggregator: Final Decision = " + signal_str + 
                " | Confidence = " + FormatDouble(final_confidence, 1) + "%" +
                " | Votes: BUY=" + IntegerToString(buy_count) + 
                " SELL=" + IntegerToString(sell_count) +
                " NEUTRAL=" + IntegerToString(neutral_count));
      
      return final_signal;
   }
   
   //+------------------------------------------------------------------+
   //| Get summary of all agent signals                                 |
   //+------------------------------------------------------------------+
   string GetSignalsSummary()
   {
      string summary = "Agent Signals:\n";
      
      for(int i = 0; i < m_signal_count; i++)
      {
         string signal_str = (m_signals[i].signal == SIGNAL_BUY) ? "BUY" : 
                            (m_signals[i].signal == SIGNAL_SELL) ? "SELL" : "NEUTRAL";
         
         summary += m_signals[i].name + ": " + signal_str + 
                   " (" + FormatDouble(m_signals[i].confidence, 1) + "%) " +
                   "W=" + FormatDouble(m_signals[i].weight, 1) + "\n";
      }
      
      return summary;
   }
   
   //+------------------------------------------------------------------+
   //| Get agent signal for dashboard                                   |
   //+------------------------------------------------------------------+
   void GetAgentSignal(int index, string &name, int &signal, double &confidence)
   {
      if(index >= 0 && index < m_signal_count)
      {
         name = m_signals[index].name;
         signal = m_signals[index].signal;
         confidence = m_signals[index].confidence;
      }
      else
      {
         name = "";
         signal = SIGNAL_NEUTRAL;
         confidence = 0;
      }
   }
   
   //+------------------------------------------------------------------+
   //| Get number of signals                                            |
   //+------------------------------------------------------------------+
   int GetSignalCount()
   {
      return m_signal_count;
   }
};
