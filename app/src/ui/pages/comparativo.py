"""
Página: Comparativo entre Períodos.
Informe 6.10 — Compara dos años con tablas y gráficos de variación.
"""
import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator
from app.config.settings import COLORES


def render():
    st.title("📈 Comparativo entre Períodos")
    st.markdown("Comparación de delitos entre dos años seleccionados")

    df = cargar_datos()
    # No usar filtros globales aquí, los años se seleccionan directamente
    engine = get_engine(df)
    charts = ChartGenerator()

    # ---- Selección de años ----
    anios = sorted(df["_anio"].dropna().unique().astype(int).tolist())

    if len(anios) < 2:
        st.warning("Se necesitan al menos 2 años de datos para hacer comparativos.")
        st.info(f"Años disponibles: {anios}")
        return

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        anio_anterior = st.selectbox("📅 Año anterior", anios, index=0)
    with col_sel2:
        anio_actual = st.selectbox(
            "📅 Año actual",
            anios,
            index=min(1, len(anios) - 1),
        )

    if anio_anterior == anio_actual:
        st.warning("Seleccione dos años diferentes para comparar.")
        return

    st.divider()

    # ---- Filtro opcional por UR ----
    from app.config.settings import UNIDADES_REGIONALES
    ur_sel = st.selectbox(
        "Filtrar por Unidad Regional (opcional)",
        ["Todas"] + list(UNIDADES_REGIONALES.keys()),
    )

    if ur_sel != "Todas":
        engine = engine.filtrar(ur=ur_sel)

    # ---- Métricas principales comparativas ----
    eng_ant = engine.filtrar(anio=anio_anterior)
    eng_act = engine.filtrar(anio=anio_actual)

    total_ant = eng_ant.total_registros
    total_act = eng_act.total_registros
    diferencia = total_act - total_ant
    pct_var = round((diferencia / total_ant * 100), 2) if total_ant > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Delitos {anio_anterior}", f"{total_ant:,}")
    c2.metric(f"Delitos {anio_actual}", f"{total_act:,}")
    c3.metric("Diferencia", f"{diferencia:+,}", delta=f"{pct_var:+.1f}%")
    c4.metric(
        "Tendencia",
        "📈 Aumento" if diferencia > 0 else ("📉 Baja" if diferencia < 0 else "➡️ Igual"),
    )

    st.divider()

    # ---- Pestañas comparativas ----
    tab_mensual, tab_delitos, tab_tabla = st.tabs([
        "📅 Comparativo Mensual",
        "📋 Comparativo por Delito",
        "📊 Tabla Detallada",
    ])

    # ---- Comparativo Mensual ----
    with tab_mensual:
        st.markdown(f"### Comparativo Mensual: {anio_anterior} vs {anio_actual}")
        df_comp_mes = engine.comparativo_mensual(anio_actual, anio_anterior)

        if len(df_comp_mes) > 1:
            fig = charts.lineas_comparativo(
                df_comp_mes,
                f"Evolución Mensual — {anio_anterior} vs {anio_actual}",
                label_y1=str(anio_anterior),
                label_y2=str(anio_actual),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tabla con colores de variación
            st.markdown("#### Tabla comparativa mensual")
            _tabla_comparativa(df_comp_mes, "mes_label", anio_anterior, anio_actual)

    # ---- Comparativo por Delito ----
    with tab_delitos:
        st.markdown(f"### Comparativo por Tipo de Delito: {anio_anterior} vs {anio_actual}")
        df_comp_del = engine.comparativo_periodos(anio_actual, anio_anterior, "DELITO")

        if len(df_comp_del) > 1:
            # Excluir fila TOTAL para el gráfico
            df_chart = df_comp_del[df_comp_del["categoria"] != "TOTAL"]
            fig = charts.barras_comparativo(
                df_chart,
                f"Delitos por Modalidad — {anio_anterior} vs {anio_actual}",
                label_y1=str(anio_anterior),
                label_y2=str(anio_actual),
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Tabla comparativa por delito")
            _tabla_comparativa(df_comp_del, "categoria", anio_anterior, anio_actual)

    # ---- Tabla general ----
    with tab_tabla:
        st.markdown(f"### Resumen Comparativo Completo")

        dimension = st.selectbox("Dimensión a comparar", [
            "DELITO", "DIA_HECHO", "FRAN_HORAR", "LUGR_HECHO",
        ])

        df_comp = engine.comparativo_periodos(anio_actual, anio_anterior, dimension)
        _tabla_comparativa(df_comp, "categoria", anio_anterior, anio_actual)

    # ---- Exportar ----
    st.divider()
    csv = engine.comparativo_mensual(anio_actual, anio_anterior).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar comparativo mensual (CSV)",
        csv,
        f"comparativo_{anio_anterior}_vs_{anio_actual}.csv",
        "text/csv",
    )


def _tabla_comparativa(df, col_label, anio_ant, anio_act):
    """Tabla comparativa con colores para variación."""
    display = df.copy()

    # Renombrar columnas
    rename = {}
    if "cantidad_anterior" in display.columns:
        rename["cantidad_anterior"] = str(anio_ant)
    if "cantidad_actual" in display.columns:
        rename["cantidad_actual"] = str(anio_act)
    if "diferencia" in display.columns:
        rename["diferencia"] = "Dif."
    if "pct_variacion" in display.columns:
        rename["pct_variacion"] = "% Var."
    if col_label in display.columns:
        rename[col_label] = "Categoría"

    display = display.rename(columns=rename)

    # Mostrar con colores
    cols_to_show = [c for c in ["Categoría", str(anio_ant), str(anio_act), "Dif.", "% Var."]
                    if c in display.columns]

    st.dataframe(
        display[cols_to_show],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Dif.": st.column_config.NumberColumn(format="%+d"),
            "% Var.": st.column_config.NumberColumn(format="%+.1f%%"),
        },
    )
