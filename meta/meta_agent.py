"""Meta-Agent for aggregating signals and making final trading decisions."""

from typing import List, Dict, Optional
import logging
import yaml
from datetime import datetime

from data.models import AgentSignal, TradeSignal, SignalDirection, MarketType
from strategies.confidence_calculator import ConfidenceCalculator

logger = logging.getLogger(__name__)


class MetaAgent:
    """Meta-agent that aggregates signals from all agents and makes final decisions."""

    def __init__(
        self,
        market_type: MarketType,
        config_path: Optional[str] = None,
        agent_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize Meta-Agent.
        
        Args:
            market_type: Type of market (forex, gold, stocks, crypto)
            config_path: Path to market-specific config file
            agent_weights: Custom agent weights (overrides config)
        """
        self.market_type = market_type
        self.config = self._load_config(config_path, market_type)
        
        # Get thresholds from config
        meta_config = self.config.get('meta_agent', {})
        self.confidence_threshold = meta_config.get('confidence_threshold', 0.75)
        self.min_agents_required = meta_config.get('min_agents_required', 3)
        
        # Get agent weights
        if agent_weights:
            self.agent_weights = agent_weights
        else:
            self.agent_weights = self.config.get('agent_weights', {
                'TrendAgent': 0.25,
                'SMCAgent': 0.25,
                'StatisticalAgent': 0.20,
                'WaveAgent': 0.20,
                'LearningAgent': 0.10
            })
        
        self.confidence_calculator = ConfidenceCalculator()
        logger.info(f"MetaAgent initialized for {market_type.value} with threshold {self.confidence_threshold}")

    def _load_config(self, config_path: Optional[str], market_type: MarketType) -> dict:
        """
        Load market-specific configuration.
        
        Args:
            config_path: Path to config file
            market_type: Market type
            
        Returns:
            Configuration dictionary
        """
        if config_path is None:
            # Determine config path based on market type
            config_map = {
                MarketType.FOREX: 'config/forex_config.yaml',
                MarketType.GOLD: 'config/gold_config.yaml',
                MarketType.STOCKS: 'config/stocks_config.yaml',
                MarketType.CRYPTO: 'config/crypto_config.yaml'
            }
            config_path = config_map.get(market_type, 'config/settings.yaml')
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return {}

    def aggregate_signals(
        self,
        agent_signals: List[AgentSignal],
        symbol: str
    ) -> TradeSignal:
        """
        Aggregate signals from all agents and make final decision.
        
        Args:
            agent_signals: List of signals from individual agents
            symbol: Trading symbol
            
        Returns:
            TradeSignal with final decision
        """
        # Validate we have enough agents
        if len(agent_signals) < self.min_agents_required:
            logger.warning(f"Insufficient agents ({len(agent_signals)}/{self.min_agents_required})")
            return TradeSignal(
                symbol=symbol,
                market_type=self.market_type,
                direction=SignalDirection.WAIT,
                confidence=0.0,
                agent_signals=agent_signals,
                reasoning=f"Insufficient agents ({len(agent_signals)}/{self.min_agents_required})"
            )

        # Separate signals by direction
        buy_signals = [s for s in agent_signals if s.direction == SignalDirection.BUY]
        sell_signals = [s for s in agent_signals if s.direction == SignalDirection.SELL]
        wait_signals = [s for s in agent_signals if s.direction == SignalDirection.WAIT]
        
        # Calculate weighted confidence for each direction
        buy_confidence = self._calculate_weighted_confidence(buy_signals)
        sell_confidence = self._calculate_weighted_confidence(sell_signals)
        
        # Determine final direction and confidence
        final_direction = SignalDirection.WAIT
        final_confidence = 0.0
        reasoning_parts = []
        
        # Check if BUY signals meet threshold
        if buy_confidence >= self.confidence_threshold:
            final_direction = SignalDirection.BUY
            final_confidence = buy_confidence
            reasoning_parts.append(f"BUY confidence {buy_confidence:.2%} meets threshold {self.confidence_threshold:.2%}")
            reasoning_parts.append(f"{len(buy_signals)} agents favor BUY")
        
        # Check if SELL signals meet threshold
        elif sell_confidence >= self.confidence_threshold:
            final_direction = SignalDirection.SELL
            final_confidence = sell_confidence
            reasoning_parts.append(f"SELL confidence {sell_confidence:.2%} meets threshold {self.confidence_threshold:.2%}")
            reasoning_parts.append(f"{len(sell_signals)} agents favor SELL")
        
        # Neither direction meets threshold
        else:
            reasoning_parts.append(f"No direction meets threshold (BUY: {buy_confidence:.2%}, SELL: {sell_confidence:.2%})")
            reasoning_parts.append(f"Signals: {len(buy_signals)} BUY, {len(sell_signals)} SELL, {len(wait_signals)} WAIT")
        
        # Add individual agent reasonings
        for signal in agent_signals:
            if signal.direction != SignalDirection.WAIT:
                reasoning_parts.append(f"{signal.agent_name}: {signal.reasoning}")
        
        reasoning = " | ".join(reasoning_parts)
        
        trade_signal = TradeSignal(
            symbol=symbol,
            market_type=self.market_type,
            direction=final_direction,
            confidence=final_confidence,
            agent_signals=agent_signals,
            reasoning=reasoning
        )
        
        logger.info(f"{symbol} - Final Signal: {final_direction.value} with confidence {final_confidence:.2%}")
        
        return trade_signal

    def _calculate_weighted_confidence(self, signals: List[AgentSignal]) -> float:
        """
        Calculate weighted confidence score from agent signals.
        
        Args:
            signals: List of agent signals
            
        Returns:
            Weighted confidence score (0.0 to 1.0)
        """
        if not signals:
            return 0.0
        
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for signal in signals:
            agent_weight = self.agent_weights.get(signal.agent_name, 0.2)
            weighted_confidence = signal.confidence * agent_weight
            total_weighted_confidence += weighted_confidence
            total_weight += agent_weight
        
        if total_weight == 0:
            return 0.0
        
        # Normalize by total weight
        normalized_confidence = total_weighted_confidence / total_weight
        
        return min(normalized_confidence, 1.0)

    def update_agent_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Update agent weights.
        
        Args:
            new_weights: Dictionary of agent_name: weight
        """
        self.agent_weights.update(new_weights)
        logger.info(f"Updated agent weights: {self.agent_weights}")

    def get_decision_summary(self, agent_signals: List[AgentSignal]) -> Dict:
        """
        Get summary of decision-making process.
        
        Args:
            agent_signals: List of agent signals
            
        Returns:
            Dictionary with decision summary
        """
        buy_signals = [s for s in agent_signals if s.direction == SignalDirection.BUY]
        sell_signals = [s for s in agent_signals if s.direction == SignalDirection.SELL]
        wait_signals = [s for s in agent_signals if s.direction == SignalDirection.WAIT]
        
        buy_confidence = self._calculate_weighted_confidence(buy_signals)
        sell_confidence = self._calculate_weighted_confidence(sell_signals)
        
        return {
            'total_agents': len(agent_signals),
            'buy_count': len(buy_signals),
            'sell_count': len(sell_signals),
            'wait_count': len(wait_signals),
            'buy_confidence': buy_confidence,
            'sell_confidence': sell_confidence,
            'threshold': self.confidence_threshold,
            'buy_meets_threshold': buy_confidence >= self.confidence_threshold,
            'sell_meets_threshold': sell_confidence >= self.confidence_threshold,
            'agent_weights': self.agent_weights
        }

    def validate_statistical_gate(self, agent_signals: List[AgentSignal]) -> bool:
        """
        Check if statistical agent (gatekeeper) approves trading.
        
        Args:
            agent_signals: List of agent signals
            
        Returns:
            True if statistical agent approves
        """
        statistical_signal = next(
            (s for s in agent_signals if s.agent_name == 'StatisticalAgent'),
            None
        )
        
        if statistical_signal is None:
            logger.warning("Statistical agent signal not found")
            return False
        
        # Statistical agent should have BUY signal (neutral approval) with good confidence
        if statistical_signal.direction == SignalDirection.WAIT:
            logger.info(f"Statistical gate blocked: {statistical_signal.reasoning}")
            return False
        
        if statistical_signal.confidence < 0.6:
            logger.info(f"Statistical gate blocked: Low confidence ({statistical_signal.confidence:.2%})")
            return False
        
        return True
