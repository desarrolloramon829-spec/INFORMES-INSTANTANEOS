"""
Página: Análisis Temporal.
Informes 6.2 (Día semana), 6.3 (Franja horaria), 6.7 (Mes).
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator
from app.src.ui.editorial import close_stage, open_stage, render_hero, render_panel, render_section_heading


def render():
    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    render_hero(
        "Cadencia temporal",
        "Análisis temporal",
        "Página orientada al ritmo operativo: días, franjas, meses y años para detectar dónde se concentra la actividad en el tiempo.",
        chips=["Lectura semanal", "Ventanas horarias", "Evolución mensual y anual"],
        seq=1,
    )

    mostrar_metricas_header(engine)
    st.divider()

    df_dia_preview = engine.delitos_por_dia_semana()
    df_franja_preview = engine.delitos_por_franja_horaria()
    df_mes_preview = engine.delitos_por_mes()
    hallazgo_dia = df_dia_preview.iloc[0]["categoria_label"] if len(df_dia_preview) else "Sin dato"
    hallazgo_franja = df_franja_preview.iloc[0]["categoria_label"] if len(df_franja_preview) else "Sin dato"
    hallazgo_mes = df_mes_preview.iloc[0]["categoria_label"] if len(df_mes_preview) else "Sin dato"

    render_section_heading(
        2,
        "Lectura principal",
        "Pulso operativo resumido",
        "Antes de abrir las pestañas, la página fija el día, la franja y el mes con mayor presión en la selección activa.",
    )
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        render_panel(2, "Semana", "Día con mayor carga", f"El pico semanal se registra en {hallazgo_dia}.", tone="accent")
    with col_p2:
        render_panel(3, "Horario", "Franja dominante", f"La mayor intensidad operativa aparece en {hallazgo_franja}.")
    with col_p3:
        render_panel(4, "Mes", "Mes más cargado", f"El volumen mensual más alto se concentra en {hallazgo_mes}.", tone="success")

    # =====================================================
    # Pestañas para cada dimensión temporal
    # =====================================================
    open_stage(
        4,
        "Escena analítica",
        "Exploración temporal",
        "Las pestañas ordenan la lectura temporal desde la semana y el horario hasta la evolución anual.",
        stage_class="analysis-stage",
    )
    tab_dia, tab_franja, tab_mes, tab_anio = st.tabs([
        "📅 Por Día de la Semana",
        "🕐 Por Franja Horaria",
        "📆 Por Mes",
        "📊 Por Año",
    ])

    # ---- Pestaña: Día de la Semana ----
    with tab_dia:
        st.markdown("### Distribución por día de la semana")
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
                st.markdown("#### Detalle ejecutivo")
                _tabla_simple(df_dia, "Día", "Cantidad", "%")

                max_dia = df_dia.loc[df_dia["cantidad"].idxmax()]
                min_dia = df_dia.loc[df_dia["cantidad"].idxmin()]
                st.markdown(f"""
                **Lectura rápida:**
                - Día con más delitos: **{max_dia['categoria_label']}** ({int(max_dia['cantidad']):,})
                - Día con menos delitos: **{min_dia['categoria_label']}** ({int(min_dia['cantidad']):,})
                """)

    # ---- Pestaña: Franja Horaria ----
    with tab_franja:
        st.markdown("### Distribución por franja horaria")
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
                st.markdown("#### Detalle ejecutivo")
                _tabla_simple(df_franja, "Franja", "Cantidad", "%")

                max_f = df_franja.loc[df_franja["cantidad"].idxmax()]
                st.markdown(f"""
                **Lectura rápida:**
                - Franja más activa: **{max_f['categoria_label']}** ({int(max_f['cantidad']):,})
                """)

    # ---- Pestaña: Mes ----
    with tab_mes:
        st.markdown("### Distribución por mes")
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
                st.markdown("#### Detalle ejecutivo")
                _tabla_simple(df_mes, "Mes", "Cantidad", "%")

    # ---- Pestaña: Año ----
    with tab_anio:
        st.markdown("### Evolución por año")
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

    close_stage()

    # ---- Exportar ----
    st.divider()
    render_section_heading(
        5,
        "Cierre documental",
        "Exportación temporal",
        "Las salidas se mantienen separadas por dimensión para reutilizar el análisis semanal, horario o mensual sin reprocesar la vista.",
    )
    open_stage(
        5,
        "Archivos finales",
        "Descargas por dimensión",
        "Cada botón exporta la estructura limpia de la dimensión temporal elegida.",
        stage_class="export-stage",
    )
    st.markdown("### Descarga documental")
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
    close_stage()


def _tabla_simple(df, col1_name, col2_name, col3_name):
    """Tabla compacta con st.dataframe."""
    display = df[["categoria_label", "cantidad", "porcentaje"]].copy()
    display.columns = [col1_name, col2_name, col3_name]
    display[col2_name] = display[col2_name].astype(int)
    display[col3_name] = display[col3_name].apply(lambda x: f"{x:.1f}%")
    st.dataframe(display, hide_index=True, use_container_width=True)
