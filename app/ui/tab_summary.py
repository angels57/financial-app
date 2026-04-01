"""Tab de resumen general."""

import plotly.graph_objects as go
import streamlit as st

from models import StockInfo
from services import StockService
from ui.base_tab import BaseTab
from utils import calculate_52_week_delta, format_large_number


class SummaryTab(BaseTab):
    """Renderiza el tab de resumen con precio, métricas y historial."""

    def render(
        self, *, stock_service: StockService, info: StockInfo, period: str, **kwargs
    ) -> None:
        self._render_price_metrics(info)
        st.markdown("---")
        self._render_market_metrics(info)
        self._render_price_history(stock_service, info.currency, period)

    def _render_price_metrics(self, info: StockInfo) -> None:
        col1, col2, col3 = st.columns(3)
        low_delta = calculate_52_week_delta(info.price, info.week_52_low)
        high_delta = calculate_52_week_delta(info.price, info.week_52_high)

        with col1:
            st.metric("Precio Actual", f"{info.currency} {info.price:,.2f}")
        with col2:
            st.metric(
                "Mínimo 52 Semanas",
                f"{info.currency} {info.week_52_low:,.2f}"
                if info.week_52_low
                else "N/A",
                f"{low_delta:+.2f}%" if low_delta else None,
            )
        with col3:
            st.metric(
                "Máximo 52 Semanas",
                f"{info.currency} {info.week_52_high:,.2f}"
                if info.week_52_high
                else "N/A",
                f"{high_delta:+.2f}%" if high_delta else None,
            )

    def _render_market_metrics(self, info: StockInfo) -> None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Market Cap", format_large_number(info.market_cap, info.currency))
        c2.metric("P/E Ratio", f"{info.pe_ratio:.2f}" if info.pe_ratio else "N/A")
        c3.metric("Volumen", f"{info.volume:,.0f}")
        with c4:
            st.link_button(
                "📈 Ver en TradingView",
                f"https://www.tradingview.com/symbols/{info.ticker}/",
                use_container_width=True,
            )

    def _render_price_history(
        self, stock_service: StockService, currency: str, period: str
    ) -> None:
        st.subheader(f"Historial de Precios ({period})")
        hist = stock_service.get_history(period=period)
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist["Close"],
                    mode="lines",
                    name="Precio",
                    line={"color": "#1f77b4", "width": 1.5},
                    fill="tozeroy",
                    fillcolor="rgba(31,119,180,0.1)",
                    hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f} "
                    + currency
                    + "<extra></extra>",
                )
            )
            fig.update_layout(
                yaxis_title=f"Precio ({currency})",
                xaxis_rangeslider_visible=True,
                xaxis={
                    "rangeselector": {
                        "buttons": [
                            {"count": 1, "label": "1M", "step": "month"},
                            {"count": 3, "label": "3M", "step": "month"},
                            {"count": 6, "label": "6M", "step": "month"},
                            {
                                "count": 1,
                                "label": "YTD",
                                "step": "year",
                                "stepmode": "todate",
                            },
                            {"count": 1, "label": "1Y", "step": "year"},
                            {"label": "Todo", "step": "all"},
                        ]
                    },
                },
                hovermode="x unified",
                height=500,
                margin={"l": 0, "r": 0, "t": 10, "b": 0},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay datos históricos para este periodo.")
