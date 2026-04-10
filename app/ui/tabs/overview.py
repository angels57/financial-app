"""Tab de overview con hero card, combo chart EPS/precio, KPI row y sub-tabs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from app.domain.models import FinancialMetrics, StockInfo
from app.domain.services import FinancialCalculator
from app.domain.services.protocols import StockDataFetcherProtocol
from app.ui.tabs.base import BaseTab
from app.ui.theme import (
    COLOR_GROWTH_NEGATIVE,
    COLOR_GROWTH_POSITIVE,
    COLOR_NEUTRAL,
    COLOR_PRICE_LINE,
    LABEL_CRECIMIENTO,
    LABEL_MARGEN,
)
from app.ui.components import (
    render_52_week_range,
    render_diff_badge,
    render_period_pills,
    render_price_eps_chart,
    slice_history_to_period,
)
from app.utils import (
    calculate_cagr,
    calculate_yoy_growth,
    draw_plotly_bar_chart,
    draw_plotly_dual_axis_chart,
    draw_plotly_grouped_bar_chart,
    draw_plotly_multi_line_chart,
    format_large_number,
)


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_benchmark_history(period: str) -> pd.DataFrame:
    """Fetch S&P 500 history (process-level cache, separate from app DB cache)."""
    try:
        return yf.Ticker("^GSPC").history(period=period)
    except (ValueError, KeyError):
        return pd.DataFrame()


METRIC_COLORS = {
    "Revenue": COLOR_PRICE_LINE,
    "Net Income": COLOR_GROWTH_POSITIVE,
    "FCF": COLOR_NEUTRAL,
    "Debt": COLOR_GROWTH_NEGATIVE,
    "EPS": COLOR_GROWTH_POSITIVE,
    "Ratios": "#9467bd",
}

CHART_INSIGHTS = {
    "revenue_vs_income": (
        "**Revenue vs Net Income** muestra si los beneficios crecen al ritmo de las ventas. "
        "Si el Revenue sube pero el Net Income se estanca o baja, los márgenes se están comprimiendo "
        "— la empresa vende más pero gana menos por cada dólar. Lo ideal es ver ambas barras "
        "creciendo en paralelo año tras año."
    ),
    "sales_growth": (
        "**Crecimiento de Ventas** mide el ritmo al que la empresa expande sus ingresos. "
        "Un crecimiento constante y positivo indica demanda sólida. Crecimientos irregulares "
        "o negativos pueden señalar problemas competitivos o dependencia de ciclos económicos."
    ),
    "net_margin": (
        "**Margen Neto** indica cuánto de cada dólar de ventas queda como ganancia después de "
        "todos los gastos. Un margen del 20% significa que de cada $100 vendidos, $20 son beneficio. "
        "Márgenes estables o crecientes reflejan eficiencia operativa y poder de fijación de precios."
    ),
    "fcf_vs_income": (
        "**Net Income vs FCF** revela la calidad de los beneficios. El Net Income puede inflarse "
        "con ajustes contables, pero el Free Cash Flow muestra el dinero real que entra. "
        'Si el FCF es consistentemente menor al Net Income, los beneficios pueden ser "de papel". '
        "Lo ideal es que ambos se muevan juntos."
    ),
    "fcf_growth": (
        "**Free Cash Flow** es el dinero que queda después de cubrir gastos operativos y de capital. "
        "Es el recurso real para pagar dividendos, recomprar acciones o reinvertir. "
        "Un FCF positivo y creciente es una de las señales más fuertes de salud financiera."
    ),
    "debt": (
        "**Deuda Total** muestra cuánto debe la empresa. Lo importante no es solo el monto, "
        "sino la tendencia: deuda creciente sin crecimiento de ingresos es una señal de alarma. "
        "Compárala siempre con el FCF — si la empresa puede pagar su deuda con 3-4 años de FCF, "
        "generalmente es manejable."
    ),
    "leverage_vs_roe": (
        "**Deuda/Equity vs ROE** muestra la relación entre apalancamiento y rentabilidad. "
        "Un ROE alto (>15%) es positivo, pero si viene acompañado de Deuda/Equity alta (>100%), "
        "la rentabilidad puede ser artificial — generada por deuda, no por eficiencia operativa. "
        "El escenario ideal es ROE alto con apalancamiento moderado."
    ),
    "dividends": (
        "**Dividendos** reflejan el compromiso de la empresa con sus accionistas. "
        "Un historial de dividendos crecientes año tras año es señal de confianza de la directiva "
        "en los flujos futuros. Busca un crecimiento consistente y un payout ratio sostenible "
        "(idealmente <60% del beneficio neto)."
    ),
    "shares": (
        "**Acciones en Circulación** revelan si la empresa recompra acciones (buybacks) o las diluye. "
        "Una tendencia bajista es positiva: menos acciones = mayor beneficio por acción para ti. "
        "Si las acciones suben año tras año, la empresa está diluyendo a los accionistas, "
        "a menudo para financiar compensaciones o adquisiciones."
    ),
    "eps": (
        "**EPS (Earnings Per Share)** es el beneficio neto por acción. Es la métrica más directa "
        "de rentabilidad para el accionista. Un EPS creciente indica que la empresa genera "
        "más beneficios por cada acción, ya sea por mayor rentabilidad o por recompras de acciones."
    ),
}


def _cagr_badges(
    cagr: float | None, n_years: int, label: str
) -> list[tuple[float, str]]:
    if cagr is None:
        return []
    return [(cagr, f"{label} {n_years}a")]


class OverviewTab(BaseTab):
    """Renderiza el tab de overview con hero card, KPIs y sub-tabs."""

    def render(self, **kwargs: Any) -> None:
        stock_service: StockDataFetcherProtocol = kwargs["stock_service"]
        info: StockInfo = kwargs["info"]
        ticker: str = kwargs["ticker"]
        force_refresh: bool = bool(kwargs.get("force_refresh", False))

        with st.spinner("Cargando datos financieros..."):
            financials = stock_service.get_financials(force_refresh=force_refresh)
            balance = stock_service.get_balance_sheet(force_refresh=force_refresh)
            cashflow = stock_service.get_cashflow(force_refresh=force_refresh)

        metrics: FinancialMetrics = FinancialCalculator().compute(
            financials=financials,
            balance=balance,
            cashflow=cashflow,
            pe_ratio=info.pe_ratio,
        )

        self._render_hero(info)
        st.markdown("---")
        self._render_combo_chart_section(stock_service, info)
        st.markdown("---")
        self._render_kpi_row(metrics)
        st.markdown("---")
        self._render_sub_tabs(ticker, metrics, stock_service, info)

    def _render_hero(self, info: StockInfo) -> None:
        col_name, col_price, col_eps = st.columns([2, 1, 1])

        with col_name:
            st.markdown(
                f"""
                <div style="padding-top:8px;">
                    <div style="font-size:1.6rem; font-weight:600; line-height:1.2;">
                        {info.short_name}
                    </div>
                    <div style="font-size:0.9rem; color:#888; margin-top:4px;">
                        {info.ticker}
                        {f"· {info.sector}" if info.sector else ""}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_price:
            with st.container(border=True):
                st.caption("PRICE")
                st.markdown(
                    f"<div style='font-size:1.7rem; font-weight:600;'>"
                    f"{info.currency} {info.price:,.2f}</div>",
                    unsafe_allow_html=True,
                )

        with col_eps:
            with st.container(border=True):
                st.caption("EPS (TTM)")
                eps_str = (
                    f"{info.currency} {info.eps:,.2f}"
                    if info.eps is not None
                    else "N/A"
                )
                st.markdown(
                    f"<div style='font-size:1.7rem; font-weight:600;'>{eps_str}</div>",
                    unsafe_allow_html=True,
                )

        # 52-week range bar full-width below the hero cards
        render_52_week_range(
            info.price, info.week_52_low, info.week_52_high, info.currency
        )

    # -- Combo chart + period pills + benchmark toggle ----------------------

    def _render_combo_chart_section(
        self,
        stock_service: StockDataFetcherProtocol,
        info: StockInfo,
    ) -> None:
        full_history = stock_service.get_history(period="max")
        if full_history.empty:
            st.warning("No hay datos históricos para este ticker.")
            return

        # Toggle right-aligned above the pills
        _, toggle_col = st.columns([3, 1])
        with toggle_col:
            compare_benchmark = st.toggle(
                "Comparar S&P 500",
                value=False,
                key="overview_compare_sp500",
            )

        selected_period = render_period_pills(
            full_history, key="overview_period", default="5y"
        )

        sliced_history = slice_history_to_period(full_history, selected_period)
        # Auto-pick frequency: quarterly for short ranges, annual for long ones
        frequency = "annual" if selected_period in ("5y", "10y", "max") else "quarterly"
        eps_series = stock_service.get_eps_series(frequency=frequency)

        # Filter EPS to the visible window so bars don't overflow
        # Normalize tz: history index is tz-aware (UTC), EPS dates are tz-naive
        if eps_series is not None and not sliced_history.empty:
            window_start = sliced_history.index[0]
            if hasattr(window_start, "tzinfo") and window_start.tzinfo is not None:
                window_start = window_start.replace(tzinfo=None)
            eps_dates = pd.to_datetime(eps_series.index)
            if eps_dates.tz is not None:
                eps_dates = eps_dates.tz_localize(None)
            mask = eps_dates >= window_start
            eps_series = eps_series[mask]

        benchmark_df: pd.DataFrame | None = None
        if compare_benchmark:
            benchmark_df = _fetch_benchmark_history(selected_period)
            if benchmark_df is None or benchmark_df.empty:
                st.warning("No se pudo cargar el S&P 500.")
                benchmark_df = None

        render_price_eps_chart(
            hist=sliced_history,
            eps_series=eps_series,
            currency=info.currency,
            frequency=frequency,
            benchmark=benchmark_df,
        )

    def _render_kpi_row(self, metrics: FinancialMetrics) -> None:
        deltas = metrics.yoy_deltas()
        n = len(metrics.years)

        rev_cagr = calculate_cagr(metrics.revenue_billions)
        ni_cagr = calculate_cagr(metrics.net_income_billions)
        fcf_cagr = calculate_cagr(metrics.fcf_billions)

        cols = st.columns(4)

        kpi_config: list[tuple[str, str, bool, list[tuple[float, str]]]] = [
            ("Revenue", "${val:.2f}B", False, _cagr_badges(rev_cagr, n, "CAGR")),
            ("Net Margin", "{val:.1f}%", False, _cagr_badges(ni_cagr, n, "NI CAGR")),
            ("FCF", "${val:.2f}B", False, _cagr_badges(fcf_cagr, n, "CAGR")),
            ("Debt/Equity", "{val:.1f}%", True, []),
        ]

        for col, (key, val_fmt, is_inverse, extra_badges) in zip(cols, kpi_config):
            with col:
                with st.container(border=True):
                    if key in deltas:
                        val, delta, _ = deltas[key]
                        st.metric(
                            key,
                            val_fmt.format(val=val) if val is not None else "N/A",
                        )
                        if delta is not None and val is not None:
                            badge_delta = -delta if is_inverse else delta
                            render_diff_badge(badge_delta, label="var. YoY")
                        for badge_val, badge_label in extra_badges:
                            render_diff_badge(badge_val, label=badge_label)
                    else:
                        st.metric(key, "N/A")

    def _render_sub_tabs(
        self,
        ticker: str,  # noqa: ARG002 — kept for future per-ticker subtab data
        metrics: FinancialMetrics,
        stock_service: StockDataFetcherProtocol,
        info: StockInfo,
    ) -> None:
        sub_tabs = st.tabs(
            [
                "🏢 Empresa",
                "📈 Crecimiento",
                "💵 Cash Flow",
                "🏥 Salud",
                "🧾 Accionista",
                "📋 Resultados",
            ]
        )

        with sub_tabs[0]:
            self._render_company_subtab(info)

        with sub_tabs[1]:
            self._render_growth_subtab(metrics)

        with sub_tabs[2]:
            self._render_cashflow_subtab(metrics)

        with sub_tabs[3]:
            self._render_health_subtab(metrics)

        with sub_tabs[4]:
            self._render_shareholder_subtab(stock_service)

        with sub_tabs[5]:
            self._render_results_subtab(stock_service)

    def _render_company_subtab(self, info: StockInfo) -> None:
        # Market & valuation metrics row
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Market Cap", format_large_number(info.market_cap, info.currency))
        c2.metric("P/E", f"{info.pe_ratio:.2f}" if info.pe_ratio else "N/A")
        c3.metric("P/FCF", f"{info.price_to_fcf:.2f}" if info.price_to_fcf else "N/A")
        c4.metric("Beta", f"{info.beta:.2f}" if info.beta is not None else "N/A")
        c5.metric(
            "Target",
            f"{info.currency} {info.target_price:,.2f}"
            if info.target_price is not None
            else "N/A",
            info.recommendation.upper() if info.recommendation else None,
        )

        st.markdown("---")

        col_info, col_desc = st.columns([1, 2])

        with col_info:
            if info.sector:
                st.markdown(f"**Sector:** {info.sector}")
            if info.industry:
                st.markdown(f"**Industria:** {info.industry}")
            if info.country:
                st.markdown(f"**País:** {info.country}")
            if info.employees is not None:
                st.markdown(f"**Empleados:** {info.employees:,}")
            if info.website:
                st.markdown(f"**Web:** [{info.website}]({info.website})")
            if info.dividend_yield is not None:
                st.markdown(f"**Dividend Yield:** {info.dividend_yield * 100:.2f}%")

        with col_desc:
            if info.description:
                preview = info.description[:300]
                st.markdown(f"{preview}...")
                with st.expander("Ver descripción completa"):
                    st.write(info.description)
            else:
                st.info("Descripción no disponible.")

        st.markdown("---")

        self._render_external_links(info)

    def _render_external_links(self, info: StockInfo) -> None:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.link_button(
                "📈 TradingView",
                f"https://www.tradingview.com/symbols/{info.ticker}/",
                width="stretch",
            )
        with c2:
            st.link_button(
                "🧠 AlphaSpread",
                f"https://www.alphaspread.com/security/nasdaq/{info.ticker.lower()}/summary",
                width="stretch",
            )
        with c3:
            st.link_button(
                "💡 Smart Investor",
                "https://thesmartinvestortool.com",
                width="stretch",
            )

    def _render_growth_subtab(self, metrics: FinancialMetrics) -> None:
        if metrics.revenue_billions and metrics.net_income_billions:
            fig = draw_plotly_grouped_bar_chart(
                series={
                    "Revenue": metrics.revenue_billions,
                    "Net Income": metrics.net_income_billions,
                },
                labels=metrics.years,
                title="Revenue vs Net Income",
                ylabel="Billones ($)",
                colors={
                    "Revenue": METRIC_COLORS["Revenue"],
                    "Net Income": METRIC_COLORS["Net Income"],
                },
            )
            st.plotly_chart(fig, width="stretch")
            with st.expander("¿Cómo leer este gráfico?"):
                st.markdown(CHART_INSIGHTS["revenue_vs_income"])

        col1, col2 = st.columns(2)
        with col1:
            if metrics.sales_growth:
                fig = draw_plotly_bar_chart(
                    metrics.sales_growth,
                    metrics.years,
                    "Crecimiento Ventas YoY",
                    LABEL_CRECIMIENTO,
                    is_percent=True,
                    signed=True,
                    value_suffix="%",
                    color=METRIC_COLORS["Ratios"],
                )
                st.plotly_chart(fig, width="stretch")
                with st.expander("¿Cómo leer este gráfico?"):
                    st.markdown(CHART_INSIGHTS["sales_growth"])
        with col2:
            if metrics.net_margin:
                fig = draw_plotly_bar_chart(
                    metrics.net_margin,
                    metrics.years,
                    "Margen Neto",
                    LABEL_MARGEN,
                    is_percent=True,
                    signed=True,
                    value_suffix="%",
                    color=METRIC_COLORS["Net Income"],
                )
                st.plotly_chart(fig, width="stretch")
                with st.expander("¿Cómo leer este gráfico?"):
                    st.markdown(CHART_INSIGHTS["net_margin"])

    def _render_cashflow_subtab(self, metrics: FinancialMetrics) -> None:
        if metrics.fcf_billions and metrics.net_income_billions:
            fig = draw_plotly_grouped_bar_chart(
                series={
                    "Net Income": metrics.net_income_billions,
                    "Free Cash Flow": metrics.fcf_billions,
                },
                labels=metrics.years,
                title="Net Income vs FCF — Calidad de los Beneficios",
                ylabel="Billones ($)",
                colors={
                    "Net Income": METRIC_COLORS["Net Income"],
                    "Free Cash Flow": METRIC_COLORS["FCF"],
                },
            )
            st.plotly_chart(fig, width="stretch")
            with st.expander("¿Cómo leer este gráfico?"):
                st.markdown(CHART_INSIGHTS["fcf_vs_income"])

        if metrics.fcf_billions:
            fcf_yoy = calculate_yoy_growth(metrics.fcf_billions)
            fig = draw_plotly_dual_axis_chart(
                bar_values=metrics.fcf_billions,
                line_values=fcf_yoy,
                labels=metrics.years,
                title="Free Cash Flow + Crecimiento YoY",
                bar_label="FCF (Billones $)",
                line_label="Cambio YoY (%)",
                bar_color=METRIC_COLORS["FCF"],
                line_color=METRIC_COLORS["Debt"],
            )
            st.plotly_chart(fig, width="stretch")
            with st.expander("¿Cómo leer este gráfico?"):
                st.markdown(CHART_INSIGHTS["fcf_growth"])
        elif not metrics.net_income_billions:
            st.info("Datos de Cash Flow no disponibles.")

    def _render_health_subtab(self, metrics: FinancialMetrics) -> None:
        col1, col2 = st.columns(2)

        with col1:
            if metrics.debt_billions:
                debt_yoy = calculate_yoy_growth(metrics.debt_billions)
                fig = draw_plotly_dual_axis_chart(
                    bar_values=metrics.debt_billions,
                    line_values=debt_yoy,
                    labels=metrics.years,
                    title="Deuda Total",
                    bar_label="Deuda (Billones $)",
                    line_label="Cambio YoY (%)",
                    bar_color=METRIC_COLORS["Debt"],
                    line_color=METRIC_COLORS["Revenue"],
                )
                st.plotly_chart(fig, width="stretch")
                with st.expander("¿Cómo leer este gráfico?"):
                    st.markdown(CHART_INSIGHTS["debt"])
            else:
                st.info("Datos de deuda no disponibles.")

        with col2:
            if metrics.debt_equity and metrics.roe:
                fig = draw_plotly_multi_line_chart(
                    {
                        "Deuda/Equity (%)": {
                            "x": metrics.years,
                            "y": metrics.debt_equity,
                        },
                        "ROE (%)": {"x": metrics.years, "y": metrics.roe},
                    },
                    title="Apalancamiento vs Rentabilidad",
                    ylabel="Porcentaje (%)",
                    is_percent=True,
                )
                st.plotly_chart(fig, width="stretch")
                with st.expander("¿Cómo leer este gráfico?"):
                    st.markdown(CHART_INSIGHTS["leverage_vs_roe"])
            elif metrics.roe:
                fig = draw_plotly_bar_chart(
                    metrics.roe,
                    metrics.years,
                    "ROE",
                    "ROE (%)",
                    is_percent=True,
                    signed=True,
                    value_suffix="%",
                    color=METRIC_COLORS["Ratios"],
                )
                st.plotly_chart(fig, width="stretch")

    def _render_shareholder_subtab(
        self, stock_service: StockDataFetcherProtocol
    ) -> None:
        col1, col2 = st.columns(2)
        with col1:
            self._render_dividends_chart(stock_service)
        with col2:
            self._render_shares_chart(stock_service)
        self._render_eps_chart(stock_service)

    def _render_dividends_chart(self, stock_service: StockDataFetcherProtocol) -> None:
        div_df = stock_service.get_dividends()
        info = stock_service.get_info()

        if div_df is None or div_df.empty:
            st.info("Datos de dividendos no disponibles.")
            return

        current_year = datetime.now().year
        div_df = div_df[div_df.index < current_year]
        years = [str(idx) for idx in div_df.index]
        dividends = div_df["Dividend"].tolist()

        div_growth = calculate_yoy_growth(dividends)

        fig = draw_plotly_dual_axis_chart(
            bar_values=dividends[:10],
            line_values=div_growth[:10],
            labels=years[:10],
            title="Dividendos por Acción",
            bar_label="Dividendo ($)",
            line_label="Crecimiento (%)",
            bar_color=COLOR_GROWTH_POSITIVE,
            line_color=COLOR_NEUTRAL,
        )
        st.plotly_chart(fig, width="stretch")
        with st.expander("¿Cómo leer este gráfico?"):
            st.markdown(CHART_INSIGHTS["dividends"])

        c1, c2 = st.columns(2)
        with c1:
            if info.dividend_yield is not None:
                st.metric(
                    "Dividend Yield (TTM)",
                    f"{info.dividend_yield * 100:.2f}%",
                )
        with c2:
            if dividends:
                st.metric(
                    "Último Dividendo Anual",
                    f"${dividends[-1]:.2f}",
                )

    def _render_shares_chart(self, stock_service: StockDataFetcherProtocol) -> None:
        shares_df = stock_service.get_financials()
        if shares_df is None or "Diluted Average Shares" not in shares_df.index:
            st.info("Datos de acciones en circulación no disponibles.")
            return

        shares = (shares_df.loc["Diluted Average Shares"] / 1e9).tolist()
        years = [str(c)[:4] for c in shares_df.columns]

        shares_yoy = calculate_yoy_growth(shares)

        fig = draw_plotly_dual_axis_chart(
            bar_values=shares[-10:],
            line_values=shares_yoy[-10:],
            labels=years[-10:],
            title="Acciones Promedio Diluidas",
            bar_label="Acciones (Miles de Millones)",
            line_label="Cambio YoY (%)",
            bar_color="#9467bd",
            line_color=COLOR_PRICE_LINE,
        )
        st.plotly_chart(fig, width="stretch")
        with st.expander("¿Cómo leer este gráfico?"):
            st.markdown(CHART_INSIGHTS["shares"])

    def _render_eps_chart(self, stock_service: StockDataFetcherProtocol) -> None:
        fin_df = stock_service.get_financials()
        if fin_df is None or "Diluted EPS" not in fin_df.index:
            st.info("Datos de EPS no disponibles.")
            return

        eps_series = fin_df.loc["Diluted EPS"]
        years = [str(c)[:4] for c in fin_df.columns]
        eps_values = eps_series.tolist()

        fig = draw_plotly_bar_chart(
            eps_values[-10:],
            years[-10:],
            "EPS — Beneficio por Acción ($/acción)",
            "EPS ($/acción)",
            value_suffix="",
            color=METRIC_COLORS["EPS"],
        )
        st.plotly_chart(fig, width="stretch")
        with st.expander("¿Cómo leer este gráfico?"):
            st.markdown(CHART_INSIGHTS["eps"])

    def _render_results_subtab(self, stock_service: StockDataFetcherProtocol) -> None:
        st.subheader("Estado de Resultados")
        df = stock_service.get_financials()
        if df is None or df.empty:
            st.info("Datos del estado de resultados no disponibles.")
            return

        years = [str(c)[:4] for c in df.columns]
        revenue = df.loc["Total Revenue"] if "Total Revenue" in df.index else None

        income_rows: list[tuple[str, str, bool]] = [
            ("Total Revenue", "Ingresos Totales", True),
            ("Cost Of Revenue", "Coste de Ventas", False),
            ("Gross Profit", "Beneficio Bruto", True),
            ("_margin_gross", "  Margen Bruto (%)", False),
            ("Research And Development", "I+D", False),
            ("Selling General And Administration", "SG&A", False),
            ("Operating Income", "Resultado Operativo (EBIT)", True),
            ("_margin_operating", "  Margen Operativo (%)", False),
            ("Interest Expense", "Gastos Financieros", False),
            ("Pretax Income", "Resultado antes de Impuestos", False),
            ("Tax Provision", "Impuestos", False),
            ("Net Income", "Beneficio Neto", True),
            ("_margin_net", "  Margen Neto (%)", False),
            ("EBITDA", "EBITDA", True),
            ("Diluted EPS", "EPS Diluido", False),
        ]

        rows: list[tuple[str, list[str], bool]] = []
        for key, label, is_bold in income_rows:
            if key.startswith("_margin_"):
                row_values = self._calc_margin_row(key, df, revenue)
                if row_values is None:
                    continue
                rows.append((label, row_values, False))
            elif key in df.index:
                raw = df.loc[key]
                formatted = [
                    format_large_number(v) if pd.notna(v) else "—" for v in raw
                ]
                rows.append((label, formatted, is_bold))

        if not rows:
            st.info("Datos del estado de resultados no disponibles.")
            return

        yoy_values = self._calc_yoy_column(df, rows)
        header = ["Concepto"] + years + ["YoY %"]

        cell_labels = []
        cell_columns: list[list[str]] = [[] for _ in range(len(years) + 1)]
        fill_colors: list[list[str]] = []
        font_colors: list[list[str]] = []

        highlight_bg = "#e8f0fe"
        for i, (label, values, is_bold) in enumerate(rows):
            is_margin = label.startswith("  Margen")
            base_bg = (
                highlight_bg if is_bold else ("#f8f9fa" if i % 2 == 0 else "#ffffff")
            )
            text_color = "#888888" if is_margin else "#1a1a2e" if is_bold else "#2c3e50"

            display_label = f"▸ {label}" if is_bold else label
            cell_labels.append(display_label)
            row_bg = [base_bg]
            row_fc = [text_color]

            for j, val_str in enumerate(values):
                cell_columns[j].append(val_str)
                row_bg.append(base_bg)
                row_fc.append(text_color)

            yoy = yoy_values[i]
            cell_columns[len(years)].append(yoy)
            if yoy and yoy != "—":
                yoy_float = float(yoy.replace("%", "").replace("+", ""))
                row_bg.append("#e6f4ea" if yoy_float >= 0 else "#fce8e6")
                row_fc.append("#1e7e34" if yoy_float >= 0 else "#c0392b")
            else:
                row_bg.append(base_bg)
                row_fc.append("#888888")

            fill_colors.append(row_bg)
            font_colors.append(row_fc)

        all_columns = [cell_labels] + cell_columns

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=header,
                        fill_color="#2c3e50",
                        font=dict(size=12, color="white"),
                        align=["left"] + ["right"] * (len(years) + 1),
                        height=38,
                    ),
                    cells=dict(
                        values=all_columns,
                        fill_color=[list(col) for col in zip(*fill_colors)],
                        font=dict(
                            size=11,
                            color=[list(col) for col in zip(*font_colors)],
                        ),
                        align=["left"] + ["right"] * (len(years) + 1),
                        height=32,
                        line=dict(color="#dee2e6", width=1),
                    ),
                )
            ]
        )

        fig.update_layout(
            margin=dict(l=0, r=0, t=5, b=0),
            height=38 + (len(rows) * 32) + 10,
        )

        st.plotly_chart(fig, width="stretch")

    @staticmethod
    def _calc_margin_row(
        key: str, df: pd.DataFrame, revenue: pd.Series | None
    ) -> list[str] | None:
        if revenue is None:
            return None
        margin_map = {
            "_margin_gross": "Gross Profit",
            "_margin_operating": "Operating Income",
            "_margin_net": "Net Income",
        }
        numerator_key = margin_map.get(key)
        if numerator_key is None or numerator_key not in df.index:
            return None
        numerator = df.loc[numerator_key]
        values = []
        for num, rev in zip(numerator, revenue):
            if pd.notna(num) and pd.notna(rev) and rev != 0:
                values.append(f"{(num / rev) * 100:.1f}%")
            else:
                values.append("—")
        return values

    def _calc_yoy_column(
        self, df: pd.DataFrame, rows: list[tuple[str, list[str], bool]]
    ) -> list[str]:
        income_rows: list[tuple[str, str, bool]] = [
            ("Total Revenue", "Ingresos Totales", True),
            ("Cost Of Revenue", "Coste de Ventas", False),
            ("Gross Profit", "Beneficio Bruto", True),
            ("_margin_gross", "  Margen Bruto (%)", False),
            ("Research And Development", "I+D", False),
            ("Selling General And Administration", "SG&A", False),
            ("Operating Income", "Resultado Operativo (EBIT)", True),
            ("_margin_operating", "  Margen Operativo (%)", False),
            ("Interest Expense", "Gastos Financieros", False),
            ("Pretax Income", "Resultado antes de Impuestos", False),
            ("Tax Provision", "Impuestos", False),
            ("Net Income", "Beneficio Neto", True),
            ("_margin_net", "  Margen Neto (%)", False),
            ("EBITDA", "EBITDA", True),
            ("Diluted EPS", "EPS Diluido", False),
        ]

        yoy_values = []
        for key, label, _bold in income_rows:
            matching = [r for r in rows if r[0] == label]
            if not matching:
                continue

            if key.startswith("_margin_"):
                yoy_values.append("—")
                continue

            if key not in df.index or len(df.columns) < 2:
                yoy_values.append("—")
                continue

            curr, prev = df.loc[key].iloc[0], df.loc[key].iloc[1]
            if pd.notna(curr) and pd.notna(prev) and prev != 0:
                change = ((curr - prev) / abs(prev)) * 100
                yoy_values.append(f"{change:+.1f}%")
            else:
                yoy_values.append("—")

        return yoy_values
