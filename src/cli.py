"""
Interactive CLI and menu for Kalshi Arbitrage Bot.
"""
from typing import Callable, Optional

from src.bot import KalshiArbitrageBot


def get_user_input(
    prompt: str,
    default: str = "",
    validator: Optional[Callable[[str], bool]] = None,
) -> str:
    """Get user input with optional validation."""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()

        if validator:
            try:
                if validator(user_input):
                    return user_input
                print("Invalid input. Please try again.")
            except Exception as e:
                print(f"Error: {e}")
        else:
            return user_input


def _get_yes_no_input(prompt: str, default: str = "n") -> bool:
    """Get yes/no input and convert to boolean."""
    response = get_user_input(
        prompt, default, lambda x: x.lower() in ("y", "n", "yes", "no")
    )
    return response.lower() in ("y", "yes")


def handle_single_scan(bot: KalshiArbitrageBot) -> None:
    """Handle single scan with all opportunities."""
    print("\n" + "=" * 70)
    print("  Single Scan Configuration")
    print("=" * 70 + "\n")

    limit = int(
        get_user_input("Number of markets to scan", "100", lambda x: x.isdigit() and int(x) > 0)
    )
    display_all = _get_yes_no_input("Display all opportunities? (y/n)", "n")
    auto_execute = _get_yes_no_input(
        "⚠️  Enable automatic trade execution? (y/n) - USE WITH CAUTION", "n"
    )

    if auto_execute and not bot.trade_executor.auto_execute:
        bot = KalshiArbitrageBot(auto_execute_trades=True)

    print(f"\n{'='*70}")
    print(f"Starting scan of {limit} markets...")
    print(f"{'='*70}\n")

    bot.run_scan(limit=limit, display_all=display_all, auto_execute=auto_execute)


def handle_trades_only_scan(bot: KalshiArbitrageBot) -> None:
    """Handle spread trading opportunities scan."""
    print("\n" + "=" * 70)
    print("  Spread Trading Scan Configuration")
    print("=" * 70 + "\n")

    limit = int(
        get_user_input("Number of markets to scan", "100", lambda x: x.isdigit() and int(x) > 0)
    )
    display_all = _get_yes_no_input("Display all opportunities? (y/n)", "n")
    auto_execute = _get_yes_no_input(
        "⚠️  Enable automatic trade execution? (y/n) - USE WITH CAUTION", "n"
    )

    if auto_execute and not bot.trade_executor.auto_execute:
        bot = KalshiArbitrageBot(auto_execute_trades=True)

    print(f"\n{'='*70}")
    print("Scanning for spread trading opportunities...")
    print(f"{'='*70}\n")

    opportunities = bot.scan_immediate_trades(limit=limit, auto_execute=auto_execute)
    if opportunities:
        display_count = len(opportunities) if display_all else min(10, len(opportunities))
        for i, opp in enumerate(opportunities[:display_count], 1):
            bot.display_trade_opportunity(opp, index=i)
        if len(opportunities) > display_count:
            print(f"\n... and {len(opportunities) - display_count} more opportunities.")
    else:
        print("\nNo spread trading opportunities found.")


def handle_arbitrage_only_scan(bot: KalshiArbitrageBot) -> None:
    """Handle probability arbitrage opportunities scan."""
    print("\n" + "=" * 70)
    print("  Probability Arbitrage Scan Configuration")
    print("=" * 70 + "\n")

    limit = int(
        get_user_input("Number of markets to scan", "100", lambda x: x.isdigit() and int(x) > 0)
    )
    display_all = _get_yes_no_input("Display all opportunities? (y/n)", "n")

    print(f"\n{'='*70}")
    print("Scanning for probability arbitrage opportunities...")
    print(f"{'='*70}\n")

    opportunities = bot.scan_arbitrage_opportunities(limit=limit)
    if opportunities:
        display_count = len(opportunities) if display_all else min(10, len(opportunities))
        for i, opp in enumerate(opportunities[:display_count], 1):
            bot.display_arbitrage_opportunity(opp, index=i)
        if len(opportunities) > display_count:
            print(f"\n... and {len(opportunities) - display_count} more opportunities.")
    else:
        print("\nNo probability arbitrage opportunities found.")


def handle_continuous_monitoring(bot: KalshiArbitrageBot) -> None:
    """Handle continuous monitoring mode."""
    print("\n" + "=" * 70)
    print("  Continuous Monitoring Configuration")
    print("=" * 70 + "\n")

    interval = int(
        get_user_input("Scan interval in seconds", "300", lambda x: x.isdigit() and int(x) > 0)
    )
    limit = int(
        get_user_input(
            "Number of markets to scan per iteration", "100", lambda x: x.isdigit() and int(x) > 0
        )
    )
    auto_execute = _get_yes_no_input(
        "⚠️  Enable automatic trade execution? (y/n) - USE WITH CAUTION", "n"
    )
    max_scans_input = get_user_input(
        "Maximum number of scans (press Enter for unlimited)",
        "",
        lambda x: x == "" or (x.isdigit() and int(x) > 0),
    )
    max_scans = int(max_scans_input) if max_scans_input else None

    if auto_execute and not bot.trade_executor.auto_execute:
        bot = KalshiArbitrageBot(auto_execute_trades=True)

    bot.run_continuous(
        scan_interval=interval,
        limit=limit,
        auto_execute=auto_execute,
        max_scans=max_scans,
    )


def handle_configure_settings(bot: KalshiArbitrageBot) -> None:
    """Handle settings configuration."""
    print("\n" + "=" * 70)
    print("  Bot Settings Configuration")
    print("=" * 70 + "\n")

    current_min_liquidity = bot.min_liquidity / 100  # cents to dollars
    min_liquidity_input = get_user_input(
        f"Minimum liquidity in dollars (current: ${current_min_liquidity:.2f})",
        str(current_min_liquidity),
        lambda x: x.replace(".", "").replace("-", "").isdigit() and float(x) > 0,
    )
    min_liquidity_dollars = float(min_liquidity_input)
    bot.min_liquidity = int(min_liquidity_dollars * 100)

    print("\n✅ Settings updated:")
    print(f"   Minimum liquidity: ${min_liquidity_dollars:.2f}")
    print("\nPress Enter to return to main menu...")
    input()
    show_interactive_menu()


def show_interactive_menu() -> None:
    """Display interactive menu and handle user selections."""
    try:
        import inquirer
    except ImportError:
        show_simple_menu()
        return

    print("\n" + "=" * 70)
    print("  KALSHI ARBITRAGE TRADING BOT - Interactive Menu")
    print("=" * 70 + "\n")

    menu_options = [
        "📊 Single Scan (All Opportunities)",
        "📈 Scan Spread Trading Opportunities Only",
        "🎯 Scan Probability Arbitrage Opportunities Only",
        "🔄 Continuous Monitoring Mode",
        "⚙️  Configure Settings",
        "❌ Exit",
    ]
    questions = [
        inquirer.List(
            "action",
            message="Select an option (Use ↑↓ arrows, Enter to select)",
            choices=menu_options,
        )
    ]

    try:
        answers = inquirer.prompt(questions)
    except (KeyboardInterrupt, EOFError, Exception):
        show_simple_menu()
        return

    if not answers:
        print("\nOperation cancelled.")
        return

    action = answers["action"]
    bot = KalshiArbitrageBot(auto_execute_trades=False)

    if action == "📊 Single Scan (All Opportunities)":
        handle_single_scan(bot)
    elif action == "📈 Scan Spread Trading Opportunities Only":
        handle_trades_only_scan(bot)
    elif action == "🎯 Scan Probability Arbitrage Opportunities Only":
        handle_arbitrage_only_scan(bot)
    elif action == "🔄 Continuous Monitoring Mode":
        handle_continuous_monitoring(bot)
    elif action == "⚙️  Configure Settings":
        handle_configure_settings(bot)
    elif action == "❌ Exit":
        print("\nGoodbye! 👋")


def show_simple_menu() -> None:
    """Fallback simple menu when inquirer is not available."""
    print("\n" + "=" * 70)
    print("  KALSHI ARBITRAGE TRADING BOT - Menu")
    print("=" * 70 + "\n")

    menu_options = [
        "Single Scan (All Opportunities)",
        "Scan Spread Trading Opportunities Only",
        "Scan Probability Arbitrage Opportunities Only",
        "Continuous Monitoring Mode",
        "Configure Settings",
        "Exit",
    ]
    print("Available options:")
    for i, option in enumerate(menu_options, 1):
        print(f"  {i}. {option}")

    try:
        choice = input("\nEnter your choice (1-6): ").strip()
        choice_num = int(choice)
    except (ValueError, KeyboardInterrupt):
        print("\nOperation cancelled.")
        return

    if not (1 <= choice_num <= 6):
        print("Invalid choice. Please select 1-6.")
        return

    bot = KalshiArbitrageBot(auto_execute_trades=False)
    if choice_num == 1:
        handle_single_scan(bot)
    elif choice_num == 2:
        handle_trades_only_scan(bot)
    elif choice_num == 3:
        handle_arbitrage_only_scan(bot)
    elif choice_num == 4:
        handle_continuous_monitoring(bot)
    elif choice_num == 5:
        handle_configure_settings(bot)
    elif choice_num == 6:
        print("\nGoodbye! 👋")
