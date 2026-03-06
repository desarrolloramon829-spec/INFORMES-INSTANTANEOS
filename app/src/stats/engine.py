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


def _pct_variacion(base: int, actual: int) -> float:
    """Calcula la variación porcentual con la convención usada por la app."""
    if base > 0:
        return round(((actual - base) / base) * 100, 2)
    return 100.0 if actual > 0 else 0.0


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
    if granularidad == "dias":
        return f"DIA {posicion:02d}"
    return f"TRAMO {posicion:02d}"


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
        df_valid["bucket_label"] = semanas.map(lambda x: _label_periodo_anual(granularidad, x))
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
            labels=DELITO_CATEGORIAS,
        )

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
        df_clean["delito_label"] = (
            df_clean["DELITO"].map(DELITO_CATEGORIAS).fillna(df_clean["DELITO"])
        )

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
        anio: Optional[int] = None,
        mes: Optional[str] = None,
        ur: Optional[str] = None,
        delito: Optional[str] = None,
        jurisdiccion: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
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
        if fecha_desde is not None and fecha_hasta is not None and "_fecha" in df.columns:
            mask = df["_fecha"].apply(
                lambda x: fecha_desde <= x <= fecha_hasta if pd.notna(x) and x is not None else False
            )
            df = df[mask]
        return StatsEngine(df)

    def _filtrar_df_por_rango_fecha(self, fecha_desde: date, fecha_hasta: date) -> pd.DataFrame:
        """Devuelve un DataFrame filtrado por rango de fechas inclusive."""
        if "_fecha" not in self.df.columns:
            return self.df.iloc[0:0].copy()

        mask = self.df["_fecha"].apply(
            lambda x: fecha_desde <= x <= fecha_hasta if pd.notna(x) and x is not None else False
        )
        return self.df[mask].copy()

    def _comparativo_entre_dataframes(
        self,
        df_actual: pd.DataFrame,
        df_anterior: pd.DataFrame,
        campo: str,
    ) -> pd.DataFrame:
        """Construye una tabla comparativa estándar entre dos subconjuntos."""
        conteo_ant = df_anterior[campo].dropna().value_counts()
        conteo_act = df_actual[campo].dropna().value_counts()

        categorias = sorted(set(conteo_ant.index) | set(conteo_act.index))

        result = pd.DataFrame({"categoria": categorias})
        result["cantidad_anterior"] = result["categoria"].map(conteo_ant).fillna(0).astype(int)
        result["cantidad_actual"] = result["categoria"].map(conteo_act).fillna(0).astype(int)
        result["diferencia"] = result["cantidad_actual"] - result["cantidad_anterior"]
        result["pct_variacion"] = result.apply(
            lambda row: _pct_variacion(int(row["cantidad_anterior"]), int(row["cantidad_actual"])),
            axis=1,
        )

        total_ant = int(result["cantidad_anterior"].sum())
        total_act = int(result["cantidad_actual"].sum())
        result.loc[len(result)] = [
            "TOTAL",
            total_ant,
            total_act,
            total_act - total_ant,
            _pct_variacion(total_ant, total_act),
        ]
        return result

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
