"""
Kalshi Arbitrage Bot – main orchestrator.

Coordinates market scanning, opportunity analysis, and trade execution.
"""
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

from src.config import (
    get_max_position_size,
    get_min_liquidity,
    get_min_profit_cents,
    get_min_profit_per_day,
)
from src.execution_engine import TradeExecutor, TradeOpportunity
from src.market_api import KalshiClient
from src.opportunity_analyzer import ArbitrageAnalyzer, ArbitrageOpportunity

logger = logging.getLogger(__name__)


class KalshiArbitrageBot:
    """
    Main trading bot orchestrator for identifying and executing arbitrage opportunities.

    Coordinates market scanning, opportunity analysis, and trade execution
    across multiple market types. It intelligently filters markets by liquidity,
    calculates net profitability after fees, and provides comprehensive reporting
    on discovered opportunities.

    The bot identifies two primary opportunity types:
    - Probability Arbitrage: Market inefficiencies where contract probabilities
      deviate from expected 100% total, creating guaranteed profit scenarios.
    - Spread Trading: Orderbook imbalances where immediate buy-sell execution
      generates instant profit with minimal risk exposure.
    """

    def __init__(self, auto_execute_trades: bool = False):
        """
        Initialize the bot.

        Args:
            auto_execute_trades: If True, automatically execute profitable trades
        """
        self.client = KalshiClient()
        self.arbitrage_analyzer = ArbitrageAnalyzer()
        self.trade_executor = TradeExecutor(
            client=self.client,
            min_profit_cents=get_min_profit_cents(),
            max_position_size=get_max_position_size(),
            auto_execute=auto_execute_trades,
        )
        self.min_profit_per_day = get_min_profit_per_day()
        self.min_liquidity = get_min_liquidity()

    def filter_markets_by_liquidity(self, markets: List[Dict]) -> List[Dict]:
        """
        Filter markets to only include those with sufficient liquidity.

        Only includes markets that have:
        - Liquidity >= minimum threshold
        - Both bid and ask prices available (tradeable)
        """
        return [
            market
            for market in markets
            if market.get("liquidity", 0) >= self.min_liquidity
            and self._has_tradeable_liquidity(market)
        ]

    def _has_tradeable_liquidity(self, market: Dict) -> bool:
        """Check if market has tradeable bid/ask prices."""
        yes_bid = market.get("yes_bid")
        yes_ask = market.get("yes_ask")
        no_bid = market.get("no_bid")
        no_ask = market.get("no_ask")
        has_yes = yes_bid is not None and yes_ask is not None and yes_bid != yes_ask
        has_no = no_bid is not None and no_ask is not None and no_bid != no_ask
        return has_yes or has_no

    def _fetch_and_filter_markets(self, limit: int) -> List[Dict]:
        """Fetch and filter markets – shared logic to avoid duplication."""
        markets = self.client.get_markets(limit=limit, status="open")
        if not markets:
            return []
        original_count = len(markets)
        filtered = self.filter_markets_by_liquidity(markets)
        if filtered:
            logger.info(
                "Found %d active markets. Filtered to %d with liquidity >= $%.2f",
                original_count,
                len(filtered),
                self.min_liquidity / 100,
            )
        return filtered

    def scan_arbitrage_opportunities(self, limit: int = 100) -> List[ArbitrageOpportunity]:
        """Scan active markets for probability arbitrage opportunities."""
        logger.info("Scanning %d markets for arbitrage opportunities...", limit)
        markets = self._fetch_and_filter_markets(limit)
        if not markets:
            logger.warning("No markets found or API error.")
            return []
        opportunities = self.arbitrage_analyzer.find_opportunities(
            markets, client=self.client
        )
        return [o for o in opportunities if o.profit_per_day >= self.min_profit_per_day]

    def scan_immediate_trades(
        self, limit: int = 100, auto_execute: bool = False
    ) -> List[TradeOpportunity]:
        """Scan markets for immediate spread trading opportunities."""
        logger.info("Scanning %d markets for immediate trade opportunities...", limit)
        markets = self._fetch_and_filter_markets(limit)
        if not markets:
            logger.warning("No markets found or API error.")
            return []
        original_auto = self.trade_executor.auto_execute
        self.trade_executor.auto_execute = auto_execute
        try:
            opportunities = self.trade_executor.scan_and_execute(markets, limit=limit)
            opportunities.sort(key=lambda x: x.net_profit, reverse=True)
            return opportunities
        finally:
            self.trade_executor.auto_execute = original_auto

    def scan_all_opportunities(
        self, limit: int = 100, auto_execute: bool = False
    ) -> tuple:
        """
        Comprehensive market scan for all trading opportunities.

        Returns:
            Tuple of (arbitrage_opportunities, trade_opportunities, executed_count).
        """
        logger.info("Scanning %d markets for all opportunities...", limit)
        markets = self._fetch_and_filter_markets(limit)
        if not markets:
            logger.warning("No markets found or API error.")
            return [], [], 0

        arbitrage_opps = self.arbitrage_analyzer.find_opportunities(
            markets, client=self.client
        )
        arbitrage_opps = [
            o for o in arbitrage_opps if o.profit_per_day >= self.min_profit_per_day
        ]

        original_auto = self.trade_executor.auto_execute
        self.trade_executor.auto_execute = False
        try:
            trade_opps = self.trade_executor.scan_and_execute(markets, limit=limit)
            trade_opps.sort(key=lambda x: x.net_profit, reverse=True)
        finally:
            self.trade_executor.auto_execute = original_auto

        executed_count = 0
        if auto_execute and trade_opps:
            profitable = [o for o in trade_opps if o.net_profit > 0]
            for trade_opp in profitable:
                success, message = self.trade_executor.execute_trade(trade_opp)
                if success:
                    logger.info("AUTO-EXECUTE: %s", message)
                    executed_count += 1

        return arbitrage_opps, trade_opps, executed_count

    def display_arbitrage_opportunity(
        self, opp: ArbitrageOpportunity, index: Optional[int] = None
    ) -> None:
        """Print formatted details of a probability arbitrage opportunity."""
        prefix = f"[{index}] " if index is not None else ""
        lines = [
            f"\n{prefix}{'='*60}",
            f"Market: {opp.market_title}",
            f"Ticker: {opp.market_ticker}",
            f"Total Probability: {opp.total_probability:.2f}%",
            f"Deviation from 100%: {opp.deviation:.2f}%",
            f"Expiration: {opp.expiration_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Days to Expiration: {opp.days_to_expiration:.2f}",
            "\nProfit Analysis:",
            f"  Gross Profit: ${opp.gross_profit:.2f}",
            f"  Net Profit (after fees): ${opp.net_profit:.2f}",
            f"  Profit per Day: ${opp.profit_per_day:.2f}",
            "\nRecommended Trades:",
        ]
        for i, trade in enumerate(opp.trades, 1):
            lines.append(
                f"  {i}. {trade['action'].upper()} {trade['quantity']} contracts "
                f"of {trade['ticker']} at {trade['price']}¢ (side: {trade['side']})"
            )
        lines.append(f"{'='*60}\n")
        print("\n".join(lines))

    def display_trade_opportunity(
        self, opp: TradeOpportunity, index: Optional[int] = None
    ) -> None:
        """Print formatted details of a spread trading opportunity."""
        prefix = f"[{index}] " if index is not None else ""
        profit_per_contract = opp.net_profit / opp.quantity if opp.quantity else 0
        lines = [
            f"\n{prefix}{'='*60}",
            f"Market: {opp.market_title}",
            f"Ticker: {opp.market_ticker}",
            f"Side: {opp.side.upper()}",
            f"Buy Price: {opp.buy_price}¢",
            f"Sell Price: {opp.sell_price}¢",
            f"Spread: {opp.spread}¢",
            f"Quantity: {opp.quantity} contracts",
            "\nProfit Analysis:",
            f"  Gross Profit: ${opp.gross_profit:.2f}",
            f"  Net Profit (after fees): ${opp.net_profit:.2f}",
            f"  Profit per Contract: ${profit_per_contract:.4f}",
            f"{'='*60}\n",
        ]
        print("\n".join(lines))

    def run_scan(
        self,
        limit: int = 100,
        display_all: bool = False,
        auto_execute: bool = False,
    ) -> None:
        """Execute a single comprehensive market scan and display results."""
        arbitrage_opps, trade_opps, executed_count = self.scan_all_opportunities(
            limit=limit, auto_execute=auto_execute
        )

        if not arbitrage_opps and not trade_opps:
            print("\nNo profitable opportunities found that meet the current criteria.")
            if executed_count > 0:
                print(f"Successfully executed {executed_count} trades automatically.")
            return

        if trade_opps:
            print(f"\n{'='*70}")
            print(f"SPREAD TRADING OPPORTUNITIES: Found {len(trade_opps)} profitable opportunities!")
            print(f"{'='*70}\n")
            display_count = len(trade_opps) if display_all else min(10, len(trade_opps))
            for i, opp in enumerate(trade_opps[:display_count], 1):
                self.display_trade_opportunity(opp, index=i)
            if len(trade_opps) > display_count:
                print(f"\n... and {len(trade_opps) - display_count} more spread trading opportunities.")

        if arbitrage_opps:
            print(f"\n{'='*70}")
            print(f"PROBABILITY ARBITRAGE OPPORTUNITIES: Found {len(arbitrage_opps)} profitable opportunities!")
            print(f"{'='*70}\n")
            display_count = len(arbitrage_opps) if display_all else min(10, len(arbitrage_opps))
            for i, opp in enumerate(arbitrage_opps[:display_count], 1):
                self.display_arbitrage_opportunity(opp, index=i)
            if len(arbitrage_opps) > display_count:
                print(f"\n... and {len(arbitrage_opps) - display_count} more arbitrage opportunities.")

        if trade_opps and arbitrage_opps:
            print(f"\n{'='*70}")
            print("COMPARISON:")
            print(f"{'='*70}")
            best_trade = trade_opps[0]
            best_arb = arbitrage_opps[0]
            print(f"Spread Trading: ${best_trade.net_profit:.2f} profit (instant execution)")
            print(f"Probability Arbitrage: ${best_arb.profit_per_day:.2f}/day (over {best_arb.days_to_expiration:.1f} days)")
            arb_total = best_arb.profit_per_day * best_arb.days_to_expiration
            if best_trade.net_profit > arb_total:
                print("\n→ RECOMMENDATION: Spread trading opportunity offers higher immediate profit!")
            elif best_arb.profit_per_day > 0:
                print("\n→ RECOMMENDATION: Probability arbitrage may provide better long-term returns!")

        if executed_count > 0:
            print(f"\n[AUTO-EXECUTE] Executed {executed_count} trades automatically.")

    def run_continuous(
        self,
        scan_interval: int = 300,
        limit: int = 100,
        auto_execute: bool = False,
        max_scans: Optional[int] = None,
    ) -> None:
        """Run continuous market monitoring mode."""
        print(f"Starting continuous market monitoring (scan interval: {scan_interval} seconds)...")
        if auto_execute:
            print("⚠️  WARNING: Auto-execute mode enabled - trades will be executed automatically!")
        if max_scans:
            print(f"Maximum scan iterations: {max_scans}")
        print("Press Ctrl+C to stop monitoring.\n")

        scan_count = 0
        try:
            while True:
                scan_count += 1
                if max_scans and scan_count > max_scans:
                    print(f"\nReached maximum scan count ({max_scans}). Stopping.")
                    break
                arbitrage_opps, trade_opps, _ = self.scan_all_opportunities(
                    limit=limit, auto_execute=auto_execute
                )
                total = len(arbitrage_opps) + len(trade_opps)
                if total > 0:
                    print(f"\n✅ Found {total} profitable opportunities!")
                    print(f"  • {len(trade_opps)} spread trading opportunities")
                    print(f"  • {len(arbitrage_opps)} probability arbitrage opportunities")
                else:
                    print(f"\nNo profitable opportunities found (scan #{scan_count})")
                print(f"\nWaiting {scan_interval} seconds until next scan...\n")
                time.sleep(scan_interval)
        except KeyboardInterrupt:
            print("\n\nScanning stopped by user.")
