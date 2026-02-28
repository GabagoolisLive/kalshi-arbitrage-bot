"""Unit tests for FeeCalculator."""
import pytest

from src.cost_calculator import FeeCalculator


class TestFeeCalculator:
    """Tests for fee rate and fee calculation."""

    def test_get_fee_rate_at_50_cents_taker(self):
        """Near 50¢ has highest fee (~3.5%) for taker."""
        assert FeeCalculator.get_fee_rate(50, is_maker=False) == 0.035

    def test_get_fee_rate_at_50_cents_maker(self):
        """Maker gets 50% discount."""
        assert FeeCalculator.get_fee_rate(50, is_maker=True) == 0.035 * 0.5

    def test_get_fee_rate_extremes_low(self):
        """Very low prices have 1% fee."""
        assert FeeCalculator.get_fee_rate(2, is_maker=False) == 0.01

    def test_get_fee_rate_extremes_high(self):
        """Very high prices have 1% fee."""
        assert FeeCalculator.get_fee_rate(98, is_maker=False) == 0.01

    def test_calculate_fee_zero_quantity(self):
        """Zero quantity returns zero fee."""
        assert FeeCalculator.calculate_fee(50, 0, is_maker=False) == 0.0

    def test_calculate_fee_positive(self):
        """Fee is (price * quantity * rate) / 100."""
        # 50¢, 100 contracts, 3.5% = 50*100*0.035/100 = 1.75
        assert FeeCalculator.calculate_fee(50, 100, is_maker=False) == 1.75

    def test_calculate_net_profit_single_trade(self):
        """Net profit = gross - sum of fees."""
        gross = 10.0
        trades = [{"price": 50, "quantity": 100}]
        net = FeeCalculator.calculate_net_profit(gross, trades, all_maker=False)
        fee = FeeCalculator.calculate_fee(50, 100, is_maker=False)
        assert net == pytest.approx(gross - fee)

    def test_calculate_net_profit_multiple_trades(self):
        """Net profit with multiple trades."""
        gross = 25.0
        trades = [
            {"price": 52, "quantity": 50},
            {"price": 50, "quantity": 50},
        ]
        net = FeeCalculator.calculate_net_profit(gross, trades, all_maker=True)
        total_fees = (
            FeeCalculator.calculate_fee(52, 50, is_maker=True)
            + FeeCalculator.calculate_fee(50, 50, is_maker=True)
        )
        assert net == pytest.approx(gross - total_fees)
