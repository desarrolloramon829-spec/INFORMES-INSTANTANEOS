"""
Generador de informes por página.

Recolecta gráficos y métricas de cada sección del dashboard y
genera un documento Word consolidado usando WordReportBuilder.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st
import pandas as pd

from app.src.charts.generator import ChartGenerator
from app.src.stats.engine import StatsEngine
from app.src.export.word_builder import WordReportBuilder


def _safe_chart(charts_fn, *args, **kwargs):
    """Ejecuta una función de gráficos con manejo de errores."""
    try:
        return charts_fn(*args, **kwargs)
    except Exception:
        return None


def generar_informe_inicio(engine: StatsEngine) -> bytes:
    """Genera el informe Word de la página Inicio."""
    charts = ChartGenerator()
    resumen = engine.resumen()
    builder = WordReportBuilder(
        titulo="INFORME EJECUTIVO - PANEL DE INICIO",
        subtitulo="Sistema de Informes Instantáneos — Policía de Tucumán",
    )

    # Métricas principales
    builder.add_section("Indicadores Principales")
    builder.add_metricas({
        "Total Delitos": f"{resumen['total_delitos']:,}",
        "Jurisdicciones": f"{resumen['total_jurisdicciones']:,}",
        "Unidades Regionales": f"{resumen['total_unidades_regionales']:,}",
        "Shapefiles": f"{resumen['total_shapefiles']:,}",
    })

    # Síntesis textual
    builder.add_section("Síntesis Rápida")
    builder.add_text(
        f"Delito dominante: {resumen['delito_mas_frecuente']}", bold=True
    )
    dia = resumen["dia_mas_frecuente"].title() if resumen["dia_mas_frecuente"] != "N/A" else "N/A"
    builder.add_text(f"Día con mayor actividad: {dia}")
    franja = resumen["franja_mas_frecuente"]
    if franja and franja != "N/A":
        builder.add_text(f"Franja horaria más activa: {franja.replace('_', ' ')}")

    # Gráfico de modalidades
    df_modal = engine.delitos_por_modalidad()
    if len(df_modal) > 0:
        fig = _safe_chart(charts.barras_horizontal, df_modal, "Top Delitos por Modalidad")
        if fig:
            builder.add_chart(fig, "Delitos por Modalidad")

    # Gráfico de días
    df_dia = engine.delitos_por_dia_semana()
    if len(df_dia) > 0:
        fig = _safe_chart(charts.barras_vertical, df_dia, "Delitos por Día de la Semana")
        if fig:
            builder.add_chart(fig, "Distribución por Día de la Semana")

    # Franja horaria
    df_franja = engine.delitos_por_franja_horaria()
    if len(df_franja) > 0:
        fig = _safe_chart(
            charts.barras_vertical, df_franja,
            "Distribución por Franja Horaria", color="#ED7D31",
        )
        if fig:
            builder.add_chart(fig, "Distribución por Franja Horaria")

    # Dona UR
    df_ur = engine.delitos_por_unidad_regional()
    if len(df_ur) > 0:
        fig = _safe_chart(charts.dona, df_ur, "Distribución por Unidad Regional")
        if fig:
            builder.add_chart(fig, "Distribución por Unidad Regional")

    # Heatmap
    pivot = engine.matriz_dia_franja()
    if not pivot.empty:
        fig = _safe_chart(charts.heatmap, pivot, "Mapa de calor: Día vs Franja")
        if fig:
            builder.add_chart(fig, "Cruce Día vs Franja Horaria")

    return builder.build()


def generar_informe_delitos(engine: StatsEngine) -> bytes:
    """Genera el informe Word de la página Delitos por Modalidad."""
    charts = ChartGenerator()
    resumen = engine.resumen()
    builder = WordReportBuilder(
        titulo="INFORME - DELITOS POR MODALIDAD",
        subtitulo="Sistema de Informes Instantáneos — Policía de Tucumán",
    )

    builder.add_section("Indicadores Principales")
    builder.add_metricas({
        "Total Delitos": f"{resumen['total_delitos']:,}",
        "Jurisdicciones": f"{resumen['total_jurisdicciones']:,}",
        "Unidades Regionales": f"{resumen['total_unidades_regionales']:,}",
    })

    df_modal = engine.delitos_por_modalidad()
    if len(df_modal) > 0:
        fig = _safe_chart(charts.barras_horizontal, df_modal, "Distribución por Modalidad Delictiva")
        if fig:
            builder.add_chart(fig, "Distribución por Modalidad Delictiva")

    # Modus operandi
    df_modus = engine.modus_operandi()
    if len(df_modus) > 0:
        fig = _safe_chart(charts.barras_horizontal, df_modus, "Distribución por Modus Operandi")
        if fig:
            builder.add_chart(fig, "Distribución por Modus Operandi")

    return builder.build()


def generar_informe_caracteristicas(engine: StatsEngine) -> bytes:
    """Genera el informe Word de la página Características."""
    charts = ChartGenerator()
    resumen = engine.resumen()
    builder = WordReportBuilder(
        titulo="INFORME - CARACTERÍSTICAS DEL HECHO",
        subtitulo="Sistema de Informes Instantáneos — Policía de Tucumán",
    )

    builder.add_section("Indicadores Principales")
    builder.add_metricas({
        "Total Delitos": f"{resumen['total_delitos']:,}",
    })

    # Movilidad
    df_mov = engine.medios_movilidad()
    if len(df_mov) > 0:
        fig = _safe_chart(charts.barras_horizontal, df_mov, "Tipo de Movilidad")
        if fig:
            builder.add_chart(fig, "Distribución por Tipo de Movilidad")

    # Armas
    df_arma = engine.armas_utilizadas()
    if len(df_arma) > 0:
        fig = _safe_chart(charts.barras_horizontal, df_arma, "Tipo de Arma")
        if fig:
            builder.add_chart(fig, "Distribución por Tipo de Arma")

    # Ámbito
    df_ambito = engine.ambito_ocurrencia()
    if len(df_ambito) > 0:
        fig = _safe_chart(charts.barras_horizontal, df_ambito, "Ámbito del Hecho")
        if fig:
            builder.add_chart(fig, "Distribución por Ámbito")

    # Modus operandi
    df_modus = engine.modus_operandi()
    if len(df_modus) > 0:
        fig = _safe_chart(charts.barras_horizontal, df_modus, "Modus Operandi")
        if fig:
            builder.add_chart(fig, "Distribución por Modus Operandi")

    return builder.build()


def generar_informe_geografico(engine: StatsEngine) -> bytes:
    """Genera el informe Word de la página Análisis Geográfico."""
    charts = ChartGenerator()
    resumen = engine.resumen()
    builder = WordReportBuilder(
        titulo="INFORME - ANÁLISIS GEOGRÁFICO",
        subtitulo="Sistema de Informes Instantáneos — Policía de Tucumán",
    )

    builder.add_section("Indicadores Principales")
    builder.add_metricas({
        "Total Delitos": f"{resumen['total_delitos']:,}",
        "Jurisdicciones": f"{resumen['total_jurisdicciones']:,}",
        "Unidades Regionales": f"{resumen['total_unidades_regionales']:,}",
    })

    df_ur = engine.delitos_por_unidad_regional()
    if len(df_ur) > 0:
        fig = _safe_chart(charts.barras_horizontal, df_ur, "Delitos por Unidad Regional")
        if fig:
            builder.add_chart(fig, "Distribución por Unidad Regional")

    df_juris = engine.delitos_por_jurisdiccion()
    if len(df_juris) > 0:
        fig = _safe_chart(
            charts.barras_horizontal, df_juris, "Top Jurisdicciones",
        )
        if fig:
            builder.add_chart(fig, "Top Jurisdicciones por Volumen")

    return builder.build()


def generar_informe_temporal(engine: StatsEngine) -> bytes:
    """Genera el informe Word de la página Análisis Temporal."""
    charts = ChartGenerator()
    resumen = engine.resumen()
    builder = WordReportBuilder(
        titulo="INFORME - ANÁLISIS TEMPORAL",
        subtitulo="Sistema de Informes Instantáneos — Policía de Tucumán",
    )

    builder.add_section("Indicadores Principales")
    builder.add_metricas({
        "Total Delitos": f"{resumen['total_delitos']:,}",
    })

    # Día de la semana
    df_dia = engine.delitos_por_dia_semana()
    if len(df_dia) > 0:
        fig = _safe_chart(charts.barras_vertical, df_dia, "Delitos por Día de la Semana")
        if fig:
            builder.add_chart(fig, "Distribución por Día de la Semana")

    # Franja horaria
    df_franja = engine.delitos_por_franja_horaria()
    if len(df_franja) > 0:
        fig = _safe_chart(
            charts.barras_vertical, df_franja,
            "Distribución por Franja Horaria", color="#ED7D31",
        )
        if fig:
            builder.add_chart(fig, "Distribución por Franja Horaria")

    # Heatmap
    pivot = engine.matriz_dia_franja()
    if not pivot.empty:
        fig = _safe_chart(charts.heatmap, pivot, "Mapa de calor: Día vs Franja")
        if fig:
            builder.add_chart(fig, "Cruce Día vs Franja Horaria")

    return builder.build()


# ====================================================================
# Mapeo de páginas a funciones generadoras
# ====================================================================

PAGE_REPORT_MAP = {
    "🏠 Inicio": generar_informe_inicio,
    "📋 Delitos por Modalidad": generar_informe_delitos,
    "📅 Análisis Temporal": generar_informe_temporal,
    "🔍 Características": generar_informe_caracteristicas,
    "🗺️ Análisis Geográfico": generar_informe_geografico,
}


def generar_informe_pagina_actual(pagina: str, engine: StatsEngine) -> Optional[bytes]:
    """
    Genera el informe correspondiente a la página activa.
    Retorna None si la página no tiene generador de informe.
    """
    generador = PAGE_REPORT_MAP.get(pagina)
    if generador is None:
        return None
    return generador(engine)
