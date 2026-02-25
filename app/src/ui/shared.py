"""
Utilidades compartidas para las páginas del dashboard.
Maneja la carga de datos con caché de Streamlit y filtros globales.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from app.src.data.loader import ShapefileLoader
from app.src.stats.engine import StatsEngine
from app.config.settings import MESES, MESES_LABELS, UNIDADES_REGIONALES


@st.cache_data(show_spinner="Cargando shapefiles... esto puede tomar unos minutos la primera vez.")
def cargar_datos() -> pd.DataFrame:
    """Carga todos los shapefiles con caché de Streamlit."""
    loader = ShapefileLoader()
    progress_bar = st.progress(0)
    status_text = st.empty()

    def callback(pct, msg):
        progress_bar.progress(pct)
        status_text.text(msg)

    df = loader.cargar_todo(use_cache=False, progress_callback=callback)
    progress_bar.empty()
    status_text.empty()
    return df


def get_engine(df: pd.DataFrame = None) -> StatsEngine:
    """Obtiene el StatsEngine con los datos actuales."""
    if df is None:
        df = cargar_datos()
    return StatsEngine(df)


def render_filtros_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renderiza filtros globales en el sidebar y devuelve el DataFrame filtrado.
    """
    with st.sidebar:
        st.markdown("### 🎯 Filtros")

        # Filtro de Año
        anios = sorted(df["_anio"].dropna().unique().astype(int).tolist())
        if anios:
            anio_sel = st.selectbox(
                "Año",
                ["Todos"] + anios,
                index=0,
            )
        else:
            anio_sel = "Todos"

        # Filtro de Unidad Regional
        urs = sorted(df["_unidad_regional"].dropna().unique().tolist())
        ur_labels = {k: f"{k} - {UNIDADES_REGIONALES.get(k, k)}" for k in urs}
        ur_options = ["Todas"] + [ur_labels.get(u, u) for u in urs]
        ur_sel = st.selectbox("Unidad Regional", ur_options, index=0)

        # Filtro de Mes
        mes_options = ["Todos"] + [MESES_LABELS.get(m, m) for m in MESES]
        mes_sel = st.selectbox("Mes", mes_options, index=0)

        # Filtro de Delito
        delitos = sorted(df["DELITO"].dropna().unique().tolist())
        delito_sel = st.selectbox("Tipo de Delito", ["Todos"] + delitos, index=0)

    # Aplicar filtros
    df_filtered = df.copy()

    if anio_sel != "Todos":
        df_filtered = df_filtered[df_filtered["_anio"] == int(anio_sel)]

    if ur_sel != "Todas":
        # Extraer código UR del label
        ur_code = ur_sel.split(" - ")[0] if " - " in ur_sel else ur_sel
        df_filtered = df_filtered[df_filtered["_unidad_regional"] == ur_code]

    if mes_sel != "Todos":
        # Buscar la clave del mes
        mes_key = next((k for k, v in MESES_LABELS.items() if v == mes_sel), None)
        if mes_key:
            df_filtered = df_filtered[df_filtered["MES_DENU"] == mes_key]

    if delito_sel != "Todos":
        df_filtered = df_filtered[df_filtered["DELITO"] == delito_sel]

    return df_filtered


def mostrar_metricas_header(engine: StatsEngine):
    """Muestra las 4 métricas principales en la parte superior."""
    resumen = engine.resumen()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Delitos", f"{resumen['total_delitos']:,}")
    c2.metric("Jurisdicciones", f"{resumen['total_jurisdicciones']:,}")
    c3.metric("Unidades Regionales", f"{resumen['total_unidades_regionales']:,}")
    c4.metric("Shapefiles", f"{resumen['total_shapefiles']:,}")
