"""Tab de análisis financiero."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models import FinancialMetrics
from domain.services.protocols import StockDataFetcherProtocol
from ui.base_tab import BaseTab
from ui.components import render_diff_badge
from utils import (
    calculate_cagr,
    calculate_yoy_growth,
    draw_plotly_bar_chart,
    draw_plotly_dual_axis_chart,
    draw_plotly_grouped_bar_chart,
    draw_plotly_multi_line_chart,
    format_large_number,
)


METRIC_COLORS = {
    "Revenue": "#1f77b4",
    "Net Income": "#2ca02c",
    "FCF": "#ff7f0e",
    "Debt": "#d62728",
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
}


class FinancialsTab(BaseTab):
    """Renderiza el tab de finanzas con métricas y gráficos."""

    def render(
        self,
        *,
        ticker: str,
        metrics: FinancialMetrics,
        stock_service: StockDataFetcherProtocol,
        **kwargs: object,
    ) -> None:
        self._render_kpi_cards(metrics)
        st.markdown("---")
        self._render_summary_chart(ticker, metrics)
        st.markdown("---")
        self._render_themed_tabs(ticker, metrics, stock_service)
        st.markdown("---")
        self._render_data_table(stock_service)

    def _render_kpi_cards(self, metrics: FinancialMetrics) -> None:
        deltas = metrics.yoy_deltas()

        rev_cagr = calculate_cagr(metrics.revenue_billions)
        ni_cagr = calculate_cagr(metrics.net_income_billions)
        fcf_cagr = calculate_cagr(metrics.fcf_billions)

        cols = st.columns(4)

        kpi_config = [
            ("Revenue", "${val:.2f}B", False, rev_cagr),
            ("Net Margin", "{val:.1f}%", False, None),
            ("FCF", "${val:.2f}B", False, fcf_cagr),
            ("Debt/Equity", "{val:.1f}%", True, None),
        ]

        for col, (key, val_fmt, is_inverse, cagr) in zip(cols, kpi_config):
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
                        if cagr is not None:
                            render_diff_badge(cagr, label=f"CAGR {len(metrics.years)}a")
                    else:
                        st.metric(key, "N/A")

        if ni_cagr is not None:
            with cols[1]:
                render_diff_badge(ni_cagr, label=f"NI CAGR {len(metrics.years)}a")

    def _render_summary_chart(self, ticker: str, metrics: FinancialMetrics) -> None:
        st.subheader("Resumen Financiero (5 Años)")
        chart_data = metrics.to_summary_chart_data()
        if chart_data:
            data = {k: {"x": v.x, "y": v.y} for k, v in chart_data.items()}
            fig = draw_plotly_multi_line_chart(
                data, f"{ticker} - Resumen Financiero", "Valor"
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No hay suficientes datos para generar el resumen.")

    def _render_themed_tabs(
        self,
        ticker: str,
        metrics: FinancialMetrics,
        stock_service: StockDataFetcherProtocol,
    ) -> None:
        if not metrics.years:
            st.info("Datos financieros no disponibles.")
            return

        tabs = st.tabs(
            [
                "Crecimiento",
                "Cash Flow",
                "Salud Financiera",
                "Retorno al Accionista",
            ]
        )

        with tabs[0]:
            self._render_growth_tab(metrics)

        with tabs[1]:
            self._render_cashflow_tab(metrics)

        with tabs[2]:
            self._render_health_tab(metrics)

        with tabs[3]:
            self._render_shareholder_tab(stock_service)

    # -- Tab 1: Crecimiento --------------------------------------------------

    def _render_growth_tab(self, metrics: FinancialMetrics) -> None:
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
                    "Crecimiento (%)",
                    is_percent=True,
                    signed=True,
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
                    "Margen (%)",
                    is_percent=True,
                    signed=True,
                    color=METRIC_COLORS["Net Income"],
                )
                st.plotly_chart(fig, width="stretch")
                with st.expander("¿Cómo leer este gráfico?"):
                    st.markdown(CHART_INSIGHTS["net_margin"])

    # -- Tab 2: Cash Flow -----------------------------------------------------

    def _render_cashflow_tab(self, metrics: FinancialMetrics) -> None:
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

    # -- Tab 3: Salud Financiera ----------------------------------------------

    def _render_health_tab(self, metrics: FinancialMetrics) -> None:
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
                    color=METRIC_COLORS["Ratios"],
                )
                st.plotly_chart(fig, width="stretch")

    # -- Tab 4: Retorno al Accionista -----------------------------------------

    def _render_shareholder_tab(self, stock_service: StockDataFetcherProtocol) -> None:
        col1, col2 = st.columns(2)
        with col1:
            self._render_dividends_chart(stock_service)
        with col2:
            self._render_shares_chart(stock_service)

    def _render_dividends_chart(self, stock_service: StockDataFetcherProtocol) -> None:
        div_df = stock_service.get_dividends()
        info = stock_service.get_info()

        if div_df is None or div_df.empty:
            st.info("Datos de dividendos no disponibles.")
            return

        years = [str(idx) for idx in div_df.index]
        dividends = div_df["Dividend"].tolist()

        div_growth = calculate_yoy_growth(dividends)

        fig = draw_plotly_dual_axis_chart(
            bar_values=dividends[-10:],
            line_values=div_growth[-10:],
            labels=years[-10:],
            title="Dividendos por Acción",
            bar_label="Dividendo ($)",
            line_label="Crecimiento (%)",
            bar_color="#2ca02c",
            line_color="#ff7f0e",
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
            line_color="#1f77b4",
        )
        st.plotly_chart(fig, width="stretch")
        with st.expander("¿Cómo leer este gráfico?"):
            st.markdown(CHART_INSIGHTS["shares"])

    # -- Tabla de datos -------------------------------------------------------

    # Income statement rows in funnel order: revenue -> costs -> profits -> per-share
    _INCOME_ROWS: list[tuple[str, str, bool]] = [
        # (yfinance_key, spanish_label, is_highlight)
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

    def _render_data_table(self, stock_service: StockDataFetcherProtocol) -> None:
        st.subheader("Estado de Resultados")
        df = stock_service.get_financials()
        if df is None or df.empty:
            st.info("Datos del estado de resultados no disponibles.")
            return

        years = [str(c)[:4] for c in df.columns]
        revenue = df.loc["Total Revenue"] if "Total Revenue" in df.index else None

        rows: list[tuple[str, list[str], bool]] = []
        for key, label, is_bold in self._INCOME_ROWS:
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

        # Add YoY column for the most recent year
        yoy_values = self._calc_yoy_column(df, rows)
        header = ["Concepto"] + years + ["YoY %"]

        # Build cell data
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

            # Prepend marker to highlight rows visually
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
        yoy_values = []
        for key, label, _bold in self._INCOME_ROWS:
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
