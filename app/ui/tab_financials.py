"""Tab de análisis financiero."""

import streamlit as st

from models import FinancialMetrics
from ui.base_tab import BaseTab
from utils import draw_bar_chart, draw_multi_line_chart


class FinancialsTab(BaseTab):
    """Renderiza el tab de finanzas con métricas y gráficos."""

    def render(self, *, ticker: str, metrics: FinancialMetrics, **kwargs) -> None:
        chart_data = metrics.to_summary_chart_data()

        self._render_summary_chart(ticker, chart_data)
        st.markdown("---")
        self._render_annual_performance(ticker, metrics)
        st.markdown("---")
        self._render_individual_charts(ticker, metrics)

    def _render_summary_chart(self, ticker: str, chart_data: dict) -> None:
        st.subheader("Resumen Financiero (5 Años)")
        if chart_data:
            data = {k: {"x": v.x, "y": v.y} for k, v in chart_data.items()}
            fig = draw_multi_line_chart(data, f"{ticker} - Resumen Financiero", "Valor")
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("No hay suficientes datos para generar el resumen.")

    def _render_annual_performance(
        self, ticker: str, metrics: FinancialMetrics
    ) -> None:
        st.subheader("Rendimiento Financiero Anual")

        if not metrics.years:
            st.info("Datos financieros no disponibles.")
            return

        col_f1, col_f2 = st.columns(2)

        with col_f1:
            if metrics.revenue_billions:
                fig = draw_bar_chart(
                    metrics.revenue_billions,
                    metrics.years,
                    "Ingresos Anuales",
                    "Billions ($)",
                )
                st.pyplot(fig, use_container_width=True)

        with col_f2:
            if metrics.net_margin:
                fig = draw_bar_chart(
                    metrics.net_margin,
                    metrics.years,
                    "Margen Neto (%)",
                    "Porcentaje",
                    signed=True,
                    is_percent=True,
                )
                st.pyplot(fig, use_container_width=True)

        st.markdown("---")
        col_f3, col_f4 = st.columns(2)

        with col_f3:
            if metrics.fcf_billions:
                fig = draw_bar_chart(
                    metrics.fcf_billions,
                    metrics.years,
                    "Free Cash Flow",
                    "Billions ($)",
                    signed=True,
                )
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("Datos de Free Cash Flow no disponibles.")

        with col_f4:
            if metrics.debt_billions:
                fig = draw_bar_chart(
                    metrics.debt_billions,
                    metrics.years,
                    "Deuda Total",
                    "Billions ($)",
                )
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("Datos de deuda no disponibles.")

    def _render_individual_charts(self, ticker: str, metrics: FinancialMetrics) -> None:
        st.subheader("Gráficos Individuales (5 Años)")

        if not metrics.years:
            return

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            if metrics.sales_growth:
                fig = draw_bar_chart(
                    metrics.sales_growth,
                    metrics.years,
                    f"{ticker} - Crecimiento de Ventas",
                    "Crecimiento (%)",
                    is_percent=True,
                    signed=True,
                )
                st.pyplot(fig, use_container_width=True)

        with col_g2:
            if metrics.net_margin:
                fig = draw_bar_chart(
                    metrics.net_margin,
                    metrics.years,
                    f"{ticker} - Margen Neto",
                    "Margen (%)",
                    is_percent=True,
                    signed=True,
                )
                st.pyplot(fig, use_container_width=True)

        col_g3, col_g4 = st.columns(2)

        with col_g3:
            if metrics.roe:
                fig = draw_bar_chart(
                    metrics.roe,
                    metrics.years,
                    f"{ticker} - ROE",
                    "ROE (%)",
                    is_percent=True,
                    signed=True,
                )
                st.pyplot(fig, use_container_width=True)

        with col_g4:
            if metrics.fcf_billions:
                fig = draw_bar_chart(
                    metrics.fcf_billions,
                    metrics.years,
                    f"{ticker} - Free Cash Flow",
                    "FCF (Billions)",
                    signed=True,
                )
                st.pyplot(fig, use_container_width=True)

        col_g5, col_g6 = st.columns(2)

        with col_g5:
            if metrics.debt_billions:
                fig = draw_bar_chart(
                    metrics.debt_billions,
                    metrics.years,
                    f"{ticker} - Deuda Total",
                    "Deuda (Billions)",
                )
                st.pyplot(fig, use_container_width=True)

        with col_g6:
            if metrics.debt_equity:
                fig = draw_bar_chart(
                    metrics.debt_equity,
                    metrics.years,
                    f"{ticker} - Deuda/Equity",
                    "Ratio (%)",
                    is_percent=True,
                )
                st.pyplot(fig, use_container_width=True)
