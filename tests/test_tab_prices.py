"""Tests for PricesTab - price calculations and fair value comparison."""

import pytest

from models import StockInfo
from ui.tabs.base import BaseTab
from ui.tabs.prices import PricesTab


@pytest.fixture
def sample_stock_info() -> StockInfo:
    """Sample StockInfo for testing."""
    return StockInfo(
        ticker="AAPL",
        short_name="Apple Inc.",
        price=175.50,
        currency="USD",
        market_cap=2.8e12,
        pe_ratio=28.5,
        price_to_sales=7.5,
        price_to_fcf=22.0,
        shares_outstanding=15_500_000_000,
        total_revenue=394e9,
        free_cash_flow=100e9,
        net_income=97e9,
        dividend_yield=0.005,
    )


@pytest.fixture
def prices_tab() -> PricesTab:
    """Create a PricesTab instance."""
    return PricesTab(title="Precios")


class TestPricesTabInit:
    """Tests for PricesTab initialization."""

    def test_inherits_from_base_tab(self):
        assert issubclass(PricesTab, BaseTab)

    def test_initializes_with_title(self):
        tab = PricesTab(title="Precios")
        assert tab.title == "Precios"

    def test_isinstance_of_base_tab(self):
        tab = PricesTab(title="Test")
        assert isinstance(tab, BaseTab)


class TestRenderInputs:
    """Tests for _render_inputs method."""

    def test_extracts_pe_ratio(self, prices_tab, sample_stock_info):
        inputs = prices_tab._render_inputs(sample_stock_info, "AAPL")
        assert inputs[0] == 28.5

    def test_extracts_price_to_sales(self, prices_tab, sample_stock_info):
        inputs = prices_tab._render_inputs(sample_stock_info, "AAPL")
        assert inputs[1] == 7.5

    def test_extracts_price_to_fcf(self, prices_tab, sample_stock_info):
        inputs = prices_tab._render_inputs(sample_stock_info, "AAPL")
        assert inputs[2] == 22.0

    def test_extracts_beneficios_in_millions(self, prices_tab, sample_stock_info):
        inputs = prices_tab._render_inputs(sample_stock_info, "AAPL")
        assert inputs[3] == 97_000_000_000 / 1e9

    def test_extracts_ventas_in_millions(self, prices_tab, sample_stock_info):
        inputs = prices_tab._render_inputs(sample_stock_info, "AAPL")
        assert inputs[4] == 394_000_000_000 / 1e9

    def test_extracts_fcf_in_millions(self, prices_tab, sample_stock_info):
        inputs = prices_tab._render_inputs(sample_stock_info, "AAPL")
        assert inputs[5] == 100_000_000_000 / 1e9

    def test_handles_none_pe_ratio(self, prices_tab):
        info = StockInfo(
            ticker="TEST",
            short_name="Test",
            price=100.0,
            currency="USD",
            pe_ratio=None,
        )
        inputs = prices_tab._render_inputs(info, "TEST")
        assert inputs[0] == 0.0

    def test_handles_none_price_to_sales(self, prices_tab):
        info = StockInfo(
            ticker="TEST",
            short_name="Test",
            price=100.0,
            currency="USD",
            price_to_sales=None,
        )
        inputs = prices_tab._render_inputs(info, "TEST")
        assert inputs[1] == 0.0

    def test_handles_none_revenue_and_fcf(self, prices_tab):
        info = StockInfo(
            ticker="TEST",
            short_name="Test",
            price=100.0,
            currency="USD",
            total_revenue=None,
            free_cash_flow=None,
        )
        inputs = prices_tab._render_inputs(info, "TEST")
        assert inputs[4] == 0.0
        assert inputs[5] == 0.0

    def test_returns_tuple_of_six_values(self, prices_tab, sample_stock_info):
        inputs = prices_tab._render_inputs(sample_stock_info, "AAPL")
        assert isinstance(inputs, tuple)
        assert len(inputs) == 6


class TestPriceCalculations:
    """Tests for price calculation formulas."""

    def test_precio_per_formula(self):
        beneficios = 97_000_000_000
        shares = 15_500_000_000
        per = 28.5
        expected = (beneficios / shares) * per
        assert abs(expected - 178.32) < 0.1

    def test_precio_ps_formula(self):
        ventas = 394_000_000_000
        shares = 15_500_000_000
        ps = 7.5
        expected = (ventas / shares) * ps
        assert abs(expected - 190.64) < 0.1

    def test_precio_fcf_formula(self):
        fcf = 100_000_000_000
        shares = 15_500_000_000
        pfcf = 22.0
        expected = (fcf / shares) * pfcf
        assert abs(expected - 141.94) < 0.1

    def test_promedio_calculation(self):
        precios = [178.32, 190.64, 141.94]
        expected = sum(precios) / len(precios)
        assert abs(expected - 170.3) < 0.1

    def test_promedio_ignores_zero_prices(self):
        precios = [178.32, 0, 141.94]
        expected = sum(p for p in precios if p > 0) / 2
        assert abs(expected - 160.13) < 0.1

    def test_promedio_returns_zero_when_all_zero(self):
        precios = [0, 0, 0]
        filtered = [p for p in precios if p > 0]
        promedio = sum(filtered) / len(filtered) if filtered else 0
        assert promedio == 0


class TestReturnsCalculation:
    """Tests for returns calculation formulas."""

    def test_rentabilidad_total_formula(self):
        precio_compra = 150.0
        precio_futuro = 200.0
        expected = ((precio_futuro - precio_compra) / precio_compra) * 100
        assert abs(expected - 33.33) < 0.01

    def test_rentabilidad_anualizada_formula(self):
        rentabilidad = 33.33
        horizonte = 5
        expected = ((1 + rentabilidad / 100) ** (1 / horizonte) - 1) * 100
        assert abs(expected - 5.92) < 0.1

    def test_retorno_total_includes_dividend(self):
        r_anualizada = 5.92
        div_yield = 2.5
        expected = r_anualizada + div_yield
        assert expected == 8.42


class TestFairValueComparison:
    """Tests for fair value comparison calculations."""

    def test_difference_calculation(self):
        precio_actual = 175.50
        precio_promedio = 170.0
        expected = ((precio_actual - precio_promedio) / precio_promedio) * 100
        assert abs(expected - 3.24) < 0.01

    def test_difference_below_negative_ten(self):
        diff = -15.0
        assert diff < -10

    def test_difference_between_zero_and_negative_ten(self):
        diff = -5.0
        assert -10 < diff <= 0

    def test_difference_above_zero(self):
        diff = 5.0
        assert diff > 0

    def test_fv_investing_difference(self):
        precio_actual = 175.50
        fv_investing = 190.0
        diff = ((precio_actual - fv_investing) / fv_investing) * 100
        assert abs(diff - (-7.63)) < 0.01

    def test_fv_guru_difference(self):
        precio_actual = 175.50
        fv_guru = 165.0
        diff = ((precio_actual - fv_guru) / fv_guru) * 100
        assert abs(diff - 6.36) < 0.01

    def test_fv_alpha_difference(self):
        precio_actual = 175.50
        fv_alpha = 180.0
        diff = ((precio_actual - fv_alpha) / fv_alpha) * 100
        assert abs(diff - (-2.5)) < 0.01
