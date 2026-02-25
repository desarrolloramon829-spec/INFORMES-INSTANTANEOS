"""
Página: Características del Hecho.
Informes 6.4 (Movilidad), 6.5 (Armas), 6.6 (Ámbito), 6.10 (Modus operandi), 6.11 (Resueltos).
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator


def render():
    st.title("🔍 Características del Hecho")
    st.markdown("Análisis de movilidad, armas, ámbito, modus operandi y resolución")

    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    mostrar_metricas_header(engine)
    st.divider()

    tab_movil, tab_armas, tab_ambito, tab_modus, tab_resueltos = st.tabs([
        "🚗 Movilidad",
        "🔫 Armas",
        "📍 Ámbito",
        "🎯 Modus Operandi",
        "✅ Hechos Resueltos",
    ])

    # ---- Movilidad ----
    with tab_movil:
        st.markdown("### Medios de Movilidad Utilizados")
        df_movil = engine.medios_movilidad()
        if len(df_movil) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                fig = charts.barras_horizontal(
                    df_movil, "Medios de Movilidad",
                    color="#5B9BD5",
                )
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("#### Detalle")
                _mostrar_tabla(df_movil)

    # ---- Armas ----
    with tab_armas:
        st.markdown("### Armas Utilizadas")
        df_armas = engine.armas_utilizadas()
        if len(df_armas) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                fig = charts.barras_horizontal(
                    df_armas, "Armas Utilizadas en Hechos Delictivos",
                    color="#CC0000",
                )
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("#### Detalle")
                _mostrar_tabla(df_armas)

    # ---- Ámbito ----
    with tab_ambito:
        st.markdown("### Ámbito de Ocurrencia")
        df_ambito = engine.ambito_ocurrencia()
        if len(df_ambito) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                fig = charts.dona(df_ambito, "Distribución por Ámbito")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = charts.barras_horizontal(
                    df_ambito, "Delitos por Ámbito de Ocurrencia",
                    color="#70AD47",
                )
                st.plotly_chart(fig, use_container_width=True)

    # ---- Modus Operandi ----
    with tab_modus:
        st.markdown("### Modus Operandi más Frecuentes")
        top_n = st.slider("Cantidad a mostrar", 5, 30, 15)
        df_modus = engine.modus_operandi(top_n=top_n)
        if len(df_modus) == 0:
            st.warning("Sin datos disponibles")
        else:
            fig = charts.barras_horizontal(
                df_modus, f"Top {top_n} Modus Operandi",
                color="#9B59B6",
            )
            st.plotly_chart(fig, use_container_width=True)

    # ---- Hechos Resueltos ----
    with tab_resueltos:
        st.markdown("### Estado de Resolución de Hechos")
        df_resueltos = engine.hechos_resueltos()
        if len(df_resueltos) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                fig = charts.dona(df_resueltos, "Proporción de Hechos Resueltos")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("#### Detalle")
                _mostrar_tabla(df_resueltos)

                total = df_resueltos["cantidad"].sum()
                resueltos = df_resueltos[
                    df_resueltos["categoria"].str.upper() == "SI"
                ]["cantidad"].sum()
                pct_resueltos = (resueltos / total * 100) if total > 0 else 0

                if pct_resueltos >= 50:
                    st.success(f"Tasa de resolución: **{pct_resueltos:.1f}%**")
                else:
                    st.warning(f"Tasa de resolución: **{pct_resueltos:.1f}%**")

    # ---- Exportar ----
    st.divider()
    st.markdown("### 📥 Exportar")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        csv = engine.medios_movilidad().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Movilidad (CSV)", csv, "movilidad.csv", "text/csv")
    with col_e2:
        csv = engine.armas_utilizadas().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Armas (CSV)", csv, "armas.csv", "text/csv")


def _mostrar_tabla(df):
    """Muestra tabla compacta en streamlit."""
    display = df[["categoria_label", "cantidad", "porcentaje"]].copy()
    display.columns = ["Categoría", "Cantidad", "%"]
    display["Cantidad"] = display["Cantidad"].astype(int)
    display["%"] = display["%"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(display, hide_index=True, use_container_width=True)
