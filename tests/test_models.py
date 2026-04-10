"""Tests for Pydantic domain models."""

import pytest
from pydantic import ValidationError

from app.domain.models import ChartSeries, FinancialMetrics, NewsItem, StockInfo


class TestStockInfo:
    """Tests for StockInfo model."""

    def test_creates_with_required_fields(self):
        info = StockInfo(
            ticker="AAPL", short_name="Apple Inc.", price=175.50, currency="USD"
        )
        assert info.ticker == "AAPL"
        assert info.price == 175.50
        assert info.volume == 0
        assert info.sector == ""

    def test_creates_with_all_fields(self):
        info = StockInfo(
            ticker="AAPL",
            short_name="Apple Inc.",
            price=175.50,
            currency="USD",
            market_cap=2.8e12,
            pe_ratio=28.5,
            volume=45_000_000,
            week_52_low=164.00,
            week_52_high=199.00,
            sector="Technology",
            industry="Consumer Electronics",
            country="United States",
            employees=164000,
            website="https://apple.com",
            description="Apple Inc. designs, manufactures, and markets smartphones.",
            beta=1.2,
            dividend_yield=0.005,
            eps=6.13,
            target_price=210.00,
            recommendation="buy",
            shares_outstanding=15_500_000_000,
            forward_pe=24.0,
            price_to_sales=7.5,
            price_to_fcf=22.0,
            total_revenue=394e9,
            free_cash_flow=100e9,
            net_income=97e9,
        )
        assert info.market_cap == 2.8e12
        assert info.pe_ratio == 28.5
        assert info.sector == "Technology"
        assert info.dividend_yield == 0.005

    def test_optional_fields_default_to_none(self):
        info = StockInfo(ticker="AAPL", short_name="Apple", price=175.0, currency="USD")
        assert info.market_cap is None
        assert info.pe_ratio is None
        assert info.beta is None


class TestChartSeries:
    """Tests for ChartSeries model."""

    def test_creates_with_x_and_y_lists(self):
        series = ChartSeries(x=["2020", "2021", "2022"], y=[100.0, 120.0, 140.0])
        assert len(series.x) == 3
        assert len(series.y) == 3

    def test_y_can_contain_zeros(self):
        series = ChartSeries(x=["2020", "2021"], y=[0.0, 0.0])
        assert series.y == [0.0, 0.0]


class TestFinancialMetrics:
    """Tests for FinancialMetrics model."""

    def test_creates_with_defaults(self):
        metrics = FinancialMetrics()
        assert metrics.years == []
        assert metrics.revenue_billions == []
        assert metrics.net_income_billions == []
        assert metrics.sales_growth == []
        assert metrics.net_margin == []
        assert metrics.roe == []
        assert metrics.fcf_billions == []
        assert metrics.debt_billions == []
        assert metrics.debt_equity == []
        assert metrics.pe_ratio is None

    def test_creates_with_values(self):
        metrics = FinancialMetrics(
            years=["2024", "2023"],
            revenue_billions=[500.0, 450.0],
            net_income_billions=[50.0, 45.0],
            sales_growth=[0.0, 11.11],
            net_margin=[10.0, 10.0],
            roe=[25.0, 25.0],
            fcf_billions=[30.0, 25.0],
            debt_billions=[100.0, 90.0],
            debt_equity=[50.0, 50.0],
            pe_ratio=25.0,
        )
        assert len(metrics.years) == 2
        assert metrics.pe_ratio == 25.0

    def test_to_summary_chart_data_with_all_fields(self):
        metrics = FinancialMetrics(
            years=["2024", "2023"],
            revenue_billions=[500.0, 450.0],
            sales_growth=[0.0, 11.11],
            net_margin=[10.0, 10.0],
            roe=[25.0, 25.0],
            fcf_billions=[30.0, 25.0],
            debt_equity=[50.0, 50.0],
            pe_ratio=25.0,
        )
        chart_data = metrics.to_summary_chart_data()

        assert "Crecimiento Ventas" in chart_data
        assert "Margen Neto (%)" in chart_data
        assert "ROE (%)" in chart_data
        assert "FCF" in chart_data
        assert "Deuda/Equity (%)" in chart_data
        assert "PER" in chart_data

    def test_to_summary_chart_data_with_empty_fields(self):
        metrics = FinancialMetrics(years=["2024"])
        chart_data = metrics.to_summary_chart_data()
        assert chart_data == {}

    def test_to_summary_chart_data_per_includes_last_year(self):
        metrics = FinancialMetrics(
            years=["2024", "2023", "2022"],
            pe_ratio=25.0,
        )
        chart_data = metrics.to_summary_chart_data()
        assert chart_data["PER"].x == ["2022"]

    def test_yoy_deltas_with_two_years(self):
        metrics = FinancialMetrics(
            years=["2024", "2023"],
            revenue_billions=[500.0, 450.0],
            net_margin=[10.0, 9.0],
            fcf_billions=[30.0, 25.0],
            debt_equity=[50.0, 45.0],
        )
        deltas = metrics.yoy_deltas()

        assert deltas["Revenue"][0] == 500.0
        assert deltas["Revenue"][1] == 50.0
        assert deltas["Net Margin"][0] == 10.0
        assert deltas["Net Margin"][2] is True
        assert deltas["FCF"][1] == 5.0

    def test_yoy_deltas_with_single_year(self):
        metrics = FinancialMetrics(
            years=["2024"],
            revenue_billions=[500.0],
            net_margin=[10.0],
        )
        deltas = metrics.yoy_deltas()

        assert deltas["Revenue"][0] == 500.0
        assert deltas["Revenue"][1] is None
        assert deltas["Net Margin"][1] is None

    def test_yoy_deltas_handles_empty_metrics(self):
        metrics = FinancialMetrics()
        deltas = metrics.yoy_deltas()
        assert deltas == {}


class TestNewsItem:
    """Tests for NewsItem model."""

    def test_creates_with_required_fields(self):
        item = NewsItem(
            title="Apple reports earnings", link="https://example.com/news/123"
        )
        assert item.title == "Apple reports earnings"
        assert item.link == "https://example.com/news/123"
        assert item.publisher == "Fuente desconocida"
        assert item.thumbnail == ""
        assert item.published_at == ""

    def test_creates_with_all_fields(self):
        item = NewsItem(
            title="Apple reports record earnings",
            link="https://example.com/news/123",
            publisher="Reuters",
            thumbnail="https://example.com/thumb.jpg",
            published_at="2024-01-15T09:00:00Z",
        )
        assert item.publisher == "Reuters"
        assert item.thumbnail == "https://example.com/thumb.jpg"
        assert item.published_at == "2024-01-15T09:00:00Z"

    def test_title_and_link_required(self):
        with pytest.raises(ValidationError):
            NewsItem(title="Only title")
        with pytest.raises(ValidationError):
            NewsItem(link="https://example.com")
