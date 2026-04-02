"""Tab de análisis financiero."""

import streamlit as st

from models import FinancialMetrics
from services import StockService
from ui.base_tab import BaseTab
from utils import draw_bar_chart, draw_multi_line_chart


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
            ("Revenue", "${val:.2f}B", "{delta:+.2f}B", "normal"),
            ("Net Margin", "{val:.1f}%", "{delta:+.1f}pp", "normal"),
            ("FCF", "${val:.2f}B", "{delta:+.2f}B", "normal"),
            ("Debt/Equity", "{val:.1f}%", "{delta:+.1f}pp", "inverse"),
        ]

        for col, (key, val_fmt, delta_fmt, delta_color) in zip(cols, kpi_config):
            with col:
                if key in deltas:
                    val, delta, _ = deltas[key]
                    st.metric(
                        key,
                        val_fmt.format(val=val) if val is not None else "N/A",
                        delta_fmt.format(delta=delta) if delta is not None else None,
                        delta_color=delta_color,
                    )
                else:
                    st.metric(key, "N/A")

    def _render_summary_chart(self, ticker: str, metrics: FinancialMetrics) -> None:
        st.subheader("Resumen Financiero (5 Años)")
        chart_data = metrics.to_summary_chart_data()
        if chart_data:
            data = {k: {"x": v.x, "y": v.y} for k, v in chart_data.items()}
            fig = draw_multi_line_chart(data, f"{ticker} - Resumen Financiero", "Valor")
            st.pyplot(fig, width="stretch")
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
                    fig = draw_bar_chart(
                        metrics.revenue_billions,
                        metrics.years,
                        "Revenue",
                        "Billions ($)",
                        color=METRIC_COLORS["Revenue"],
                    )
                    st.pyplot(fig, width="stretch")
            with col2:
                if metrics.sales_growth:
                    fig = draw_bar_chart(
                        metrics.sales_growth,
                        metrics.years,
                        "Sales Growth",
                        "Crecimiento (%)",
                        is_percent=True,
                        signed=True,
                        color=METRIC_COLORS["Ratios"],
                    )
                    st.pyplot(fig, width="stretch")

        with tabs[1]:
            col1, col2 = st.columns(2)
            with col1:
                if metrics.net_margin:
                    fig = draw_bar_chart(
                        metrics.net_margin,
                        metrics.years,
                        "Net Margin",
                        "Margen (%)",
                        is_percent=True,
                        signed=True,
                        color=METRIC_COLORS["Ratios"],
                    )
                    st.pyplot(fig, width="stretch")
            with col2:
                if metrics.roe:
                    fig = draw_bar_chart(
                        metrics.roe,
                        metrics.years,
                        "ROE",
                        "ROE (%)",
                        is_percent=True,
                        signed=True,
                        color=METRIC_COLORS["Ratios"],
                    )
                    st.pyplot(fig, width="stretch")

        with tabs[2]:
            if metrics.fcf_billions:
                fig = draw_bar_chart(
                    metrics.fcf_billions,
                    metrics.years,
                    "Free Cash Flow",
                    "FCF (Billions)",
                    signed=True,
                    color=METRIC_COLORS["FCF"],
                )
                st.pyplot(fig, width="stretch")
            else:
                st.info("Datos de Free Cash Flow no disponibles.")

        with tabs[3]:
            col1, col2 = st.columns(2)
            with col1:
                if metrics.debt_billions:
                    fig = draw_bar_chart(
                        metrics.debt_billions,
                        metrics.years,
                        "Deuda Total",
                        "Deuda (Billions)",
                        color=METRIC_COLORS["Debt"],
                    )
                    st.pyplot(fig, width="stretch")
            with col2:
                if metrics.debt_equity:
                    fig = draw_bar_chart(
                        metrics.debt_equity,
                        metrics.years,
                        "Deuda/Equity",
                        "Ratio (%)",
                        is_percent=True,
                        color=METRIC_COLORS["Ratios"],
                    )
                    st.pyplot(fig, width="stretch")

    def _render_data_table(self, stock_service: StockService) -> None:
        with st.expander("Ver Datos del Estado de Resultados", expanded=False):
            df = stock_service.get_financials()
            if df is not None and not df.empty:
                st.dataframe(df.T, width="stretch")
            else:
                st.info("Datos del estado de resultados no disponibles.")
