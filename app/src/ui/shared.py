"""
Utilidades compartidas para las páginas del dashboard.
Maneja la carga de datos con caché de Streamlit y filtros globales.
"""
from __future__ import annotations

import datetime
import calendar
import os
import re
import unicodedata

import streamlit as st
import pandas as pd

from app.src.data.loader import (
    ShapefileLoader,
    extraer_anio_mes,
    extraer_fecha,
    parse_curly_braces,
)
from app.src.stats.engine import StatsEngine
from app.config.settings import (
    MESES, MESES_LABELS, UNIDADES_REGIONALES, COMISARIAS_POR_REGION,
)


def _resolve_loader_debug_options() -> dict:
    """Resuelve opciones de diagnóstico del loader a partir del entorno."""
    debug_enabled = os.getenv("INFORMES_DEBUG_DIAGNOSTICS", "0").strip().lower() in {"1", "true", "yes", "on"}
    diagnostic_path = os.getenv(
        "INFORMES_DEBUG_DIAGNOSTICS_PATH",
        "diagnostics/reporte_diagnostico_carga.json",
    ).strip()

    return {
        "diagnostic_json_path": diagnostic_path if debug_enabled and diagnostic_path else None,
    }


def _ensure_filter_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Reconstruye columnas derivadas y garantiza el esquema mínimo de filtros."""
    if df is None:
        df = pd.DataFrame()

    df = df.copy()

    if "_anio" not in df.columns and "anio" in df.columns:
        df["_anio"] = pd.to_numeric(df["anio"], errors="coerce")

    if "FECHA_HECH" in df.columns:
        if "_anio" not in df.columns or "_mes_num" not in df.columns:
            parsed = df["FECHA_HECH"].apply(extraer_anio_mes)
            if "_anio" not in df.columns:
                df["_anio"] = parsed.apply(lambda value: value[0])
            if "_mes_num" not in df.columns:
                df["_mes_num"] = parsed.apply(lambda value: value[1])

        if "_fecha" not in df.columns:
            df["_fecha"] = df["FECHA_HECH"].apply(extraer_fecha)

    required_defaults = {
        "_anio": None,
        "_mes_num": None,
        "_fecha": None,
        "_unidad_regional": None,
        "_shapefile_key": None,
        "JURIS_HECH": None,
        "DELITO": None,
        "MODUS_OPER": None,
        "MES_DENU": None,
        "DIA_HECHO": None,
        "FRAN_HORAR": None,
        "HORA_HECH": None,
        "FECHA_HECH": None,
        "DPCIA_INT": None,
        "HECH_RESUE": None,
    }
    for column, default in required_defaults.items():
        if column not in df.columns:
            df[column] = default

    return df


@st.cache_data(show_spinner="Cargando shapefiles... esto puede tomar unos minutos la primera vez.")
def cargar_datos() -> pd.DataFrame:
    """Carga todos los shapefiles con caché de Streamlit."""
    loader = ShapefileLoader()
    progress_bar = st.progress(0)
    status_text = st.empty()

    def callback(pct, msg):
        progress_bar.progress(pct)
        status_text.text(msg)

    debug_options = _resolve_loader_debug_options()
    df = loader.cargar_todo(use_cache=True, progress_callback=callback, **debug_options)
    progress_bar.empty()
    status_text.empty()
    return _ensure_filter_schema(df)


def regenerar_datos():
    """Invalida todos los cachés y fuerza re-lectura desde shapefiles."""
    loader = ShapefileLoader.get_instance()
    loader.invalidar_cache(incluir_parquet=True)
    cargar_datos.clear()  # Limpiar caché de Streamlit
    st.rerun()


def get_engine(df: pd.DataFrame = None) -> StatsEngine:
    """Obtiene el StatsEngine con los datos actuales."""
    if df is None:
        df = cargar_datos()
    return StatsEngine(df)


def render_boton_regenerar():
    """Renderiza botón de regeneración de datos en el sidebar."""
    with st.sidebar:
        st.divider()
        if st.button("🔄 Regenerar datos", help="Fuerza re-lectura desde shapefiles originales. Usar cuando hay datos nuevos."):
            regenerar_datos()


# ====================================================================
# Normalización para matching robusto entre JURIS_HECH y nombres display
# ====================================================================

def _normalize(text: str) -> str:
    """
    Normaliza un texto para comparación:
    - Quita acentos
    - Quita prefijos UR (URC_, URE_, …)
    - Quita prefijos institucionales (COMISARIA_DE_, COMISARIA__, Cria., Sub., etc.)
    - Expande abreviaturas comunes (V.→VILLA, Sta.→SANTA, etc.)
    - Reemplaza _ por espacio, colapsa espacios
    - Para URC: quita la 'A' final de números ('10A' → '10')
    - Pasa a MAYÚSCULAS
    """
    # Quitar acentos
    s = unicodedata.normalize("NFKD", str(text))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().strip()

    # Quitar prefijos UR
    for pfx in ("URC_", "URE_", "URO_", "URS_", "URN_"):
        if s.startswith(pfx):
            s = s[len(pfx):]
            break

    # Quitar prefijos institucionales (en datos: COMISARIA_DE_, COMISARIA__,
    # COMISARIA_, SUBCOMISARIA_, DESTACAMENTO_)
    for pfx in (
        "COMISARIA_DE_", "COMISARIA__", "COMISARIA_",
        "SUBCOMISARIA_DE_", "SUBCOMISARIA_",
        "DESTACAMENTO_",
    ):
        if s.startswith(pfx):
            s = s[len(pfx):]
            break

    # Quitar prefijos institucionales (en labels: COMISARIA, CRIA., SUB. CRIA., etc.)
    for pfx in (
        "SUB. CRIA. DE ", "SUB CRIA. DE ", "SUB.CRIA. DE ",
        "SUB. CRIA. ", "SUB CRIA. ", "SUB.CRIA. ",
        "CRIA. DE ", "CRIA. ",
        "COMISARIA ",
        "DEST. ",
    ):
        if s.startswith(pfx):
            s = s[len(pfx):]
            break

    # Reemplazar _ y colapsar espacios
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()

    # Expandir abreviaturas comunes
    _ABBR = {
        "V.": "VILLA",
        "STA.": "SANTA",
        "J. B.": "JUAN BAUTISTA",
        "B.": "BENJAMIN",
        "P.": "PADRE",
        "TTE.": "TENIENTE",
        "GRAL.": "GENERAL",
        "CAP.": "CAPITAN",
    }
    for abbr, full in _ABBR.items():
        s = s.replace(abbr, full)
    s = re.sub(r"\s+", " ", s).strip()

    # Quitar 'A' final si es un número de comisaría ("10A" → "10", "1A" → "1")
    m = re.match(r"^(\d+)\s*A$", s)
    if m:
        s = m.group(1)

    return s


def _build_juris_match(
    df: pd.DataFrame,
    ur_code: str | None,
) -> tuple[list[str], dict[str, list[str]]]:
    """
    Construye la lista de comisarías para el dropdown y el mapa
    {nombre_display → [JURIS_HECH codes...]} para filtrar.

    Devuelve:
        (display_names, match_map)
    """
    # 1) Obtener los JURIS_HECH reales del DataFrame, incluyendo ESPECIALES
    if ur_code and ur_code != "ESPECIAL":
        mask_data = (
            (df["_unidad_regional"] == ur_code)
            | (df["JURIS_HECH"].str.startswith(ur_code + "_", na=False))
        )
    else:
        mask_data = pd.Series(True, index=df.index)

    juris_reales = set(df.loc[mask_data, "JURIS_HECH"].dropna().unique())

    # 2) Nombres display desde COMISARIAS_POR_REGION
    if ur_code and ur_code in COMISARIAS_POR_REGION:
        display_names = list(COMISARIAS_POR_REGION[ur_code])
    elif ur_code:
        # UR no tiene lista definida (ej. ESPECIAL): usar fallback dinámico
        display_names = []
    else:
        # "Todas" – concatenar todas las regiones con prefijo [UR]
        display_names = []
        for ur, nombres in COMISARIAS_POR_REGION.items():
            for n in nombres:
                display_names.append(f"[{ur}] {n}")

    # 3) Construir mapa normalizado: display_name → [juris_codes...]
    # Pre-normalizar todos los códigos reales
    norm_to_codes: dict[str, list[str]] = {}
    for code in juris_reales:
        nk = _normalize(code)
        norm_to_codes.setdefault(nk, []).append(code)

    match_map: dict[str, list[str]] = {}
    matched_codes: set[str] = set()

    for name in display_names:
        nk = _normalize(name)
        codes = norm_to_codes.get(nk, [])
        if codes:
            match_map[name] = codes
            matched_codes.update(codes)

    # Segundo pase: substring match para abreviaturas como "Piedrabuena" → "GOBERNADOR PIEDRABUENA"
    for name in display_names:
        if name in match_map:
            continue
        nk = _normalize(name)
        if not nk:
            continue
        best: list[str] = []
        for norm_code, codes_list in norm_to_codes.items():
            if any(c in matched_codes for c in codes_list):
                continue  # Ya fue matcheado por otro nombre
            # El nombre normalizado es parte del código, o viceversa
            if nk in norm_code or norm_code in nk:
                best.extend(codes_list)
        if best:
            match_map[name] = best
            matched_codes.update(best)

    # 4) Agregar jurisdicciones que están en los datos pero no en la lista
    unmatched = juris_reales - matched_codes
    for code in sorted(unmatched):
        # Generar un label legible como fallback
        label = _fallback_label(code, ur_code)
        display_names.append(label)
        match_map[label] = [code]

    return display_names, match_map


def _fallback_label(code: str, ur_code: str | None) -> str:
    """Genera un label legible de un código JURIS_HECH no encontrado en la lista."""
    name = code
    for pfx in ("URC_", "URE_", "URO_", "URS_", "URN_"):
        if name.startswith(pfx):
            name = name[len(pfx):]
            break
    label = (
        name.replace("COMISARIA_DE_", "Cria. ")
            .replace("COMISARIA__", "Comisaria ")
            .replace("COMISARIA_", "Cria. ")
            .replace("SUBCOMISARIA_DE_", "Sub. Cria. ")
            .replace("SUBCOMISARIA_", "Sub. Cria. ")
            .replace("DESTACAMENTO_", "Dest. ")
            .replace("_", " ")
            .title()
    )
    if ur_code is None:
        # Agregar prefijo UR para desambiguar
        ur = code.split("_")[0] if "_" in code else ""
        if ur:
            label = f"[{ur}] {label}"
    return label


# ====================================================================
# Filtros del sidebar
# ====================================================================

def render_filtros_sidebar(
    df: pd.DataFrame,
    excluir: set[str] | None = None,
) -> pd.DataFrame:
    """
    Renderiza filtros globales en el sidebar y devuelve el DataFrame filtrado.
    Incluye: Año, Unidad Regional, Comisaría/Jurisdicción (dinámica), Mes,
    Tipo de Delito y Modus Operandi.

    Parameters
    ----------
    excluir : set[str] | None
        Conjunto de filtros a omitir.  Claves válidas:
        ``"anio"`` — no muestra ni aplica filtro de Año.
        ``"fecha_rango"`` — no muestra ni aplica Desde / Hasta.
    """
    _excluir: set[str] = excluir or set()
    df = _ensure_filter_schema(df)

    with st.sidebar:
        st.markdown("### 🎯 Filtros")

        # ---- Filtro de Año ----
        if "anio" not in _excluir:
            anios = sorted(df["_anio"].dropna().unique().astype(int).tolist())
            if anios:
                anio_sel = st.selectbox("Año", ["Todos"] + anios, index=0)
            else:
                anio_sel = "Todos"
        else:
            anio_sel = "Todos"

        # ---- Filtro de Unidad Regional ----
        urs = sorted(
            u for u in df["_unidad_regional"].dropna().unique().tolist()
            if u != "ESPECIAL"
        )
        ur_labels = {k: f"{k} - {UNIDADES_REGIONALES.get(k, k)}" for k in urs}
        ur_options = ["Todas"] + [ur_labels.get(u, u) for u in urs]
        ur_sel = st.selectbox("Unidad Regional", ur_options, index=0)

        # Determinar código UR seleccionado
        ur_code = None
        if ur_sel != "Todas":
            ur_code = ur_sel.split(" - ")[0] if " - " in ur_sel else ur_sel

        # ---- Filtro de Comisaría / Jurisdicción (dinámico según UR) ----
        display_names, juris_match_map = _build_juris_match(df, ur_code)
        juris_display = ["Todas"] + display_names
        juris_sel = st.selectbox("Comisaría / Jurisdicción", juris_display, index=0)

        # ---- Filtro de Mes ----
        mes_options = ["Todos"] + [MESES_LABELS.get(m, m) for m in MESES]
        mes_sel = st.selectbox("Mes", mes_options, index=0)

        # ---- Filtro de Rango de Fechas (Desde / Hasta) ----
        # Determinar rango por defecto según Año y Mes seleccionados
        _has_fecha = (
            "fecha_rango" not in _excluir
            and "_fecha" in df.columns
            and df["_fecha"].notna().any()
        )
        if _has_fecha:
            _fecha_min = df["_fecha"].dropna().min()
            _fecha_max = df["_fecha"].dropna().max()

            # Ajustar según Año y Mes seleccionados
            if anio_sel != "Todos":
                _a = int(anio_sel)
                if mes_sel != "Todos":
                    _mk = next((k for k, v in MESES_LABELS.items() if v == mes_sel), None)
                    _m = MESES.index(_mk) + 1 if _mk and _mk in MESES else 1
                    _default_desde = datetime.date(_a, _m, 1)
                    _default_hasta = datetime.date(_a, _m, calendar.monthrange(_a, _m)[1])
                else:
                    _default_desde = datetime.date(_a, 1, 1)
                    _default_hasta = datetime.date(_a, 12, 31)
            else:
                _default_desde = _fecha_min
                _default_hasta = _fecha_max

            # Asegurar que los defaults estén dentro del rango real
            if _default_desde < _fecha_min:
                _default_desde = _fecha_min
            if _default_hasta > _fecha_max:
                _default_hasta = _fecha_max

            st.markdown("**Rango de Fechas**")
            col_desde, col_hasta = st.columns(2)
            with col_desde:
                fecha_desde = st.date_input(
                    "Desde",
                    value=_default_desde,
                    min_value=_fecha_min,
                    max_value=_fecha_max,
                )
            with col_hasta:
                fecha_hasta = st.date_input(
                    "Hasta",
                    value=_default_hasta,
                    min_value=_fecha_min,
                    max_value=_fecha_max,
                )
        else:
            fecha_desde = None
            fecha_hasta = None

        # ---- Filtro de Delito (multiselect) ----
        delitos = sorted(df["DELITO"].dropna().unique().tolist())
        delito_sel = st.multiselect(
            "Tipo de Delito",
            options=delitos,
            default=[],
            placeholder="Todos",
            key="filtro_tipo_delito",
        )

        # ---- Filtro de Modus Operandi (multiselect) ----
        modus_set: set[str] = set()
        for val in df["MODUS_OPER"].dropna().unique():
            for m in parse_curly_braces(str(val)):
                clean = m.strip()
                if clean and clean not in {"#NO_CONSTA", "#OTROS", "zzz", "TEST"}:
                    modus_set.add(clean)
        modus_list = sorted(modus_set)
        modus_labels = {m: m.replace("_", " ").title() for m in modus_list}
        modus_display = [modus_labels[m] for m in modus_list]
        modus_sel = st.multiselect(
            "Modus Operandi",
            options=modus_display,
            default=[],
            placeholder="Todos",
        )

    # ================================================================
    # Aplicar filtros
    # ================================================================
    df_filtered = df.copy()

    if anio_sel != "Todos":
        df_filtered = df_filtered[df_filtered["_anio"] == int(anio_sel)]

    if ur_code:
        # Filtrar SOLO por la UR seleccionada.
        # Los registros ESPECIALES (CARGA_FINCAS/ABIGEATO) quedan excluidos
        # para evitar doble conteo; solo son visibles con "Todas" o "ESPECIAL".
        df_filtered = df_filtered[
            df_filtered["_unidad_regional"] == ur_code
        ]

    if juris_sel != "Todas":
        # Obtener los códigos JURIS_HECH que coinciden con la selección
        matched_codes = juris_match_map.get(juris_sel, [])
        if matched_codes:
            df_filtered = df_filtered[
                df_filtered["JURIS_HECH"].isin(matched_codes)
            ]

    if mes_sel != "Todos":
        mes_key = next((k for k, v in MESES_LABELS.items() if v == mes_sel), None)
        if mes_key:
            df_filtered = df_filtered[df_filtered["MES_DENU"] == mes_key]

    # Aplicar rango de fechas
    if fecha_desde is not None and fecha_hasta is not None and "_fecha" in df_filtered.columns:
        mask_fecha = df_filtered["_fecha"].apply(
            lambda x: fecha_desde <= x <= fecha_hasta if x is not None else False
        )
        df_filtered = df_filtered[mask_fecha]

    if delito_sel:  # lista no vacía → filtrar
        df_filtered = df_filtered[df_filtered["DELITO"].isin(delito_sel)]

    if modus_sel:  # lista no vacía → filtrar
        # Convertir labels seleccionados de vuelta a claves internas
        modus_keys_sel = [
            k for k, v in modus_labels.items() if v in modus_sel
        ]
        if modus_keys_sel:
            modus_keys_set = set(modus_keys_sel)
            mask = df_filtered["MODUS_OPER"].apply(
                lambda x: bool(modus_keys_set & set(parse_curly_braces(str(x))))
                if pd.notna(x) else False
            )
            df_filtered = df_filtered[mask]

    return df_filtered


def mostrar_metricas_header(engine: StatsEngine):
    """Muestra las 4 métricas principales en la parte superior."""
    resumen = engine.resumen()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Delitos", f"{resumen['total_delitos']:,}")
    c2.metric("Jurisdicciones", f"{resumen['total_jurisdicciones']:,}")
    c3.metric("Unidades Regionales", f"{resumen['total_unidades_regionales']:,}")
    c4.metric("Shapefiles", f"{resumen['total_shapefiles']:,}")
