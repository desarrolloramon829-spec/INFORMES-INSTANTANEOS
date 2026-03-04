"""
Página: Delitos por Modalidad.
Informe 6.1 — Tabla y gráficos de delitos clasificados por tipo.
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator
from app.config.settings import DELITO_CATEGORIAS


def render():
    st.title("📋 Delitos por Modalidad")
    st.markdown("Análisis de hechos delictivos clasificados por tipo de delito")

    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    mostrar_metricas_header(engine)
    st.divider()

    # ---- Tabla de datos ----
    df_modal = engine.delitos_con_modus_operandi()

    if len(df_modal) == 0:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    col_tabla, col_grafico = st.columns([1, 1.5])

    with col_tabla:
        st.markdown("### Tabla de Delitos por Modalidad")

        # Crear tabla HTML estilizada
        html = _generar_tabla_html(df_modal)
        st.markdown(html, unsafe_allow_html=True)

    with col_grafico:
        st.markdown("### Distribución de Delitos")
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

    st.divider()

    # ---- Heatmap: Delito x Mes ----
    st.markdown("### Mapa de Calor: Delitos por Modalidad y Mes")

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

    # ---- Exportar ----
    st.divider()
    st.markdown("### 📥 Exportar Datos")
    csv = df_modal.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar como CSV",
        data=csv,
        file_name="delitos_por_modalidad.csv",
        mime="text/csv",
    )


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
