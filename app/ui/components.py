"""Componentes UI reutilizables para el dashboard."""

import streamlit as st


def render_diff_badge(diff: float, label: str = "upside") -> None:
    """
    Renderiza una etiqueta de diferencia con colores.

    Verde: diff > 0 (precio necesita subir para alcanzar fair value = oportunidad)
    Rojo: diff < 0 (precio está por encima del fair value = sobrevalorado)

    Args:
        diff: Porcentaje de diferencia (upside o downside)
        label: Etiqueta a mostrar (default: "upside")
    """
    color = "green" if diff > 0 else "red"
    st.markdown(
        f'<span style="color:{color}; font-size:0.9em;">{label}: {diff:+.1f}%</span>',
        unsafe_allow_html=True,
    )
