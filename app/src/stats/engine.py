"""
Motor de estadísticas para informes del mapa delictual.
Genera tablas de conteo, porcentajes, comparativos y rankings
necesarios para los 13 tipos de informe.
"""
from __future__ import annotations

from datetime import date, timedelta
import re
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
    if campo not in df.columns:
        return pd.DataFrame(columns=["categoria", "cantidad", "porcentaje", "categoria_label", "total"])
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
    if campo not in df.columns:
        return pd.DataFrame(columns=["categoria", "cantidad", "porcentaje", "categoria_label", "total"])
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


def _pct_variacion(base: int, actual: int) -> float:
    """Calcula la variación porcentual con la convención usada por la app."""
    if base > 0:
        return round(((actual - base) / base) * 100, 2)
    return 100.0 if actual > 0 else 0.0


def _valor_informado(valor) -> bool:
    """Determina si un valor puede usarse como categoría visible."""
    if pd.isna(valor):
        return False
    if isinstance(valor, str):
        return valor.strip() != ""
    return True


def _mask_campos_informados(df: pd.DataFrame, campos: list[str]) -> pd.Series:
    """Máscara booleana para filas con todos los campos requeridos informados."""
    if df.empty:
        return pd.Series(dtype=bool, index=df.index)

    mask = pd.Series(True, index=df.index)
    for campo in campos:
        if campo not in df.columns:
            return pd.Series(False, index=df.index)
        mask &= df[campo].apply(_valor_informado)
    return mask


def _serie_valores_informados(df: pd.DataFrame, campo: str) -> pd.Series:
    """Devuelve solo los valores informados de un campo, excluyendo nulos y blancos."""
    if campo not in df.columns:
        return pd.Series(dtype="object")
    mask = _mask_campos_informados(df, [campo])
    return df.loc[mask, campo]


def _resumen_cobertura_df(df: pd.DataFrame, campos: list[str]) -> dict:
    """Resume cuántos registros quedan disponibles para una dimensión comparativa."""
    total = int(len(df))
    if total == 0:
        return {
            "totales": 0,
            "validos": 0,
            "excluidos": 0,
            "pct_cobertura": 0.0,
        }

    mask = _mask_campos_informados(df, campos)
    validos = int(mask.sum())
    excluidos = total - validos
    return {
        "totales": total,
        "validos": validos,
        "excluidos": excluidos,
        "pct_cobertura": round((validos / total) * 100, 2),
    }


def _label_jurisdiccion(valor: str) -> str:
    """Genera un nombre corto y legible para una jurisdicción/comisaría."""
    if pd.isna(valor):
        return ""

    s = str(valor).strip()
    for pfx in ("URC_", "URE_", "URO_", "URS_", "URN_"):
        if s.startswith(pfx):
            s = s[len(pfx):]
            break

    s = (
        s.replace("COMISARIA_DE_", "Cria. ")
         .replace("COMISARIA__", "Cria. ")
         .replace("COMISARIA_", "Cria. ")
         .replace("SUBCOMISARIA_DE_", "Subcria. ")
         .replace("SUBCOMISARIA_", "Subcria. ")
         .replace("DESTACAMENTO_", "Dest. ")
         .replace("_", " ")
         .strip()
    )

    match = re.match(r"(?i)^(comisaria|cria\.)\s+(\d+)\s*a?$", s)
    if match:
        return f"CRIA. {match.group(2)}°"

    for prefijo in (
        "Subcria. de ", "Subcria. ",
        "Sub. Cria. de ", "Sub Cria. de ", "Sub.Cria. de ",
        "Sub. Cria. ", "Sub Cria. ", "Sub.Cria. ",
        "Cria. de ", "Cria. ",
        "Dest. ",
    ):
        if s.lower().startswith(prefijo.lower()):
            s = s[len(prefijo):]
            break

    return s.upper().strip()


def _label_delito(valor: str) -> str:
    """Genera una etiqueta legible para un valor crudo del campo DELITO."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()
    if texto in DELITO_CATEGORIAS:
        return DELITO_CATEGORIAS[texto]

    texto = re.sub(r"^\d{3}-", "", texto)
    texto = texto.replace("#", "")
    texto = texto.replace("_", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.title()


def _label_categoria_comparativo(campo: str, valor) -> str:
    """Centraliza labels visibles para tablas comparativas por dimensión."""
    if pd.isna(valor):
        return "Sin dato"

    if campo == "DELITO":
        return _label_delito(valor)
    if campo == "DIA_HECHO":
        return DIAS_LABELS.get(str(valor), str(valor).replace("_", " ").title())
    if campo == "FRAN_HORAR":
        return FRANJAS_LABELS.get(str(valor), str(valor).replace("_", " ").title())
    if campo == "JURIS_HECH":
        return _label_jurisdiccion(str(valor))
    if campo == "_unidad_regional":
        return UNIDADES_REGIONALES.get(str(valor), str(valor))

    texto = str(valor).replace("#", "").replace("_", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.title()


def _normalizar_modus_operandi(valor: str) -> str:
    """Normaliza MODUS_OPER para construir modalidades operativas legibles."""
    if pd.isna(valor):
        return "No Consta"

    texto = str(valor).strip()
    if texto in {"", "NULL", "null", "None", "zzz", "#NO_CONSTA", "NO CONSTA", "NO_CONSTA"}:
        return "No Consta"

    texto = texto.replace("#", "")
    texto = texto.replace("_", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.title()


def _label_modalidad_operativa(delito: str, modus: str) -> str:
    """Combina delito y modus operandi en una etiqueta operativa visible."""
    delito_label = _label_delito(delito)
    modus_label = _normalizar_modus_operandi(modus)
    delito_upper = delito_label.upper()
    modus_upper = modus_label.upper()

    if not modus_label or modus_label == "No Consta":
        return delito_upper

    if modus_upper.startswith(delito_upper):
        return modus_upper

    delito_tokens = delito_upper.split()
    modus_tokens = modus_upper.split()
    if delito_tokens and modus_tokens and delito_tokens[0] == modus_tokens[0]:
        modus_upper = " ".join(modus_tokens[1:]).strip()
        if not modus_upper:
            return delito_upper

    return f"{delito_upper} {modus_upper}".strip()


def _label_periodo_anual(granularidad: str, bucket) -> str:
    """Etiqueta visible para comparativos temporales anuales."""
    if granularidad == "semestres":
        return {1: "1ER SEMESTRE", 2: "2DO SEMESTRE"}.get(int(bucket), f"SEMESTRE {bucket}")
    if granularidad == "cuatrimestres":
        return {1: "1ER CUATRIM.", 2: "2DO CUATRIM.", 3: "3ER CUATRIM."}.get(int(bucket), f"CUATRIM. {bucket}")
    if granularidad == "trimestres":
        return {1: "1ER TRIM.", 2: "2DO TRIM.", 3: "3ER TRIM.", 4: "4TO TRIM."}.get(int(bucket), f"TRIM. {bucket}")
    if granularidad == "bimestres":
        return f"BIM. {int(bucket):02d}"
    if granularidad == "meses":
        return MESES_LABELS[MESES[int(bucket) - 1]].upper()
    if granularidad == "semanas":
        return f"SEM. {int(bucket):02d}"
    if granularidad == "bisemanas":
        return f"BISEM. {int(bucket):02d}"
    if granularidad == "trisemanas":
        return f"TRISEM. {int(bucket):02d}"
    if granularidad == "dias":
        return str(bucket)
    return str(bucket)


def _label_periodo_rango(granularidad: str, posicion: int) -> str:
    """Etiqueta visible para comparativos temporales de rangos, alineados por posición."""
    if granularidad == "semestres":
        return f"SEMESTRE {posicion}"
    if granularidad == "cuatrimestres":
        return f"CUATRIM. {posicion}"
    if granularidad == "trimestres":
        return f"TRIM. {posicion}"
    if granularidad == "bimestres":
        return f"BIM. {posicion:02d}"
    if granularidad == "meses":
        return f"MES {posicion:02d}"
    if granularidad == "semanas":
        return f"SEM. {posicion:02d}"
    if granularidad == "bisemanas":
        return f"BISEM. {posicion:02d}"
    if granularidad == "trisemanas":
        return f"TRISEM. {posicion:02d}"
    if granularidad == "dias":
        return f"DIA {posicion:02d}"
    return f"TRAMO {posicion:02d}"


def _tabla_serie_temporal(serie: pd.DataFrame) -> pd.DataFrame:
    """Convierte una serie temporal agrupada en una tabla homogénea para la UI."""
    if serie.empty:
        return pd.DataFrame(columns=["categoria", "categoria_label", "cantidad", "porcentaje", "total"])

    total = int(serie["cantidad"].sum())
    result = pd.DataFrame({
        "categoria": serie["bucket"],
        "categoria_label": serie["bucket_label"],
        "cantidad": serie["cantidad"].astype(int),
    })
    result["porcentaje"] = (
        (result["cantidad"] / total) * 100
    ).round(2) if total > 0 else 0.0
    result["total"] = total
    return result


def _serie_temporal_por_granularidad(df: pd.DataFrame, granularidad: str) -> pd.DataFrame:
    """Agrupa registros por una granularidad temporal anual."""
    if "_fecha" not in df.columns:
        return pd.DataFrame(columns=["bucket", "bucket_label", "cantidad"])

    df_valid = df[df["_fecha"].notna()].copy()
    if df_valid.empty:
        return pd.DataFrame(columns=["bucket", "bucket_label", "cantidad"])

    fechas = pd.to_datetime(df_valid["_fecha"])

    if granularidad == "semestres":
        df_valid["bucket"] = ((fechas.dt.month - 1) // 6) + 1
        df_valid["bucket_label"] = df_valid["bucket"].map(lambda x: _label_periodo_anual(granularidad, x))
    elif granularidad == "cuatrimestres":
        df_valid["bucket"] = ((fechas.dt.month - 1) // 4) + 1
        df_valid["bucket_label"] = df_valid["bucket"].map(lambda x: _label_periodo_anual(granularidad, x))
    elif granularidad == "trimestres":
        df_valid["bucket"] = ((fechas.dt.month - 1) // 3) + 1
        df_valid["bucket_label"] = df_valid["bucket"].map(lambda x: _label_periodo_anual(granularidad, x))
    elif granularidad == "bimestres":
        df_valid["bucket"] = ((fechas.dt.month - 1) // 2) + 1
        df_valid["bucket_label"] = df_valid["bucket"].map(lambda x: _label_periodo_anual(granularidad, x))
    elif granularidad == "meses":
        df_valid["bucket"] = fechas.dt.month
        df_valid["bucket_label"] = df_valid["bucket"].map(lambda x: _label_periodo_anual(granularidad, x))
    elif granularidad == "semanas":
        semanas = fechas.dt.isocalendar().week.astype(int)
        df_valid["bucket"] = semanas
        inicio = (fechas - pd.to_timedelta(fechas.dt.weekday, unit="D"))
        fin = inicio + pd.to_timedelta(6, unit="D")
        df_valid["bucket_label"] = inicio.dt.strftime("%d/%m") + " al " + fin.dt.strftime("%d/%m")
    elif granularidad == "bisemanas":
        bisemanas = ((fechas.dt.isocalendar().week.astype(int) - 1) // 2) + 1
        df_valid["bucket"] = bisemanas
        semana_inicio = (fechas - pd.to_timedelta(fechas.dt.weekday, unit="D")).dt.normalize()
        desplazamiento = (fechas.dt.isocalendar().week.astype(int) - 1) % 2
        inicio = semana_inicio - pd.to_timedelta(desplazamiento * 7, unit="D")
        fin = inicio + pd.to_timedelta(13, unit="D")
        df_valid["bucket_label"] = inicio.dt.strftime("%d/%m") + " al " + fin.dt.strftime("%d/%m")
    elif granularidad == "trisemanas":
        trisemanas = ((fechas.dt.isocalendar().week.astype(int) - 1) // 3) + 1
        df_valid["bucket"] = trisemanas
        semana_inicio = (fechas - pd.to_timedelta(fechas.dt.weekday, unit="D")).dt.normalize()
        desplazamiento = (fechas.dt.isocalendar().week.astype(int) - 1) % 3
        inicio = semana_inicio - pd.to_timedelta(desplazamiento * 7, unit="D")
        fin = inicio + pd.to_timedelta(20, unit="D")
        df_valid["bucket_label"] = inicio.dt.strftime("%d/%m") + " al " + fin.dt.strftime("%d/%m")
    elif granularidad == "dias":
        df_valid["bucket"] = fechas.dt.strftime("%m-%d")
        df_valid["bucket_label"] = fechas.dt.strftime("%d/%m")
    else:
        raise ValueError(f"Granularidad no soportada: {granularidad}")

    if granularidad == "dias":
        agrupado = (
            df_valid.groupby(["bucket", "bucket_label"])
            .size()
            .reset_index(name="cantidad")
            .sort_values("bucket", ignore_index=True)
        )
        return agrupado

    return (
        df_valid.groupby(["bucket", "bucket_label"])
        .size()
        .reset_index(name="cantidad")
        .sort_values("bucket", ignore_index=True)
    )


def _serie_temporal_rango_por_granularidad(df: pd.DataFrame, granularidad: str) -> pd.DataFrame:
    """Agrupa registros de un rango por unidad temporal y alinea por posición de aparición."""
    if "_fecha" not in df.columns:
        return pd.DataFrame(columns=["bucket", "periodo_label", "cantidad"])

    df_valid = df[df["_fecha"].notna()].copy()
    if df_valid.empty:
        return pd.DataFrame(columns=["bucket", "periodo_label", "cantidad"])

    fechas = pd.to_datetime(df_valid["_fecha"])

    if granularidad == "semestres":
        start_month = np.where(fechas.dt.month <= 6, 1, 7)
        df_valid["bucket_base"] = pd.to_datetime({"year": fechas.dt.year, "month": start_month, "day": 1})
    elif granularidad == "cuatrimestres":
        start_month = ((fechas.dt.month - 1) // 4) * 4 + 1
        df_valid["bucket_base"] = pd.to_datetime({"year": fechas.dt.year, "month": start_month, "day": 1})
    elif granularidad == "trimestres":
        start_month = ((fechas.dt.month - 1) // 3) * 3 + 1
        df_valid["bucket_base"] = pd.to_datetime({"year": fechas.dt.year, "month": start_month, "day": 1})
    elif granularidad == "bimestres":
        start_month = ((fechas.dt.month - 1) // 2) * 2 + 1
        df_valid["bucket_base"] = pd.to_datetime({"year": fechas.dt.year, "month": start_month, "day": 1})
    elif granularidad == "meses":
        df_valid["bucket_base"] = fechas.dt.to_period("M").dt.to_timestamp()
    elif granularidad == "semanas":
        df_valid["bucket_base"] = (fechas - pd.to_timedelta(fechas.dt.weekday, unit="D")).dt.normalize()
    elif granularidad == "bisemanas":
        semana_inicio = (fechas - pd.to_timedelta(fechas.dt.weekday, unit="D")).dt.normalize()
        desplazamiento = (fechas.dt.isocalendar().week.astype(int) - 1) % 2
        df_valid["bucket_base"] = semana_inicio - pd.to_timedelta(desplazamiento * 7, unit="D")
    elif granularidad == "trisemanas":
        semana_inicio = (fechas - pd.to_timedelta(fechas.dt.weekday, unit="D")).dt.normalize()
        desplazamiento = (fechas.dt.isocalendar().week.astype(int) - 1) % 3
        df_valid["bucket_base"] = semana_inicio - pd.to_timedelta(desplazamiento * 7, unit="D")
    elif granularidad == "dias":
        df_valid["bucket_base"] = fechas.dt.normalize()
    else:
        raise ValueError(f"Granularidad no soportada en rangos: {granularidad}")

    agrupado = (
        df_valid.groupby("bucket_base")
        .size()
        .reset_index(name="cantidad")
        .sort_values("bucket_base", ignore_index=True)
    )
    agrupado["bucket"] = range(1, len(agrupado) + 1)
    if granularidad == "semanas":
        agrupado["periodo_label"] = agrupado["bucket_base"].dt.strftime("%d/%m") + " al " + (agrupado["bucket_base"] + pd.to_timedelta(6, unit="D")).dt.strftime("%d/%m")
    elif granularidad == "bisemanas":
        agrupado["periodo_label"] = agrupado["bucket_base"].dt.strftime("%d/%m") + " al " + (agrupado["bucket_base"] + pd.to_timedelta(13, unit="D")).dt.strftime("%d/%m")
    elif granularidad == "trisemanas":
        agrupado["periodo_label"] = agrupado["bucket_base"].dt.strftime("%d/%m") + " al " + (agrupado["bucket_base"] + pd.to_timedelta(20, unit="D")).dt.strftime("%d/%m")
    elif granularidad == "dias":
        agrupado["periodo_label"] = agrupado["bucket_base"].dt.strftime("%d/%m")
    else:
        agrupado["periodo_label"] = agrupado["bucket"].map(lambda x: _label_periodo_rango(granularidad, int(x)))
    return agrupado[["bucket", "periodo_label", "cantidad"]]


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
        """Tabla de conteo por tipo de delito (solo DELITO, para resúmenes)."""
        return _conteo_simple(
            self.df, "DELITO",
            labels={valor: _label_delito(valor) for valor in self.df["DELITO"].dropna().unique()},
        )

    def delitos_por_modalidad_detallada(self, top_n: Optional[int] = None) -> pd.DataFrame:
        """Conteo detallado de delitos usando el valor crudo de DELITO como modalidad específica."""
        if "DELITO" not in self.df.columns:
            return pd.DataFrame()

        df_clean = self.df.dropna(subset=["DELITO"]).copy()
        conteo = df_clean["DELITO"].value_counts().sort_values(ascending=False)
        total = conteo.sum()

        result = pd.DataFrame({
            "categoria": conteo.index,
            "cantidad": conteo.values,
            "porcentaje": (conteo.values / total * 100).round(2) if total > 0 else 0,
        })
        result["categoria_label"] = result["categoria"].map(_label_delito)
        result["total"] = total

        if top_n:
            result = result.head(top_n).copy()

        return result

    def modalidades_operativas(self, top_n: Optional[int] = None) -> pd.DataFrame:
        """Conteo detallado por combinación real de DELITO y MODUS_OPER."""
        if "DELITO" not in self.df.columns:
            return pd.DataFrame()

        df_clean = self.df_con_modalidad_operativa()
        if df_clean.empty:
            return pd.DataFrame()

        df_clean = df_clean.dropna(subset=["DELITO"]).copy()
        conteo = df_clean["categoria"].value_counts().sort_values(ascending=False)
        total = conteo.sum()

        result = pd.DataFrame({
            "categoria": conteo.index,
            "cantidad": conteo.values,
            "porcentaje": (conteo.values / total * 100).round(2) if total > 0 else 0,
        })
        result[["delito", "modus_clean"]] = result["categoria"].str.split("||", n=1, expand=True, regex=False)
        result["categoria_label"] = result.apply(
            lambda row: _label_modalidad_operativa(row["delito"], row["modus_clean"]),
            axis=1,
        )
        result["total"] = total

        if top_n:
            result = result.head(top_n).copy()

        return result

    def df_con_modalidad_operativa(self) -> pd.DataFrame:
        """Devuelve una copia del DataFrame con la modalidad operativa derivada por registro."""
        if "DELITO" not in self.df.columns:
            return pd.DataFrame()

        df_clean = self.df.dropna(subset=["DELITO"]).copy()
        if df_clean.empty:
            return pd.DataFrame()

        if "MODUS_OPER" in df_clean.columns:
            df_clean["modus_clean"] = df_clean["MODUS_OPER"].apply(_normalizar_modus_operandi)
        else:
            df_clean["modus_clean"] = "No Consta"

        df_clean["modalidad_operativa"] = df_clean.apply(
            lambda row: _label_modalidad_operativa(row["DELITO"], row["modus_clean"]),
            axis=1,
        )
        df_clean["categoria"] = df_clean.apply(
            lambda row: f"{row['DELITO']}||{row['modus_clean']}",
            axis=1,
        )
        return df_clean

    def delitos_con_modus_operandi(self) -> pd.DataFrame:
        """Tabla de conteo por tipo de delito + modus operandi combinados."""
        if "DELITO" not in self.df.columns:
            return pd.DataFrame()

        df_clean = self.df.dropna(subset=["DELITO"]).copy()

        # Normalizar modus operandi
        _basura_modus = {"", "NULL", "null", "None", "zzz", "#NO_CONSTA", "NO CONSTA", "NO_CONSTA"}
        if "MODUS_OPER" in df_clean.columns:
            df_clean["modus_clean"] = (
                df_clean["MODUS_OPER"]
                .fillna("No consta")
                .astype(str)
                .str.strip()
                .replace({v: "No consta" for v in _basura_modus})
            )
        else:
            df_clean["modus_clean"] = "No consta"

        # Etiqueta legible del delito
        df_clean["delito_label"] = df_clean["DELITO"].map(_label_delito)

        # Agrupar por (delito, modus)
        conteo = (
            df_clean.groupby(["delito_label", "modus_clean"])
            .size()
            .reset_index(name="cantidad")
            .sort_values("cantidad", ascending=False)
            .reset_index(drop=True)
        )

        total = conteo["cantidad"].sum()
        conteo["porcentaje"] = (
            (conteo["cantidad"] / total * 100).round(2) if total > 0 else 0.0
        )
        # Columna combinada para gráficos
        conteo["categoria_label"] = conteo["delito_label"] + " — " + conteo["modus_clean"]
        conteo["categoria"] = conteo["categoria_label"]
        conteo["total"] = total

        return conteo

    # ---- Informe 6.2: Delitos por Día de la Semana ----
    def delitos_por_dia_semana(self) -> pd.DataFrame:
        """Conteo de delitos agrupados por día de la semana (sin 'Sin Datos')."""
        orden_sin_sd = [d for d in DIAS_SEMANA if d != "sin_datos"]
        labels_sin_sd = {k: v for k, v in DIAS_LABELS.items() if k != "sin_datos"}
        df_clean = self.df[self.df["DIA_HECHO"] != "sin_datos"] if "DIA_HECHO" in self.df.columns else self.df
        return _conteo_simple(
            df_clean, "DIA_HECHO",
            orden=orden_sin_sd,
            labels=labels_sin_sd,
        )

    # ---- Informe 6.3: Delitos por Franja Horaria ----
    def delitos_por_franja_horaria(self) -> pd.DataFrame:
        """Conteo de delitos agrupados por franja horaria (sin 'Sin Datos')."""
        orden_sin_sd = [f for f in FRANJAS_HORARIAS if f != "SIN_DATOS"]
        labels_sin_sd = {k: v for k, v in FRANJAS_LABELS.items() if k != "SIN_DATOS"}
        df_clean = self.df[self.df["FRAN_HORAR"] != "SIN_DATOS"] if "FRAN_HORAR" in self.df.columns else self.df
        return _conteo_simple(
            df_clean, "FRAN_HORAR",
            orden=orden_sin_sd,
            labels=labels_sin_sd,
        )

    def matriz_dia_franja(self) -> pd.DataFrame:
        """Matriz de intensidad por día de semana y franja horaria (sin 'Sin Datos')."""
        if "DIA_HECHO" not in self.df.columns or "FRAN_HORAR" not in self.df.columns:
            return pd.DataFrame()

        df_valid = self.df[["DIA_HECHO", "FRAN_HORAR"]].dropna().copy()
        df_valid = df_valid[
            (df_valid["DIA_HECHO"] != "sin_datos") & (df_valid["FRAN_HORAR"] != "SIN_DATOS")
        ]
        if df_valid.empty:
            return pd.DataFrame()

        dias_sin_sd = [d for d in DIAS_SEMANA if d != "sin_datos"]
        franjas_sin_sd = [f for f in FRANJAS_HORARIAS if f != "SIN_DATOS"]
        pivot = pd.crosstab(df_valid["DIA_HECHO"], df_valid["FRAN_HORAR"])
        pivot = pivot.reindex(index=dias_sin_sd, columns=franjas_sin_sd, fill_value=0)
        pivot.index = [DIAS_LABELS.get(valor, valor) for valor in pivot.index]
        pivot.columns = [FRANJAS_LABELS.get(valor, valor) for valor in pivot.columns]
        return pivot

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

    def delitos_por_granularidad_temporal(self, granularidad: str = "meses") -> pd.DataFrame:
        """Serie temporal agrupada para visualizaciones temporales anuales."""
        return _tabla_serie_temporal(_serie_temporal_por_granularidad(self.df, granularidad))

    def delitos_por_semana(self, granularidad: str = "semanas") -> pd.DataFrame:
        """Serie temporal agrupada por semanas del año y derivados."""
        return self.delitos_por_granularidad_temporal(granularidad)

    def matriz_modalidad_franja(self, top_n_delitos: int = 8) -> pd.DataFrame:
        """Matriz de intensidad por modalidad delictiva y franja horaria (sin 'Sin Datos')."""
        if "DELITO" not in self.df.columns or "FRAN_HORAR" not in self.df.columns:
            return pd.DataFrame()

        df_valid = self.df[["DELITO", "FRAN_HORAR"]].dropna().copy()
        df_valid = df_valid[df_valid["FRAN_HORAR"] != "SIN_DATOS"]
        if df_valid.empty:
            return pd.DataFrame()

        delitos_top = df_valid["DELITO"].value_counts().head(top_n_delitos).index.tolist()
        if not delitos_top:
            return pd.DataFrame()

        franjas_sin_sd = [f for f in FRANJAS_HORARIAS if f != "SIN_DATOS"]
        df_valid = df_valid[df_valid["DELITO"].isin(delitos_top)].copy()
        pivot = pd.crosstab(df_valid["DELITO"], df_valid["FRAN_HORAR"])
        pivot = pivot.reindex(index=delitos_top, columns=franjas_sin_sd, fill_value=0)
        pivot.index = [_label_delito(valor) for valor in pivot.index]
        pivot.columns = [FRANJAS_LABELS.get(valor, valor) for valor in pivot.columns]
        return pivot

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

    def matriz_unidad_regional_delito(self, top_n_delitos: int = 8) -> pd.DataFrame:
        """Matriz territorial por unidad regional y modalidad delictiva."""
        if "_unidad_regional" not in self.df.columns or "DELITO" not in self.df.columns:
            return pd.DataFrame()

        df_valid = self.df[["_unidad_regional", "DELITO"]].dropna().copy()
        if df_valid.empty:
            return pd.DataFrame()

        delitos_top = (
            df_valid["DELITO"].value_counts().head(top_n_delitos).index.tolist()
        )
        if not delitos_top:
            return pd.DataFrame()

        df_valid = df_valid[df_valid["DELITO"].isin(delitos_top)].copy()
        pivot = pd.crosstab(df_valid["_unidad_regional"], df_valid["DELITO"])

        ur_orden = [codigo for codigo in UNIDADES_REGIONALES.keys() if codigo in pivot.index]
        pivot = pivot.reindex(index=ur_orden, columns=delitos_top, fill_value=0)
        pivot.index = [UNIDADES_REGIONALES.get(valor, valor) for valor in pivot.index]
        pivot.columns = [_label_delito(valor) for valor in pivot.columns]
        return pivot

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
        """Conteo de delitos agrupados por año, incluyendo registros sin fecha."""
        series = self.df["_anio"].dropna().astype(int)
        conteo = series.value_counts().sort_index()
        # Agregar registros sin fecha como categoría visible
        sin_fecha = int(self.df["_anio"].isna().sum())
        if sin_fecha > 0:
            conteo = pd.concat([conteo, pd.Series({0: sin_fecha})])
        total = conteo.sum()
        result = pd.DataFrame({
            "categoria": conteo.index,
            "cantidad": conteo.values,
            "porcentaje": (conteo.values / total * 100).round(2) if total > 0 else 0,
            "total": total,
        })
        # Renombrar año 0 a "Sin Fecha" para display
        result["categoria_label"] = result["categoria"].apply(
            lambda x: "Sin Fecha" if x == 0 else str(int(x))
        )
        return result

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

        return self._comparativo_entre_dataframes(df_act, df_ant, campo)

    def cobertura_comparativo_periodos(
        self,
        anio_actual: int,
        anio_anterior: int,
        campo: str,
        campos_requeridos: Optional[list[str]] = None,
    ) -> dict:
        """Devuelve la cobertura real de una dimensión comparativa entre dos años."""
        df_ant = self.df[self.df["_anio"] == anio_anterior]
        df_act = self.df[self.df["_anio"] == anio_actual]
        campos = campos_requeridos or [campo]
        return self._resumen_cobertura_dimension(df_act, df_ant, campo, campos)

    def comparativo_periodos_rango(
        self,
        fecha_actual_desde: date,
        fecha_actual_hasta: date,
        fecha_anterior_desde: date,
        fecha_anterior_hasta: date,
        campo: str = "DELITO",
    ) -> pd.DataFrame:
        """Compara conteos de un campo entre dos rangos de fechas."""
        df_ant = self._filtrar_df_por_rango_fecha(fecha_anterior_desde, fecha_anterior_hasta)
        df_act = self._filtrar_df_por_rango_fecha(fecha_actual_desde, fecha_actual_hasta)

        return self._comparativo_entre_dataframes(df_act, df_ant, campo)

    def cobertura_comparativo_periodos_rango(
        self,
        fecha_actual_desde: date,
        fecha_actual_hasta: date,
        fecha_anterior_desde: date,
        fecha_anterior_hasta: date,
        campo: str,
        campos_requeridos: Optional[list[str]] = None,
    ) -> dict:
        """Devuelve la cobertura real de una dimensión comparativa entre dos rangos."""
        df_ant = self._filtrar_df_por_rango_fecha(fecha_anterior_desde, fecha_anterior_hasta)
        df_act = self._filtrar_df_por_rango_fecha(fecha_actual_desde, fecha_actual_hasta)
        campos = campos_requeridos or [campo]
        return self._resumen_cobertura_dimension(df_act, df_ant, campo, campos)

    def comparativo_modalidades_operativas(
        self,
        anio_actual: int,
        anio_anterior: int,
    ) -> pd.DataFrame:
        """Compara modalidades operativas reales entre dos años."""
        df_ant = self.df[self.df["_anio"] == anio_anterior]
        df_act = self.df[self.df["_anio"] == anio_actual]
        return self._comparativo_modalidades_operativas_df(df_act, df_ant)

    def comparativo_modalidades_operativas_rango(
        self,
        fecha_actual_desde: date,
        fecha_actual_hasta: date,
        fecha_anterior_desde: date,
        fecha_anterior_hasta: date,
    ) -> pd.DataFrame:
        """Compara modalidades operativas reales entre dos rangos de fechas."""
        df_ant = self._filtrar_df_por_rango_fecha(fecha_anterior_desde, fecha_anterior_hasta)
        df_act = self._filtrar_df_por_rango_fecha(fecha_actual_desde, fecha_actual_hasta)
        return self._comparativo_modalidades_operativas_df(df_act, df_ant)

    def comparativo_diario_rango(
        self,
        fecha_actual_desde: date,
        fecha_actual_hasta: date,
        fecha_anterior_desde: date,
        fecha_anterior_hasta: date,
    ) -> pd.DataFrame:
        """Compara dos rangos alineando la evolución por posición diaria."""
        df_ant = self._filtrar_df_por_rango_fecha(fecha_anterior_desde, fecha_anterior_hasta)
        df_act = self._filtrar_df_por_rango_fecha(fecha_actual_desde, fecha_actual_hasta)

        dias_ant = max((fecha_anterior_hasta - fecha_anterior_desde).days + 1, 0)
        dias_act = max((fecha_actual_hasta - fecha_actual_desde).days + 1, 0)
        total_dias = max(dias_ant, dias_act)

        resultado = []
        for offset in range(total_dias):
            fecha_ant = fecha_anterior_desde + timedelta(days=offset) if offset < dias_ant else None
            fecha_act = fecha_actual_desde + timedelta(days=offset) if offset < dias_act else None

            cant_ant = int((df_ant["_fecha"] == fecha_ant).sum()) if fecha_ant is not None else 0
            cant_act = int((df_act["_fecha"] == fecha_act).sum()) if fecha_act is not None else 0
            dif = cant_act - cant_ant

            resultado.append({
                "dia": offset + 1,
                "dia_label": f"Día {offset + 1}",
                "fecha_anterior": fecha_ant,
                "fecha_anterior_label": fecha_ant.strftime("%d/%m/%Y") if fecha_ant else "-",
                "fecha_actual": fecha_act,
                "fecha_actual_label": fecha_act.strftime("%d/%m/%Y") if fecha_act else "-",
                "cantidad_anterior": cant_ant,
                "cantidad_actual": cant_act,
                "diferencia": dif,
                "pct_variacion": _pct_variacion(cant_ant, cant_act),
            })

        result = pd.DataFrame(resultado)
        total_ant = int(result["cantidad_anterior"].sum()) if not result.empty else 0
        total_act = int(result["cantidad_actual"].sum()) if not result.empty else 0
        total = {
            "dia": total_dias + 1,
            "dia_label": "TOTAL",
            "fecha_anterior": None,
            "fecha_anterior_label": "-",
            "fecha_actual": None,
            "fecha_actual_label": "-",
            "cantidad_anterior": total_ant,
            "cantidad_actual": total_act,
            "diferencia": total_act - total_ant,
            "pct_variacion": _pct_variacion(total_ant, total_act),
        }
        return pd.concat([result, pd.DataFrame([total])], ignore_index=True)

    def comparativo_comisarias_rango(
        self,
        fecha_actual_desde: date,
        fecha_actual_hasta: date,
        fecha_anterior_desde: date,
        fecha_anterior_hasta: date,
    ) -> pd.DataFrame:
        """Compara los totales de hechos por comisaría entre dos rangos."""
        result = self.comparativo_periodos_rango(
            fecha_actual_desde,
            fecha_actual_hasta,
            fecha_anterior_desde,
            fecha_anterior_hasta,
            "JURIS_HECH",
        )

        if result.empty:
            return result

        detalle = result[result["categoria"] != "TOTAL"].copy()
        detalle["categoria_label"] = detalle["categoria"].apply(_label_jurisdiccion)
        detalle = detalle.sort_values(
            by=["cantidad_actual", "cantidad_anterior", "categoria_label"],
            ascending=[False, False, True],
            ignore_index=True,
        )

        total = result[result["categoria"] == "TOTAL"].copy()
        total["categoria_label"] = "TOTAL"
        return pd.concat([detalle, total], ignore_index=True)

    def comparativo_comisarias_anual(
        self,
        anio_actual: int,
        anio_anterior: int,
    ) -> pd.DataFrame:
        """Compara los totales de hechos por comisaría entre dos años."""
        result = self.comparativo_periodos(anio_actual, anio_anterior, "JURIS_HECH")
        if result.empty:
            return result

        detalle = result[result["categoria"] != "TOTAL"].copy()
        detalle["categoria_label"] = detalle["categoria"].apply(_label_jurisdiccion)
        detalle = detalle.sort_values(
            by=["cantidad_actual", "cantidad_anterior", "categoria_label"],
            ascending=[False, False, True],
            ignore_index=True,
        )

        total = result[result["categoria"] == "TOTAL"].copy()
        total["categoria_label"] = "TOTAL"
        return pd.concat([detalle, total], ignore_index=True)

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

    def comparativo_temporal_anual(
        self,
        anio_actual: int,
        anio_anterior: int,
        granularidad: str = "meses",
    ) -> pd.DataFrame:
        """Compara dos años por una granularidad temporal configurable."""
        if granularidad == "meses":
            mensual = self.comparativo_mensual(anio_actual, anio_anterior).copy()
            mensual["bucket"] = mensual["mes_num"]
            mensual["periodo_label"] = mensual["mes_label"].map(
                lambda valor: valor.upper() if valor != "TOTAL" else "TOTAL"
            )
            return mensual[[
                "bucket",
                "periodo_label",
                "cantidad_anterior",
                "cantidad_actual",
                "diferencia",
                "pct_variacion",
            ]]

        df_ant = self.df[self.df["_anio"] == anio_anterior]
        df_act = self.df[self.df["_anio"] == anio_actual]

        serie_ant = _serie_temporal_por_granularidad(df_ant, granularidad)
        serie_act = _serie_temporal_por_granularidad(df_act, granularidad)

        labels_ant = dict(zip(serie_ant["bucket"], serie_ant["bucket_label"]))
        labels_act = dict(zip(serie_act["bucket"], serie_act["bucket_label"]))
        buckets = sorted(set(serie_ant["bucket"].tolist()) | set(serie_act["bucket"].tolist()))

        conteo_ant = dict(zip(serie_ant["bucket"], serie_ant["cantidad"]))
        conteo_act = dict(zip(serie_act["bucket"], serie_act["cantidad"]))

        resultado = []
        for bucket in buckets:
            cant_ant = int(conteo_ant.get(bucket, 0))
            cant_act = int(conteo_act.get(bucket, 0))
            resultado.append({
                "bucket": bucket,
                "periodo_label": labels_ant.get(bucket) or labels_act.get(bucket) or str(bucket),
                "cantidad_anterior": cant_ant,
                "cantidad_actual": cant_act,
                "diferencia": cant_act - cant_ant,
                "pct_variacion": _pct_variacion(cant_ant, cant_act),
            })

        result = pd.DataFrame(resultado)
        total_ant = int(result["cantidad_anterior"].sum()) if not result.empty else 0
        total_act = int(result["cantidad_actual"].sum()) if not result.empty else 0
        total_bucket = "99-99" if granularidad == "dias" else (max(buckets) + 1 if buckets else 1)
        total = {
            "bucket": total_bucket,
            "periodo_label": "TOTAL",
            "cantidad_anterior": total_ant,
            "cantidad_actual": total_act,
            "diferencia": total_act - total_ant,
            "pct_variacion": _pct_variacion(total_ant, total_act),
        }
        return pd.concat([result, pd.DataFrame([total])], ignore_index=True)

    def comparativo_temporal_rango(
        self,
        fecha_actual_desde: date,
        fecha_actual_hasta: date,
        fecha_anterior_desde: date,
        fecha_anterior_hasta: date,
        granularidad: str = "dias",
    ) -> pd.DataFrame:
        """Compara dos rangos con granularidad temporal configurable, alineando por posición."""
        if granularidad == "dias":
            diario = self.comparativo_diario_rango(
                fecha_actual_desde,
                fecha_actual_hasta,
                fecha_anterior_desde,
                fecha_anterior_hasta,
            ).copy()
            diario["periodo_label"] = diario["dia_label"]
            return diario[["bucket" if "bucket" in diario.columns else "dia", "periodo_label", "cantidad_anterior", "cantidad_actual", "diferencia", "pct_variacion"]].rename(columns={"dia": "bucket"})

        df_ant = self._filtrar_df_por_rango_fecha(fecha_anterior_desde, fecha_anterior_hasta)
        df_act = self._filtrar_df_por_rango_fecha(fecha_actual_desde, fecha_actual_hasta)

        serie_ant = _serie_temporal_rango_por_granularidad(df_ant, granularidad)
        serie_act = _serie_temporal_rango_por_granularidad(df_act, granularidad)

        buckets = sorted(set(serie_ant["bucket"].tolist()) | set(serie_act["bucket"].tolist()))
        labels_ant = dict(zip(serie_ant["bucket"], serie_ant["periodo_label"]))
        labels_act = dict(zip(serie_act["bucket"], serie_act["periodo_label"]))
        conteo_ant = dict(zip(serie_ant["bucket"], serie_ant["cantidad"]))
        conteo_act = dict(zip(serie_act["bucket"], serie_act["cantidad"]))

        resultado = []
        for bucket in buckets:
            cant_ant = int(conteo_ant.get(bucket, 0))
            cant_act = int(conteo_act.get(bucket, 0))
            resultado.append({
                "bucket": bucket,
                "periodo_label": labels_ant.get(bucket) or labels_act.get(bucket) or _label_periodo_rango(granularidad, int(bucket)),
                "cantidad_anterior": cant_ant,
                "cantidad_actual": cant_act,
                "diferencia": cant_act - cant_ant,
                "pct_variacion": _pct_variacion(cant_ant, cant_act),
            })

        result = pd.DataFrame(resultado)
        total_ant = int(result["cantidad_anterior"].sum()) if not result.empty else 0
        total_act = int(result["cantidad_actual"].sum()) if not result.empty else 0
        total = {
            "bucket": (max(buckets) + 1) if buckets else 1,
            "periodo_label": "TOTAL",
            "cantidad_anterior": total_ant,
            "cantidad_actual": total_act,
            "diferencia": total_act - total_ant,
            "pct_variacion": _pct_variacion(total_ant, total_act),
        }
        return pd.concat([result, pd.DataFrame([total])], ignore_index=True)

    # ====================================================================
    # Filtrado dinámico
    # ====================================================================

    def filtrar(
        self,
        anio: Optional[int | list[int]] = None,
        mes: Optional[str | list[str]] = None,
        ur: Optional[str] = None,
        delito: Optional[str] = None,
        jurisdiccion: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> "StatsEngine":
        """
        Devuelve un nuevo StatsEngine con el DataFrame filtrado.

        Uso encadenado:
            engine.filtrar(anio=[2023, 2024], ur="URC").delitos_por_modalidad()
        """
        df = self.df.copy()
        if anio is not None:
            if isinstance(anio, list):
                df = df[df["_anio"].isin(anio)]
            else:
                df = df[df["_anio"] == anio]
        if mes is not None:
            if isinstance(mes, list):
                mes_lower = [m.lower() for m in mes]
                df = df[df["MES_DENU"].isin(mes_lower)]
            else:
                df = df[df["MES_DENU"] == mes.lower()]
        if ur is not None:
            df = df[df["_unidad_regional"] == ur.upper()]
        if delito is not None:
            df = df[df["DELITO"] == delito]
        if jurisdiccion is not None:
            df = df[df["JURIS_HECH"] == jurisdiccion]
        if "_fecha" in df.columns:
            if fecha_desde is not None:
                df = df[df["_fecha"] >= fecha_desde]
            if fecha_hasta is not None:
                df = df[df["_fecha"] <= fecha_hasta]
        return StatsEngine(df)

    def _filtrar_df_por_rango_fecha(self, fecha_desde: date, fecha_hasta: date) -> pd.DataFrame:
        """Devuelve un DataFrame filtrado por rango de fechas inclusive."""
        if "_fecha" not in self.df.columns:
            return self.df.iloc[0:0].copy()

        mask = self.df["_fecha"].apply(
            lambda x: fecha_desde <= x <= fecha_hasta if pd.notna(x) and x is not None else False
        )
        return self.df[mask].copy()

    def comparativo_personalizado(
        self,
        engine_anterior: "StatsEngine",
        engine_actual: "StatsEngine",
        dimension: str,
    ) -> pd.DataFrame:
        """
        Realiza una comparación entre dos motores de estadísticas (periodos o filtros arbitrarios).
        """
        return self._comparativo_entre_dataframes(engine_actual.df, engine_anterior.df, dimension)

    def cobertura_personalizado(
        self,
        engine_anterior: "StatsEngine",
        engine_actual: "StatsEngine",
        campo: str,
        campos_requeridos: Optional[list[str]] = None,
    ) -> dict:
        """Devuelve la cobertura real de una dimensión comparativa entre dos motores."""
        campos = campos_requeridos or [campo]
        return self._resumen_cobertura_dimension(engine_actual.df, engine_anterior.df, campo, campos)

    def comparativo_modalidades_personalizado(
        self,
        engine_anterior: "StatsEngine",
        engine_actual: "StatsEngine",
    ) -> pd.DataFrame:
        """Compara modalidades operativas reales entre dos motores."""
        return self._comparativo_modalidades_operativas_df(engine_actual.df, engine_anterior.df)

    def _comparativo_entre_dataframes(
        self,
        df_actual: pd.DataFrame,
        df_anterior: pd.DataFrame,
        campo: str,
    ) -> pd.DataFrame:
        """Construye una tabla comparativa estándar entre dos subconjuntos."""
        conteo_ant = _serie_valores_informados(df_anterior, campo).value_counts()
        conteo_act = _serie_valores_informados(df_actual, campo).value_counts()

        categorias = sorted(set(conteo_ant.index) | set(conteo_act.index))

        result = pd.DataFrame({"categoria": categorias})
        result["cantidad_anterior"] = result["categoria"].map(conteo_ant).fillna(0).astype(int)
        result["cantidad_actual"] = result["categoria"].map(conteo_act).fillna(0).astype(int)
        result["diferencia"] = result["cantidad_actual"] - result["cantidad_anterior"]
        result["pct_variacion"] = result.apply(
            lambda row: _pct_variacion(int(row["cantidad_anterior"]), int(row["cantidad_actual"])),
            axis=1,
        )
        result["categoria_label"] = result["categoria"].apply(lambda valor: _label_categoria_comparativo(campo, valor))

        total_ant = int(result["cantidad_anterior"].sum())
        total_act = int(result["cantidad_actual"].sum())
        total_row = {
            "categoria": "TOTAL",
            "cantidad_anterior": total_ant,
            "cantidad_actual": total_act,
            "diferencia": total_act - total_ant,
            "pct_variacion": _pct_variacion(total_ant, total_act),
            "categoria_label": "TOTAL",
        }
        result = pd.concat([result, pd.DataFrame([total_row])], ignore_index=True)
        return result

    def _resumen_cobertura_dimension(
        self,
        df_actual: pd.DataFrame,
        df_anterior: pd.DataFrame,
        campo: str,
        campos_requeridos: list[str],
    ) -> dict:
        """Calcula la cobertura de filas utilizables para una dimensión comparativa."""
        anterior = _resumen_cobertura_df(df_anterior, campos_requeridos)
        actual = _resumen_cobertura_df(df_actual, campos_requeridos)
        return {
            "dimension": campo,
            "campos_requeridos": campos_requeridos,
            "anterior": anterior,
            "actual": actual,
            "hay_perdida": anterior["excluidos"] > 0 or actual["excluidos"] > 0,
        }

    def _comparativo_modalidades_operativas_df(
        self,
        df_actual: pd.DataFrame,
        df_anterior: pd.DataFrame,
    ) -> pd.DataFrame:
        """Comparativo estándar usando la combinación DELITO + MODUS_OPER."""
        def _build_series(df_base: pd.DataFrame) -> pd.Series:
            if "DELITO" not in df_base.columns:
                return pd.Series(dtype="int64")

            df_local = df_base.loc[_mask_campos_informados(df_base, ["DELITO"])].copy()
            if "MODUS_OPER" in df_local.columns:
                df_local["modus_clean"] = df_local["MODUS_OPER"].apply(_normalizar_modus_operandi)
            else:
                df_local["modus_clean"] = "No Consta"

            categoria = df_local.apply(
                lambda row: _label_modalidad_operativa(row["DELITO"], row["modus_clean"]),
                axis=1,
            )
            return categoria.value_counts()

        conteo_ant = _build_series(df_anterior)
        conteo_act = _build_series(df_actual)
        categorias = sorted(set(conteo_ant.index) | set(conteo_act.index))

        result = pd.DataFrame({"categoria_label": categorias})
        result["cantidad_anterior"] = result["categoria_label"].map(conteo_ant).fillna(0).astype(int)
        result["cantidad_actual"] = result["categoria_label"].map(conteo_act).fillna(0).astype(int)
        result["diferencia"] = result["cantidad_actual"] - result["cantidad_anterior"]
        result["pct_variacion"] = result.apply(
            lambda row: _pct_variacion(int(row["cantidad_anterior"]), int(row["cantidad_actual"])),
            axis=1,
        )
        result["categoria"] = result["categoria_label"]

        total_ant = int(result["cantidad_anterior"].sum())
        total_act = int(result["cantidad_actual"].sum())
        total_row = {
            "categoria": "TOTAL",
            "categoria_label": "TOTAL",
            "cantidad_anterior": total_ant,
            "cantidad_actual": total_act,
            "diferencia": total_act - total_ant,
            "pct_variacion": _pct_variacion(total_ant, total_act),
        }
        return pd.concat([result, pd.DataFrame([total_row])], ignore_index=True)

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
