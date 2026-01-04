"""Alerts component for monitoring and notifications."""

import streamlit as st
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta

from data.database import DatabaseHandler
from data.models import TradeStatus


def render_alerts(db_handler: DatabaseHandler, risk_manager=None):
    """
    Render alerts and notifications panel.
    
    Args:
        db_handler: Database handler instance
        risk_manager: Risk manager instance (optional)
    """
    st.header("🔔 Alerts & Notifications")
    
    # Get active alerts
    alerts = get_active_alerts(db_handler, risk_manager)
    
    if not alerts:
        st.success("✅ No active alerts - All systems normal")
        return
    
    # Categorize alerts by severity
    critical_alerts = [a for a in alerts if a['severity'] == 'critical']
    warning_alerts = [a for a in alerts if a['severity'] == 'warning']
    info_alerts = [a for a in alerts if a['severity'] == 'info']
    
    # Display critical alerts
    if critical_alerts:
        st.error("🚨 Critical Alerts")
        for alert in critical_alerts:
            st.error(f"**{alert['title']}**: {alert['message']}")
    
    # Display warning alerts
    if warning_alerts:
        st.warning("⚠️ Warning Alerts")
        for alert in warning_alerts:
            st.warning(f"**{alert['title']}**: {alert['message']}")
    
    # Display info alerts
    if info_alerts:
        st.info("ℹ️ Information")
        for alert in info_alerts:
            st.info(f"**{alert['title']}**: {alert['message']}")
    
    # Display alert summary
    st.subheader("Alert Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Critical", len(critical_alerts), delta=None, delta_color="inverse")
    with col2:
        st.metric("Warnings", len(warning_alerts))
    with col3:
        st.metric("Info", len(info_alerts))


def get_active_alerts(db_handler: DatabaseHandler, risk_manager=None) -> List[Dict]:
    """
    Get list of active alerts based on trading conditions.
    
    Args:
        db_handler: Database handler instance
        risk_manager: Risk manager instance
        
    Returns:
        List of alert dictionaries
    """
    alerts = []
    
    # Check daily loss limit
    today_loss_alert = check_daily_loss(db_handler)
    if today_loss_alert:
        alerts.append(today_loss_alert)
    
    # Check drawdown
    drawdown_alert = check_drawdown(db_handler)
    if drawdown_alert:
        alerts.append(drawdown_alert)
    
    # Check losing streak
    losing_streak_alert = check_losing_streak(db_handler)
    if losing_streak_alert:
        alerts.append(losing_streak_alert)
    
    # Check low confidence trades
    low_confidence_alert = check_low_confidence_trades(db_handler)
    if low_confidence_alert:
        alerts.append(low_confidence_alert)
    
    # Check agent performance
    weak_agent_alerts = check_weak_agents(db_handler)
    alerts.extend(weak_agent_alerts)
    
    # Check open positions count
    if risk_manager:
        position_alert = check_position_count(db_handler, risk_manager)
        if position_alert:
            alerts.append(position_alert)
    
    return alerts


def check_daily_loss(db_handler: DatabaseHandler) -> Dict:
    """Check if daily loss limit is approaching or exceeded."""
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        all_trades = db_handler.get_trades(status=TradeStatus.CLOSED)
        
        today_trades = [
            t for t in all_trades
            if t.exit_time and t.exit_time >= today_start
        ]
        
        today_pnl = sum(t.profit_loss for t in today_trades if t.profit_loss is not None)
        
        if today_pnl < -1000:  # Threshold - should be configurable
            return {
                'severity': 'critical',
                'title': 'Daily Loss Alert',
                'message': f'Daily loss is ${abs(today_pnl):.2f}. Consider stopping trading for today.',
                'timestamp': datetime.now()
            }
        elif today_pnl < -500:
            return {
                'severity': 'warning',
                'title': 'Daily Loss Warning',
                'message': f'Daily loss is ${abs(today_pnl):.2f}. Approaching daily limit.',
                'timestamp': datetime.now()
            }
    except Exception:
        pass
    
    return None


def check_drawdown(db_handler: DatabaseHandler) -> Dict:
    """Check if drawdown is high."""
    try:
        all_trades = db_handler.get_trades(status=TradeStatus.CLOSED)
        
        if not all_trades:
            return None
        
        cumulative_pnl = 0.0
        peak = 0.0
        max_drawdown = 0.0
        
        for trade in all_trades:
            if trade.profit_loss is not None:
                cumulative_pnl += trade.profit_loss
                peak = max(peak, cumulative_pnl)
                drawdown = peak - cumulative_pnl
                max_drawdown = max(max_drawdown, drawdown)
        
        if max_drawdown > 2000:  # Threshold - should be configurable
            return {
                'severity': 'critical',
                'title': 'High Drawdown Alert',
                'message': f'Maximum drawdown is ${max_drawdown:.2f}. Risk management review recommended.',
                'timestamp': datetime.now()
            }
        elif max_drawdown > 1000:
            return {
                'severity': 'warning',
                'title': 'Drawdown Warning',
                'message': f'Current drawdown is ${max_drawdown:.2f}.',
                'timestamp': datetime.now()
            }
    except Exception:
        pass
    
    return None


def check_losing_streak(db_handler: DatabaseHandler) -> Dict:
    """Check for losing streaks."""
    try:
        recent_trades = db_handler.get_trades(status=TradeStatus.CLOSED, limit=10)
        
        if len(recent_trades) < 3:
            return None
        
        # Sort by exit time
        sorted_trades = sorted(recent_trades, key=lambda t: t.exit_time or datetime.now(), reverse=True)
        
        # Count consecutive losses
        losing_streak = 0
        for trade in sorted_trades:
            if not trade.is_winner:
                losing_streak += 1
            else:
                break
        
        if losing_streak >= 5:
            return {
                'severity': 'critical',
                'title': 'Losing Streak Alert',
                'message': f'{losing_streak} consecutive losing trades. System review recommended.',
                'timestamp': datetime.now()
            }
        elif losing_streak >= 3:
            return {
                'severity': 'warning',
                'title': 'Losing Streak Warning',
                'message': f'{losing_streak} consecutive losing trades detected.',
                'timestamp': datetime.now()
            }
    except Exception:
        pass
    
    return None


def check_low_confidence_trades(db_handler: DatabaseHandler) -> Dict:
    """Check for trades with low confidence that were still executed."""
    try:
        recent_trades = db_handler.get_trades(status=TradeStatus.CLOSED, limit=20)
        
        low_conf_trades = [t for t in recent_trades if t.confidence < 0.6]
        
        if len(low_conf_trades) > 5:
            return {
                'severity': 'warning',
                'title': 'Low Confidence Trades',
                'message': f'{len(low_conf_trades)} recent trades had confidence below 60%. Review threshold settings.',
                'timestamp': datetime.now()
            }
    except Exception:
        pass
    
    return None


def check_weak_agents(db_handler: DatabaseHandler) -> List[Dict]:
    """Check for underperforming agents."""
    alerts = []
    
    try:
        # Get agent performance metrics
        agent_names = ['TrendAgent', 'SMCAgent', 'StatisticalAgent', 'WaveAgent', 'LearningAgent']
        
        for agent_name in agent_names:
            metrics = db_handler.get_agent_performance(agent_name)
            
            if metrics and metrics.total_trades >= 20:  # Minimum trades for evaluation
                if metrics.win_rate < 0.4:  # Less than 40% win rate
                    alerts.append({
                        'severity': 'warning',
                        'title': f'Weak Agent: {agent_name}',
                        'message': f'{agent_name} has a win rate of {metrics.win_rate:.1%} over {metrics.total_trades} trades.',
                        'timestamp': datetime.now()
                    })
    except Exception:
        pass
    
    return alerts


def check_position_count(db_handler: DatabaseHandler, risk_manager) -> Dict:
    """Check if approaching max concurrent positions."""
    try:
        open_count = len(db_handler.get_trades(status=TradeStatus.OPEN))
        max_positions = risk_manager.max_concurrent_trades
        
        if open_count >= max_positions:
            return {
                'severity': 'warning',
                'title': 'Max Positions Reached',
                'message': f'Currently at maximum concurrent positions ({open_count}/{max_positions}).',
                'timestamp': datetime.now()
            }
        elif open_count >= max_positions * 0.8:
            return {
                'severity': 'info',
                'title': 'Position Count High',
                'message': f'Approaching max positions ({open_count}/{max_positions}).',
                'timestamp': datetime.now()
            }
    except Exception:
        pass
    
    return None
