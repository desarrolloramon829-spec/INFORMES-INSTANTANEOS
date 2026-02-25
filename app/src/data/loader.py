"""
Módulo de carga y normalización de shapefiles.
Lee los 132 shapefiles, unifica esquemas, limpia datos y genera un DataFrame único.
"""
from __future__ import annotations

import os
import re
import logging
from typing import Optional

import geopandas as gpd
import pandas as pd
import numpy as np

from app.config.settings import (
    BASE_SHAPEFILE_PATH,
    VALORES_BASURA,
    FRANJAS_HORARIAS,
    DIAS_SEMANA,
    MESES,
    DELITO_CATEGORIAS,
)
from app.config.shapefile_registry import (
    _SHAPEFILES,
    get_full_path,
    get_ur_from_key,
)

logger = logging.getLogger(__name__)

# Encodings que acepta QGIS 2.14 / dBASE IV
_ENCODINGS = ["utf-8", "latin1", "cp1252", "iso-8859-1"]

# Columnas comunes a los 4 esquemas detectados (49 campos)
COLUMNAS_COMUNES = [
    "AP_NOM_CAU", "AP_NOM_DEN", "AP_NOM_VIC", "ARMA_UTILI", "DELITO",
    "DESC_ALLA", "DESC_CAUS", "DET_ARMA", "DET_ELE_SU", "DET_EL_SE1",
    "DET_EL_SE2", "DET_EL_SE3", "DET_LUG_HE", "DET_VEHIC", "DIA_HECHO",
    "DIREC_CAUS", "DIREC_DENU", "DIREC_HECH", "DIREC_VICT", "DNI_CAUSAN",
    "DNI_DENUNC", "DNI_VICTIM", "DPCIA_CARG", "DPCIA_INT", "EDAD_CAUSA",
    "EDAD_DENUN", "EDAD_VICTI", "ELEMN_SUST", "ELEM_SECU", "FECHA_HECH",
    "FRAN_HORAR", "HECH_RESUE", "HORA_HECH", "ID_N_SRIO", "JURIS_ALLA",
    "JURIS_HECH", "LUGR_HECHO", "MES_DENU", "MODUS_OPER", "PRDA_URBAN",
    "RESEN_HECH", "SEXO_CAUS", "SEXO_DENUN", "SEXO_VICTI", "SITUA_CAUS",
    "VEHIC_UTIL", "VIN_DE_VIC", "X", "Y",
]


# -------------------------------------------------------------------
# Utilidades de parsing
# -------------------------------------------------------------------

def parse_curly_braces(value: str) -> list[str]:
    """
    Parsea campos multi-valor con formato {val1,val2,...}.
    Ejemplos:
        "{ARMA_BLANCA,OTRO_TIPO_DE_ARMA}" → ["ARMA_BLANCA", "OTRO_TIPO_DE_ARMA"]
        "{}" → []
        "VALOR_SIMPLE" → ["VALOR_SIMPLE"]
    """
    if pd.isna(value):
        return []
    value = str(value).strip()
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [v.strip() for v in inner.split(",") if v.strip()]
    if value in VALORES_BASURA or value == "#NO_CONSTA":
        return []
    return [value]


def limpiar_valor(valor: str) -> Optional[str]:
    """Limpia un valor individual: elimina basura y normaliza."""
    if pd.isna(valor):
        return None
    valor = str(valor).strip()
    if valor in VALORES_BASURA or valor == "#NO_CONSTA" or valor == "NO CONSTA":
        return None
    return valor


def extraer_anio_mes(fecha_str: str) -> tuple[Optional[int], Optional[int]]:
    """
    Extrae año y mes de un string con formato "dia DD-MM-YYYY" o "DD-MM-YYYY".
    Ejemplo: "viernes 01-09-2023" → (2023, 9)
    """
    if pd.isna(fecha_str):
        return None, None
    fecha_str = str(fecha_str).strip()
    # Buscar patrón DD-MM-YYYY o DD/MM/YYYY
    match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", fecha_str)
    if match:
        dia, mes, anio = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if 1 <= mes <= 12 and 2000 <= anio <= 2100:
            return anio, mes
    return None, None


# -------------------------------------------------------------------
# Clase principal de carga
# -------------------------------------------------------------------

class ShapefileLoader:
    """
    Carga y combina los 132 shapefiles en un DataFrame normalizado.

    Uso:
        loader = ShapefileLoader()
        df = loader.cargar_todo()
        df = loader.cargar_por_ur("URC")
    """

    def __init__(self, base_path: str = BASE_SHAPEFILE_PATH):
        self.base_path = base_path
        self._cache: Optional[pd.DataFrame] = None
        self._errores: list[dict] = []

    # ----- Lectura de un shapefile individual -----

    def _leer_shapefile(self, key: str) -> Optional[pd.DataFrame]:
        """Lee un shapefile probando múltiples encodings."""
        try:
            full_path = get_full_path(key)
        except KeyError:
            logger.warning("Clave no registrada: %s", key)
            return None

        if not os.path.exists(full_path):
            logger.warning("Archivo no encontrado: %s", full_path)
            self._errores.append({"key": key, "error": "archivo no encontrado"})
            return None

        for enc in _ENCODINGS:
            try:
                gdf = gpd.read_file(full_path, encoding=enc)
                # Eliminar geometría, trabajar con DataFrame plano
                df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
                df["_shapefile_key"] = key
                df["_unidad_regional"] = get_ur_from_key(key)
                return df
            except Exception:
                continue

        # Último intento sin encoding explícito
        try:
            gdf = gpd.read_file(full_path)
            df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
            df["_shapefile_key"] = key
            df["_unidad_regional"] = get_ur_from_key(key)
            return df
        except Exception as e:
            logger.error("No se pudo leer %s: %s", key, e)
            self._errores.append({"key": key, "error": str(e)})
            return None

    # ----- Normalización de esquema -----

    @staticmethod
    def _normalizar_esquema(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza las columnas de los 4 esquemas al conjunto común.
        Maneja variantes CamelCase/UPPERCASE de columnas 'alla' (allanamiento).
        """
        # Mapeo de variantes CamelCase → UPPERCASE estándar
        rename_map = {
            "DetLugAlla": "DETLUGALLA",
            "Direc_Alla": "DIREC_ALLA",
            "Fecha_Alla": "FECHA_ALLA",
            "Hora_Alla": "HORA_ALLA",
            "ID_Alla": "ID_ALLA",
            "Mes_Alla": "MES_ALLA",
            "Resol_Hech": "RESOL_HECH",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # Eliminar columnas _1 duplicadas (Schema 2)
        cols_to_drop = [c for c in df.columns if c.endswith("_1") and c != "DET_EL_SE1"]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop, errors="ignore")

        # Seleccionar solo las columnas comunes + metadatos
        meta_cols = ["_shapefile_key", "_unidad_regional"]
        cols_presentes = [c for c in COLUMNAS_COMUNES if c in df.columns]
        cols_meta = [c for c in meta_cols if c in df.columns]

        return df[cols_presentes + cols_meta]

    # ----- Limpieza de datos -----

    @staticmethod
    def _limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
        """Limpia valores basura y normaliza campos clave."""
        df = df.copy()

        # --- FRANJA HORARIA: mantener solo valores válidos ---
        if "FRAN_HORAR" in df.columns:
            df["FRAN_HORAR"] = df["FRAN_HORAR"].apply(
                lambda x: x if (pd.notna(x) and str(x).strip() in FRANJAS_HORARIAS) else None
            )

        # --- DIA HECHO: normalizar ---
        if "DIA_HECHO" in df.columns:
            df["DIA_HECHO"] = df["DIA_HECHO"].apply(
                lambda x: str(x).strip().lower() if pd.notna(x) and str(x).strip().lower() in DIAS_SEMANA else None
            )

        # --- MES: normalizar ---
        if "MES_DENU" in df.columns:
            df["MES_DENU"] = df["MES_DENU"].apply(
                lambda x: str(x).strip().lower() if pd.notna(x) and str(x).strip().lower() in MESES else None
            )

        # --- HECHO RESUELTO: limpiar basura ({38}, zzz) ---
        if "HECH_RESUE" in df.columns:
            valid_resuelto = {"SI", "NO", "PARCIALMENTE"}
            df["HECH_RESUE"] = df["HECH_RESUE"].apply(
                lambda x: str(x).strip().upper() if (pd.notna(x) and str(x).strip().upper() in valid_resuelto) else None
            )

        # --- DELITO: normalizar duplicados ---
        if "DELITO" in df.columns:
            df["DELITO"] = df["DELITO"].apply(
                lambda x: str(x).strip() if pd.notna(x) and str(x).strip() not in VALORES_BASURA else None
            )

        # --- Extraer Año y Mes numérico de FECHA_HECH ---
        if "FECHA_HECH" in df.columns:
            parsed = df["FECHA_HECH"].apply(extraer_anio_mes)
            df["_anio"] = parsed.apply(lambda x: x[0])
            df["_mes_num"] = parsed.apply(lambda x: x[1])

        # --- Limpiar coordenadas ---
        for col in ["X", "Y"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    # ----- Métodos públicos de carga -----

    def cargar_todo(self, use_cache: bool = True, progress_callback=None) -> pd.DataFrame:
        """
        Carga y combina los 132 shapefiles en un único DataFrame normalizado.

        Args:
            use_cache: Si True, devuelve el DataFrame cacheado si ya fue cargado.
            progress_callback: Función f(pct, msg) para informar progreso.

        Returns:
            DataFrame con todos los registros normalizados.
        """
        if use_cache and self._cache is not None:
            return self._cache

        frames: list[pd.DataFrame] = []
        keys = list(_SHAPEFILES.keys())
        total = len(keys)
        self._errores = []

        for i, key in enumerate(keys):
            if progress_callback:
                pct = int((i / total) * 100)
                progress_callback(pct, f"Cargando {key} ({i+1}/{total})...")

            df = self._leer_shapefile(key)
            if df is not None and len(df) > 0:
                df = self._normalizar_esquema(df)
                frames.append(df)

        if not frames:
            logger.error("No se pudo cargar ningún shapefile.")
            return pd.DataFrame()

        combined = pd.concat(frames, ignore_index=True)
        combined = self._limpiar_datos(combined)

        if progress_callback:
            progress_callback(100, f"Carga completa: {len(combined):,} registros")

        self._cache = combined
        logger.info(
            "Cargados %d registros de %d/%d shapefiles",
            len(combined), len(frames), total,
        )
        return combined

    def cargar_por_ur(self, ur: str) -> pd.DataFrame:
        """Carga solo los shapefiles de una Unidad Regional específica."""
        df = self.cargar_todo()
        return df[df["_unidad_regional"] == ur.upper()].copy()

    def cargar_por_keys(self, keys: list[str]) -> pd.DataFrame:
        """Carga solo un subconjunto de shapefiles por sus claves."""
        frames: list[pd.DataFrame] = []
        for key in keys:
            df = self._leer_shapefile(key)
            if df is not None and len(df) > 0:
                df = self._normalizar_esquema(df)
                frames.append(df)
        if not frames:
            return pd.DataFrame()
        combined = pd.concat(frames, ignore_index=True)
        return self._limpiar_datos(combined)

    def invalidar_cache(self):
        """Invalida el DataFrame cacheado para forzar recarga."""
        self._cache = None

    @property
    def errores(self) -> list[dict]:
        """Lista de errores de carga."""
        return self._errores

    # ----- Singleton de conveniencia -----

    _instance: Optional["ShapefileLoader"] = None

    @classmethod
    def get_instance(cls) -> "ShapefileLoader":
        """Devuelve una instancia singleton del loader."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
