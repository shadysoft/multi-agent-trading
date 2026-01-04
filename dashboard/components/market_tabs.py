"""Market tabs component for individual market analysis."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict
from datetime import datetime

from data.database import DatabaseHandler
from data.models import TradeStatus, MarketType


def render_market_tabs(db_handler: DatabaseHandler):
    """
    Render individual market tabs.
    
    Args:
        db_handler: Database handler instance
    """
    st.header("📈 Market Analysis")
    
    # Create tabs for each market
    tab1, tab2, tab3, tab4 = st.tabs(["💱 Forex", "🥇 Gold", "📊 Stocks", "₿ Crypto"])
    
    with tab1:
        render_market_detail(db_handler, MarketType.FOREX, "Forex")
    
    with tab2:
        render_market_detail(db_handler, MarketType.GOLD, "Gold & Commodities")
    
    with tab3:
        render_market_detail(db_handler, MarketType.STOCKS, "Stocks")
    
    with tab4:
        render_market_detail(db_handler, MarketType.CRYPTO, "Cryptocurrency")


def render_market_detail(db_handler: DatabaseHandler, market_type: MarketType, market_name: str):
    """
    Render detail view for a specific market.
    
    Args:
        db_handler: Database handler instance
        market_type: Market type to display
        market_name: Display name for the market
    """
    st.subheader(f"{market_name} Trading")
    
    # Get trades for this market
    all_trades = db_handler.get_trades(status=TradeStatus.CLOSED)
    market_trades = [t for t in all_trades if t.market_type == market_type]
    
    if not market_trades:
        st.info(f"No trades for {market_name} yet")
        return
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_trades = len(market_trades)
    winning_trades = len([t for t in market_trades if t.is_winner])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
    total_pnl = sum(t.profit_loss for t in market_trades if t.profit_loss is not None)
    
    with col1:
        st.metric("Total Trades", total_trades)
    with col2:
        st.metric("Win Rate", f"{win_rate:.1%}")
    with col3:
        st.metric("Total P&L", f"${total_pnl:.2f}")
    with col4:
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0.0
        st.metric("Avg P&L/Trade", f"${avg_pnl:.2f}")
    
    # Display symbol breakdown
    st.subheader("Performance by Symbol")
    render_symbol_performance(market_trades)
    
    # Display agent performance
    st.subheader("Agent Signals Analysis")
    render_agent_performance(market_trades)
    
    # Display trades table
    st.subheader("All Trades")
    render_trades_table(market_trades)


def render_symbol_performance(trades: List):
    """Render performance breakdown by symbol."""
    # Group by symbol
    symbol_stats = {}
    
    for trade in trades:
        if trade.symbol not in symbol_stats:
            symbol_stats[trade.symbol] = {
                'trades': 0,
                'wins': 0,
                'total_pnl': 0.0
            }
        
        symbol_stats[trade.symbol]['trades'] += 1
        if trade.is_winner:
            symbol_stats[trade.symbol]['wins'] += 1
        if trade.profit_loss is not None:
            symbol_stats[trade.symbol]['total_pnl'] += trade.profit_loss
    
    # Create DataFrame
    df_data = []
    for symbol, stats in symbol_stats.items():
        win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0.0
        df_data.append({
            'Symbol': symbol,
            'Trades': stats['trades'],
            'Wins': stats['wins'],
            'Win Rate': f"{win_rate:.1f}%",
            'Total P&L': stats['total_pnl'],
            'Avg P&L': stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0.0
        })
    
    df = pd.DataFrame(df_data)
    df = df.sort_values('Total P&L', ascending=False)
    
    # Display table
    st.dataframe(
        df.style.format({
            'Total P&L': '${:.2f}',
            'Avg P&L': '${:.2f}'
        }).background_gradient(subset=['Total P&L'], cmap='RdYlGn'),
        use_container_width=True,
        hide_index=True
    )


def render_agent_performance(trades: List):
    """Render agent signal analysis."""
    # Analyze agent signals from trade metadata
    agent_contributions = {}
    
    for trade in trades:
        if trade.metadata and 'agent_signals' in trade.metadata:
            for signal in trade.metadata['agent_signals']:
                agent_name = signal.get('agent_name', 'Unknown')
                
                if agent_name not in agent_contributions:
                    agent_contributions[agent_name] = {
                        'count': 0,
                        'avg_confidence': [],
                        'contribution_to_wins': 0,
                        'contribution_to_losses': 0
                    }
                
                agent_contributions[agent_name]['count'] += 1
                agent_contributions[agent_name]['avg_confidence'].append(signal.get('confidence', 0.0))
                
                if trade.is_winner:
                    agent_contributions[agent_name]['contribution_to_wins'] += 1
                else:
                    agent_contributions[agent_name]['contribution_to_losses'] += 1
    
    if not agent_contributions:
        st.info("No agent signal data available")
        return
    
    # Create DataFrame
    df_data = []
    for agent, stats in agent_contributions.items():
        avg_conf = sum(stats['avg_confidence']) / len(stats['avg_confidence']) if stats['avg_confidence'] else 0.0
        df_data.append({
            'Agent': agent,
            'Signals': stats['count'],
            'Avg Confidence': f"{avg_conf:.1%}",
            'In Winning Trades': stats['contribution_to_wins'],
            'In Losing Trades': stats['contribution_to_losses']
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_trades_table(trades: List):
    """Render detailed trades table."""
    # Sort by exit time
    sorted_trades = sorted(trades, key=lambda t: t.exit_time or datetime.now(), reverse=True)
    
    # Create DataFrame
    df_data = []
    for trade in sorted_trades:
        df_data.append({
            'Symbol': trade.symbol,
            'Direction': trade.direction.value,
            'Entry Price': f"${trade.entry_price:.5f}",
            'Exit Price': f"${trade.exit_price:.5f}" if trade.exit_price else "N/A",
            'Size (lots)': f"{trade.position_size:.2f}",
            'P&L': trade.profit_loss if trade.profit_loss else 0.0,
            'Confidence': f"{trade.confidence:.1%}",
            'Entry Time': trade.entry_time.strftime("%Y-%m-%d %H:%M"),
            'Exit Time': trade.exit_time.strftime("%Y-%m-%d %H:%M") if trade.exit_time else "N/A"
        })
    
    df = pd.DataFrame(df_data)
    
    # Style the dataframe
    st.dataframe(
        df.style.format({'P&L': '${:.2f}'}).background_gradient(subset=['P&L'], cmap='RdYlGn'),
        use_container_width=True,
        hide_index=True
    )
