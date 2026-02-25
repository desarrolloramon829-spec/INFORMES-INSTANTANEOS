"""
Motor de estadísticas para informes del mapa delictual.
Genera tablas de conteo, porcentajes, comparativos y rankings
necesarios para los 13 tipos de informe.
"""
from __future__ import annotations

from typing import Optional
import pandas as pd
import numpy as np

from app.config.settings import (
    FRANJAS_HORARIAS,
    FRANJAS_LABELS,
    DIAS_SEMANA,
    DIAS_LABELS,
    MESES,
    MESES_LABELS,
    DELITO_CATEGORIAS,
    UNIDADES_REGIONALES,
)
from app.src.data.loader import parse_curly_braces


# ====================================================================
# Utilidades de conteo genérico
# ====================================================================

def _conteo_simple(
    df: pd.DataFrame,
    campo: str,
    orden: Optional[list[str]] = None,
    labels: Optional[dict[str, str]] = None,
    top_n: Optional[int] = None,
) -> pd.DataFrame:
    """
    Conteo de valores de un campo con porcentaje.

    Args:
        df: DataFrame de delitos.
        campo: Columna a contar.
        orden: Orden fijo de categorías.
        labels: Diccionario de renombrado para las categorías.
        top_n: Si se especifica, devuelve solo los primeros N.

    Returns:
        DataFrame con columnas [categoria, cantidad, porcentaje].
    """
    series = df[campo].dropna()
    conteo = series.value_counts()

    if orden:
        conteo = conteo.reindex(orden).fillna(0).astype(int)
    else:
        conteo = conteo.sort_values(ascending=False)

    total = conteo.sum()
    result = pd.DataFrame({
        "categoria": conteo.index,
        "cantidad": conteo.values,
        "porcentaje": (conteo.values / total * 100).round(2) if total > 0 else 0,
    })

    if labels:
        result["categoria_label"] = result["categoria"].map(labels).fillna(result["categoria"])
    else:
        result["categoria_label"] = result["categoria"]

    if top_n:
        result = result.head(top_n)

    result["total"] = total
    return result


def _conteo_multivalor(
    df: pd.DataFrame,
    campo: str,
    labels: Optional[dict[str, str]] = None,
    top_n: Optional[int] = None,
) -> pd.DataFrame:
    """
    Conteo de campos con formato {val1,val2,...} (explotan en múltiples filas).
    """
    valores = df[campo].dropna().apply(parse_curly_braces).explode()
    valores = valores[valores.notna() & (valores != "")]

    conteo = valores.value_counts().sort_values(ascending=False)
    total = conteo.sum()

    result = pd.DataFrame({
        "categoria": conteo.index,
        "cantidad": conteo.values,
        "porcentaje": (conteo.values / total * 100).round(2) if total > 0 else 0,
    })

    if labels:
        result["categoria_label"] = result["categoria"].map(labels).fillna(
            result["categoria"].str.replace("_", " ").str.title()
        )
    else:
        result["categoria_label"] = result["categoria"].str.replace("_", " ").str.title()

    # Limpiar prefijo # de valores como #NINGUNA
    result["categoria_label"] = result["categoria_label"].str.lstrip("#")

    if top_n:
        result = result.head(top_n)

    result["total"] = total
    return result


# ====================================================================
# Informes principales
# ====================================================================

class StatsEngine:
    """
    Genera todas las estadísticas para los informes del mapa delictual.

    Uso:
        engine = StatsEngine(df)
        tabla = engine.delitos_por_modalidad()
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._total_registros = len(df)

    @property
    def total_registros(self) -> int:
        return self._total_registros

    # ---- Informe 6.1: Delitos por Modalidad ----
    def delitos_por_modalidad(self) -> pd.DataFrame:
        """Tabla de conteo por tipo de delito."""
        return _conteo_simple(
            self.df, "DELITO",
            labels=DELITO_CATEGORIAS,
        )

    # ---- Informe 6.2: Delitos por Día de la Semana ----
    def delitos_por_dia_semana(self) -> pd.DataFrame:
        """Conteo de delitos agrupados por día de la semana."""
        return _conteo_simple(
            self.df, "DIA_HECHO",
            orden=DIAS_SEMANA,
            labels=DIAS_LABELS,
        )

    # ---- Informe 6.3: Delitos por Franja Horaria ----
    def delitos_por_franja_horaria(self) -> pd.DataFrame:
        """Conteo de delitos agrupados por franja horaria."""
        return _conteo_simple(
            self.df, "FRAN_HORAR",
            orden=FRANJAS_HORARIAS,
            labels=FRANJAS_LABELS,
        )

    # ---- Informe 6.4: Medios de Movilidad ----
    def medios_movilidad(self) -> pd.DataFrame:
        """Conteo de medios de movilidad (campo multi-valor)."""
        return _conteo_multivalor(self.df, "VEHIC_UTIL")

    # ---- Informe 6.5: Armas Utilizadas ----
    def armas_utilizadas(self) -> pd.DataFrame:
        """Conteo de armas utilizadas (campo multi-valor)."""
        return _conteo_multivalor(self.df, "ARMA_UTILI")

    # ---- Informe 6.6: Ámbito de Ocurrencia ----
    def ambito_ocurrencia(self) -> pd.DataFrame:
        """Conteo por lugar/ámbito del hecho."""
        return _conteo_simple(self.df, "LUGR_HECHO")

    # ---- Informe 6.7: Delitos por Mes ----
    def delitos_por_mes(self) -> pd.DataFrame:
        """Conteo de delitos agrupados por mes."""
        return _conteo_simple(
            self.df, "MES_DENU",
            orden=MESES,
            labels=MESES_LABELS,
        )

    # ---- Informe 6.8: Delitos por Jurisdicción ----
    def delitos_por_jurisdiccion(self, top_n: int = 20) -> pd.DataFrame:
        """Ranking de jurisdicciones con más delitos."""
        result = _conteo_simple(self.df, "JURIS_HECH", top_n=top_n)
        # Embellecer nombres de jurisdicción
        result["categoria_label"] = (
            result["categoria"]
            .str.replace("_", " ")
            .str.replace(r"^(URC|URN|URO|URE|URS)\s+", "", regex=True)
            .str.title()
        )
        return result

    # ---- Informe 6.9: Delitos por Unidad Regional ----
    def delitos_por_unidad_regional(self) -> pd.DataFrame:
        """Conteo agrupado por Unidad Regional."""
        conteo = self.df["_unidad_regional"].value_counts()
        total = conteo.sum()
        result = pd.DataFrame({
            "categoria": conteo.index,
            "cantidad": conteo.values,
            "porcentaje": (conteo.values / total * 100).round(2) if total > 0 else 0,
        })
        result["categoria_label"] = result["categoria"].map(UNIDADES_REGIONALES).fillna(result["categoria"])
        result["total"] = total
        return result

    # ---- Informe 6.10: Modus Operandi ----
    def modus_operandi(self, top_n: int = 15) -> pd.DataFrame:
        """Conteo de modus operandi más frecuentes (campo multi-valor)."""
        result = _conteo_multivalor(self.df, "MODUS_OPER", top_n=top_n)
        result["categoria_label"] = (
            result["categoria"]
            .str.replace("_", " ")
            .str.title()
        )
        return result

    # ---- Informe 6.11: Hechos Resueltos ----
    def hechos_resueltos(self) -> pd.DataFrame:
        """Porcentaje de hechos resueltos SI/NO/PARCIALMENTE."""
        return _conteo_simple(self.df, "HECH_RESUE")

    # ---- Informe: Delitos por Año ----
    def delitos_por_anio(self) -> pd.DataFrame:
        """Conteo de delitos agrupados por año."""
        series = self.df["_anio"].dropna().astype(int)
        conteo = series.value_counts().sort_index()
        total = conteo.sum()
        return pd.DataFrame({
            "categoria": conteo.index,
            "cantidad": conteo.values,
            "porcentaje": (conteo.values / total * 100).round(2) if total > 0 else 0,
            "total": total,
        })

    # ====================================================================
    # Comparativos entre períodos
    # ====================================================================

    def comparativo_periodos(
        self,
        anio_actual: int,
        anio_anterior: int,
        campo: str = "DELITO",
    ) -> pd.DataFrame:
        """
        Compara conteos de un campo entre dos años.

        Returns:
            DataFrame con columnas:
            [categoria, cantidad_anterior, cantidad_actual, diferencia, pct_variacion]
        """
        df_ant = self.df[self.df["_anio"] == anio_anterior]
        df_act = self.df[self.df["_anio"] == anio_actual]

        conteo_ant = df_ant[campo].dropna().value_counts()
        conteo_act = df_act[campo].dropna().value_counts()

        # Unificar categorías
        categorias = sorted(set(conteo_ant.index) | set(conteo_act.index))

        result = pd.DataFrame({"categoria": categorias})
        result["cantidad_anterior"] = result["categoria"].map(conteo_ant).fillna(0).astype(int)
        result["cantidad_actual"] = result["categoria"].map(conteo_act).fillna(0).astype(int)
        result["diferencia"] = result["cantidad_actual"] - result["cantidad_anterior"]
        result["pct_variacion"] = np.where(
            result["cantidad_anterior"] > 0,
            ((result["diferencia"] / result["cantidad_anterior"]) * 100).round(2),
            np.where(result["cantidad_actual"] > 0, 100.0, 0.0),
        )

        # Totales
        result.loc[len(result)] = [
            "TOTAL",
            result["cantidad_anterior"].sum(),
            result["cantidad_actual"].sum(),
            result["diferencia"].sum(),
            None,
        ]
        total_ant = result.iloc[-1]["cantidad_anterior"]
        total_act = result.iloc[-1]["cantidad_actual"]
        if total_ant > 0:
            result.at[result.index[-1], "pct_variacion"] = round(
                (total_act - total_ant) / total_ant * 100, 2
            )

        return result

    def comparativo_mensual(
        self,
        anio_actual: int,
        anio_anterior: int,
    ) -> pd.DataFrame:
        """Comparativo mensual entre dos años."""
        df_ant = self.df[self.df["_anio"] == anio_anterior]
        df_act = self.df[self.df["_anio"] == anio_actual]

        resultado = []
        for i, mes in enumerate(MESES, 1):
            cant_ant = len(df_ant[df_ant["MES_DENU"] == mes])
            cant_act = len(df_act[df_act["MES_DENU"] == mes])
            dif = cant_act - cant_ant
            pct = round((dif / cant_ant) * 100, 2) if cant_ant > 0 else (100.0 if cant_act > 0 else 0.0)
            resultado.append({
                "mes": mes,
                "mes_label": MESES_LABELS[mes],
                "mes_num": i,
                "cantidad_anterior": cant_ant,
                "cantidad_actual": cant_act,
                "diferencia": dif,
                "pct_variacion": pct,
            })

        result = pd.DataFrame(resultado)

        # Fila total
        total = {
            "mes": "TOTAL",
            "mes_label": "TOTAL",
            "mes_num": 13,
            "cantidad_anterior": result["cantidad_anterior"].sum(),
            "cantidad_actual": result["cantidad_actual"].sum(),
            "diferencia": result["diferencia"].sum(),
            "pct_variacion": None,
        }
        if total["cantidad_anterior"] > 0:
            total["pct_variacion"] = round(
                (total["diferencia"] / total["cantidad_anterior"]) * 100, 2
            )
        result = pd.concat([result, pd.DataFrame([total])], ignore_index=True)
        return result

    # ====================================================================
    # Filtrado dinámico
    # ====================================================================

    def filtrar(
        self,
        anio: Optional[int] = None,
        mes: Optional[str] = None,
        ur: Optional[str] = None,
        delito: Optional[str] = None,
        jurisdiccion: Optional[str] = None,
    ) -> "StatsEngine":
        """
        Devuelve un nuevo StatsEngine con el DataFrame filtrado.

        Uso encadenado:
            engine.filtrar(anio=2023, ur="URC").delitos_por_modalidad()
        """
        df = self.df.copy()
        if anio is not None:
            df = df[df["_anio"] == anio]
        if mes is not None:
            df = df[df["MES_DENU"] == mes.lower()]
        if ur is not None:
            df = df[df["_unidad_regional"] == ur.upper()]
        if delito is not None:
            df = df[df["DELITO"] == delito]
        if jurisdiccion is not None:
            df = df[df["JURIS_HECH"] == jurisdiccion]
        return StatsEngine(df)

    # ====================================================================
    # Resumen rápido
    # ====================================================================

    def resumen(self) -> dict:
        """Devuelve métricas resumen para cards del dashboard."""
        df = self.df
        return {
            "total_delitos": len(df),
            "total_shapefiles": df["_shapefile_key"].nunique() if "_shapefile_key" in df.columns else 0,
            "total_jurisdicciones": df["JURIS_HECH"].nunique() if "JURIS_HECH" in df.columns else 0,
            "total_unidades_regionales": df["_unidad_regional"].nunique() if "_unidad_regional" in df.columns else 0,
            "anios_disponibles": sorted(df["_anio"].dropna().unique().astype(int).tolist()) if "_anio" in df.columns else [],
            "delito_mas_frecuente": df["DELITO"].mode().iloc[0] if "DELITO" in df.columns and len(df) > 0 else "N/A",
            "dia_mas_frecuente": df["DIA_HECHO"].mode().iloc[0] if "DIA_HECHO" in df.columns and len(df["DIA_HECHO"].dropna()) > 0 else "N/A",
            "franja_mas_frecuente": df["FRAN_HORAR"].mode().iloc[0] if "FRAN_HORAR" in df.columns and len(df["FRAN_HORAR"].dropna()) > 0 else "N/A",
        }
