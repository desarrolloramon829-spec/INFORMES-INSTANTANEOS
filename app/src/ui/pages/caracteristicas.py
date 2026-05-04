"""
Página: Características del Hecho.
Informes 6.4 (Movilidad), 6.5 (Armas), 6.6 (Ámbito), 6.10 (Modus operandi), 6.11 (Resueltos).
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header, render_barras_con_toggle, render_boton_exportar
from app.src.charts.generator import ChartGenerator
from app.src.ui.editorial import close_stage, open_stage, render_hero, render_panel, render_section_heading, render_dataframe_as_html_table


def render():
    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    render_hero(
        "Contexto del hecho",
        "Características del hecho",
        "Integra medios de movilidad, armas, ámbito, modus operandi y resolución para describir cómo se configuran los hechos analizados.",
        chips=["Movilidad", "Armas y ámbito", "Resolución de hechos"],
        seq=1,
    )

    mostrar_metricas_header(engine)
    st.divider()

    df_modus_preview = engine.modus_operandi(top_n=1)
    modus_top = df_modus_preview.iloc[0]["categoria_label"] if len(df_modus_preview) else "Sin dato"
    render_section_heading(
        2,
        "Lectura principal",
        "Perfil resumido del hecho",
        "La apertura destaca el patrón operativo más repetido antes de desplegar las dimensiones en pestañas.",
    )
    render_panel(
        2,
        "Síntesis operativa",
        "Modus predominante",
        f"El patrón más recurrente dentro de la muestra filtrada es {modus_top}.",
        tone="accent",
    )

    open_stage(
        3,
        "Escena analítica",
        "Despiece del hecho",
        "Las pestañas ordenan la lectura desde los recursos utilizados y el ámbito hasta el cierre por resolución.",
        stage_class="analysis-stage",
    )
    tab_movil, tab_armas, tab_ambito, tab_modus, tab_resueltos = st.tabs([
        "🚗 Movilidad",
        "🔫 Armas",
        "📍 Ámbito",
        "🎯 Modus Operandi",
        "✅ Hechos Resueltos",
    ])

    # ---- Movilidad ----
    with tab_movil:
        st.markdown("### Medios de movilidad utilizados")
        df_movil = engine.medios_movilidad()
        if len(df_movil) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                render_barras_con_toggle(
                    charts, df_movil, "Medios de Movilidad",
                    key="caract_movilidad", color="#5B9BD5",
                )
            with col2:
                st.markdown("#### Detalle ejecutivo")
                _mostrar_tabla(df_movil)

    # ---- Armas ----
    with tab_armas:
        st.markdown("### Armas utilizadas")
        df_armas = engine.armas_utilizadas()
        if len(df_armas) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1.5, 1])
            with col1:
                render_barras_con_toggle(
                    charts, df_armas, "Armas Utilizadas en Hechos Delictivos",
                    key="caract_armas", color="#CC0000",
                )
            with col2:
                st.markdown("#### Detalle ejecutivo")
                _mostrar_tabla(df_armas)

    # ---- Ámbito ----
    with tab_ambito:
        st.markdown("### Ámbito de ocurrencia")
        df_ambito = engine.ambito_ocurrencia()
        if len(df_ambito) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                fig = charts.dona(df_ambito, "Distribución por Ámbito")
                st.plotly_chart(fig, width="stretch")
            with col2:
                render_barras_con_toggle(
                    charts, df_ambito, "Delitos por Ámbito de Ocurrencia",
                    key="caract_ambito", color="#70AD47",
                )

    # ---- Modus Operandi ----
    with tab_modus:
        st.markdown("### Modus operandi más frecuentes")
        top_n = st.slider("Cantidad a mostrar", 5, 30, 15)
        df_modus = engine.modus_operandi(top_n=top_n)
        if len(df_modus) == 0:
            st.warning("Sin datos disponibles")
        else:
            render_barras_con_toggle(
                charts, df_modus, f"Top {top_n} Modus Operandi",
                key="caract_modus", color="#9B59B6",
            )

    # ---- Hechos Resueltos ----
    with tab_resueltos:
        st.markdown("### Estado de resolución de hechos")
        df_resueltos = engine.hechos_resueltos()
        if len(df_resueltos) == 0:
            st.warning("Sin datos disponibles")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                fig = charts.dona(df_resueltos, "Proporción de Hechos Resueltos")
                st.plotly_chart(fig, width="stretch")
            with col2:
                st.markdown("#### Detalle ejecutivo")
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

    close_stage()

    # ---- Exportar ----
    st.divider()
    render_section_heading(
        4,
        "Cierre documental",
        "Exportación de características",
        "Cierre con salidas rápidas de las dimensiones más consultadas para reutilización externa.",
    )
    open_stage(
        4,
        "Archivos finales",
        "Descargas temáticas",
        "Las exportaciones priorizan movilidad y armas como salidas base de consulta.",
        stage_class="export-stage",
    )
    st.markdown("### Descarga documental")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        csv = engine.medios_movilidad().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Movilidad (CSV)", csv, "movilidad.csv", "text/csv")
    with col_e2:
        csv = engine.armas_utilizadas().to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Armas (CSV)", csv, "armas.csv", "text/csv")
    close_stage()

    # Botón de exportación a Word
    render_boton_exportar("🔍 Características", engine)


def _mostrar_tabla(df):
    """Muestra tabla compacta en streamlit."""
    display = df[["categoria_label", "cantidad", "porcentaje"]].copy()
    display.columns = ["Categoría", "Cantidad", "%"]
    display["Cantidad"] = display["Cantidad"].astype(int).apply(lambda x: f"{x:,}")
    display["%"] = display["%"].apply(lambda x: f"{x:.1f}%")
    render_dataframe_as_html_table(display)
