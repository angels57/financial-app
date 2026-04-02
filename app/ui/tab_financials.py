"""Tab de análisis financiero."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models import FinancialMetrics
from services import StockService
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


class FinancialsTab(BaseTab):
    """Renderiza el tab de finanzas con métricas y gráficos."""

    def render(
        self,
        *,
        ticker: str,
        metrics: FinancialMetrics,
        stock_service: StockService,
        **kwargs,
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

        rev_cagr = calculate_cagr(list(reversed(metrics.revenue_billions)))
        ni_cagr = calculate_cagr(list(reversed(metrics.net_income_billions)))
        fcf_cagr = calculate_cagr(list(reversed(metrics.fcf_billions)))

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
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay suficientes datos para generar el resumen.")

    def _render_themed_tabs(
        self, ticker: str, metrics: FinancialMetrics, stock_service: StockService
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
            st.plotly_chart(fig, use_container_width=True)

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
                st.plotly_chart(fig, use_container_width=True)
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
                st.plotly_chart(fig, use_container_width=True)

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
            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                "Si el FCF acompaña al Net Income, los beneficios son reales. "
                "Si divergen, pueden ser ajustes contables."
            )

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
            st.plotly_chart(fig, use_container_width=True)
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
                st.plotly_chart(fig, use_container_width=True)
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
                st.plotly_chart(fig, use_container_width=True)
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
                st.plotly_chart(fig, use_container_width=True)

    # -- Tab 4: Retorno al Accionista -----------------------------------------

    def _render_shareholder_tab(self, stock_service: StockService) -> None:
        col1, col2 = st.columns(2)
        with col1:
            self._render_dividends_chart(stock_service)
        with col2:
            self._render_shares_chart(stock_service)

    def _render_dividends_chart(self, stock_service: StockService) -> None:
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
        st.plotly_chart(fig, use_container_width=True)

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

    def _render_shares_chart(self, stock_service: StockService) -> None:
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
        st.plotly_chart(fig, use_container_width=True)

    # -- Tabla de datos -------------------------------------------------------

    def _render_data_table(self, stock_service: StockService) -> None:
        st.subheader("Estado de Resultados")
        df = stock_service.get_financials()
        if df is None or df.empty:
            st.info("Datos del estado de resultados no disponibles.")
            return

        row_label_map = {
            "Total Revenue": "Ingresos Totales",
            "Net Income": "Beneficio Neto",
            "Operating Income": "Resultado Operativo",
            "Gross Profit": "Beneficio Bruto",
            "Interest Expense": "Gastos Financieros",
            "Net Income Available To Common": "Beneficio Neto (Common)",
            "Basic EPS": "EPS Básico",
            "Diluted EPS": "EPS Diluido",
            "Shares Outstanding": "Acciones en Circulación",
            "Dividend per Share": "Dividendo por Acción",
            "Interest Income": "Ingresos por Intereses",
            "Income Tax Expense": "Impuesto sobre Beneficios",
            "Research And Development": "I+D",
            "Selling General And Administration": "SG&A",
            "Cost Of Revenue": "Coste de Ingresos",
            "Other Income Net": "Otros Ingresos Netos",
        }

        display_df = df.copy()
        display_df.index = display_df.index.map(lambda x: row_label_map.get(x, x))
        display_df.columns = [str(c)[:4] for c in display_df.columns]

        header_values = ["Concepto"] + [str(c) for c in display_df.columns]
        cell_values = []
        cell_colors = []

        for row_idx, row_label in enumerate(display_df.index):
            row_values = [row_label]
            if row_idx % 2 == 0:
                base_color = "#f8f9fa"
            else:
                base_color = "#ffffff"
            row_colors = [base_color]
            for col in display_df.columns:
                val = display_df.loc[row_label, col]
                if pd.notna(val):
                    row_values.append(format_large_number(val))
                    if val < 0:
                        row_colors.append("#ffcccc")
                    else:
                        row_colors.append(base_color)
                else:
                    row_values.append("N/A")
                    row_colors.append(base_color)
            cell_values.append(row_values)
            cell_colors.append(row_colors)

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=header_values,
                        fill_color="#2c3e50",
                        font_color="#ffffff",
                        align="left",
                        height=38,
                        font=dict(size=12, color="white"),
                    ),
                    cells=dict(
                        values=list(zip(*cell_values)),
                        fill_color=cell_colors,
                        align="left",
                        height=32,
                        font=dict(size=11, color="#2c3e50"),
                        line=dict(color="#dee2e6", width=1),
                    ),
                )
            ]
        )

        fig.update_layout(
            margin=dict(l=0, r=0, t=5, b=0),
            height=38 + (len(display_df.index) * 32),
        )

        st.plotly_chart(fig, use_container_width=True)
