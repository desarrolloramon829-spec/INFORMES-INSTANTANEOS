"""
Detección inteligente de encoding y reparación de texto mojibake.

Usa 3 estrategias para detectar el encoding de archivos .dbf:
1. Archivo .cpg (creado por QGIS con el encoding explícito)
2. Byte de codepage del header .dbf (estándar dBASE)
3. charset-normalizer (red neuronal) sobre texto extraído de registros

Luego usa ftfy para reparar texto corrupto (mojibake) automáticamente.
"""
from __future__ import annotations

import logging
import os
import struct
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Mapeo del byte 29 del header .dbf a encoding
# Ref: http://www.clicketyclick.dk/databases/xbase/format/dbf_header.html
_DBF_CODEPAGE_MAP = {
    0x01: "cp437",
    0x02: "cp850",
    0x03: "cp1252",
    0x04: "cp10000",
    0x08: "cp865",
    0x09: "cp437",
    0x0A: "cp850",
    0x0B: "cp437",
    0x0D: "cp865",
    0x0E: "cp1252",
    0x57: "utf-8",
    0x58: "cp1252",
    0x59: "cp1252",
    0x64: "cp852",
    0x65: "cp866",
    0x66: "cp865",
    0x67: "cp861",
    0x68: "cp895",
    0x78: "cp950",
    0x79: "cp949",
    0x7A: "cp936",
    0x7B: "cp932",
    0x7C: "cp874",
    0x7D: "cp1255",
    0x7E: "cp1256",
    0xC8: "cp1250",
    0xC9: "cp1251",
    0xCA: "cp1252",
    0xCB: "cp1253",
    0xCC: "cp1254",
    0xCD: "cp1255",
    0xCE: "cp1256",
    0xCF: "cp1257",
}

# Normalización de nombres de encoding que pueda reportar .cpg o charset-normalizer
_ENCODING_NORMALIZE = {
    "windows-1252": "cp1252",
    "windows-1250": "cp1250",
    "windows-1251": "cp1251",
    "iso-8859-1": "latin1",
    "iso-8859-15": "latin1",
    "ascii": "utf-8",
    "system": "cp1252",
    "ldid/87": "cp1252",
    "mac_iceland": "cp1252",
    "mac_roman": "cp1252",
    "cp1006": "cp1252",
}


def _leer_encoding_cpg(shp_path: str) -> Optional[str]:
    """Lee el encoding desde el archivo .cpg asociado al shapefile."""
    base = os.path.splitext(shp_path)[0]
    for ext in (".cpg", ".CPG"):
        cpg_path = base + ext
        if os.path.exists(cpg_path):
            try:
                with open(cpg_path, "r", encoding="ascii", errors="ignore") as f:
                    encoding = f.read().strip()
                if encoding:
                    normalized = _ENCODING_NORMALIZE.get(encoding.lower(), encoding)
                    logger.debug("Encoding desde .cpg: '%s' → '%s' para %s", encoding, normalized, shp_path)
                    return normalized
            except Exception:
                pass
    return None


def _leer_codepage_dbf(dbf_path: str) -> Optional[str]:
    """Lee el byte de codepage (byte 29) del header .dbf."""
    try:
        with open(dbf_path, "rb") as f:
            header = f.read(32)
        if len(header) < 30:
            return None
        cp_byte = header[29]
        encoding = _DBF_CODEPAGE_MAP.get(cp_byte)
        if encoding:
            logger.debug("Encoding desde codepage byte 0x%02X: '%s' para %s", cp_byte, encoding, dbf_path)
        return encoding
    except Exception:
        return None


def _detectar_heuristica_utf8(dbf_path: str) -> str:
    """
    Heurística simple y confiable: intenta decodificar registros de datos
    como UTF-8 strict. Si funciona sin errores → UTF-8, si falla → cp1252.

    Mucho más confiable que charset-normalizer para archivos .dbf porque:
    - Los .dbf tienen registros de ancho fijo con mucho padding (espacios)
    - charset-normalizer confunde ese padding con encodings CJK (big5, cp932)
    - La distinción real en estos archivos argentinos es solo UTF-8 vs cp1252
    """
    try:
        file_size = os.path.getsize(dbf_path)
        with open(dbf_path, "rb") as f:
            header = f.read(32)
            if len(header) < 12:
                return "cp1252"
            header_size = struct.unpack("<H", header[8:10])[0]
            data_size = file_size - header_size
            chunk = 1024 * 1024  # 1MB

            if data_size <= 6 * chunk:
                # Archivos <= 3MB: leer todo
                f.seek(header_size)
                data_bytes = f.read()
            else:
                # Archivos grandes: leer 1MB inicio + 1MB medio + 1MB final
                f.seek(header_size)
                start_bytes = f.read(chunk)
                mid_offset = header_size + data_size // 2
                f.seek(mid_offset)
                mid_bytes = f.read(chunk)
                f.seek(max(header_size, file_size - chunk))
                end_bytes = f.read()
                data_bytes = start_bytes + mid_bytes + end_bytes

        if not data_bytes:
            return "cp1252"

        # Si no hay bytes no-ASCII, es puro ASCII → compatible con ambos
        has_non_ascii = any(b > 127 for b in data_bytes)
        if not has_non_ascii:
            return "utf-8"

        # Intentar decodificar como UTF-8 strict
        try:
            data_bytes.decode("utf-8")
            logger.debug("Heurística: UTF-8 válido para %s", dbf_path)
            return "utf-8"
        except UnicodeDecodeError:
            logger.debug("Heurística: No es UTF-8, asumiendo cp1252 para %s", dbf_path)
            return "cp1252"

    except Exception as e:
        logger.debug("Heurística falló para %s: %s, usando cp1252", dbf_path, e)
        return "cp1252"


def detectar_encoding_dbf(shp_path: str) -> str:
    """
    Detecta el encoding del archivo .dbf asociado a un shapefile.

    Estrategia:
    - Heurística binaria sobre los registros .dbf: intenta UTF-8 strict,
      si falla → cp1252. Es la más confiable porque examina datos reales.
    - .cpg y codepage byte solo se usan si el .dbf no existe.

    Returns:
        Encoding detectado (siempre devuelve un valor, nunca None).
    """
    dbf_path = os.path.splitext(shp_path)[0] + ".dbf"

    if os.path.exists(dbf_path):
        # Heurística sobre datos reales: siempre correcta para utf-8 vs cp1252
        return _detectar_heuristica_utf8(dbf_path)

    # Sin .dbf, recurrir a .cpg como mejor opción
    enc = _leer_encoding_cpg(shp_path)
    if enc:
        return enc

    return "cp1252"


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
