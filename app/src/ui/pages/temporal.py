"""
Página: Análisis Temporal.
Informes 6.2 (Día semana), 6.3 (Franja horaria), 6.7 (Mes).
"""
import streamlit as st

from app.src.charts.generator import ChartGenerator
from app.src.ui.editorial import close_stage, open_stage, render_hero, render_panel, render_section_heading
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header


def _dataframe_height(row_count: int, base: int = 35, header: int = 40, padding: int = 8, maximum: int = 420) -> int:
    """Calcula una altura ajustada al contenido para evitar filas vacías al final."""
    visible_rows = max(row_count, 1)
    return min(header + (visible_rows * base) + padding, maximum)


def _granularidades_semanales() -> dict[str, str]:
    return {
        "Semanal": "semanas",
        "Bisemanal": "bisemanas",
        "Trisemanal": "trisemanas",
    }


def _granularidades_mensuales() -> dict[str, str]:
    return {
        "Mensual": "meses",
        "Bimensual": "bimestres",
        "Trimestral": "trimestres",
        "Cuatrimestral": "cuatrimestres",
        "Semestral": "semestres",
    }


def _filtrar_subserie_temporal(df, granularidad: str, key_prefix: str, limite_default: int = 16):
    if granularidad not in {"semanas", "bisemanas", "trisemanas", "dias"} or len(df) <= limite_default:
        return df

    etiqueta = {
        "semanas": "semanas",
        "bisemanas": "bisemanas",
        "trisemanas": "trisemanas",
        "dias": "días",
    }.get(granularidad, "periodos")

    inicio, fin = st.slider(
        f"Subconjunto visible de {etiqueta}",
        min_value=1,
        max_value=len(df),
        value=(1, min(limite_default, len(df))),
        key=f"{key_prefix}_subserie",
    )
    st.caption(f"Vista parcial: {inicio} a {fin} de {len(df)} {etiqueta}.")
    return df.iloc[inicio - 1:fin].copy()


def _tabla_simple(df, col1_name, col2_name, col3_name):
    """Tabla compacta con st.dataframe."""
    display = df[["categoria_label", "cantidad", "porcentaje"]].copy()
    display.columns = [col1_name, col2_name, col3_name]
    display[col2_name] = display[col2_name].astype(int)
    display[col3_name] = display[col3_name].apply(lambda x: f"{x:.1f}%")
    st.dataframe(display, hide_index=True, width="stretch")


def render():
    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    granularidades_semanales = _granularidades_semanales()
    granularidades_mensuales = _granularidades_mensuales()
    granularidad_semanal_actual = st.session_state.get("temporal_granularidad_semanal", "Semanal")
    granularidad_mensual_actual = st.session_state.get("temporal_granularidad_mensual", "Mensual")

    render_hero(
        "Cadencia temporal",
        "Análisis temporal",
        "Página orientada al ritmo operativo: días, franjas, semanas, meses y años para detectar dónde se concentra la actividad en el tiempo.",
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

    open_stage(
        4,
        "Escena analítica",
        "Exploración temporal",
        "Las pestañas ordenan la lectura temporal desde el patrón semanal fijo hasta la evolución por semanas, meses y años.",
        stage_class="analysis-stage",
    )
    tab_dia, tab_franja, tab_semana, tab_mes, tab_anio = st.tabs([
        "📅 Por Día de la Semana",
        "🕐 Por Franja Horaria",
        "🗓️ Por Semanas",
        "📆 Por Mes",
        "📊 Por Año",
    ])

    with tab_dia:
        st.markdown("### Distribución por día de la semana")
        df_dia = engine.delitos_por_dia_semana()

        if len(df_dia) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                fig = charts.barras_vertical(df_dia, "Distribución por Día de la Semana", color="#4472C4")
                st.plotly_chart(fig, width="stretch")

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

    with tab_franja:
        st.markdown("### Distribución por franja horaria")
        df_franja = engine.delitos_por_franja_horaria()

        if len(df_franja) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                fig = charts.barras_vertical(df_franja, "Distribución por Franja Horaria", color="#ED7D31")
                st.plotly_chart(fig, width="stretch")

            with col2:
                st.markdown("#### Detalle ejecutivo")
                _tabla_simple(df_franja, "Franja", "Cantidad", "%")
                max_f = df_franja.loc[df_franja["cantidad"].idxmax()]
                st.markdown(f"""
                **Lectura rápida:**
                - Franja más activa: **{max_f['categoria_label']}** ({int(max_f['cantidad']):,})
                """)

    with tab_semana:
        opciones_semanales = list(granularidades_semanales.keys())
        granularidad_semanal_label = st.selectbox(
            "Vista semanal",
            opciones_semanales,
            index=opciones_semanales.index(granularidad_semanal_actual) if granularidad_semanal_actual in opciones_semanales else 0,
            key="temporal_granularidad_semanal",
        )
        granularidad_semanal = granularidades_semanales[granularidad_semanal_label]
        st.markdown(f"### Distribución {granularidad_semanal_label.lower()} del año")
        df_semana = engine.delitos_por_semana(granularidad_semanal)

        if len(df_semana) == 0:
            st.warning("Sin datos con fecha válida")
        else:
            df_semana_view = _filtrar_subserie_temporal(df_semana, granularidad_semanal, "temporal_semanal")
            col1, col2 = st.columns([1.5, 1])
            with col1:
                fig = charts.barras_vertical(
                    df_semana_view,
                    f"Distribución {granularidad_semanal_label} de Delitos",
                    color="#9467BD",
                    height=520,
                )
                st.plotly_chart(fig, width="stretch")

            with col2:
                st.markdown("#### Detalle ejecutivo")
                _tabla_simple(df_semana_view, granularidad_semanal_label, "Cantidad", "%")
                max_semana = df_semana.loc[df_semana["cantidad"].idxmax()]
                st.markdown(f"""
                **Lectura rápida:**
                - Tramo más activo: **{max_semana['categoria_label']}** ({int(max_semana['cantidad']):,})
                - Tramos disponibles: **{len(df_semana):,}**
                """)

    with tab_mes:
        opciones_mensuales = list(granularidades_mensuales.keys())
        granularidad_mensual_label = st.selectbox(
            "Agrupación mensual",
            opciones_mensuales,
            index=opciones_mensuales.index(granularidad_mensual_actual) if granularidad_mensual_actual in opciones_mensuales else 0,
            key="temporal_granularidad_mensual",
        )
        granularidad_mensual = granularidades_mensuales[granularidad_mensual_label]
        st.markdown(f"### Distribución {granularidad_mensual_label.lower()} de delitos")
        if granularidad_mensual == "meses":
            df_mes = engine.delitos_por_mes()
        else:
            df_mes = engine.delitos_por_granularidad_temporal(granularidad_mensual)

        if len(df_mes) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                fig = charts.barras_vertical(
                    df_mes,
                    f"Distribución {granularidad_mensual_label} de Delitos",
                    color="#70AD47",
                )
                st.plotly_chart(fig, width="stretch")

            with col2:
                st.markdown("#### Detalle ejecutivo")
                _tabla_simple(df_mes, granularidad_mensual_label, "Cantidad", "%")

    with tab_anio:
        st.markdown("### Evolución por año")
        df_anio = engine.delitos_por_anio()

        if len(df_anio) == 0:
            st.warning("Sin datos con fecha válida")
        else:
            fig = charts.barras_vertical(
                df_anio,
                "Evolución Anual de Delitos",
                color="#5B9BD5",
                col_cat="categoria",
            )
            st.plotly_chart(fig, width="stretch")

            st.dataframe(
                df_anio.rename(columns={
                    "categoria": "Año",
                    "cantidad": "Cantidad",
                    "porcentaje": "%",
                }),
                hide_index=True,
                width="stretch",
            )

    close_stage()

    st.divider()
    render_section_heading(
        5,
        "Cruce operativo",
        "Mapa de calor día versus franja",
        "Esta matriz cruza ritmo semanal y ventana horaria para detectar concentraciones que no se ven cuando ambas dimensiones se leen por separado.",
    )
    open_stage(
        5,
        "Profundización",
        "Intensidad temporal cruzada",
        "El heatmap resume la carga por combinación de día y franja, mientras el bloque lateral destaca la intersección más intensa.",
        stage_class="analysis-stage",
    )

    pivot_dia_franja = engine.matriz_dia_franja()
    if pivot_dia_franja.empty:
        st.info("Sin datos suficientes para construir el mapa de calor día versus franja.")
    else:
        col_hm_1, col_hm_2 = st.columns([1.8, 1])
        with col_hm_1:
            fig = charts.heatmap(pivot_dia_franja, "Intensidad de delitos por día y franja horaria", height=520)
            st.plotly_chart(fig, width="stretch")

        with col_hm_2:
            valor_maximo = int(pivot_dia_franja.to_numpy().max())
            dia_max, franja_max = pivot_dia_franja.stack().idxmax()
            st.markdown("#### Lectura rápida")
            st.markdown(
                f"""
                **Mayor concentración:**
                - Día: **{dia_max}**
                - Franja: **{franja_max.replace(chr(10), ' / ')}**
                - Hechos: **{valor_maximo:,}**
                """
            )

            display_heatmap = pivot_dia_franja.copy()
            display_heatmap.insert(0, "Día", display_heatmap.index)
            st.dataframe(
                display_heatmap,
                hide_index=True,
                width="stretch",
                height=_dataframe_height(len(display_heatmap)),
            )

    close_stage()

    st.divider()
    render_section_heading(
        6,
        "Cierre documental",
        "Exportación temporal",
        "Las salidas se mantienen separadas por dimensión para reutilizar el análisis semanal, horario o mensual sin reprocesar la vista.",
    )
    open_stage(
        6,
        "Archivos finales",
        "Descargas por dimensión",
        "Cada botón exporta la estructura limpia de la dimensión temporal elegida.",
        stage_class="export-stage",
    )
    st.markdown("### Descarga documental")

    granularidad_semanal_export = granularidades_semanales[st.session_state.get("temporal_granularidad_semanal", "Semanal")]
    granularidad_mensual_export = granularidades_mensuales[st.session_state.get("temporal_granularidad_mensual", "Mensual")]
    df_semanal_export = engine.delitos_por_semana(granularidad_semanal_export)
    if granularidad_mensual_export == "meses":
        df_mensual_export = engine.delitos_por_mes()
    else:
        df_mensual_export = engine.delitos_por_granularidad_temporal(granularidad_mensual_export)

    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        csv_dia = engine.delitos_por_dia_semana().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Días de la semana (CSV)", csv_dia, "delitos_dia_semana.csv", "text/csv")
    with col_e2:
        csv_franja = engine.delitos_por_franja_horaria().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Franjas horarias (CSV)", csv_franja, "delitos_franja_horaria.csv", "text/csv")
    with col_e3:
        csv_semana = df_semanal_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"⬇️ {st.session_state.get('temporal_granularidad_semanal', 'Semanal')} (CSV)",
            csv_semana,
            f"delitos_{granularidad_semanal_export}.csv",
            "text/csv",
        )

    col_e4, col_e5, col_e6 = st.columns(3)
    with col_e4:
        csv_mes = df_mensual_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"⬇️ {st.session_state.get('temporal_granularidad_mensual', 'Mensual')} (CSV)",
            csv_mes,
            f"delitos_{granularidad_mensual_export}.csv",
            "text/csv",
        )
    with col_e5:
        csv_anio = engine.delitos_por_anio().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Años (CSV)", csv_anio, "delitos_por_anio.csv", "text/csv")
    with col_e6:
        matriz_csv = engine.matriz_dia_franja().reset_index(names="Día").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Día vs franja (CSV)", matriz_csv, "matriz_dia_franja.csv", "text/csv")

    close_stage()