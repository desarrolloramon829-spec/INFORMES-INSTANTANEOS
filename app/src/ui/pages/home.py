"""
Página de inicio - Dashboard resumen.
"""
from html import escape

import streamlit as st
from app.src.ui.shared import cargar_datos, get_engine, render_filtros_sidebar, mostrar_metricas_header
from app.src.charts.generator import ChartGenerator


def _render_home_hero(resumen, total_registros):
    anios = resumen.get("anios_disponibles", [])
    anios_texto = ", ".join(str(anio) for anio in anios) if anios else "Sin años detectados"
    st.markdown(
        f"""
        <section class="editorial-hero scene-seq seq-1">
            <div class="editorial-kicker">Centro de mando analítico</div>
            <h1>Panel ejecutivo del mapa delictual</h1>
            <p class="editorial-lead">
                Vista de síntesis para exposición rápida: concentra volumen, patrón dominante y distribución territorial
                sobre la base filtrada vigente. La idea es que la lectura principal aparezca en los primeros segundos.
            </p>
            <div class="editorial-meta-row">
                <span class="editorial-chip">{total_registros:,} registros analizados</span>
                <span class="editorial-chip">Años disponibles: {escape(anios_texto)}</span>
                <span class="editorial-chip">Enfoque institucional y de presentación</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


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


def _render_sequenced_panel(seq, kicker, titulo, cuerpo, tone="", extra_class=""):
    tone_class = f" {tone}" if tone else ""
    extra_class_name = f" {extra_class}" if extra_class else ""
    st.markdown(
        f"""
        <section class="editorial-panel scene-seq seq-{seq}{tone_class}{extra_class_name}">
            <div class="editorial-kicker">{escape(kicker)}</div>
            <h3>{escape(titulo)}</h3>
            <p>{escape(cuerpo)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _wrap_franja_label(label):
    text = str(label)
    if " " not in text:
        return text
    tramo, resto = text.split(" ", 1)
    return f"{tramo}<br>{resto}"


def render():
    # Cargar y filtrar datos
    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()
    resumen = engine.resumen()

    _render_home_hero(resumen, engine.total_registros)

    # Métricas principales
    mostrar_metricas_header(engine)
    st.divider()

    _render_section_heading(
        3,
        "Lecturas rápidas",
        "Síntesis inmediata del tablero",
        "Estos tres bloques fijan la lectura inicial antes de pasar a la evidencia visual.",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        _render_sequenced_panel(
            3,
            "Incidencia principal",
            "Delito dominante",
            f"La modalidad con mayor recurrencia en la selección actual es {resumen['delito_mas_frecuente']}.",
            tone="accent",
        )

    with col2:
        dia = resumen["dia_mas_frecuente"].title() if resumen["dia_mas_frecuente"] != "N/A" else "N/A"
        _render_sequenced_panel(
            4,
            "Patrón semanal",
            "Día crítico",
            f"El mayor volumen operativo se concentra en {dia}.",
        )

    with col3:
        franja = resumen["franja_mas_frecuente"]
        if franja and franja != "N/A":
            franja_display = franja.replace("_", " ")
        else:
            franja_display = "N/A"
        _render_sequenced_panel(
            5,
            "Pulso horario",
            "Franja más activa",
            f"La concentración principal de hechos aparece en {franja_display}.",
            tone="success",
        )

    st.divider()
    _render_section_heading(
        6,
        "Panorama operativo",
        "Evidencia visual prioritaria",
        "La lectura sigue con composición delictual, frecuencia semanal, ritmo horario y reparto territorial.",
    )

    # Gráficos resumen
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Modalidades con mayor presión")
        st.caption("Jerarquiza la composición delictual dominante dentro del universo filtrado vigente.")
        df_modal = engine.delitos_por_modalidad()
        modal_chart_height = None
        if len(df_modal) > 0:
            fig = charts.barras_horizontal(df_modal, "Top Delitos por Modalidad")
            modal_chart_height = fig.layout.height
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sin datos para mostrar")

    with col_right:
        st.markdown("### Cadencia semanal")
        st.caption("Expone qué días concentran mayor carga operativa para lectura ejecutiva rápida.")
        df_dia = engine.delitos_por_dia_semana()
        if len(df_dia) > 0:
            fig = charts.barras_vertical(df_dia, "Delitos por Día", height=modal_chart_height)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sin datos para mostrar")

    col_left2, col_right2 = st.columns(2)
    second_row_chart_height = 520

    with col_left2:
        st.markdown("### Ritmo por franja horaria")
        st.caption("Identifica las ventanas horarias donde la activación delictiva gana mayor intensidad.")
        df_franja = engine.delitos_por_franja_horaria()
        if len(df_franja) > 0:
            df_franja_plot = df_franja.copy()
            if "categoria_label" in df_franja_plot.columns:
                df_franja_plot["categoria_label"] = df_franja_plot["categoria_label"].apply(_wrap_franja_label)
            fig = charts.barras_vertical(
                df_franja_plot,
                "Distribución por Franja Horaria",
                color="#ED7D31",
                height=second_row_chart_height,
            )
            fig.update_xaxes(tickangle=0)
            fig.update_layout(margin=dict(b=120, t=78))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sin datos para mostrar")

    with col_right2:
        st.markdown("### Peso territorial por unidad regional")
        st.caption("Resume el reparto territorial del volumen observado para una lectura institucional de síntesis.")
        df_ur = engine.delitos_por_unidad_regional()
        if len(df_ur) > 0:
            fig = charts.dona(df_ur, "Distribución por Unidad Regional", height=second_row_chart_height)
            fig.update_traces(textposition="inside", selector=dict(type="pie"))
            fig.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.01,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10),
                ),
                margin=dict(t=96, b=44, l=28, r=28),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sin datos para mostrar")

    st.divider()
    _render_section_heading(
        7,
        "Cruce rápido",
        "Resumen de intensidad temporal",
        "Una matriz compacta cruza día y franja para detectar rápidamente la combinación operativa más cargada del tablero actual.",
    )

    pivot_dia_franja = engine.matriz_dia_franja()
    if not pivot_dia_franja.empty:
        st.markdown("### Día versus franja")
        st.caption("Lectura compacta del cruce temporal más útil para detectar concentración operativa.")
        col_heatmap, col_summary = st.columns([1.7, 1])
        with col_heatmap:
            fig = charts.heatmap(pivot_dia_franja, "Mapa rápido día y franja", height=380)
            st.plotly_chart(fig, use_container_width=True)

        with col_summary:
            dia_max, franja_max = pivot_dia_franja.stack().idxmax()
            valor_maximo = int(pivot_dia_franja.to_numpy().max())
            _render_sequenced_panel(
                7,
                "Intersección crítica",
                "Mayor presión temporal",
                f"La combinación más intensa se ubica en {dia_max} y {franja_max.replace(chr(10), ' / ')}, con {valor_maximo:,} hechos registrados.",
                tone="accent",
                extra_class="panel-match-heatmap",
            )
    else:
        st.info("No hay datos suficientes para resumir el cruce día versus franja.")

    # Años disponibles
    st.divider()
    _render_section_heading(
        8,
        "Cobertura del tablero",
        "Marco de disponibilidad",
        "Cierre de la página con el alcance temporal efectivo de la base analizada.",
    )
    anios = resumen.get("anios_disponibles", [])
    if anios:
        _render_sequenced_panel(
            8,
            "Disponibilidad",
            "Base consolidada lista para análisis",
            f"Años con datos: {', '.join(str(a) for a in anios)}. Total de registros vigentes: {engine.total_registros:,}.",
        )
    else:
        st.info("No se encontraron datos con fecha válida.")
