"""
Página: Análisis Temporal.
Informes 6.2 (Día semana), 6.3 (Franja horaria), 6.7 (Mes).
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator
from app.config.settings import DIAS_LABELS, FRANJAS_LABELS, MESES_LABELS


def render():
    st.title("📅 Análisis Temporal")
    st.markdown("Distribución de delitos por día de la semana, franja horaria y mes")

    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    mostrar_metricas_header(engine)
    st.divider()

    # =====================================================
    # Pestañas para cada dimensión temporal
    # =====================================================
    tab_dia, tab_franja, tab_mes, tab_anio = st.tabs([
        "📅 Por Día de la Semana",
        "🕐 Por Franja Horaria",
        "📆 Por Mes",
        "📊 Por Año",
    ])

    # ---- Pestaña: Día de la Semana ----
    with tab_dia:
        st.markdown("### Delitos por Día de la Semana")
        df_dia = engine.delitos_por_dia_semana()

        if len(df_dia) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                fig = charts.barras_vertical(
                    df_dia, "Distribución por Día de la Semana",
                    color="#4472C4",
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### Tabla de datos")
                _tabla_simple(df_dia, "Día", "Cantidad", "%")

                max_dia = df_dia.loc[df_dia["cantidad"].idxmax()]
                min_dia = df_dia.loc[df_dia["cantidad"].idxmin()]
                st.markdown(f"""
                **Hallazgos:**
                - 🔴 Día con más delitos: **{max_dia['categoria_label']}** ({int(max_dia['cantidad']):,})
                - 🟢 Día con menos delitos: **{min_dia['categoria_label']}** ({int(min_dia['cantidad']):,})
                """)

    # ---- Pestaña: Franja Horaria ----
    with tab_franja:
        st.markdown("### Delitos por Franja Horaria")
        df_franja = engine.delitos_por_franja_horaria()

        if len(df_franja) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                fig = charts.barras_vertical(
                    df_franja, "Distribución por Franja Horaria",
                    color="#ED7D31",
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### Tabla de datos")
                _tabla_simple(df_franja, "Franja", "Cantidad", "%")

                max_f = df_franja.loc[df_franja["cantidad"].idxmax()]
                st.markdown(f"""
                **Hallazgos:**
                - 🔴 Franja más activa: **{max_f['categoria_label']}** ({int(max_f['cantidad']):,})
                """)

    # ---- Pestaña: Mes ----
    with tab_mes:
        st.markdown("### Delitos por Mes")
        df_mes = engine.delitos_por_mes()

        if len(df_mes) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                fig = charts.barras_vertical(
                    df_mes, "Distribución Mensual de Delitos",
                    color="#70AD47",
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### Tabla de datos")
                _tabla_simple(df_mes, "Mes", "Cantidad", "%")

    # ---- Pestaña: Año ----
    with tab_anio:
        st.markdown("### Delitos por Año")
        df_anio = engine.delitos_por_anio()

        if len(df_anio) == 0:
            st.warning("Sin datos con fecha válida")
        else:
            fig = charts.barras_vertical(
                df_anio, "Evolución Anual de Delitos",
                color="#5B9BD5",
                col_cat="categoria",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                df_anio.rename(columns={
                    "categoria": "Año",
                    "cantidad": "Cantidad",
                    "porcentaje": "%",
                }),
                hide_index=True,
                use_container_width=True,
            )

    # ---- Exportar ----
    st.divider()
    st.markdown("### 📥 Exportar Datos Temporales")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        csv_dia = engine.delitos_por_dia_semana().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Días de la semana (CSV)", csv_dia,
                           "delitos_dia_semana.csv", "text/csv")
    with col_e2:
        csv_franja = engine.delitos_por_franja_horaria().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Franjas horarias (CSV)", csv_franja,
                           "delitos_franja_horaria.csv", "text/csv")
    with col_e3:
        csv_mes = engine.delitos_por_mes().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Meses (CSV)", csv_mes,
                           "delitos_por_mes.csv", "text/csv")


def _tabla_simple(df, col1_name, col2_name, col3_name):
    """Tabla compacta con st.dataframe."""
    display = df[["categoria_label", "cantidad", "porcentaje"]].copy()
    display.columns = [col1_name, col2_name, col3_name]
    display[col2_name] = display[col2_name].astype(int)
    display[col3_name] = display[col3_name].apply(lambda x: f"{x:.1f}%")
    st.dataframe(display, hide_index=True, use_container_width=True)
