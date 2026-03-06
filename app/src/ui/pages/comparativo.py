"""
Página: Comparativo entre Períodos.
Informe 6.10 — Compara por año o por rangos de fechas.
"""
from datetime import timedelta

import streamlit as st

from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar
from app.src.charts.generator import ChartGenerator


def render():
    st.title("📈 Comparativo entre Períodos")
    st.markdown("Comparación de delitos por años o por dos rangos de fechas")

    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df, excluir={"anio", "fecha_rango"})
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    modo = st.radio(
        "Modo de comparación",
        ["Años", "Rangos de fechas"],
        horizontal=True,
    )

    st.divider()

    if modo == "Años":
        _render_comparativo_anual(engine, charts)
        return

    _render_comparativo_rangos(df_filtered, engine, charts)


def _render_comparativo_anual(engine, charts):
    anios = sorted(engine.df["_anio"].dropna().unique().astype(int).tolist())

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

    total_ant = engine.filtrar(anio=anio_anterior).total_registros
    total_act = engine.filtrar(anio=anio_actual).total_registros
    diferencia = total_act - total_ant
    pct_var = round((diferencia / total_ant * 100), 2) if total_ant > 0 else (100.0 if total_act > 0 else 0.0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Delitos {anio_anterior}", f"{total_ant:,}")
    c2.metric(f"Delitos {anio_actual}", f"{total_act:,}")
    c3.metric("Diferencia", f"{diferencia:+,}", delta=f"{pct_var:+.1f}%")
    c4.metric(
        "Tendencia",
        "📈 Aumento" if diferencia > 0 else ("📉 Baja" if diferencia < 0 else "➡️ Igual"),
    )

    st.divider()

    tab_mensual, tab_delitos, tab_tabla = st.tabs([
        "📅 Comparativo Mensual",
        "📋 Comparativo por Delito",
        "📊 Tabla Detallada",
    ])

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

            st.markdown("#### Tabla comparativa mensual")
            _tabla_comparativa(df_comp_mes, "mes_label", str(anio_anterior), str(anio_actual))

    with tab_delitos:
        st.markdown(f"### Comparativo por Tipo de Delito: {anio_anterior} vs {anio_actual}")
        df_comp_del = engine.comparativo_periodos(anio_actual, anio_anterior, "DELITO")

        if len(df_comp_del) > 1:
            df_chart = df_comp_del[df_comp_del["categoria"] != "TOTAL"]
            fig = charts.barras_comparativo(
                df_chart,
                f"Delitos por Modalidad — {anio_anterior} vs {anio_actual}",
                label_y1=str(anio_anterior),
                label_y2=str(anio_actual),
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Tabla comparativa por delito")
            _tabla_comparativa(df_comp_del, "categoria", str(anio_anterior), str(anio_actual))

    with tab_tabla:
        st.markdown("### Resumen Comparativo Completo")

        dimension = st.selectbox("Dimensión a comparar", [
            "DELITO", "DIA_HECHO", "FRAN_HORAR", "LUGR_HECHO",
        ], key="dimension_anual")

        df_comp = engine.comparativo_periodos(anio_actual, anio_anterior, dimension)
        _tabla_comparativa(df_comp, "categoria", str(anio_anterior), str(anio_actual))

    st.divider()
    csv = engine.comparativo_mensual(anio_actual, anio_anterior).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar comparativo mensual (CSV)",
        csv,
        f"comparativo_{anio_anterior}_vs_{anio_actual}.csv",
        "text/csv",
    )


def _render_comparativo_rangos(df_filtered, engine, charts):
    fechas = df_filtered["_fecha"].dropna() if "_fecha" in df_filtered.columns else []
    if len(fechas) == 0:
        st.warning("No hay fechas válidas en el conjunto filtrado para comparar rangos.")
        return

    fecha_min = fechas.min()
    fecha_max = fechas.max()
    desde_a_default, hasta_a_default, desde_b_default, hasta_b_default = _rangos_por_defecto(fecha_min, fecha_max)

    st.markdown("### Comparativo por Rangos de Fechas")
    st.caption("Periodo A se toma como base. Periodo B se compara contra A. La evolución diaria se alinea por posición dentro de cada rango.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Periodo A (base)")
        desde_a = st.date_input(
            "Desde A",
            value=desde_a_default,
            min_value=fecha_min,
            max_value=fecha_max,
            key="comp_desde_a",
        )
        hasta_a = st.date_input(
            "Hasta A",
            value=hasta_a_default,
            min_value=fecha_min,
            max_value=fecha_max,
            key="comp_hasta_a",
        )

    with col_b:
        st.markdown("#### Periodo B (comparación)")
        desde_b = st.date_input(
            "Desde B",
            value=desde_b_default,
            min_value=fecha_min,
            max_value=fecha_max,
            key="comp_desde_b",
        )
        hasta_b = st.date_input(
            "Hasta B",
            value=hasta_b_default,
            min_value=fecha_min,
            max_value=fecha_max,
            key="comp_hasta_b",
        )

    if desde_a > hasta_a or desde_b > hasta_b:
        st.warning("Cada periodo debe tener una fecha desde menor o igual a la fecha hasta.")
        return

    dias_a = (hasta_a - desde_a).days + 1
    dias_b = (hasta_b - desde_b).days + 1
    if _rangos_solapados(desde_a, hasta_a, desde_b, hasta_b):
        st.warning("Los periodos se solapan. La comparación sigue disponible, pero parte de los registros puede contarse en ambos rangos.")
    if dias_a != dias_b:
        st.info("Los periodos tienen distinta duración. Se comparan totales brutos y la evolución diaria se alinea por posición relativa.")

    label_a = _formatear_periodo(desde_a, hasta_a)
    label_b = _formatear_periodo(desde_b, hasta_b)

    df_comp_del = engine.comparativo_periodos_rango(desde_b, hasta_b, desde_a, hasta_a, "DELITO")
    df_comp_com = engine.comparativo_comisarias_rango(desde_b, hasta_b, desde_a, hasta_a)
    df_comp_dias = engine.comparativo_diario_rango(desde_b, hasta_b, desde_a, hasta_a)
    total = df_comp_del[df_comp_del["categoria"] == "TOTAL"].iloc[0]

    total_a = int(total["cantidad_anterior"])
    total_b = int(total["cantidad_actual"])
    diferencia = int(total["diferencia"])
    pct_var = float(total["pct_variacion"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Periodo A", f"{total_a:,}", delta=label_a)
    c2.metric("Periodo B", f"{total_b:,}", delta=label_b)
    c3.metric("Diferencia", f"{diferencia:+,}", delta=f"{pct_var:+.1f}%")
    c4.metric(
        "Comparabilidad",
        "Misma duración" if dias_a == dias_b else "Duración distinta",
        delta=f"{dias_a}d vs {dias_b}d",
    )

    st.divider()

    tab_evolucion, tab_delitos, tab_comisarias, tab_tabla = st.tabs([
        "📅 Evolución diaria",
        "📋 Comparativo por Delito",
        "🏛️ Comparativo por Comisaría",
        "📊 Tabla Detallada",
    ])

    with tab_evolucion:
        st.markdown(f"### Evolución diaria alineada: {label_a} vs {label_b}")
        fig = charts.lineas_comparativo(
            df_comp_dias,
            f"Evolución diaria — {label_a} vs {label_b}",
            col_x="dia_label",
            label_y1="Periodo A",
            label_y2="Periodo B",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("#### Tabla comparativa diaria")
        _tabla_evolucion_diaria(df_comp_dias, label_a, label_b)

    with tab_delitos:
        st.markdown(f"### Comparativo por Tipo de Delito: {label_a} vs {label_b}")
        df_chart = df_comp_del[df_comp_del["categoria"] != "TOTAL"]
        if len(df_chart) > 0:
            fig = charts.barras_comparativo(
                df_chart,
                f"Delitos por Modalidad — {label_a} vs {label_b}",
                label_y1="Periodo A",
                label_y2="Periodo B",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para graficar el comparativo por delito.")

        st.markdown("#### Tabla comparativa por delito")
        _tabla_comparativa(df_comp_del, "categoria", label_a, label_b)

    with tab_comisarias:
        st.markdown(f"### Comparativo por Comisaría: {label_a} vs {label_b}")
        st.caption("La tabla compara la misma dependencia entre ambos periodos, mostrando 0 cuando una comisaría no registra hechos en uno de los rangos.")
        top_n_comisarias = st.slider(
            "Cantidad de comisarías a graficar",
            min_value=5,
            max_value=40,
            value=min(15, max(len(df_comp_com[df_comp_com["categoria_label"] != "TOTAL"]), 5)),
            key="top_comisarias_rango",
        )
        df_chart_com = df_comp_com[df_comp_com["categoria_label"] != "TOTAL"].head(top_n_comisarias)
        if len(df_chart_com) > 0:
            fig = charts.barras_comparativo(
                df_chart_com,
                f"Comisarías con más hechos — {label_a} vs {label_b}",
                col_cat="categoria_label",
                label_y1="Periodo A",
                label_y2="Periodo B",
                height=max(500, len(df_chart_com) * 28 + 180),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para graficar el comparativo por comisaría.")

        st.markdown("#### Tabla comparativa por comisaría")
        _tabla_comparativa(df_comp_com, "categoria_label", label_a, label_b)

    with tab_tabla:
        st.markdown("### Resumen Comparativo Completo")
        dimension = st.selectbox(
            "Dimensión a comparar",
            ["DELITO", "DIA_HECHO", "FRAN_HORAR", "LUGR_HECHO"],
            key="dimension_rangos",
        )
        df_comp = engine.comparativo_periodos_rango(desde_b, hasta_b, desde_a, hasta_a, dimension)
        _tabla_comparativa(df_comp, "categoria", label_a, label_b)

    st.divider()
    col_export_1, col_export_2, col_export_3 = st.columns(3)
    with col_export_1:
        csv_dias = df_comp_dias.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar evolución diaria (CSV)",
            csv_dias,
            f"comparativo_diario_{_slug_periodo(desde_a, hasta_a)}_vs_{_slug_periodo(desde_b, hasta_b)}.csv",
            "text/csv",
        )
    with col_export_2:
        csv_detalle = df_comp.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar tabla detallada (CSV)",
            csv_detalle,
            f"comparativo_detalle_{dimension.lower()}_{_slug_periodo(desde_a, hasta_a)}_vs_{_slug_periodo(desde_b, hasta_b)}.csv",
            "text/csv",
        )
    with col_export_3:
        csv_comisarias = df_comp_com.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar tabla por comisaría (CSV)",
            csv_comisarias,
            f"comparativo_comisarias_{_slug_periodo(desde_a, hasta_a)}_vs_{_slug_periodo(desde_b, hasta_b)}.csv",
            "text/csv",
        )


def _tabla_comparativa(df, col_label, label_anterior, label_actual):
    display = df.copy()

    rename = {}
    if "cantidad_anterior" in display.columns:
        rename["cantidad_anterior"] = label_anterior
    if "cantidad_actual" in display.columns:
        rename["cantidad_actual"] = label_actual
    if "diferencia" in display.columns:
        rename["diferencia"] = "Dif."
    if "pct_variacion" in display.columns:
        rename["pct_variacion"] = "% Var."
    if col_label in display.columns:
        rename[col_label] = "Categoría"

    display = display.rename(columns=rename)
    cols_to_show = [
        c for c in ["Categoría", label_anterior, label_actual, "Dif.", "% Var."]
        if c in display.columns
    ]

    st.dataframe(
        display[cols_to_show],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Dif.": st.column_config.NumberColumn(format="%+d"),
            "% Var.": st.column_config.NumberColumn(format="%+.1f%%"),
        },
    )


def _tabla_evolucion_diaria(df, label_anterior, label_actual):
    display = df[df["dia_label"] != "TOTAL"].copy().rename(columns={
        "dia_label": "Tramo",
        "fecha_anterior_label": f"Fecha {label_anterior}",
        "fecha_actual_label": f"Fecha {label_actual}",
        "cantidad_anterior": label_anterior,
        "cantidad_actual": label_actual,
        "diferencia": "Dif.",
        "pct_variacion": "% Var.",
    })

    st.dataframe(
        display[[
            "Tramo",
            f"Fecha {label_anterior}",
            f"Fecha {label_actual}",
            label_anterior,
            label_actual,
            "Dif.",
            "% Var.",
        ]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Dif.": st.column_config.NumberColumn(format="%+d"),
            "% Var.": st.column_config.NumberColumn(format="%+.1f%%"),
        },
    )


def _rangos_por_defecto(fecha_min, fecha_max):
    total_dias = (fecha_max - fecha_min).days + 1
    if total_dias >= 14:
        hasta_b = fecha_max
        desde_b = fecha_max - timedelta(days=6)
        hasta_a = desde_b - timedelta(days=1)
        desde_a = max(fecha_min, hasta_a - timedelta(days=6))
        if desde_a <= hasta_a:
            return desde_a, hasta_a, desde_b, hasta_b

    if total_dias <= 1:
        return fecha_min, fecha_min, fecha_max, fecha_max

    corte = max(total_dias // 2, 1)
    desde_a = fecha_min
    hasta_a = fecha_min + timedelta(days=corte - 1)
    desde_b = min(hasta_a + timedelta(days=1), fecha_max)
    hasta_b = fecha_max
    return desde_a, hasta_a, desde_b, hasta_b


def _rangos_solapados(desde_a, hasta_a, desde_b, hasta_b):
    return max(desde_a, desde_b) <= min(hasta_a, hasta_b)


def _formatear_periodo(desde, hasta):
    if desde == hasta:
        return desde.strftime("%d/%m/%Y")
    return f"{desde.strftime('%d/%m/%Y')} al {hasta.strftime('%d/%m/%Y')}"


def _slug_periodo(desde, hasta):
    if desde == hasta:
        return desde.strftime("%Y%m%d")
    return f"{desde.strftime('%Y%m%d')}_{hasta.strftime('%Y%m%d')}"
