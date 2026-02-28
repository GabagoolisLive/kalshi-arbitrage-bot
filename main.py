#!/usr/bin/env python3
"""
Kalshi Arbitrage Trading Bot

An intelligent trading system designed to identify and capitalize on arbitrage opportunities
in Kalshi prediction markets. The bot continuously monitors market conditions and identifies
two distinct types of profitable trading opportunities:

1. Probability Arbitrage: Markets where YES and NO contract probabilities don't sum to 100%,
   creating risk-free profit opportunities when properly executed.

2. Spread Trading: Orderbook inefficiencies where bid prices exceed ask prices, enabling
   instant profit through simultaneous buy and sell execution.

The system includes comprehensive fee calculations, risk management, and automated execution
capabilities to maximize profitability while maintaining safe trading practices.

Author: vladmeer
License: MIT
Repository: https://github.com/GabagoolisLive/kalshi-arbitrage-bot
"""
import logging
import sys

from dotenv import load_dotenv

from src.cli import show_interactive_menu

load_dotenv()

# Configure logging: INFO to console so users see scan progress
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)


def main() -> None:
    """Entry point: launch the interactive menu."""
    show_interactive_menu()


if __name__ == "__main__":
    main()
