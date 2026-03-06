"""
Página: Delitos por Modalidad.
Informe 6.1 — Tabla y gráficos de delitos clasificados por tipo.
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
        "Modalidades delictivas",
        "Delitos por modalidad",
        "Página centrada en composición delictual, detalle por modus operandi y contraste mensual para lectura ejecutiva.",
        chips=["Tabla y gráficos coordinados", "Mapa de calor mensual", "Exportación inmediata"],
        seq=1,
    )

    mostrar_metricas_header(engine)
    st.divider()

    # ---- Tabla de datos ----
    df_modal = engine.delitos_con_modus_operandi()

    if len(df_modal) == 0:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    modalidad_top = df_modal.iloc[0]
    render_section_heading(
        2,
        "Lectura principal",
        "Composición por modalidad",
        "Primero se fija la modalidad dominante y luego se abre la combinación de tabla y visuales.",
    )
    render_panel(
        2,
        "Síntesis",
        str(modalidad_top.get("categoria_label", "Modalidad líder")),
        f"La modalidad con mayor incidencia aporta {int(modalidad_top['cantidad']):,} hechos, equivalente a {modalidad_top['porcentaje']:.1f}% del universo filtrado.",
        tone="accent",
    )

    open_stage(
        3,
        "Escena analítica",
        "Tabla y distribución",
        "La tabla aporta detalle por modalidad y modus operandi, mientras los gráficos resuelven jerarquía y proporción.",
        stage_class="analysis-stage",
    )
    col_tabla, col_grafico = st.columns([1, 1.5])

    with col_tabla:
        st.markdown("### Detalle por modalidad")

        # Crear tabla HTML estilizada
        html = _generar_tabla_html(df_modal)
        st.markdown(html, unsafe_allow_html=True)

    with col_grafico:
        st.markdown("### Distribución visual")
        tab_barras, tab_dona = st.tabs(["📊 Barras", "🍩 Dona"])

        with tab_barras:
            fig = charts.barras_horizontal(
                df_modal,
                "Delitos por Modalidad",
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_dona:
            fig = charts.dona(df_modal, "Proporción por Tipo de Delito")
            st.plotly_chart(fig, use_container_width=True)

    close_stage()

    st.divider()

    # ---- Heatmap: Delito x Mes ----
    render_section_heading(
        4,
        "Profundización",
        "Intensidad mensual por modalidad",
        "Este plano muestra si la presión delictual cambia a lo largo del año y ayuda a detectar concentraciones persistentes.",
    )
    open_stage(
        4,
        "Mapa de calor",
        "Cruce modalidad por mes",
        "La matriz resume intensidad relativa y permite ubicar periodos con mayor densidad para cada categoría.",
        stage_class="analysis-stage",
    )

    if "MES_DENU" in df_filtered.columns and "DELITO" in df_filtered.columns:
        from app.config.settings import MESES, MESES_LABELS

        df_cross = df_filtered.dropna(subset=["DELITO", "MES_DENU"])
        if len(df_cross) > 0:
            pivot = df_cross.pivot_table(
                index="DELITO",
                columns="MES_DENU",
                aggfunc="size",
                fill_value=0,
            )
            # Reordenar meses
            meses_presentes = [m for m in MESES if m in pivot.columns]
            pivot = pivot[meses_presentes]
            pivot.columns = [MESES_LABELS.get(m, m) for m in meses_presentes]

            fig = charts.heatmap(pivot, "Intensidad de Delitos por Modalidad y Mes")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos cruzados disponibles.")

    close_stage()

    # ---- Exportar ----
    st.divider()
    render_section_heading(
        5,
        "Cierre documental",
        "Exportación de modalidades",
        "Cierre con el archivo plano listo para circular hallazgos o reutilizar la tabla en otros informes.",
    )
    open_stage(
        5,
        "Archivo final",
        "Descarga CSV",
        "Incluye el detalle de modalidades y porcentajes sobre la muestra filtrada vigente.",
        stage_class="export-stage",
    )
    st.markdown("### Descarga documental")
    csv = df_modal.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar como CSV",
        data=csv,
        file_name="delitos_por_modalidad.csv",
        mime="text/csv",
    )
    close_stage()


def _generar_tabla_html(df) -> str:
    """Genera tabla HTML estilizada tipo Power BI con Delito + Modus Operandi."""
    rows = ""
    total_cant = df["cantidad"].sum()
    total_pct = 100.0

    for _, row in df.iterrows():
        delito = row.get('delito_label', row.get('categoria_label', ''))
        modus = row.get('modus_clean', '')
        rows += f"""
        <tr>
            <td style="text-align:left; font-weight:500;">{delito}</td>
            <td style="text-align:left; color:#a0c4ff;">{modus}</td>
            <td>{int(row['cantidad']):,}</td>
            <td>{row['porcentaje']:.1f}%</td>
        </tr>"""

    rows += f"""
    <tr class="total-row">
        <td style="text-align:left; font-weight:bold;">TOTAL</td>
        <td></td>
        <td><b>{int(total_cant):,}</b></td>
        <td><b>{total_pct:.1f}%</b></td>
    </tr>"""

    return f"""
    <table class="styled-table">
        <thead>
            <tr>
                <th style="text-align:left;">Delito</th>
                <th style="text-align:left;">Modus Operandi</th>
                <th>Cantidad</th>
                <th>Porcentaje</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """
