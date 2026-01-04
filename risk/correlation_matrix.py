"""Correlation Matrix for analyzing correlation between trading pairs."""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta

from data.market_data import MarketDataFetcher

logger = logging.getLogger(__name__)


class CorrelationMatrix:
    """Analyzes correlation between trading pairs to manage portfolio risk."""

    def __init__(self, max_correlation: float = 0.7):
        """
        Initialize Correlation Matrix.
        
        Args:
            max_correlation: Maximum allowed correlation between pairs
        """
        self.max_correlation = max_correlation
        self.market_data_fetcher = MarketDataFetcher()
        self.correlation_cache: Dict[str, pd.DataFrame] = {}
        self.cache_timestamp: Optional[datetime] = None
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        
        logger.info(f"CorrelationMatrix initialized with max correlation {max_correlation}")

    def calculate_correlation(
        self,
        symbols: List[str],
        timeframe: str = "H1",
        bars: int = 100,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for given symbols.
        
        Args:
            symbols: List of trading symbols
            timeframe: Timeframe for analysis
            bars: Number of bars to analyze
            force_refresh: Force refresh of cached data
            
        Returns:
            Correlation matrix as DataFrame
        """
        # Check cache
        cache_key = f"{'-'.join(sorted(symbols))}_{timeframe}_{bars}"
        
        if not force_refresh and cache_key in self.correlation_cache:
            if self.cache_timestamp and (datetime.now() - self.cache_timestamp) < self.cache_duration:
                logger.info("Using cached correlation matrix")
                return self.correlation_cache[cache_key]
        
        try:
            # Initialize market data fetcher if needed
            if not self.market_data_fetcher.initialized:
                self.market_data_fetcher.initialize()
            
            # Fetch price data for all symbols
            price_data = {}
            for symbol in symbols:
                df = self.market_data_fetcher.get_bars(symbol, timeframe, bars)
                if df is not None and len(df) > 0:
                    price_data[symbol] = df['close']
                else:
                    logger.warning(f"No data available for {symbol}")
            
            if not price_data:
                logger.error("No price data available for correlation calculation")
                return pd.DataFrame()
            
            # Create combined DataFrame
            combined_df = pd.DataFrame(price_data)
            
            # Calculate correlation
            correlation_matrix = combined_df.corr()
            
            # Cache the result
            self.correlation_cache[cache_key] = correlation_matrix
            self.cache_timestamp = datetime.now()
            
            logger.info(f"Correlation matrix calculated for {len(symbols)} symbols")
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return pd.DataFrame()

    def check_correlation(
        self,
        symbol1: str,
        symbol2: str,
        timeframe: str = "H1",
        bars: int = 100
    ) -> float:
        """
        Check correlation between two symbols.
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            timeframe: Timeframe for analysis
            bars: Number of bars to analyze
            
        Returns:
            Correlation coefficient (-1.0 to 1.0)
        """
        try:
            correlation_matrix = self.calculate_correlation([symbol1, symbol2], timeframe, bars)
            
            if correlation_matrix.empty:
                return 0.0
            
            correlation = correlation_matrix.loc[symbol1, symbol2]
            return correlation
            
        except Exception as e:
            logger.error(f"Error checking correlation between {symbol1} and {symbol2}: {e}")
            return 0.0

    def validate_new_position(
        self,
        new_symbol: str,
        open_symbols: List[str],
        timeframe: str = "H1",
        bars: int = 100
    ) -> Dict:
        """
        Validate if new position has acceptable correlation with open positions.
        
        Args:
            new_symbol: Symbol for new position
            open_symbols: List of symbols with open positions
            timeframe: Timeframe for analysis
            bars: Number of bars to analyze
            
        Returns:
            Dictionary with validation result
        """
        if not open_symbols:
            return {
                'is_valid': True,
                'message': 'No open positions to check correlation',
                'correlations': {}
            }
        
        try:
            # Calculate correlation with each open position
            correlations = {}
            violations = []
            
            for open_symbol in open_symbols:
                if open_symbol == new_symbol:
                    continue
                
                correlation = self.check_correlation(new_symbol, open_symbol, timeframe, bars)
                correlations[open_symbol] = correlation
                
                # Check if correlation exceeds threshold
                if abs(correlation) > self.max_correlation:
                    violations.append(
                        f"High correlation with {open_symbol}: {correlation:.2f}"
                    )
            
            is_valid = len(violations) == 0
            
            return {
                'is_valid': is_valid,
                'message': ' | '.join(violations) if violations else 'Correlation acceptable',
                'correlations': correlations,
                'max_correlation': max(abs(c) for c in correlations.values()) if correlations else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error validating new position: {e}")
            return {
                'is_valid': True,  # Default to allow if error
                'message': f'Error checking correlation: {str(e)}',
                'correlations': {}
            }

    def get_highly_correlated_pairs(
        self,
        symbols: List[str],
        threshold: float = 0.7,
        timeframe: str = "H1",
        bars: int = 100
    ) -> List[Dict]:
        """
        Get pairs with high correlation.
        
        Args:
            symbols: List of symbols to analyze
            threshold: Correlation threshold
            timeframe: Timeframe for analysis
            bars: Number of bars to analyze
            
        Returns:
            List of highly correlated pairs
        """
        try:
            correlation_matrix = self.calculate_correlation(symbols, timeframe, bars)
            
            if correlation_matrix.empty:
                return []
            
            highly_correlated = []
            
            # Iterate through upper triangle of correlation matrix
            for i in range(len(symbols)):
                for j in range(i + 1, len(symbols)):
                    symbol1 = symbols[i]
                    symbol2 = symbols[j]
                    correlation = correlation_matrix.loc[symbol1, symbol2]
                    
                    if abs(correlation) >= threshold:
                        highly_correlated.append({
                            'symbol1': symbol1,
                            'symbol2': symbol2,
                            'correlation': correlation,
                            'type': 'positive' if correlation > 0 else 'negative'
                        })
            
            # Sort by absolute correlation
            highly_correlated.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            return highly_correlated
            
        except Exception as e:
            logger.error(f"Error getting highly correlated pairs: {e}")
            return []

    def get_diversification_score(
        self,
        symbols: List[str],
        timeframe: str = "H1",
        bars: int = 100
    ) -> float:
        """
        Calculate portfolio diversification score.
        
        Args:
            symbols: List of symbols in portfolio
            timeframe: Timeframe for analysis
            bars: Number of bars to analyze
            
        Returns:
            Diversification score (0.0 to 1.0, higher is better)
        """
        try:
            if len(symbols) < 2:
                return 1.0  # Single asset is fully "diversified" in this context
            
            correlation_matrix = self.calculate_correlation(symbols, timeframe, bars)
            
            if correlation_matrix.empty:
                return 0.5  # Default neutral score
            
            # Calculate average absolute correlation
            # Lower average correlation = better diversification
            total_correlation = 0.0
            count = 0
            
            for i in range(len(symbols)):
                for j in range(i + 1, len(symbols)):
                    correlation = abs(correlation_matrix.iloc[i, j])
                    total_correlation += correlation
                    count += 1
            
            avg_correlation = total_correlation / count if count > 0 else 0.0
            
            # Convert to diversification score (inverse of correlation)
            diversification_score = 1.0 - avg_correlation
            
            return max(0.0, min(1.0, diversification_score))
            
        except Exception as e:
            logger.error(f"Error calculating diversification score: {e}")
            return 0.5

    def clear_cache(self) -> None:
        """Clear correlation cache."""
        self.correlation_cache.clear()
        self.cache_timestamp = None
        logger.info("Correlation cache cleared")
