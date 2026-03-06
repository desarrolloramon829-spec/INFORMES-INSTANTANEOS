"""
Página: Comparativo entre Períodos.
Informe 6.10 — Compara por año o por rangos de fechas.
"""
from io import BytesIO
from datetime import timedelta
from html import escape

import pandas as pd
import streamlit as st

from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar
from app.src.charts.generator import ChartGenerator


def _render_editorial_panel(kicker, titulo, cuerpo, tone=""):
    tone_class = f" {tone}" if tone else ""
    st.markdown(
        f"""
        <section class="editorial-panel{tone_class}">
            <div class="editorial-kicker">{escape(kicker)}</div>
            <h3>{escape(titulo)}</h3>
            <p>{escape(cuerpo)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_section_heading(seq, kicker, titulo, cuerpo):
    st.markdown(
        f"""
        <section class="editorial-section-heading scene-seq seq-{seq}">
            <div class="editorial-kicker">{escape(kicker)}</div>
            <h2>{escape(titulo)}</h2>
            <p>{escape(cuerpo)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_sequenced_panel(seq, kicker, titulo, cuerpo, tone=""):
    tone_class = f" {tone}" if tone else ""
    st.markdown(
        f"""
        <section class="editorial-panel scene-seq seq-{seq}{tone_class}">
            <div class="editorial-kicker">{escape(kicker)}</div>
            <h3>{escape(titulo)}</h3>
            <p>{escape(cuerpo)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _open_scene_stage(seq, kicker, titulo, cuerpo, stage_class=""):
    extra_class = f" {stage_class}" if stage_class else ""
    st.markdown(
        f"""
        <section class="scene-stage scene-seq seq-{seq}{extra_class}">
            <div class="editorial-kicker">{escape(kicker)}</div>
            <h3>{escape(titulo)}</h3>
            <p>{escape(cuerpo)}</p>
        """,
        unsafe_allow_html=True,
    )


def _close_scene_stage():
    st.markdown("</section>", unsafe_allow_html=True)


def _render_hero():
    st.markdown(
        """
        <section class="editorial-hero scene-seq seq-1">
            <div class="editorial-kicker">Informe comparativo</div>
            <h1>Comparativo entre períodos</h1>
            <p class="editorial-lead">
                Vista preparada para contraste ejecutivo entre cortes temporales. La pantalla combina lectura de tendencia,
                composición por delito, desempeño por comisaría y exportación inmediata para revisión o exposición.
            </p>
            <div class="editorial-meta-row">
                <span class="editorial-chip">Comparación anual y por rangos</span>
                <span class="editorial-chip">Series temporales con granularidad operativa</span>
                <span class="editorial-chip">Exportación CSV y Excel</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render():
    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df, excluir={"anio", "fecha_rango"})
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    _render_hero()

    _render_section_heading(
        2,
        "Modo de análisis",
        "Definición del contraste",
        "Primero se define el tipo de contraste para ordenar la lectura y las métricas de apertura.",
    )
    modo = st.radio(
        "Modo de comparación",
        ["Años", "Rangos de fechas"],
        horizontal=True,
    )

    _render_sequenced_panel(
        2,
        "Marco de lectura",
        "Cómo interpretar esta pantalla",
        "El modo anual evalúa variaciones entre ejercicios. El modo por rangos contrasta ventanas operativas concretas y alinea la evolución por posición relativa dentro de cada tramo.",
        tone="accent",
    )

    st.divider()

    if modo == "Años":
        _render_comparativo_anual(engine, charts)
        return

    _render_comparativo_rangos(df_filtered, engine, charts)


def _granularidades_temporales():
    return {
        "Semestres": "semestres",
        "Cuatrimestres": "cuatrimestres",
        "Trimestres": "trimestres",
        "Bimestres": "bimestres",
        "Meses": "meses",
        "Semanas": "semanas",
        "Días": "dias",
    }


def _filtrar_subserie_temporal(df, granularidad, key_prefix):
    detalle = df[df["periodo_label"] != "TOTAL"].copy()
    total = df[df["periodo_label"] == "TOTAL"].copy()

    if granularidad not in {"semanas", "dias"} or len(detalle) <= 16:
        return df

    etiqueta = "semanas" if granularidad == "semanas" else "días"
    inicio, fin = st.slider(
        f"Subconjunto visible de {etiqueta}",
        min_value=1,
        max_value=len(detalle),
        value=(1, min(16, len(detalle))),
        key=f"{key_prefix}_subserie",
    )
    st.caption(f"Vista parcial: {inicio} a {fin} de {len(detalle)} {etiqueta}.")
    filtrado = detalle.iloc[inicio - 1:fin].copy()
    if not total.empty:
        filtrado = pd.concat([filtrado, total], ignore_index=True)
    return filtrado


def _to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for nombre, dataframe in sheets.items():
            dataframe.to_excel(writer, sheet_name=nombre[:31], index=False)
    buffer.seek(0)
    return buffer.getvalue()


def _render_comparativo_anual(engine, charts):
    granularidades = _granularidades_temporales()
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
    c1.metric(f"Año base {anio_anterior}", f"{total_ant:,}")
    c2.metric(f"Año comparado {anio_actual}", f"{total_act:,}")
    c3.metric("Diferencia", f"{diferencia:+,}", delta=f"{pct_var:+.1f}%")
    c4.metric(
        "Tendencia",
        "📈 Aumento" if diferencia > 0 else ("📉 Baja" if diferencia < 0 else "➡️ Igual"),
    )

    tendencia = "aumenta" if diferencia > 0 else ("disminuye" if diferencia < 0 else "se mantiene")
    _render_section_heading(
        3,
        "Lectura ejecutiva",
        "Apertura anual",
        "Las métricas abren la lectura y luego la síntesis fija el mensaje antes de pasar a la evidencia analítica.",
    )
    _render_sequenced_panel(
        3,
        "Síntesis anual",
        f"{anio_actual} frente a {anio_anterior}",
        f"El volumen total {tendencia} en {abs(diferencia):,} hechos, equivalente a {abs(pct_var):.1f}% respecto del año base. Use las pestañas para ver si el cambio se concentra por periodo, delito o contexto.",
    )

    st.divider()

    _open_scene_stage(
        4,
        "Escena analítica",
        "Exploración anual detallada",
        "La síntesis ya dejó la lectura central. Desde aquí aparecen la tendencia temporal, la composición por delito y la tabla de contraste.",
        stage_class="analysis-stage",
    )
    tab_temporal, tab_delitos, tab_tabla = st.tabs([
        "📅 Comparativo Temporal",
        "📋 Comparativo por Delito",
        "📊 Tabla Detallada",
    ])

    with tab_temporal:
        granularidad_label = st.selectbox(
            "Agrupar por",
            list(granularidades.keys()),
            index=4,
            key="granularidad_temporal_anual",
        )
        granularidad = granularidades[granularidad_label]
        st.markdown(f"### Comparativo por {granularidad_label}: {anio_anterior} vs {anio_actual}")
        df_comp_temporal = engine.comparativo_temporal_anual(anio_actual, anio_anterior, granularidad)
        df_comp_temporal_view = _filtrar_subserie_temporal(df_comp_temporal, granularidad, "anual_temporal")
        mostrar_texto = granularidad in {"semestres", "cuatrimestres", "trimestres", "bimestres", "meses"}

        if len(df_comp_temporal_view) > 1:
            fig = charts.lineas_comparativo(
                df_comp_temporal_view,
                f"Evolución por {granularidad_label} — {anio_anterior} vs {anio_actual}",
                col_x="periodo_label",
                label_y1=str(anio_anterior),
                label_y2=str(anio_actual),
                mostrar_texto=mostrar_texto,
                height=520 if granularidad in {"semanas", "dias"} else 450,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"#### Tabla comparativa por {granularidad_label.lower()}")
            _tabla_comparativa(df_comp_temporal_view, "periodo_label", str(anio_anterior), str(anio_actual))

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
        st.markdown("### Resumen consolidado")

        dimension = st.selectbox("Dimensión a comparar", [
            "DELITO", "DIA_HECHO", "FRAN_HORAR", "LUGR_HECHO",
        ], key="dimension_anual")

        df_comp = engine.comparativo_periodos(anio_actual, anio_anterior, dimension)
        _tabla_comparativa(df_comp, "categoria", str(anio_anterior), str(anio_actual))

    _close_scene_stage()

    st.divider()
    _open_scene_stage(
        6,
        "Cierre documental",
        "Exportaciones anuales",
        "Cierre con los archivos listos para circular, archivar o respaldar la lectura comparativa.",
        stage_class="export-stage",
    )
    st.markdown("### Descarga documental")
    df_export_temporal = engine.comparativo_temporal_anual(anio_actual, anio_anterior, granularidad)
    csv = df_export_temporal.to_csv(index=False).encode("utf-8")
    xlsx = _to_excel_bytes({
        "Comparativo temporal": df_export_temporal,
        "Comparativo delito": df_comp_del,
        "Detalle": df_comp,
    })
    col_export_csv, col_export_xlsx = st.columns(2)
    with col_export_csv:
        st.download_button(
            "⬇️ Descargar comparativo temporal (CSV)",
            csv,
            f"comparativo_{granularidad}_{anio_anterior}_vs_{anio_actual}.csv",
            "text/csv",
        )
    with col_export_xlsx:
        st.download_button(
            "⬇️ Descargar comparativo anual (Excel)",
            xlsx,
            f"comparativo_{granularidad}_{anio_anterior}_vs_{anio_actual}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    _close_scene_stage()


def _render_comparativo_rangos(df_filtered, engine, charts):
    granularidades = _granularidades_temporales()
    fechas = df_filtered["_fecha"].dropna() if "_fecha" in df_filtered.columns else []
    if len(fechas) == 0:
        st.warning("No hay fechas válidas en el conjunto filtrado para comparar rangos.")
        return

    fecha_min = fechas.min()
    fecha_max = fechas.max()
    desde_a_default, hasta_a_default, desde_b_default, hasta_b_default = _rangos_por_defecto(fecha_min, fecha_max)

    st.markdown("### Comparativo por rangos de fechas")
    st.caption("El periodo A funciona como base. El periodo B se compara contra A y la evolución temporal se alinea por posición relativa dentro de cada tramo.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Periodo A · base de contraste")
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
        st.markdown("#### Periodo B · tramo comparado")
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
    granularidad_label = st.selectbox(
        "Granularidad temporal del rango",
        list(granularidades.keys()),
        index=6,
        key="granularidad_temporal_rango",
    )
    granularidad = granularidades[granularidad_label]

    df_comp_del = engine.comparativo_periodos_rango(desde_b, hasta_b, desde_a, hasta_a, "DELITO")
    df_comp_com = engine.comparativo_comisarias_rango(desde_b, hasta_b, desde_a, hasta_a)
    df_comp_temporal = engine.comparativo_temporal_rango(desde_b, hasta_b, desde_a, hasta_a, granularidad)
    df_comp_temporal_view = _filtrar_subserie_temporal(df_comp_temporal, granularidad, "rangos_temporal")
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
        "Duración",
        "Misma duración" if dias_a == dias_b else "Duración distinta",
        delta=f"{dias_a}d vs {dias_b}d",
    )

    tendencia = "sube" if diferencia > 0 else ("baja" if diferencia < 0 else "permanece estable")
    _render_section_heading(
        4,
        "Lectura ejecutiva",
        "Apertura por rangos",
        "Se presentan primero los cortes temporales y luego la lectura resumida para ordenar la comparación operativa.",
    )
    _render_sequenced_panel(
        4,
        "Síntesis por rango",
        f"{label_b} frente a {label_a}",
        f"El segundo periodo {tendencia} en {abs(diferencia):,} hechos, con una variación de {abs(pct_var):.1f}%. La lectura temporal se alinea por posición relativa para que semanas o días equivalentes queden enfrentados.",
        tone="accent",
    )

    st.divider()

    _open_scene_stage(
        5,
        "Escena analítica",
        "Exploración táctica por rangos",
        "Después de la síntesis aparecen la evolución, los delitos, las comisarías y el detalle consolidado.",
        stage_class="analysis-stage",
    )
    tab_evolucion, tab_delitos, tab_comisarias, tab_tabla = st.tabs([
        "📅 Comparativo Temporal",
        "📋 Comparativo por Delito",
        "🏛️ Comparativo por Comisaría",
        "📊 Tabla Detallada",
    ])

    with tab_evolucion:
        st.markdown(f"### Comparativo por {granularidad_label}: {label_a} vs {label_b}")
        mostrar_texto = granularidad in {"semestres", "cuatrimestres", "trimestres", "bimestres", "meses"}
        if granularidad in {"semanas", "dias"}:
            st.caption("El subconjunto visible afecta solo esta vista. La exportación conserva la serie completa.")
        fig = charts.lineas_comparativo(
            df_comp_temporal_view,
            f"Comparativo por {granularidad_label} — {label_a} vs {label_b}",
            col_x="periodo_label",
            label_y1="Periodo A",
            label_y2="Periodo B",
            mostrar_texto=mostrar_texto,
            height=520 if granularidad in {"semanas", "dias"} else 450,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"#### Tabla comparativa por {granularidad_label.lower()}")
        _tabla_comparativa(df_comp_temporal_view, "periodo_label", label_a, label_b)

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
        st.caption("La tabla enfrenta la misma dependencia en ambos periodos y muestra 0 cuando una comisaría no registra hechos en uno de los tramos.")
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
        st.markdown("### Resumen consolidado")
        dimension = st.selectbox(
            "Dimensión a comparar",
            ["DELITO", "DIA_HECHO", "FRAN_HORAR", "LUGR_HECHO"],
            key="dimension_rangos",
        )
        df_comp = engine.comparativo_periodos_rango(desde_b, hasta_b, desde_a, hasta_a, dimension)
        _tabla_comparativa(df_comp, "categoria", label_a, label_b)

    _close_scene_stage()

    st.divider()
    _render_section_heading(
        6,
        "Salida operativa",
        "Cierre documental",
        "La exportación queda al final para cerrar el recorrido con evidencia descargable.",
    )
    _render_sequenced_panel(
        6,
        "Exportación",
        "Descarga de evidencias comparativas",
        "Las descargas conservan la serie completa, incluso cuando la visual actual muestra solo un subconjunto de semanas o días.",
    )
    _open_scene_stage(
        7,
        "Archivos finales",
        "Paquete exportable por rangos",
        "Este bloque reúne las salidas operativas para circular resultados o respaldar la presentación.",
        stage_class="export-stage",
    )
    st.markdown("### Descarga documental")
    slug_a = _slug_periodo(desde_a, hasta_a)
    slug_b = _slug_periodo(desde_b, hasta_b)
    excel_temporal = _to_excel_bytes({"Comparativo temporal": df_comp_temporal})
    excel_detalle = _to_excel_bytes({"Detalle": df_comp})
    excel_comisarias = _to_excel_bytes({"Comisarias": df_comp_com})
    col_csv_1, col_xlsx_1 = st.columns(2)
    with col_csv_1:
        st.download_button(
            "⬇️ Comparativo temporal (CSV)",
            df_comp_temporal.to_csv(index=False).encode("utf-8"),
            f"comparativo_{granularidad}_{slug_a}_vs_{slug_b}.csv",
            "text/csv",
        )
    with col_xlsx_1:
        st.download_button(
            "⬇️ Comparativo temporal (Excel)",
            excel_temporal,
            f"comparativo_{granularidad}_{slug_a}_vs_{slug_b}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    col_csv_2, col_xlsx_2 = st.columns(2)
    with col_csv_2:
        st.download_button(
            "⬇️ Tabla detallada (CSV)",
            df_comp.to_csv(index=False).encode("utf-8"),
            f"comparativo_detalle_{dimension.lower()}_{slug_a}_vs_{slug_b}.csv",
            "text/csv",
        )
    with col_xlsx_2:
        st.download_button(
            "⬇️ Tabla detallada (Excel)",
            excel_detalle,
            f"comparativo_detalle_{dimension.lower()}_{slug_a}_vs_{slug_b}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    col_csv_3, col_xlsx_3 = st.columns(2)
    with col_csv_3:
        st.download_button(
            "⬇️ Tabla por comisaría (CSV)",
            df_comp_com.to_csv(index=False).encode("utf-8"),
            f"comparativo_comisarias_{slug_a}_vs_{slug_b}.csv",
            "text/csv",
        )
    with col_xlsx_3:
        st.download_button(
            "⬇️ Tabla por comisaría (Excel)",
            excel_comisarias,
            f"comparativo_comisarias_{slug_a}_vs_{slug_b}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    _close_scene_stage()


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
    return f"DEL {desde.strftime('%d/%m/%Y')} AL {hasta.strftime('%d/%m/%Y')}"


def _slug_periodo(desde, hasta):
    if desde == hasta:
        return desde.strftime("%Y%m%d")
    return f"{desde.strftime('%Y%m%d')}_{hasta.strftime('%Y%m%d')}"
