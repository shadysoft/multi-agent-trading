"""Main Streamlit Dashboard Application."""

import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.database import DatabaseHandler
from risk.risk_manager import RiskManager
from dashboard.components.overview import render_overview
from dashboard.components.market_tabs import render_market_tabs
from dashboard.components.alerts import render_alerts


def run_dashboard():
    """Run the Streamlit dashboard."""
    # Page configuration
    st.set_page_config(
        page_title="Multi-Agent Trading System",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding-top: 2rem;
        }
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize components
    db_handler = DatabaseHandler()
    
    # Try to initialize risk manager with default account balance
    try:
        risk_manager = RiskManager(account_balance=10000.0)
    except Exception:
        risk_manager = None
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 Multi-Agent Trading")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigate to:",
            ["Overview", "Markets", "Alerts", "Settings"],
            index=0
        )
        
        st.markdown("---")
        
        # System Status
        st.subheader("System Status")
        
        # Get metrics
        if risk_manager:
            metrics = risk_manager.get_risk_metrics()
            
            st.metric("Account Balance", f"${metrics.get('account_balance', 0):.2f}")
            st.metric("Open Trades", metrics.get('open_trades', 0))
            st.metric("Total Trades", metrics.get('total_trades', 0))
            st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1%}")
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        # Info
        st.markdown("---")
        st.caption("Multi-Agent AI Trading System")
        st.caption("Version 0.1.0")
    
    # Main content based on selected page
    if page == "Overview":
        render_overview(db_handler)
    
    elif page == "Markets":
        render_market_tabs(db_handler)
    
    elif page == "Alerts":
        render_alerts(db_handler, risk_manager)
    
    elif page == "Settings":
        render_settings(risk_manager)


def render_settings(risk_manager):
    """Render settings page."""
    st.header("⚙️ Settings")
    
    st.subheader("Risk Management")
    
    if risk_manager:
        col1, col2 = st.columns(2)
        
        with col1:
            st.number_input(
                "Max Daily Loss (%)",
                min_value=0.0,
                max_value=10.0,
                value=risk_manager.max_daily_loss_percent,
                step=0.1,
                help="Maximum daily loss percentage"
            )
            
            st.number_input(
                "Max Position Size (%)",
                min_value=0.0,
                max_value=5.0,
                value=risk_manager.max_position_size_percent,
                step=0.1,
                help="Maximum position size as percentage of account"
            )
        
        with col2:
            st.number_input(
                "Max Concurrent Trades",
                min_value=1,
                max_value=20,
                value=risk_manager.max_concurrent_trades,
                step=1,
                help="Maximum number of concurrent open trades"
            )
            
            st.number_input(
                "Max Drawdown (%)",
                min_value=0.0,
                max_value=50.0,
                value=risk_manager.max_drawdown_percent,
                step=1.0,
                help="Maximum drawdown percentage before stopping"
            )
    
    st.markdown("---")
    
    st.subheader("Agent Weights")
    st.info("Agent weights can be adjusted by the Learning Agent based on performance")
    
    # Would display agent weights here from database
    st.text("Agent weights are managed automatically by the Learning Agent")
    
    st.markdown("---")
    
    st.subheader("Trading Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("Enable Live Trading", value=False, help="Enable live trading (use with caution)")
        st.checkbox("Enable Paper Trading", value=True, help="Enable paper trading mode")
    
    with col2:
        st.checkbox("Enable Telegram Alerts", value=False, help="Send alerts via Telegram")
        st.checkbox("Enable Email Alerts", value=False, help="Send alerts via email")
    
    st.markdown("---")
    
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")


if __name__ == "__main__":
    run_dashboard()
