"""
Detección inteligente de encoding y reparación de texto mojibake.

Usa charset-normalizer (red neuronal probabilística) para detectar el encoding
correcto de archivos .dbf y ftfy para reparar texto corrupto automáticamente.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def detectar_encoding_dbf(shp_path: str) -> Optional[str]:
    """
    Detecta el encoding del archivo .dbf asociado a un shapefile usando
    charset-normalizer (modelo neuronal probabilístico).

    Args:
        shp_path: Ruta completa al archivo .shp

    Returns:
        Encoding detectado con mayor confianza, o None si no se puede determinar.
    """
    from charset_normalizer import from_bytes

    dbf_path = os.path.splitext(shp_path)[0] + ".dbf"
    if not os.path.exists(dbf_path):
        logger.debug("Archivo .dbf no encontrado: %s", dbf_path)
        return None

    try:
        # Leer los primeros 64KB del .dbf (suficiente para detección confiable)
        with open(dbf_path, "rb") as f:
            raw_bytes = f.read(65536)

        resultado = from_bytes(raw_bytes)
        mejor = resultado.best()

        if mejor is None:
            logger.debug("charset-normalizer no pudo detectar encoding para %s", dbf_path)
            return None

        encoding = mejor.encoding
        # charset-normalizer usa nombres como 'ascii', 'windows-1252', etc.
        # Normalizar a nombres que geopandas/pyogrio aceptan
        _NORMALIZE_MAP = {
            "windows-1252": "cp1252",
            "windows-1250": "cp1250",
            "iso-8859-1": "latin1",
            "iso-8859-15": "latin1",
            "ascii": "utf-8",  # ASCII es subconjunto de UTF-8
        }
        encoding = _NORMALIZE_MAP.get(encoding.lower(), encoding)

        logger.debug(
            "charset-normalizer detectó encoding '%s' para %s",
            encoding, dbf_path,
        )
        return encoding

    except Exception as e:
        logger.debug("Error detectando encoding de %s: %s", dbf_path, e)
        return None


def reparar_texto_mojibake(df: pd.DataFrame) -> pd.DataFrame:
    """
    Repara texto corrupto (mojibake) en todas las columnas de texto del DataFrame
    usando ftfy (heurísticas de IA para reparación de encoding).

    Transforma: Ã© → é, Ã¡ → á, Ã± → ñ, Ã³ → ó, etc.

    Args:
        df: DataFrame con posible texto corrupto.

    Returns:
        DataFrame con texto reparado (copia).
    """
    from ftfy import fix_text

    df = df.copy()
    text_cols = df.select_dtypes(include="object").columns

    for col in text_cols:
        mask = df[col].notna()
        if mask.any():
            df.loc[mask, col] = df.loc[mask, col].apply(
                lambda x: fix_text(str(x)) if x else x
            )

    return df


def leer_dbf_como_dataframe(shp_path: str) -> Optional[pd.DataFrame]:
    """
    Lee un archivo .dbf directamente usando dbfread como fallback
    cuando geopandas no puede leer el shapefile.

    Recupera todos los datos tabulares aunque se pierda la geometría.

    Args:
        shp_path: Ruta completa al archivo .shp

    Returns:
        DataFrame con los registros del .dbf, o None si falla.
    """
    from dbfread import DBF

    dbf_path = os.path.splitext(shp_path)[0] + ".dbf"
    if not os.path.exists(dbf_path):
        logger.warning("Archivo .dbf no encontrado para fallback: %s", dbf_path)
        return None

    # Detectar encoding para el .dbf
    encoding = detectar_encoding_dbf(shp_path) or "latin1"

    try:
        table = DBF(dbf_path, encoding=encoding, char_decode_errors="replace")
        records = list(table)
        if not records:
            return None

        df = pd.DataFrame(records)
        # Reparar mojibake residual
        df = reparar_texto_mojibake(df)

        logger.info(
            "Fallback dbfread exitoso para %s: %d registros recuperados con encoding '%s'",
            dbf_path, len(df), encoding,
        )
        return df

    except Exception as e:
        logger.error("Fallback dbfread falló para %s: %s", dbf_path, e)
        return None
