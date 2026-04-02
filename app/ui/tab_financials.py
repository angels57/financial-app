"""Tab de análisis financiero."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models import FinancialMetrics
from services import StockService
from ui.base_tab import BaseTab
from ui.components import render_diff_badge
from utils import (
    draw_plotly_bar_chart,
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
        self._render_themed_tabs(ticker, metrics)
        st.markdown("---")
        self._render_data_table(stock_service)

    def _render_kpi_cards(self, metrics: FinancialMetrics) -> None:
        deltas = metrics.yoy_deltas()
        cols = st.columns(4)

        kpi_config = [
            ("Revenue", "${val:.2f}B", "var. YoY", False),
            ("Net Margin", "{val:.1f}%", "var. YoY", False),
            ("FCF", "${val:.2f}B", "var. YoY", False),
            ("Debt/Equity", "{val:.1f}%", "var. YoY", True),
        ]

        for col, (key, val_fmt, delta_label, is_inverse) in zip(cols, kpi_config):
            with col:
                with st.container(border=True):
                    if key in deltas:
                        val, delta, _ = deltas[key]
                        st.metric(
                            key,
                            val_fmt.format(val=val) if val is not None else "N/A",
                        )
                        if delta is not None and val is not None:
                            if is_inverse:
                                badge_delta = -delta
                            else:
                                badge_delta = delta
                            render_diff_badge(badge_delta, label=delta_label)
                    else:
                        st.metric(key, "N/A")

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

    def _render_themed_tabs(self, ticker: str, metrics: FinancialMetrics) -> None:
        if not metrics.years:
            st.info("Datos financieros no disponibles.")
            return

        tabs = st.tabs(["Ingresos", "Rentabilidad", "Cash Flow", "Deuda"])

        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                if metrics.revenue_billions:
                    fig = draw_plotly_bar_chart(
                        metrics.revenue_billions,
                        metrics.years,
                        "Revenue",
                        "Billones ($)",
                        color=METRIC_COLORS["Revenue"],
                    )
                    st.plotly_chart(fig, use_container_width=True)
            with col2:
                if metrics.sales_growth:
                    fig = draw_plotly_bar_chart(
                        metrics.sales_growth,
                        metrics.years,
                        "Sales Growth",
                        "Crecimiento (%)",
                        is_percent=True,
                        signed=True,
                        color=METRIC_COLORS["Ratios"],
                    )
                    st.plotly_chart(fig, use_container_width=True)

        with tabs[1]:
            col1, col2 = st.columns(2)
            with col1:
                if metrics.net_margin:
                    fig = draw_plotly_bar_chart(
                        metrics.net_margin,
                        metrics.years,
                        "Net Margin",
                        "Margen (%)",
                        is_percent=True,
                        signed=True,
                        color=METRIC_COLORS["Ratios"],
                    )
                    st.plotly_chart(fig, use_container_width=True)
            with col2:
                if metrics.roe:
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

        with tabs[2]:
            if metrics.fcf_billions:
                fig = draw_plotly_bar_chart(
                    metrics.fcf_billions,
                    metrics.years,
                    "Free Cash Flow",
                    "FCF (Billones)",
                    signed=True,
                    color=METRIC_COLORS["FCF"],
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Datos de Free Cash Flow no disponibles.")

        with tabs[3]:
            col1, col2 = st.columns(2)
            with col1:
                if metrics.debt_billions:
                    fig = draw_plotly_bar_chart(
                        metrics.debt_billions,
                        metrics.years,
                        "Deuda Total",
                        "Deuda (Billones)",
                        color=METRIC_COLORS["Debt"],
                    )
                    st.plotly_chart(fig, use_container_width=True)
            with col2:
                if metrics.debt_equity:
                    fig = draw_plotly_bar_chart(
                        metrics.debt_equity,
                        metrics.years,
                        "Deuda/Equity",
                        "Ratio (%)",
                        is_percent=True,
                        color=METRIC_COLORS["Ratios"],
                    )
                    st.plotly_chart(fig, use_container_width=True)

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
