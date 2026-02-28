"""
Kalshi Arbitrage Bot - Source Package

Core modules: API client, opportunity analysis, execution engine, fee calculation, config, CLI.
"""

from src.cost_calculator import FeeCalculator
from src.execution_engine import TradeExecutor, TradeOpportunity
from src.market_api import KalshiClient
from src.opportunity_analyzer import ArbitrageAnalyzer, ArbitrageOpportunity

__all__ = [
    "ArbitrageAnalyzer",
    "ArbitrageOpportunity",
    "FeeCalculator",
    "KalshiClient",
    "TradeExecutor",
    "TradeOpportunity",
]

