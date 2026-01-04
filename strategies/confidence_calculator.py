"""Confidence score calculator for trading signals."""

from typing import List, Dict, Optional
import logging
from datetime import datetime

from data.models import AgentSignal, SignalDirection

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """Calculator for aggregating and normalizing confidence scores."""

    def __init__(self):
        """Initialize confidence calculator."""
        pass

    def calculate_aggregate_confidence(
        self,
        signals: List[AgentSignal],
        weights: Dict[str, float]
    ) -> float:
        """
        Calculate aggregate confidence from multiple signals.
        
        Args:
            signals: List of agent signals
            weights: Dictionary of agent weights
            
        Returns:
            Aggregate confidence score (0.0 to 1.0)
        """
        if not signals:
            return 0.0
        
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for signal in signals:
            agent_weight = weights.get(signal.agent_name, 0.2)
            weighted_confidence = signal.confidence * agent_weight
            total_weighted_confidence += weighted_confidence
            total_weight += agent_weight
        
        if total_weight == 0:
            return 0.0
        
        # Normalize by total weight
        aggregate_confidence = total_weighted_confidence / total_weight
        
        return min(aggregate_confidence, 1.0)

    def calculate_signal_strength(
        self,
        buy_signals: List[AgentSignal],
        sell_signals: List[AgentSignal],
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate signal strength for both directions.
        
        Args:
            buy_signals: List of BUY signals
            sell_signals: List of SELL signals
            weights: Dictionary of agent weights
            
        Returns:
            Dictionary with buy_strength and sell_strength
        """
        buy_strength = self.calculate_aggregate_confidence(buy_signals, weights)
        sell_strength = self.calculate_aggregate_confidence(sell_signals, weights)
        
        return {
            'buy_strength': buy_strength,
            'sell_strength': sell_strength,
            'net_strength': buy_strength - sell_strength
        }

    def calculate_consensus_score(
        self,
        signals: List[AgentSignal],
        direction: SignalDirection
    ) -> float:
        """
        Calculate consensus score for a specific direction.
        
        Args:
            signals: List of all agent signals
            direction: Direction to calculate consensus for
            
        Returns:
            Consensus score (0.0 to 1.0)
        """
        if not signals:
            return 0.0
        
        # Count signals in the specified direction
        matching_signals = [s for s in signals if s.direction == direction]
        
        # Calculate consensus as percentage of agents agreeing
        consensus = len(matching_signals) / len(signals)
        
        return consensus

    def calculate_confidence_band(
        self,
        signals: List[AgentSignal],
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate confidence bands (high, medium, low).
        
        Args:
            signals: List of agent signals
            weights: Dictionary of agent weights
            
        Returns:
            Dictionary with confidence bands
        """
        if not signals:
            return {
                'high_confidence': 0.0,
                'medium_confidence': 0.0,
                'low_confidence': 0.0
            }
        
        high_conf_signals = [s for s in signals if s.confidence >= 0.7]
        medium_conf_signals = [s for s in signals if 0.4 <= s.confidence < 0.7]
        low_conf_signals = [s for s in signals if s.confidence < 0.4]
        
        return {
            'high_confidence': self.calculate_aggregate_confidence(high_conf_signals, weights),
            'medium_confidence': self.calculate_aggregate_confidence(medium_conf_signals, weights),
            'low_confidence': self.calculate_aggregate_confidence(low_conf_signals, weights),
            'high_count': len(high_conf_signals),
            'medium_count': len(medium_conf_signals),
            'low_count': len(low_conf_signals)
        }

    def normalize_confidence(
        self,
        confidence: float,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0
    ) -> float:
        """
        Normalize confidence score to a specific range.
        
        Args:
            confidence: Raw confidence score
            min_confidence: Minimum confidence value
            max_confidence: Maximum confidence value
            
        Returns:
            Normalized confidence score
        """
        return max(min_confidence, min(confidence, max_confidence))

    def apply_time_decay(
        self,
        signals: List[AgentSignal],
        decay_factor: float = 0.1
    ) -> List[AgentSignal]:
        """
        Apply time decay to signal confidence based on age.
        
        Args:
            signals: List of agent signals
            decay_factor: Decay factor per hour (0.0 to 1.0)
            
        Returns:
            List of signals with decayed confidence
        """
        current_time = datetime.now()
        decayed_signals = []
        
        for signal in signals:
            # Calculate age in hours
            age_hours = (current_time - signal.timestamp).total_seconds() / 3600
            
            # Apply exponential decay
            decay = (1 - decay_factor) ** age_hours
            decayed_confidence = signal.confidence * decay
            
            # Create new signal with decayed confidence
            decayed_signal = AgentSignal(
                agent_name=signal.agent_name,
                symbol=signal.symbol,
                direction=signal.direction,
                confidence=decayed_confidence,
                reasoning=f"{signal.reasoning} (age: {age_hours:.1f}h, decay: {decay:.2f})",
                timestamp=signal.timestamp,
                metadata=signal.metadata
            )
            decayed_signals.append(decayed_signal)
        
        return decayed_signals

    def calculate_risk_adjusted_confidence(
        self,
        confidence: float,
        risk_reward_ratio: float,
        win_rate: float = 0.5
    ) -> float:
        """
        Calculate risk-adjusted confidence based on R:R and win rate.
        
        Args:
            confidence: Base confidence score
            risk_reward_ratio: Expected risk-reward ratio
            win_rate: Historical win rate
            
        Returns:
            Risk-adjusted confidence score
        """
        # Expected value = (Win Rate * Reward) - (Loss Rate * Risk)
        # For R:R ratio, reward = R:R, risk = 1
        expected_value = (win_rate * risk_reward_ratio) - ((1 - win_rate) * 1)
        
        # Normalize expected value to 0-1 range (assuming max EV of 2)
        ev_normalized = max(0.0, min(expected_value / 2.0, 1.0))
        
        # Blend original confidence with EV adjustment
        risk_adjusted = (confidence * 0.7) + (ev_normalized * 0.3)
        
        return min(risk_adjusted, 1.0)

    def get_confidence_interpretation(self, confidence: float) -> str:
        """
        Get text interpretation of confidence score.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Text interpretation
        """
        if confidence >= 0.8:
            return "Very High"
        elif confidence >= 0.7:
            return "High"
        elif confidence >= 0.6:
            return "Moderate"
        elif confidence >= 0.5:
            return "Low"
        else:
            return "Very Low"
