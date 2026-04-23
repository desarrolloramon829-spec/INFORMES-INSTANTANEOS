"""
Página: Robos y Hurtos por Regional.
Cuadro resumen de robos y hurtos desglosado por comisaría
para cada Unidad Regional (Capital, Norte, Este, Oeste, Sur).
"""
from __future__ import annotations

import re
import unicodedata

import streamlit as st
import pandas as pd

from app.src.ui.shared import (
    cargar_datos,
    get_engine,
    render_filtros_sidebar,
    mostrar_metricas_header,
    _normalize,
    _build_juris_match,
)
from app.config.settings import (
    COMISARIAS_POR_REGION,
    UNIDADES_REGIONALES,
)
from app.src.charts.generator import ChartGenerator
from app.src.ui.editorial import close_stage, open_stage, render_hero, render_panel, render_section_heading

# ====================================================================
# Clasificación de delitos en ROBOS / HURTOS
# ====================================================================

_DELITOS_ROBO = {
    "010-ROBO",
    "020-TENTATIVAS_DE_ROBO",
    "030-ROBO_AGRAVADO",
    "040-TENTATIVA_DE_ROBO_AGRAVADO",
    "ROBO",
}

_DELITOS_HURTO = {
    "050-HURTO",
    "060-TENTATIVA_DE_HURTO",
    "HURTO",
}

# Orden de visualización de las URs (coincide con las imágenes de referencia)
_UR_ORDEN = [
    ("URC", "UNIDAD REGIONAL CAPITAL"),
    ("URN", "UNIDAD REGIONAL NORTE"),
    ("URE", "UNIDAD REGIONAL ESTE"),
    ("URO", "UNIDAD REGIONAL OESTE"),
    ("URS", "UNIDAD REGIONAL SUR"),
]


# ====================================================================
# Helpers
# ====================================================================

def _limpiar_nombre_comisaria(nombre: str) -> str:
    """
    Genera un nombre corto y legible para la tabla.
    Ej: 'Comisaria 1a' → 'COMISARIA 1°'
         'Cria. Yerba Buena' → 'YERBA BUENA'
         'Sub. Cria. Alto Verde' → 'ALTO VERDE'
         '[URC] Comisaria 1a' → 'COMISARIA 1°'
    """
    s = nombre.strip()
    # Quitar prefijo [UR] si existe
    s = re.sub(r"^\[.*?\]\s*", "", s)

    # Comisarías de Capital: "Comisaria Xa" → "COMISARIA X°"
    m = re.match(r"(?i)comisaria\s+(\d+)\s*a?$", s)
    if m:
        return f"COMISARIA {m.group(1)}°"

    # Quitar prefijos institucionales para las demás
    for pfx in (
        "Sub. Cria. de ", "Sub Cria. de ", "Sub.Cria. de ",
        "Sub. Cria. ", "Sub Cria. ", "Sub.Cria. ",
        "Cria. de ", "Cria. ",
        "Dest. ",
    ):
        if s.lower().startswith(pfx.lower()):
            s = s[len(pfx):]
            break

    return s.upper().strip()


def _construir_tabla_regional(
    df: pd.DataFrame,
    ur_code: str,
) -> pd.DataFrame:
    """
    Construye un DataFrame con columnas [COMISARIAS, ROBOS, HURTOS, TOTAL]
    para una Unidad Regional dada.
    Solo incluye comisarías oficiales definidas en COMISARIAS_POR_REGION.
    """
    # 1) Filtrar registros de esta UR
    df_ur = df[
        (df["_unidad_regional"] == ur_code)
        | (df["JURIS_HECH"].str.startswith(ur_code + "_", na=False))
    ].copy()

    # 2) Clasificar cada registro
    df_ur["_es_robo"] = df_ur["DELITO"].isin(_DELITOS_ROBO)
    df_ur["_es_hurto"] = df_ur["DELITO"].isin(_DELITOS_HURTO)

    # 3) Obtener mapeo display_name → juris_codes
    _, juris_match_map = _build_juris_match(df, ur_code)

    # 4) Usar SOLO las comisarías oficiales de COMISARIAS_POR_REGION
    official_names = COMISARIAS_POR_REGION.get(ur_code, [])

    # 5) Construir filas solo para comisarías oficiales
    filas = []
    for name in official_names:
        codes = juris_match_map.get(name, [])
        if not codes:
            continue
        mask = df_ur["JURIS_HECH"].isin(codes)
        robos = int(df_ur.loc[mask, "_es_robo"].sum())
        hurtos = int(df_ur.loc[mask, "_es_hurto"].sum())
        filas.append({
            "COMISARIAS": _limpiar_nombre_comisaria(name),
            "ROBOS": robos,
            "HURTOS": hurtos,
            "TOTAL": robos + hurtos,
        })

    if not filas:
        return pd.DataFrame(columns=["COMISARIAS", "ROBOS", "HURTOS", "TOTAL"])

    tabla = pd.DataFrame(filas)
    # Ordenar alfabéticamente por nombre de comisaría
    tabla = tabla.sort_values("COMISARIAS", ignore_index=True)
    return tabla


def _resumen_robos_hurtos(total_robos: int, total_hurtos: int) -> pd.DataFrame:
    """Construye una tabla simple para la dona global de robos vs hurtos."""
    total = total_robos + total_hurtos
    filas = [
        {"categoria": "ROBOS", "categoria_label": "Robos", "cantidad": total_robos},
        {"categoria": "HURTOS", "categoria_label": "Hurtos", "cantidad": total_hurtos},
    ]
    resumen = pd.DataFrame(filas)
    resumen["porcentaje"] = (
        (resumen["cantidad"] / total * 100).round(2) if total > 0 else 0.0
    )
    resumen["total"] = total
    return resumen


def _ranking_comisarias_robos_hurtos(
    df: pd.DataFrame,
    ur_code: str | None = None,
    top_n: int = 12,
) -> pd.DataFrame:
    """Consolida comisarías con sus totales de robos y hurtos para visualización."""
    frames = []

    for codigo, titulo_ur in _UR_ORDEN:
        if ur_code and codigo != ur_code:
            continue

        tabla = _construir_tabla_regional(df, codigo)
        if len(tabla) == 0:
            continue

        tabla = tabla.copy()
        tabla["UNIDAD_REGIONAL"] = codigo
        tabla["UNIDAD_REGIONAL_LABEL"] = titulo_ur
        tabla["categoria_label"] = (
            tabla["COMISARIAS"] if ur_code else tabla["UNIDAD_REGIONAL"] + " · " + tabla["COMISARIAS"]
        )
        frames.append(tabla)

    if not frames:
        return pd.DataFrame(columns=["COMISARIAS", "ROBOS", "HURTOS", "TOTAL", "categoria_label"])

    ranking = pd.concat(frames, ignore_index=True)
    ranking = ranking.sort_values(["TOTAL", "ROBOS", "HURTOS"], ascending=False, ignore_index=True)
    return ranking.head(top_n).copy()


def _generar_tabla_html(df: pd.DataFrame, titulo_ur: str) -> str:
    """
    Genera HTML de una tabla estilizada con encabezado azul oscuro
    y fila de totales amarilla, idéntica al diseño de referencia.
    Usa estilos inline en cada elemento para garantizar renderizado
    correcto en Streamlit.
    """
    total_robos = int(df["ROBOS"].sum())
    total_hurtos = int(df["HURTOS"].sum())
    total_total = int(df["TOTAL"].sum())

    rows_html = ""
    for _, row in df.iterrows():
        rows_html += (
            f'<tr>'
            f'<td style="text-align:left;font-weight:bold;">{row["COMISARIAS"]}</td>'
            f'<td style="text-align:center;">{int(row["ROBOS"])}</td>'
            f'<td style="text-align:center;">{int(row["HURTOS"])}</td>'
            f'<td style="text-align:center;font-weight:bold;">{int(row["TOTAL"])}</td>'
            f'</tr>'
        )

    # Fila TOTAL
    rows_html += (
        '<tr class="total-row">'
        '<td style="text-align:left;font-weight:bold;">TOTAL</td>'
        f'<td style="text-align:center;font-weight:bold;">{total_robos}</td>'
        f'<td style="text-align:center;font-weight:bold;">{total_hurtos}</td>'
        f'<td style="text-align:center;font-weight:bold;">{total_total}</td>'
        '</tr>'
    )

    html = (
        f'<div style="margin-bottom:20px;font-family:var(--font-ui);background-color:var(--app-surface); border: 1px solid var(--app-border); border-radius: 8px;">'
        f'<div style="text-align:center;color:#ffffff;background-color:#000000;padding:14px 20px;border-radius:8px 8px 0 0;font-size:1.5rem;font-weight:bold;letter-spacing:1px;">{titulo_ur}</div>'
        f'<table class="styled-table" style="margin: 0; border-radius: 0 0 8px 8px; border: none;">'
        f'<thead><tr>'
        f'<th style="text-align:left;min-width:180px;">COMISARIAS</th>'
        f'<th style="text-align:center;">ROBOS</th>'
        f'<th style="text-align:center;">HURTOS</th>'
        f'<th style="text-align:center;">TOTAL</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>'
    )
    return html


# ====================================================================
# Render principal
# ====================================================================

def render():
    df = cargar_datos()
    df_filtered = render_filtros_sidebar(df)
    engine = get_engine(df_filtered)
    charts = ChartGenerator()

    render_hero(
        "Delitos patrimoniales",
        "Robos y hurtos por regional",
        "Página de cuadro resumen por unidad regional y comisaría para exponer robos y hurtos sobre la base filtrada vigente.",
        chips=["Resumen por regional", "Detalle por comisaría", "Exportación CSV"],
        seq=1,
    )

    mostrar_metricas_header(engine)
    st.divider()

    # Filtrar solo robos y hurtos
    delitos_rh = _DELITOS_ROBO | _DELITOS_HURTO
    df_rh = df_filtered[df_filtered["DELITO"].isin(delitos_rh)].copy()

    if len(df_rh) == 0:
        st.warning("No hay datos de robos ni hurtos para los filtros seleccionados.")
        return

    # Métricas rápidas de Robos vs Hurtos
    total_robos = int(df_rh["DELITO"].isin(_DELITOS_ROBO).sum())
    total_hurtos = int(df_rh["DELITO"].isin(_DELITOS_HURTO).sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Robos", f"{total_robos:,}")
    c2.metric("Total Hurtos", f"{total_hurtos:,}")
    c3.metric("Total General", f"{total_robos + total_hurtos:,}")

    render_section_heading(
        2,
        "Lectura principal",
        "Balance patrimonial",
        "Las métricas abren la página y anticipan el peso relativo entre robos y hurtos antes del detalle regional.",
    )
    delito_dominante = "Robos" if total_robos >= total_hurtos else "Hurtos"
    render_panel(
        2,
        "Síntesis",
        f"Predominan {delito_dominante}",
        f"La diferencia entre ambos grupos es de {abs(total_robos - total_hurtos):,} hechos dentro de la muestra filtrada.",
        tone="accent",
    )

    st.divider()

    # Determinar qué URs mostrar según el filtro de UR del sidebar
    urs_en_datos = set(df_rh["_unidad_regional"].dropna().unique())
    urs_disponibles = []
    for ur_code, _ in _UR_ORDEN:
        if ur_code in urs_en_datos or df_rh["JURIS_HECH"].str.startswith(ur_code + "_", na=False).any():
            urs_disponibles.append(ur_code)

    render_section_heading(
        3,
        "Lectura visual",
        "Distribución ejecutiva",
        "Antes del bloque tabular, la vista resume el peso relativo entre robos y hurtos y muestra dónde se concentra el volumen por comisaría.",
    )
    open_stage(
        3,
        "Visualización inicial",
        "Resumen patrimonial",
        "La dona fija la relación global y el ranking comparado baja al detalle operativo por dependencia.",
        stage_class="analysis-stage",
    )

    df_resumen = _resumen_robos_hurtos(total_robos, total_hurtos)
    col_ctrl1, col_ctrl2 = st.columns([1.2, 0.8])
    with col_ctrl1:
        ur_selector = st.selectbox(
            "Regional a visualizar",
            ["Todas"] + urs_disponibles,
            format_func=lambda code: "Todas las regionales" if code == "Todas" else dict(_UR_ORDEN).get(code, code),
            key="robos_hurtos_ur_selector",
        )
    with col_ctrl2:
        top_n = st.slider(
            "Comisarías visibles",
            min_value=5,
            max_value=20,
            value=10,
            key="robos_hurtos_top_n",
        )

    df_chart = _ranking_comisarias_robos_hurtos(
        df_rh,
        ur_code=None if ur_selector == "Todas" else ur_selector,
        top_n=top_n,
    )
    shared_chart_height = max(420, min(920, 220 + top_n * 28))

    col_chart_left, col_chart_right = st.columns([0.9, 1.6])

    with col_chart_left:
        fig = charts.dona(
            df_resumen,
            "Participación global de robos y hurtos",
            height=shared_chart_height,
        )
        st.plotly_chart(fig, width="stretch")

    with col_chart_right:
        if len(df_chart) > 0:
            fig = charts.barras_horizontal_comparativo(
                df_chart.iloc[::-1],
                "Comparativo de robos y hurtos por comisaría",
                col_cat="categoria_label",
                col_y1="ROBOS",
                col_y2="HURTOS",
                label_y1="Robos",
                label_y2="Hurtos",
                height=shared_chart_height,
            )
            st.plotly_chart(fig, width="stretch")

            lider = df_chart.iloc[0]
            st.caption(
                f"Mayor volumen visible: {lider['categoria_label']} con {int(lider['TOTAL']):,} hechos ({int(lider['ROBOS']):,} robos y {int(lider['HURTOS']):,} hurtos)."
            )
        else:
            st.info("Sin comisarías disponibles para el recorte seleccionado.")

    close_stage()

    # Generar tablas por cada UR
    tablas_csv = []

    open_stage(
        4,
        "Escena analítica",
        "Cuadros por unidad regional",
        "La secuencia central presenta cada unidad regional como bloque independiente para una lectura rápida por comisaría.",
        stage_class="analysis-stage",
    )

    for ur_code, titulo_ur in _UR_ORDEN:
        if ur_code not in urs_en_datos:
            # Verificar si hay registros con JURIS_HECH que empiece con este código
            tiene_juris = df_rh["JURIS_HECH"].str.startswith(
                ur_code + "_", na=False
            ).any()
            if not tiene_juris:
                continue

        tabla = _construir_tabla_regional(df_rh, ur_code)
        if len(tabla) == 0:
            continue

        html = _generar_tabla_html(tabla, titulo_ur)
        st.markdown(html, unsafe_allow_html=True)

        # Botones de descarga individual por regional
        col_csv, col_excel, _ = st.columns([1, 1, 3])
        with col_csv:
            csv_individual = tabla.to_csv(index=False).encode("utf-8")
            st.download_button(
                f"⬇️ CSV {ur_code}",
                data=csv_individual,
                file_name=f"robos_hurtos_{ur_code}.csv",
                mime="text/csv",
                key=f"download_csv_{ur_code}",
            )
        with col_excel:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                tabla.to_excel(writer, index=False, sheet_name=titulo_ur[:31])
            st.download_button(
                f"⬇️ Excel {ur_code}",
                data=buffer.getvalue(),
                file_name=f"robos_hurtos_{ur_code}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_excel_{ur_code}",
            )

        # Acumular para CSV
        tabla_export = tabla.copy()
        tabla_export.insert(0, "UNIDAD_REGIONAL", titulo_ur)
        tablas_csv.append(tabla_export)

    close_stage()

    # ---- Exportar ----
    if tablas_csv:
        st.divider()
        render_section_heading(
            5,
            "Cierre documental",
            "Exportación patrimonial",
            "La salida final consolida todas las regionales en un único archivo para distribución, respaldo o archivo.",
        )
        open_stage(
            5,
            "Archivo final",
            "Descarga consolidada",
            "Incluye todas las tablas regionales generadas en la vista actual.",
            stage_class="export-stage",
        )
        st.markdown("### Descarga documental")
        df_export = pd.concat(tablas_csv, ignore_index=True)

        col_csv_all, col_excel_all = st.columns(2)
        with col_csv_all:
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Descargar Todo (CSV)",
                data=csv,
                file_name="robos_y_hurtos_por_regional.csv",
                mime="text/csv",
                key="download_csv_consolidado",
            )
        with col_excel_all:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Consolidado")
                # Una hoja por regional
                for tabla_ur in tablas_csv:
                    ur_name = tabla_ur["UNIDAD_REGIONAL"].iloc[0] if len(tabla_ur) > 0 else "Regional"
                    sheet_name = ur_name[:31]  # Excel limita a 31 chars
                    tabla_ur.to_excel(writer, index=False, sheet_name=sheet_name)
            st.download_button(
                "⬇️ Descargar Todo (Excel)",
                data=buffer.getvalue(),
                file_name="robos_y_hurtos_por_regional.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_consolidado",
            )
        close_stage()
