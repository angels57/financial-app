"""Tab de cálculo de precios de compra y futuros."""

import streamlit as st

from models import StockInfo
from ui.base_tab import BaseTab


class PricesTab(BaseTab):
    """Calcula precios de compra y futuros según múltiplos financieros."""

    def render(self, *, info: StockInfo, **kwargs) -> None:
        t = info.ticker
        ps, pfcf, ventas, fcf, per_default, beneficios_default = self._render_inputs(
            info, t
        )
        buy_prices = self._render_buy_prices(
            ps, pfcf, ventas, fcf, per_default, beneficios_default, info, t
        )

        st.markdown("---")
        future_avg = self._render_future_prices(per_default, ps, pfcf, info, t)

        st.markdown("---")
        self._render_returns(info.price, future_avg, info.dividend_yield, t)

        st.markdown("---")
        self._render_fair_value_comparison(buy_prices, info.price, t)

    def _render_inputs(self, info: StockInfo, t: str) -> tuple:
        st.subheader("Datos Fundamentales")

        ps_default = float(info.price_to_sales or 0)
        pfcf_default = float(info.price_to_fcf or 0)
        ventas_default = float((info.total_revenue or 0) / 1e6)
        fcf_default = float((info.free_cash_flow or 0) / 1e6)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Ratios Promedio**")
            ps = st.number_input(
                "P/S promedio",
                value=ps_default,
                min_value=0.0,
                format="%.2f",
                key=f"ps_{t}",
            )
            pfcf = st.number_input(
                "P/FCF promedio",
                value=pfcf_default,
                min_value=0.0,
                format="%.2f",
                key=f"pfcf_{t}",
            )

        with col2:
            st.markdown("**Datos Actuales (M)**")
            ventas = st.number_input(
                "Ventas (M)",
                value=ventas_default,
                min_value=0.0,
                format="%.2f",
                key=f"ventas_{t}",
            )
            fcf = st.number_input(
                "Flujo de Caja (M)",
                value=fcf_default,
                format="%.2f",
                key=f"fcf_{t}",
            )

        per_default = float(info.pe_ratio or 0)
        beneficios_default = float((info.net_income or 0) / 1e6)

        return ps, pfcf, ventas, fcf, per_default, beneficios_default

    def _render_buy_prices(
        self,
        ps: float,
        pfcf: float,
        ventas: float,
        fcf: float,
        per_default: float,
        beneficios_default: float,
        info: StockInfo,
        t: str,
    ) -> float:
        st.subheader("Precios de Compra según Ratios")

        shares_default = float((info.shares_outstanding or 0) / 1e6)
        shares = st.number_input(
            "Acciones en circulación (M)",
            value=shares_default,
            min_value=0.0,
            format="%.2f",
            key=f"shares_{t}",
        )

        col1, col2, col3 = st.columns([2, 1, 1])

        per_input = col2.empty()
        ben_input = col2.empty()

        with col1:
            metric_per = st.empty()
            metric_ps = st.empty()
            metric_fcf = st.empty()
            st.markdown("---")
            metric_promedio = st.empty()

        with col2:
            per = per_input.number_input(
                "PER promedio",
                value=per_default,
                min_value=0.0,
                format="%.2f",
                key=f"per_{t}",
            )
            beneficios = ben_input.number_input(
                "Beneficios (M)",
                value=beneficios_default,
                format="%.2f",
                key=f"beneficios_{t}",
            )

        with col3:
            st.markdown("")

        precio_per = (beneficios / shares) * per if shares > 0 and per > 0 else 0
        precio_ps = (ventas / shares) * ps if shares > 0 and ps > 0 else 0
        precio_fcf = (fcf / shares) * pfcf if shares > 0 and pfcf > 0 else 0

        precios = [p for p in [precio_per, precio_ps, precio_fcf] if p > 0]
        promedio = sum(precios) / len(precios) if precios else 0

        metric_per.metric("Según PER", f"${precio_per:,.1f}" if precio_per else "N/A")
        metric_ps.metric("Según Ventas", f"${precio_ps:,.1f}" if precio_ps else "N/A")
        metric_fcf.metric("Según FCF", f"${precio_fcf:,.1f}" if precio_fcf else "N/A")
        metric_promedio.metric("PROMEDIO", f"${promedio:,.1f}" if promedio else "N/A")

        with col3:
            st.markdown("**Fórmulas**")
            st.markdown("**PER:**")
            st.latex(
                r"\frac{\text{Beneficios}}{\text{Acciones}} \times \text{PER promedio}"
            )
            st.caption(
                f"({beneficios:.2f}M / {shares:.2f}M) × {per:.2f} = ${precio_per:,.2f}"
            )

            st.markdown("**P/S:**")
            st.latex(
                r"\frac{\text{Ventas}}{\text{Acciones}} \times \text{P/S promedio}"
            )
            st.caption(
                f"({ventas:.2f}M / {shares:.2f}M) × {ps:.2f} = ${precio_ps:,.2f}"
            )

            st.markdown("**P/FCF:**")
            st.latex(r"\frac{\text{FCF}}{\text{Acciones}} \times \text{P/FCF promedio}")
            st.caption(
                f"({fcf:.2f}M / {shares:.2f}M) × {pfcf:.2f} = ${precio_fcf:,.2f}"
            )

            st.markdown("---")
            st.markdown("**PROMEDIO:**")
            st.latex(r"\frac{\text{PER} + \text{P/S} + \text{P/FCF}}{3}")
            precios_calc = [p for p in [precio_per, precio_ps, precio_fcf] if p > 0]
            promedio_calc = sum(precios_calc) / len(precios_calc) if precios_calc else 0
            st.caption(
                f"(${precio_per:,.2f} + ${precio_ps:,.2f} + ${precio_fcf:,.2f}) / 3 = ${promedio_calc:,.2f}"
            )

        return promedio

    def _render_future_prices(
        self,
        per: float,
        ps: float,
        pfcf: float,
        info: StockInfo,
        t: str = "",
    ) -> float:
        st.subheader("Precios Futuros (Proyección)")

        shares = st.session_state.get(f"shares_{t}", 0.0)

        col1, col2, col3 = st.columns(3)
        with col1:
            ben_futuro = st.number_input(
                "Beneficios futuros (M)",
                value=0.0,
                format="%.2f",
                key=f"ben_futuro_{t}",
            )
        with col2:
            ventas_futuro = st.number_input(
                "Ventas futuras (M)",
                value=0.0,
                min_value=0.0,
                format="%.2f",
                key=f"ventas_futuro_{t}",
            )
        with col3:
            fcf_futuro = st.number_input(
                "Flujo de Caja futuro (M)",
                value=0.0,
                format="%.2f",
                key=f"fcf_futuro_{t}",
            )

        precio_eps = (ben_futuro / shares) * per if shares > 0 and per > 0 else 0
        precio_ventas = (ventas_futuro / shares) * ps if shares > 0 and ps > 0 else 0
        precio_fcf = (fcf_futuro / shares) * pfcf if shares > 0 and pfcf > 0 else 0

        precios = [p for p in [precio_eps, precio_ventas, precio_fcf] if p > 0]
        promedio = sum(precios) / len(precios) if precios else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Según EPS", f"${precio_eps:,.1f}" if precio_eps else "N/A")
        c2.metric("Según Ventas", f"${precio_ventas:,.1f}" if precio_ventas else "N/A")
        c3.metric("Según FCF", f"${precio_fcf:,.1f}" if precio_fcf else "N/A")
        c4.metric("PROMEDIO", f"${promedio:,.1f}" if promedio else "N/A")

        return promedio

    def _render_returns(
        self,
        precio_compra: float,
        precio_futuro: float,
        dividend_yield: float | None,
        t: str = "",
    ) -> None:
        st.subheader("Rentabilidad Esperada")

        col1, col2 = st.columns(2)
        with col1:
            horizonte = st.slider(
                "Horizonte de inversión (años)",
                min_value=1,
                max_value=10,
                value=5,
                key=f"horizonte_{t}",
            )
        with col2:
            div_yield = st.number_input(
                "Dividend Yield (%)",
                value=(dividend_yield or 0) * 100,
                min_value=0.0,
                format="%.2f",
                key=f"div_yield_{t}",
            )

        if precio_compra > 0 and precio_futuro > 0:
            rentabilidad = ((precio_futuro - precio_compra) / precio_compra) * 100
            r_anualizada = ((1 + rentabilidad / 100) ** (1 / horizonte) - 1) * 100
            retorno_total = r_anualizada + div_yield

            c1, c2, c3 = st.columns(3)
            c1.metric("Rentabilidad Total", f"{rentabilidad:,.2f}%")
            c2.metric("R. Anualizada", f"{r_anualizada:,.2f}%", f"{horizonte} años")
            c3.metric(
                "Retorno Total", f"{retorno_total:,.2f}%", f"+{div_yield:.2f}% div"
            )
        else:
            st.info("Ingresa datos de precios futuros para calcular la rentabilidad.")

    def _render_fair_value_comparison(
        self, precio_promedio: float, precio_actual: float, t: str = ""
    ) -> None:
        st.subheader("Comparación con Fair Values Externos")
        if t:
            st.link_button(
                "📊 Ver en InvestingPro",
                f"https://www.investing.com/pro/{t.lower()}",
                use_container_width=False,
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            fv_investing = st.number_input(
                "InvestingPro Fair Value",
                value=0.0,
                min_value=0.0,
                format="%.2f",
                key=f"fv_investing_{t}",
            )
        with col2:
            fv_guru = st.number_input(
                "GuruFocus Fair Value",
                value=0.0,
                min_value=0.0,
                format="%.2f",
                key=f"fv_guru_{t}",
            )
        with col3:
            fv_alpha = st.number_input(
                "AlphaSpread Fair Value",
                value=0.0,
                min_value=0.0,
                format="%.2f",
                key=f"fv_alpha_{t}",
            )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Mi Cálculo", f"${precio_promedio:,.1f}" if precio_promedio else "N/A"
        )
        c2.metric("InvestingPro", f"${fv_investing:,.1f}" if fv_investing else "—")
        c3.metric("GuruFocus", f"${fv_guru:,.1f}" if fv_guru else "—")
        c4.metric("AlphaSpread", f"${fv_alpha:,.1f}" if fv_alpha else "—")

        if precio_promedio > 0 and precio_actual > 0:
            diff = ((precio_actual - precio_promedio) / precio_promedio) * 100

            if diff < -10:
                st.success(
                    f"Oportunidad de compra ({diff:+.1f}% por debajo del precio justo)"
                )
            elif diff <= 0:
                st.warning(f"Precio razonable ({diff:+.1f}% respecto al precio justo)")
            else:
                st.error(f"Le falta caer {diff:.1f}% para llegar al precio justo")
