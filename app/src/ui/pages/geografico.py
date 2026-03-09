"""
Página: Análisis Geográfico.
Informes 6.8 (Jurisdicción), 6.9 (Unidad Regional).
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator
from app.config.settings import UNIDADES_REGIONALES
from app.src.ui.editorial import close_stage, open_stage, render_hero, render_panel, render_section_heading

def _dataframe_height(row_count: int, base: int = 38, header: int = 38, padding: int = 6, maximum: int = 600) -> int:
    """Calcula una altura ajustada al contenido para evitar filas vacías."""
    visible_rows = max(row_count, 1)
    return min(header + (visible_rows * base) + padding, maximum)


def render():
    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    render_hero(
        "Territorio y despliegue",
        "Análisis geográfico",
        "Visualiza cómo se reparte la presión delictual por unidad regional y jurisdicción para una lectura territorial clara.",
        chips=["Unidades regionales", "Ranking de jurisdicciones", "Exportación territorial"],
        seq=1,
    )

    mostrar_metricas_header(engine)
    st.divider()

    df_ur_preview = engine.delitos_por_unidad_regional()
    ur_top = df_ur_preview.iloc[0]["categoria_label"] if len(df_ur_preview) else "Sin dato"
    render_section_heading(
        2,
        "Lectura principal",
        "Territorio dominante",
        "La apertura identifica qué unidad regional concentra más hechos antes de pasar al detalle por pestañas.",
    )
    render_panel(
        2,
        "Síntesis territorial",
        "Unidad regional líder",
        f"La mayor concentración observada se ubica en {ur_top} dentro de la selección filtrada.",
        tone="accent",
    )

    open_stage(
        3,
        "Escena analítica",
        "Distribución espacial",
        "Primero se contrasta el peso por unidad regional y después se baja al ranking de jurisdicciones.",
        stage_class="analysis-stage",
    )
    tab_ur, tab_juris = st.tabs([
        "🏛️ Por Unidad Regional",
        "📍 Por Jurisdicción",
    ])

    # ---- Unidad Regional ----
    with tab_ur:
        st.markdown("### Distribución por unidad regional")
        df_ur = engine.delitos_por_unidad_regional()

        if len(df_ur) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                fig = charts.dona(df_ur, "Distribución por Unidad Regional")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = charts.barras_horizontal(
                    df_ur, "Ranking por Unidad Regional",
                    color="#2563EB",
                )
                st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.markdown("#### Detalle ejecutivo")
            display = df_ur[["categoria", "categoria_label", "cantidad", "porcentaje"]].copy()
            display.columns = ["Código", "Unidad Regional", "Cantidad", "%"]
            display["Cantidad"] = display["Cantidad"].astype(int)
            display["%"] = display["%"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display, hide_index=True, use_container_width=True)

    # ---- Jurisdicción ----
    with tab_juris:
        st.markdown("### Ranking de jurisdicciones")
        top_n = st.slider("Cantidad de jurisdicciones a mostrar", 10, 50, 20, key="top_juris")
        df_juris = engine.delitos_por_jurisdiccion(top_n=top_n)

        if len(df_juris) == 0:
            st.warning("Sin datos disponibles")
        else:
            fig = charts.barras_horizontal(
                df_juris,
                f"Top {top_n} Jurisdicciones con más Delitos",
                color="#4472C4",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Tabla de jurisdicciones con filtro por UR
            st.markdown("#### Detalle por jurisdicción")
            ur_filter = st.selectbox(
                "Filtrar por Unidad Regional",
                ["Todas"] + list(UNIDADES_REGIONALES.keys()),
                key="ur_filter_juris",
            )

            df_juris_all = engine.delitos_por_jurisdiccion(top_n=200)
            if ur_filter != "Todas":
                df_juris_all = df_juris_all[
                    df_juris_all["categoria"].str.startswith(ur_filter)
                ]

            display = df_juris_all[["categoria_label", "cantidad", "porcentaje"]].copy()
            display.columns = ["Jurisdicción", "Cantidad", "%"]
            display["Cantidad"] = display["Cantidad"].astype(int)
            display["%"] = display["%"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display, hide_index=True, use_container_width=True,
                          height=min(len(display) * 35 + 50, 600))

    close_stage()

    st.divider()
    render_section_heading(
        4,
        "Cruce territorial",
        "Mapa de calor por regional y delito",
        "La vista cruza territorio y modalidad para ubicar dónde se concentra cada familia delictiva dominante sin depender solo del ranking general.",
    )
    open_stage(
        4,
        "Profundización",
        "Intensidad territorial cruzada",
        "El heatmap resume la presión por unidad regional y modalidad, mientras el panel lateral destaca la combinación más intensa del recorte actual.",
        stage_class="analysis-stage",
    )

    top_modalidades = st.slider(
        "Modalidades visibles en la matriz territorial",
        min_value=4,
        max_value=12,
        value=8,
        key="top_modalidades_heatmap_geo",
    )
    pivot_geo = engine.matriz_unidad_regional_delito(top_n_delitos=top_modalidades)

    if pivot_geo.empty:
        st.info("Sin datos suficientes para construir el cruce territorial por modalidad.")
    else:
        col_geo_1, col_geo_2 = st.columns([1.8, 1])
        with col_geo_1:
            fig = charts.heatmap(pivot_geo, "Intensidad territorial por unidad regional y modalidad", height=500)
            st.plotly_chart(fig, use_container_width=True)

        with col_geo_2:
            valor_maximo = int(pivot_geo.to_numpy().max())
            ur_max, delito_max = pivot_geo.stack().idxmax()
            st.markdown("#### Lectura rápida")
            st.markdown(
                f"""
                **Mayor concentración territorial:**
                - Regional: **{ur_max}**
                - Modalidad: **{delito_max}**
                - Hechos: **{valor_maximo:,}**
                """
            )

            display_geo = pivot_geo.copy()
            display_geo.insert(0, "Unidad Regional", display_geo.index)
            st.dataframe(
                display_geo,
                hide_index=True,
                use_container_width=True,
                height=_dataframe_height(len(display_geo), base=35, header=40, padding=8, maximum=420),
            )

    close_stage()

    # ---- Exportar ----
    st.divider()
    render_section_heading(
        5,
        "Cierre documental",
        "Exportación geográfica",
        "Cierra el recorrido con archivos directos para unidades regionales y jurisdicciones.",
    )
    open_stage(
        5,
        "Archivos finales",
        "Descargas territoriales",
        "Los archivos se generan desde la misma base filtrada para conservar coherencia con la vista.",
        stage_class="export-stage",
    )
    st.markdown("### Descarga documental")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        csv = engine.delitos_por_unidad_regional().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Unidades Regionales (CSV)", csv,
                           "delitos_por_ur.csv", "text/csv")
    with col_e2:
        csv = engine.delitos_por_jurisdiccion(top_n=200).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Jurisdicciones (CSV)", csv,
                           "delitos_por_jurisdiccion.csv", "text/csv")
    with col_e3:
        csv = engine.matriz_unidad_regional_delito(top_n_delitos=top_modalidades).reset_index(names="Unidad Regional").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Regional vs delito (CSV)", csv,
                           "matriz_unidad_regional_delito.csv", "text/csv")
    close_stage()
