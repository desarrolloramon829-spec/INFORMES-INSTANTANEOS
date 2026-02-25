"""
Página de inicio - Dashboard resumen.
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator


def render():
    st.title("🏠 Panel de Control — Mapa Delictual")
    st.markdown("**Sistema de informes estadísticos de delitos — Policía de Tucumán**")

    # Cargar y filtrar datos
    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    # Métricas principales
    mostrar_metricas_header(engine)
    st.divider()

    # Resumen rápido
    resumen = engine.resumen()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🔴 Delito más frecuente")
        st.info(f"**{resumen['delito_mas_frecuente']}**")

    with col2:
        st.markdown("### 📅 Día con más delitos")
        st.info(f"**{resumen['dia_mas_frecuente'].title() if resumen['dia_mas_frecuente'] != 'N/A' else 'N/A'}**")

    with col3:
        st.markdown("### 🕐 Franja más activa")
        franja = resumen["franja_mas_frecuente"]
        if franja and franja != "N/A":
            franja_display = franja.replace("_", " ").replace("(", "\n(")
        else:
            franja_display = "N/A"
        st.info(f"**{franja_display}**")

    st.divider()

    # Gráficos resumen
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Delitos por Modalidad")
        df_modal = engine.delitos_por_modalidad()
        if len(df_modal) > 0:
            fig = charts.barras_horizontal(df_modal, "Top Delitos por Modalidad")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sin datos para mostrar")

    with col_right:
        st.markdown("### Distribución por Día de la Semana")
        df_dia = engine.delitos_por_dia_semana()
        if len(df_dia) > 0:
            fig = charts.barras_vertical(df_dia, "Delitos por Día")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sin datos para mostrar")

    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.markdown("### Delitos por Franja Horaria")
        df_franja = engine.delitos_por_franja_horaria()
        if len(df_franja) > 0:
            fig = charts.barras_vertical(df_franja, "Distribución por Franja Horaria",
                                          color="#ED7D31")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sin datos para mostrar")

    with col_right2:
        st.markdown("### Delitos por Unidad Regional")
        df_ur = engine.delitos_por_unidad_regional()
        if len(df_ur) > 0:
            fig = charts.dona(df_ur, "Distribución por Unidad Regional")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sin datos para mostrar")

    # Años disponibles
    st.divider()
    st.markdown("### 📊 Datos disponibles")
    anios = resumen.get("anios_disponibles", [])
    if anios:
        st.success(f"Años con datos: **{', '.join(str(a) for a in anios)}** — Total de registros: **{engine.total_registros:,}**")
    else:
        st.info("No se encontraron datos con fecha válida.")
