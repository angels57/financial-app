"""Tab de resumen general."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from models import StockInfo
from services.protocols import StockDataFetcherProtocol
from ui.base_tab import BaseTab
from utils import format_large_number


class SummaryTab(BaseTab):
    """Renderiza el tab de resumen con precio, métricas y historial."""

    def render(
        self,
        *,
        stock_service: StockDataFetcherProtocol,
        info: StockInfo,
        period: str,
        **kwargs: object,
    ) -> None:
        self._render_price_metrics(info)
        st.markdown("---")
        self._render_market_metrics(info)
        st.markdown("---")
        self._render_company_profile(info)
        st.markdown("---")
        self._render_valuation_metrics(info)
        self._render_price_history(stock_service, info.currency, period)
        st.markdown("---")
        self._render_external_links(info)

    def _render_price_metrics(self, info: StockInfo) -> None:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric("Precio Actual", f"{info.currency} {info.price:,.2f}")

        with col2:
            self._render_52_week_range(info)

    def _render_52_week_range(self, info: StockInfo) -> None:
        low = info.week_52_low
        high = info.week_52_high

        if not low or not high or high == low:
            st.caption("Rango 52 semanas no disponible")
            return

        pct = ((info.price - low) / (high - low)) * 100
        pct = max(0.0, min(100.0, pct))

        bar_color = "#2ca02c" if pct < 70 else "#ff7f0e" if pct < 90 else "#d62728"

        st.caption("Rango 52 Semanas")
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:8px; font-size:0.85em;">
                <span>{info.currency} {low:,.2f}</span>
                <div style="flex:1; position:relative; height:8px;
                            background:#e0e0e0; border-radius:4px;">
                    <div style="width:{pct:.1f}%; height:100%;
                                background:{bar_color}; border-radius:4px;"></div>
                    <div style="position:absolute; top:-3px; left:calc({pct:.1f}% - 7px);
                                width:14px; height:14px; background:{bar_color};
                                border:2px solid white; border-radius:50%;
                                box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>
                </div>
                <span>{info.currency} {high:,.2f}</span>
            </div>
            <div style="text-align:center; font-size:0.8em; margin-top:4px; color:#666;">
                {info.currency} {info.price:,.2f} — {pct:.0f}% del rango
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _render_market_metrics(self, info: StockInfo) -> None:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Market Cap", format_large_number(info.market_cap, info.currency))
        c2.metric("P/E Ratio", f"{info.pe_ratio:.2f}" if info.pe_ratio else "N/A")
        c3.metric("P/S", f"{info.price_to_sales:.2f}" if info.price_to_sales else "N/A")
        c4.metric("P/FCF", f"{info.price_to_fcf:.2f}" if info.price_to_fcf else "N/A")
        c5.metric("Volumen", f"{info.volume:,.0f}")

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

    def _render_company_profile(self, info: StockInfo) -> None:
        st.subheader("Perfil de la Empresa")
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

        with col_desc:
            if info.description:
                preview = info.description[:300]
                st.markdown(f"{preview}...")
                with st.expander("Ver descripción completa"):
                    st.write(info.description)
            else:
                st.info("Descripción no disponible.")

    def _render_valuation_metrics(self, info: StockInfo) -> None:
        st.subheader("Valuación & Trading")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "EPS", f"{info.currency} {info.eps:.2f}" if info.eps is not None else "N/A"
        )
        c2.metric("Beta", f"{info.beta:.2f}" if info.beta is not None else "N/A")
        c3.metric(
            "Dividend Yield",
            f"{info.dividend_yield * 100:.2f}%"
            if info.dividend_yield is not None
            else "N/A",
        )
        c4.metric(
            "Target Price",
            f"{info.currency} {info.target_price:,.2f}"
            if info.target_price is not None
            else "N/A",
            info.recommendation.upper() if info.recommendation else None,
        )

    def _render_price_history(
        self,
        stock_service: StockDataFetcherProtocol,
        currency: str,
        period: str,
    ) -> None:
        st.subheader(f"Historial de Precios ({period})")
        hist = stock_service.get_history(period=period)
        if not hist.empty:
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.75, 0.25],
            )

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
                ),
                row=1,
                col=1,
            )

            if "Volume" in hist.columns:
                fig.add_trace(
                    go.Bar(
                        x=hist.index,
                        y=hist["Volume"],
                        name="Volumen",
                        marker_color="rgba(31,119,180,0.3)",
                        hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f}<extra></extra>",
                    ),
                    row=2,
                    col=1,
                )

            fig.update_layout(
                xaxis2={
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
                    "rangeslider": {"visible": True},
                },
                yaxis_title=f"Precio ({currency})",
                yaxis2_title="Volumen",
                hovermode="x unified",
                height=600,
                margin={"l": 0, "r": 0, "t": 10, "b": 0},
                showlegend=False,
            )

            st.plotly_chart(fig, width="stretch")
        else:
            st.warning("No hay datos históricos para este periodo.")
