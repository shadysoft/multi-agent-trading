"""Adaptive Learning Agent for adjusting agent weights based on performance."""

import pandas as pd
from typing import Optional, Dict, List
import logging
from datetime import datetime, timedelta

from .base_agent import BaseAgent
from data.models import AgentSignal, SignalDirection, PerformanceMetrics, Trade, TradeStatus
from data.database import DatabaseHandler

logger = logging.getLogger(__name__)


class LearningAgent(BaseAgent):
    """Adaptive learning agent that adjusts agent weights based on performance."""

    def __init__(
        self,
        symbol: str,
        timeframe: str = "H1",
        weight: float = 0.10,
        learning_rate: float = 0.01,
        evaluation_window: int = 100,
        min_trades_for_learning: int = 20
    ):
        """
        Initialize Learning Agent.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            weight: Agent weight
            learning_rate: Rate of weight adjustment (±1% per 100 trades)
            evaluation_window: Number of trades to evaluate
            min_trades_for_learning: Minimum trades before starting to learn
        """
        super().__init__("LearningAgent", symbol, timeframe, weight)
        self.learning_rate = learning_rate
        self.evaluation_window = evaluation_window
        self.min_trades_for_learning = min_trades_for_learning
        self.db_handler = DatabaseHandler()

    def analyze(self, data: pd.DataFrame) -> AgentSignal:
        """
        Analyze agent performance and provide recommendations.
        
        Args:
            data: DataFrame with OHLCV data (not used directly, but required by interface)
            
        Returns:
            AgentSignal with recommendations
        """
        try:
            # Get recent trades
            recent_trades = self.db_handler.get_trades(
                symbol=self.symbol,
                status=TradeStatus.CLOSED,
                limit=self.evaluation_window
            )
            
            # Check if we have enough data to learn
            if len(recent_trades) < self.min_trades_for_learning:
                return self.create_signal(
                    SignalDirection.WAIT,
                    0.5,
                    f"Insufficient trade history ({len(recent_trades)}/{self.min_trades_for_learning})",
                    metadata={'trade_count': len(recent_trades)}
                )
            
            # Evaluate performance and determine if we should continue learning
            performance_analysis = self._evaluate_performance(recent_trades)
            
            # Check for losing streak
            if performance_analysis['losing_streak'] >= 5:
                return self.create_signal(
                    SignalDirection.WAIT,
                    0.3,
                    f"Losing streak detected ({performance_analysis['losing_streak']} trades). Pausing learning.",
                    metadata=performance_analysis
                )
            
            # Calculate recommended weight adjustments
            weight_adjustments = self._calculate_weight_adjustments(recent_trades)
            
            # Determine overall confidence based on recent performance
            win_rate = performance_analysis['win_rate']
            avg_rr = performance_analysis['avg_rr']
            
            confidence = 0.5  # Neutral baseline
            
            if win_rate >= 0.6 and avg_rr >= 1.5:
                confidence = 0.8
                direction = SignalDirection.BUY
                reasoning = f"Strong performance (WR: {win_rate:.1%}, RR: {avg_rr:.2f}). Recommending weight increases."
            elif win_rate >= 0.5 and avg_rr >= 1.0:
                confidence = 0.6
                direction = SignalDirection.BUY
                reasoning = f"Adequate performance (WR: {win_rate:.1%}, RR: {avg_rr:.2f}). Maintaining current weights."
            else:
                confidence = 0.4
                direction = SignalDirection.WAIT
                reasoning = f"Underperformance (WR: {win_rate:.1%}, RR: {avg_rr:.2f}). Recommending weight decreases."
            
            metadata = {
                **performance_analysis,
                'weight_adjustments': weight_adjustments,
                'total_trades_analyzed': len(recent_trades)
            }
            
            return self.create_signal(direction, confidence, reasoning, metadata)
            
        except Exception as e:
            logger.error(f"Error in LearningAgent analysis: {e}")
            return self.create_signal(
                SignalDirection.WAIT,
                0.0,
                f"Analysis error: {str(e)}"
            )

    def _evaluate_performance(self, trades: List[Trade]) -> Dict:
        """
        Evaluate trading performance.
        
        Args:
            trades: List of closed trades
            
        Returns:
            Dictionary with performance metrics
        """
        if not trades:
            return {
                'win_rate': 0.0,
                'avg_rr': 0.0,
                'total_profit': 0.0,
                'losing_streak': 0,
                'winning_streak': 0,
                'max_drawdown': 0.0
            }
        
        winning_trades = [t for t in trades if t.is_winner]
        losing_trades = [t for t in trades if not t.is_winner and t.profit_loss is not None]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0.0
        
        # Calculate average risk-reward ratio
        rr_ratios = [t.risk_reward_ratio for t in trades if t.risk_reward_ratio is not None]
        avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0.0
        
        # Calculate total profit
        total_profit = sum(t.profit_loss for t in trades if t.profit_loss is not None)
        
        # Calculate losing/winning streaks
        current_streak = 0
        losing_streak = 0
        winning_streak = 0
        
        for trade in reversed(trades):
            if trade.is_winner:
                if current_streak >= 0:
                    current_streak += 1
                    winning_streak = max(winning_streak, current_streak)
                else:
                    break
            else:
                if current_streak <= 0:
                    current_streak -= 1
                    losing_streak = max(losing_streak, abs(current_streak))
                else:
                    break
        
        # Calculate max drawdown
        cumulative_profit = 0.0
        peak = 0.0
        max_drawdown = 0.0
        
        for trade in trades:
            if trade.profit_loss is not None:
                cumulative_profit += trade.profit_loss
                peak = max(peak, cumulative_profit)
                drawdown = peak - cumulative_profit
                max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'win_rate': win_rate,
            'avg_rr': avg_rr,
            'total_profit': total_profit,
            'losing_streak': losing_streak,
            'winning_streak': winning_streak,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades)
        }

    def _calculate_weight_adjustments(self, trades: List[Trade]) -> Dict[str, float]:
        """
        Calculate recommended weight adjustments for each agent.
        
        Args:
            trades: List of closed trades
            
        Returns:
            Dictionary with agent_name: weight_adjustment
        """
        # Group trades by contributing agents (would need to be stored in trade metadata)
        # For now, return a placeholder implementation
        
        # In a full implementation, we would:
        # 1. Track which agents contributed to each trade
        # 2. Calculate performance metrics per agent
        # 3. Adjust weights based on individual agent performance
        
        adjustments = {}
        
        # Calculate overall performance
        performance = self._evaluate_performance(trades)
        win_rate = performance['win_rate']
        avg_rr = performance['avg_rr']
        
        # Simplified adjustment logic
        if win_rate >= 0.6 and avg_rr >= 1.5:
            # Good performance - small positive adjustments
            base_adjustment = self.learning_rate
        elif win_rate >= 0.5 and avg_rr >= 1.0:
            # Neutral performance - no adjustment
            base_adjustment = 0.0
        else:
            # Poor performance - small negative adjustments
            base_adjustment = -self.learning_rate
        
        # Apply adjustments (in real implementation, would be per-agent)
        agent_names = ['TrendAgent', 'SMCAgent', 'StatisticalAgent', 'WaveAgent']
        for agent_name in agent_names:
            adjustments[agent_name] = base_adjustment
        
        return adjustments

    def update_agent_weights(self, weight_adjustments: Dict[str, float]) -> None:
        """
        Update agent weights in the database.
        
        Args:
            weight_adjustments: Dictionary of agent_name: adjustment
        """
        try:
            current_weights = self.db_handler.get_agent_weights()
            
            for agent_name, adjustment in weight_adjustments.items():
                current_weight = current_weights.get(agent_name, 0.2)
                new_weight = max(0.05, min(0.5, current_weight + adjustment))  # Clamp between 5% and 50%
                
                self.db_handler.save_agent_weight(agent_name, new_weight)
                logger.info(f"Updated {agent_name} weight: {current_weight:.3f} -> {new_weight:.3f}")
        
        except Exception as e:
            logger.error(f"Error updating agent weights: {e}")

    def get_performance_summary(self, days: int = 30) -> Dict:
        """
        Get performance summary for the last N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with performance summary
        """
        try:
            # Get trades from the last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            all_trades = self.db_handler.get_trades(symbol=self.symbol, status=TradeStatus.CLOSED)
            
            recent_trades = [
                t for t in all_trades
                if t.entry_time >= cutoff_date
            ]
            
            performance = self._evaluate_performance(recent_trades)
            
            return {
                'period_days': days,
                'symbol': self.symbol,
                **performance
            }
        
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
