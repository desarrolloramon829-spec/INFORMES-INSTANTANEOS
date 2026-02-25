"""
Página: Análisis Geográfico.
Informes 6.8 (Jurisdicción), 6.9 (Unidad Regional).
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator
from app.config.settings import UNIDADES_REGIONALES


def render():
    st.title("🗺️ Análisis Geográfico")
    st.markdown("Distribución de delitos por jurisdicción y unidad regional")

    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    mostrar_metricas_header(engine)
    st.divider()

    tab_ur, tab_juris = st.tabs([
        "🏛️ Por Unidad Regional",
        "📍 Por Jurisdicción",
    ])

    # ---- Unidad Regional ----
    with tab_ur:
        st.markdown("### Delitos por Unidad Regional")
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
            st.markdown("#### Tabla detallada")
            display = df_ur[["categoria", "categoria_label", "cantidad", "porcentaje"]].copy()
            display.columns = ["Código", "Unidad Regional", "Cantidad", "%"]
            display["Cantidad"] = display["Cantidad"].astype(int)
            display["%"] = display["%"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display, hide_index=True, use_container_width=True)

    # ---- Jurisdicción ----
    with tab_juris:
        st.markdown("### Ranking de Jurisdicciones")
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
            st.markdown("#### Detalle por Jurisdicción")
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

    # ---- Exportar ----
    st.divider()
    st.markdown("### 📥 Exportar")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        csv = engine.delitos_por_unidad_regional().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Unidades Regionales (CSV)", csv,
                           "delitos_por_ur.csv", "text/csv")
    with col_e2:
        csv = engine.delitos_por_jurisdiccion(top_n=200).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Jurisdicciones (CSV)", csv,
                           "delitos_por_jurisdiccion.csv", "text/csv")
