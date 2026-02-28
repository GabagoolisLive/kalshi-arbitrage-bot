"""
Configuration module for Kalshi Arbitrage Bot.

Centralizes environment variable loading and exposes typed settings
with sensible defaults.
"""
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _int_env(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def get_api_key() -> Optional[str]:
    """Kalshi API key ID."""
    return os.getenv("KALSHI_API_KEY")


def get_api_secret() -> Optional[str]:
    """Kalshi API secret (private key)."""
    return os.getenv("KALSHI_API_SECRET")


def get_base_url() -> str:
    """Kalshi API base URL."""
    return os.getenv(
        "KALSHI_API_BASE_URL",
        "https://api.elections.kalshi.com/trade-api/v2",
    )


def get_min_profit_cents() -> int:
    """Minimum profit in cents per contract to execute."""
    return _int_env("MIN_PROFIT_CENTS", 2)


def get_max_position_size() -> int:
    """Maximum number of contracts per trade."""
    return _int_env("MAX_POSITION_SIZE", 1000)


def get_min_profit_per_day() -> float:
    """Minimum profit per day for arbitrage opportunities (dollars)."""
    return _float_env("MIN_PROFIT_PER_DAY", 0.1)


def get_min_liquidity() -> int:
    """Minimum liquidity in cents (e.g. 10000 = $100)."""
    return _int_env("MIN_LIQUIDITY", 10000)


def get_api_min_interval() -> float:
    """Minimum seconds between API requests."""
    return _float_env("API_MIN_INTERVAL", 0.1)


def is_placeholder(value: Optional[str], placeholder: str) -> bool:
    """Return True if value is unset or still the placeholder."""
    return not value or value.strip() == placeholder
