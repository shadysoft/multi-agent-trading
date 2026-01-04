"""Overview tab component for the dashboard."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
from datetime import datetime, timedelta

from data.database import DatabaseHandler
from data.models import TradeStatus


def render_overview(db_handler: DatabaseHandler):
    """
    Render the overview tab with P&L, metrics, and performance charts.
    
    Args:
        db_handler: Database handler instance
    """
    st.header("📊 Multi-Agent Trading System - Overview")
    
    # Get all closed trades
    all_trades = db_handler.get_trades(status=TradeStatus.CLOSED)
    
    # Calculate metrics
    metrics = calculate_metrics(all_trades)
    
    # Display key metrics
    render_key_metrics(metrics)
    
    # Display equity curve
    st.subheader("Equity Curve")
    render_equity_curve(all_trades)
    
    # Display performance by market
    st.subheader("Performance by Market")
    render_performance_by_market(all_trades)
    
    # Display recent trades
    st.subheader("Recent Trades")
    render_recent_trades(all_trades, limit=10)


def calculate_metrics(trades: List) -> Dict:
    """Calculate trading metrics."""
    if not trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'avg_rr': 0.0
        }
    
    winning_trades = [t for t in trades if t.is_winner]
    losing_trades = [t for t in trades if not t.is_winner and t.profit_loss is not None]
    
    total_pnl = sum(t.profit_loss for t in trades if t.profit_loss is not None)
    
    total_wins = sum(t.profit_loss for t in winning_trades if t.profit_loss is not None)
    total_losses = abs(sum(t.profit_loss for t in losing_trades if t.profit_loss is not None))
    
    avg_win = total_wins / len(winning_trades) if winning_trades else 0.0
    avg_loss = total_losses / len(losing_trades) if losing_trades else 0.0
    
    profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
    
    # Calculate max drawdown
    cumulative_pnl = 0.0
    peak = 0.0
    max_drawdown = 0.0
    
    for trade in trades:
        if trade.profit_loss is not None:
            cumulative_pnl += trade.profit_loss
            peak = max(peak, cumulative_pnl)
            drawdown = peak - cumulative_pnl
            max_drawdown = max(max_drawdown, drawdown)
    
    # Calculate average R:R
    rr_ratios = [t.risk_reward_ratio for t in trades if t.risk_reward_ratio is not None]
    avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0.0
    
    return {
        'total_trades': len(trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': len(winning_trades) / len(trades) if trades else 0.0,
        'total_pnl': total_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'avg_rr': avg_rr
    }


def render_key_metrics(metrics: Dict):
    """Render key metrics in columns."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total P&L", f"${metrics['total_pnl']:.2f}")
        st.metric("Total Trades", metrics['total_trades'])
    
    with col2:
        st.metric("Win Rate", f"{metrics['win_rate']:.1%}")
        st.metric("Winning Trades", metrics['winning_trades'])
    
    with col3:
        st.metric("Avg Win", f"${metrics['avg_win']:.2f}")
        st.metric("Avg Loss", f"${metrics['avg_loss']:.2f}")
    
    with col4:
        st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
        st.metric("Max Drawdown", f"${metrics['max_drawdown']:.2f}")


def render_equity_curve(trades: List):
    """Render equity curve chart."""
    if not trades:
        st.info("No trades to display")
        return
    
    # Sort trades by exit time
    sorted_trades = sorted(trades, key=lambda t: t.exit_time or datetime.now())
    
    # Calculate cumulative P&L
    dates = []
    cumulative_pnl = []
    running_total = 0.0
    
    for trade in sorted_trades:
        if trade.profit_loss is not None and trade.exit_time:
            running_total += trade.profit_loss
            dates.append(trade.exit_time)
            cumulative_pnl.append(running_total)
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=cumulative_pnl,
        mode='lines',
        name='Equity',
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.2)'
    ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative P&L ($)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_performance_by_market(trades: List):
    """Render performance breakdown by market type."""
    if not trades:
        st.info("No trades to display")
        return
    
    # Group by market type
    market_performance = {}
    
    for trade in trades:
        market = trade.market_type.value
        if market not in market_performance:
            market_performance[market] = {
                'trades': 0,
                'wins': 0,
                'total_pnl': 0.0
            }
        
        market_performance[market]['trades'] += 1
        if trade.is_winner:
            market_performance[market]['wins'] += 1
        if trade.profit_loss is not None:
            market_performance[market]['total_pnl'] += trade.profit_loss
    
    # Create DataFrame
    df_data = []
    for market, stats in market_performance.items():
        df_data.append({
            'Market': market.upper(),
            'Trades': stats['trades'],
            'Win Rate': f"{(stats['wins'] / stats['trades'] * 100):.1f}%" if stats['trades'] > 0 else "0%",
            'Total P&L': f"${stats['total_pnl']:.2f}"
        })
    
    df = pd.DataFrame(df_data)
    
    # Create heatmap-style display
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    with col2:
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=[d['Market'] for d in df_data],
                y=[market_performance[m.lower()]['total_pnl'] for m in [d['Market'] for d in df_data]],
                marker_color=['green' if market_performance[m.lower()]['total_pnl'] > 0 else 'red' 
                             for m in [d['Market'].lower() for d in df_data]]
            )
        ])
        
        fig.update_layout(
            xaxis_title="Market",
            yaxis_title="Total P&L ($)",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_recent_trades(trades: List, limit: int = 10):
    """Render recent trades table."""
    if not trades:
        st.info("No trades to display")
        return
    
    # Sort by exit time (most recent first)
    sorted_trades = sorted(trades, key=lambda t: t.exit_time or datetime.now(), reverse=True)[:limit]
    
    # Create DataFrame
    df_data = []
    for trade in sorted_trades:
        df_data.append({
            'Symbol': trade.symbol,
            'Direction': trade.direction.value,
            'Entry': f"${trade.entry_price:.5f}",
            'Exit': f"${trade.exit_price:.5f}" if trade.exit_price else "N/A",
            'Size': f"{trade.position_size:.2f}",
            'P&L': f"${trade.profit_loss:.2f}" if trade.profit_loss else "N/A",
            'Confidence': f"{trade.confidence:.1%}",
            'Exit Time': trade.exit_time.strftime("%Y-%m-%d %H:%M") if trade.exit_time else "N/A"
        })
    
    df = pd.DataFrame(df_data)
    
    # Style the dataframe
    st.dataframe(df, use_container_width=True, hide_index=True)
