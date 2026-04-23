"""
Página: Delitos por Modalidad.
Informe 6.1 — Tabla y gráficos de delitos clasificados por tipo.
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator
from app.src.ui.editorial import close_stage, open_stage, render_hero, render_panel, render_section_heading, render_dataframe_as_html_table


def render():
    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    df_modalidades_base = engine.df_con_modalidad_operativa()
    modalidades_disponibles = []
    if not df_modalidades_base.empty and "modalidad_operativa" in df_modalidades_base.columns:
        modalidades_disponibles = (
            df_modalidades_base["modalidad_operativa"]
            .dropna()
            .value_counts()
            .index
            .tolist()
        )

    render_section_heading(
        1,
        "Filtro local",
        "Modalidad operativa",
        "Este filtro actúa solo dentro de la pantalla de delitos y permite aislar combinaciones reales de delito y modus operandi.",
    )
    modalidad_operativa_sel = st.multiselect(
        "Modalidades operativas específicas",
        options=modalidades_disponibles,
        placeholder="Todas las modalidades operativas",
        key="delitos_modalidad_operativa_local",
    )

    if modalidad_operativa_sel and not df_modalidades_base.empty:
        df_page = df_modalidades_base[
            df_modalidades_base["modalidad_operativa"].isin(modalidad_operativa_sel)
        ].copy()
    else:
        df_page = df_filtered.copy()

    # Always re-create engine from effectively filtered data
    engine = get_engine(df_page)

    render_hero(
        "Modalidades delictivas",
        "Delitos por modalidad",
        "Página centrada en composición delictual, detalle por modus operandi y contraste mensual para lectura ejecutiva.",
        chips=["Tabla y gráficos coordinados", "Mapas de calor", "Exportación inmediata"],
        seq=1,
    )

    mostrar_metricas_header(engine)
    st.divider()

    # ---- Tabla de datos ----
    df_modal = engine.delitos_con_modus_operandi()

    if len(df_modal) == 0:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    df_modal_detalle_full = engine.delitos_por_modalidad_detallada()
    df_modalidades_operativas_full = engine.modalidades_operativas()
    detalle_label_map = df_modal_detalle_full.set_index("categoria")["categoria_label"].to_dict()

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
        tab_barras, tab_vertical, tab_dona = st.tabs(["📊 Barras", "📈 Verticales", "🍩 Dona"])

        with tab_barras:
            max_modalidades_barras = max(5, min(len(df_modal), 40))
            default_modalidades_barras = min(15, max_modalidades_barras)
            top_modalidades_barras = st.slider(
                "Modalidades visibles en barras",
                min_value=5,
                max_value=max_modalidades_barras,
                value=default_modalidades_barras,
                key="top_modalidades_barras_delitos",
            )
            df_modal_barras = df_modal.head(top_modalidades_barras).copy()
            fig = charts.barras_horizontal(
                df_modal_barras,
                "Delitos por Modalidad",
            )
            st.plotly_chart(fig, width="stretch")
            if len(df_modal) > len(df_modal_barras):
                st.caption(
                    f"Se muestran las {len(df_modal_barras)} modalidades con mayor volumen. El detalle completo sigue disponible en la tabla de la izquierda y en la exportación CSV."
                )

        with tab_vertical:
            max_modalidades_detalle = max(5, min(len(df_modalidades_operativas_full), 120))
            default_modalidades_detalle = min(12, max_modalidades_detalle)
            top_modalidades_detalle = st.slider(
                "Modalidades operativas visibles",
                min_value=5,
                max_value=max_modalidades_detalle,
                value=default_modalidades_detalle,
                key="top_modalidades_detalle_vertical",
            )
            df_modal_detalle = df_modalidades_operativas_full.head(top_modalidades_detalle).copy()
            if len(df_modal_detalle) > 0:
                fig = charts.barras_vertical(
                    df_modal_detalle,
                    "Delitos por modalidad operativa real",
                    color="#2563EB",
                    highlight_max=True,
                )
                st.plotly_chart(fig, width="stretch")

                lider_detalle = df_modal_detalle.iloc[0]
                st.caption(
                    f"Modalidad operativa líder: {lider_detalle['categoria_label']} con {int(lider_detalle['cantidad']):,} hechos."
                )

                st.markdown("#### Tabla completa de modalidades operativas")
                display_detalle = df_modalidades_operativas_full[["categoria_label", "cantidad", "porcentaje"]].copy()
                display_detalle.columns = ["Modalidad operativa", "Cantidad", "%"]
                display_detalle["Cantidad"] = display_detalle["Cantidad"].astype(int).apply(lambda x: f"{x:,}")
                display_detalle["%"] = display_detalle["%"].apply(lambda x: f"{x:.1f}%")
                render_dataframe_as_html_table(
                    display_detalle,
                    height=max(len(display_detalle) * 35 + 40, 420),
                )
            else:
                st.info("Sin datos suficientes para graficar modalidades específicas.")

        with tab_dona:
            fig = charts.dona(df_modal, "Proporción por Tipo de Delito")
            st.plotly_chart(fig, width="stretch")

    close_stage()

    st.divider()

    # ---- Heatmaps: Delito x Mes / Delito x Franja ----
    render_section_heading(
        4,
        "Profundización",
        "Cruces por modalidad",
        "Los mapas de calor permiten ver si la presión cambia por mes o por franja horaria sin perder de vista qué modalidades dominan en cada cruce.",
    )
    open_stage(
        4,
        "Mapa de calor",
        "Cruces de modalidad",
        "Cada matriz resume intensidad relativa y permite ubicar periodos o franjas con mayor densidad para cada categoría.",
        stage_class="analysis-stage",
    )

    tab_mes_hm, tab_franja_hm = st.tabs(["📆 Modalidad vs mes", "🕐 Modalidad vs franja"])

    with tab_mes_hm:
        if "MES_DENU" in df_page.columns and "DELITO" in df_page.columns:
            from app.config.settings import MESES, MESES_LABELS

            df_cross = df_page.dropna(subset=["DELITO", "MES_DENU"])
            if len(df_cross) > 0:
                pivot = df_cross.pivot_table(
                    index="DELITO",
                    columns="MES_DENU",
                    aggfunc="size",
                    fill_value=0,
                )
                meses_presentes = [m for m in MESES if m in pivot.columns]
                pivot = pivot[meses_presentes]
                pivot.index = [detalle_label_map.get(valor, valor) for valor in pivot.index]
                pivot.columns = [MESES_LABELS.get(m, m) for m in meses_presentes]

                col_mes_1, col_mes_2 = st.columns([1.8, 1])
                with col_mes_1:
                    fig = charts.heatmap(pivot, "Intensidad de delitos por modalidad y mes")
                    st.plotly_chart(fig, width="stretch")
                with col_mes_2:
                    valor_maximo = int(pivot.to_numpy().max())
                    modalidad_max, mes_max = pivot.stack().idxmax()
                    st.markdown("#### Lectura rápida")
                    st.markdown(
                        f"""
                        **Mayor concentración mensual:**
                        - Modalidad: **{modalidad_max}**
                        - Mes: **{mes_max}**
                        - Hechos: **{valor_maximo:,}**
                        """
                    )
            else:
                st.info("Sin datos cruzados disponibles.")

    with tab_franja_hm:
        top_modalidades = st.slider(
            "Modalidades visibles en el cruce por franja",
            min_value=4,
            max_value=12,
            value=8,
            key="top_modalidades_franja_delitos",
        )
        pivot_franja = engine.matriz_modalidad_franja(top_n_delitos=top_modalidades)
        if pivot_franja.empty:
            st.info("Sin datos suficientes para construir el cruce modalidad versus franja.")
        else:
            col_franja_1, col_franja_2 = st.columns([1.8, 1])
            with col_franja_1:
                fig = charts.heatmap(pivot_franja, "Intensidad de delitos por modalidad y franja horaria")
                st.plotly_chart(fig, width="stretch")
            with col_franja_2:
                valor_maximo = int(pivot_franja.to_numpy().max())
                modalidad_max, franja_max = pivot_franja.stack().idxmax()
                st.markdown("#### Lectura rápida")
                st.markdown(
                    f"""
                    **Mayor concentración horaria:**
                    - Modalidad: **{modalidad_max}**
                    - Franja: **{franja_max.replace(chr(10), ' / ')}**
                    - Hechos: **{valor_maximo:,}**
                    """
                )

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
        "Incluye el detalle principal y la variante de modalidades específicas sobre la muestra filtrada vigente.",
        stage_class="export-stage",
    )
    st.markdown("### Descarga documental")
    col_export_1, col_export_2 = st.columns(2)
    with col_export_1:
        csv = df_modal.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Modalidades resumidas (CSV)",
            data=csv,
            file_name="delitos_por_modalidad.csv",
            mime="text/csv",
        )
    with col_export_2:
        csv_detalle = df_modalidades_operativas_full.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Modalidades operativas (CSV)",
            data=csv_detalle,
            file_name="delitos_modalidades_operativas.csv",
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
            <td style="text-align:left; color:var(--app-primary);">{modus}</td>
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
