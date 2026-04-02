"""
Módulo de carga y normalización de shapefiles.
Lee los 132 shapefiles, unifica esquemas, limpia datos y genera un DataFrame único.
"""
from __future__ import annotations

import json
import os
import re
import logging
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import geopandas as gpd
import pandas as pd
import numpy as np

from app.config.settings import (
    BASE_SHAPEFILE_PATH,
    CACHE_DIR,
    CACHE_PARQUET_PATH,
    VALORES_BASURA,
    FRANJAS_HORARIAS,
    DIAS_SEMANA,
    MESES,
    DELITO_CATEGORIAS,
    FECHA_MINIMA_CARGA,
)
from app.config.shapefile_registry import (
    _SHAPEFILES,
    get_full_path,
    get_ur_from_key,
)
from app.src.data.encoding_detector import (
    detectar_encoding_dbf,
    reparar_texto_mojibake,
    leer_dbf_como_dataframe,
)

logger = logging.getLogger(__name__)

# Encodings que acepta QGIS 2.14 / dBASE IV
# Orden: utf-8 primero; latin1 al final porque nunca lanza excepción.
_ENCODINGS = ["utf-8", "cp1252", "iso-8859-1", "latin1"]

# Secuencias mojibake comunes de UTF-8 leído como latin1
_MOJIBAKE_PATTERNS = ["Ã©", "Ã¡", "Ã±", "Ã³", "Ã\xad", "Ã¼", "Ã\x89"]

_ENCODING_WARNING_SNIPPETS = (
    "couldn't be converted correctly",
    "could not be converted correctly",
    "converted correctly from cp1252 to utf-8",
)

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


def extraer_fecha(fecha_str: str):
    """
    Extrae un datetime.date de un string "dia DD-MM-YYYY" o "DD-MM-YYYY".
    Devuelve None si no es parseable.
    """
    import datetime
    if pd.isna(fecha_str):
        return None
    fecha_str = str(fecha_str).strip()
    match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", fecha_str)
    if match:
        dia, mes, anio = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            return datetime.date(anio, mes, dia)
        except ValueError:
            return None
    return None


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
        self._encoding_fallbacks: list[dict] = []

    @staticmethod
    def _has_encoding_warning(captured_warnings) -> bool:
        """Detecta advertencias típicas de pyogrio sobre conversión defectuosa."""
        for warning_item in captured_warnings:
            message = str(warning_item.message).lower()
            if any(snippet in message for snippet in _ENCODING_WARNING_SNIPPETS):
                return True
        return False

    def _read_geofile(self, full_path: str, key: str, encoding: Optional[str] = None):
        """Lee un shapefile capturando advertencias de encoding para decidir reintentos."""
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always", RuntimeWarning)
            gdf = gpd.read_file(full_path, encoding=encoding)

        if self._has_encoding_warning(captured_warnings):
            logger.debug(
                "Advertencia de conversión detectada al leer %s con encoding '%s'. Se probará otra alternativa.",
                key,
                encoding or "auto",
            )
            return None

        return gdf

    def _registrar_fallback_encoding(
        self,
        key: str,
        full_path: str,
        encoding_final: str,
        intentos_descartados: list[dict],
    ) -> None:
        """Registra en logs qué shapefiles necesitaron fallback de encoding."""
        evento = {
            "key": key,
            "path": full_path,
            "encoding_final": encoding_final,
            "intentos_descartados": list(intentos_descartados),
        }
        self._encoding_fallbacks.append(evento)

        detalle_intentos = ", ".join(
            f"{item['encoding']} ({item['motivo']})" for item in intentos_descartados
        ) or "sin intentos previos"
        logger.info(
            "Fallback de encoding en %s. Encoding final=%s. Intentos descartados=%s",
            key,
            encoding_final,
            detalle_intentos,
        )

    def _resumen_encoding_fallbacks(self) -> dict:
        """Construye un resumen estructurado de fallbacks de encoding."""
        resumen_por_encoding: dict[str, int] = {}
        for item in self._encoding_fallbacks:
            encoding_final = item.get("encoding_final", "desconocido")
            resumen_por_encoding[encoding_final] = resumen_por_encoding.get(encoding_final, 0) + 1

        return {
            "total_fallbacks": len(self._encoding_fallbacks),
            "por_encoding_final": resumen_por_encoding,
            "shapefiles": [item["key"] for item in self._encoding_fallbacks],
            "detalles": self._encoding_fallbacks,
        }

    def _exportar_diagnostico_json(self, diagnostic_json_path: str, payload: dict) -> None:
        """Escribe un archivo JSON de diagnóstico si el usuario lo solicita."""
        output_dir = os.path.dirname(diagnostic_json_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(diagnostic_json_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        logger.info("Diagnóstico de carga exportado a JSON: %s", diagnostic_json_path)

    # ----- Lectura de un shapefile individual -----

    def _leer_shapefile(self, key: str) -> Optional[pd.DataFrame]:
        """
        Lee un shapefile con detección inteligente de encoding.

        Estrategia (de más rápido a más lento):
        1. charset-normalizer detecta encoding del .dbf → 1 sola lectura
        2. Si hay mojibake residual → ftfy lo repara en post-proceso
        3. Si geopandas falla → fallback con _ENCODINGS clásicos
        4. Si todo falla → dbfread lee el .dbf directamente (sin geometría)
        """
        try:
            full_path = get_full_path(key)
        except KeyError:
            logger.warning("Clave no registrada: %s", key)
            return None

        if not os.path.exists(full_path):
            logger.warning("Archivo no encontrado: %s", full_path)
            self._errores.append({"key": key, "error": "archivo no encontrado"})
            return None

        intentos_descartados: list[dict] = []

        # --- Paso 1: Detección inteligente + lectura directa + ftfy ---
        # No usamos _read_geofile aquí porque su check de warnings es
        # innecesario: ftfy repara cualquier mojibake residual.
        encoding_detectado = detectar_encoding_dbf(full_path)
        if encoding_detectado:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    gdf = gpd.read_file(full_path, encoding=encoding_detectado)
                df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
                df = reparar_texto_mojibake(df)
                df["_shapefile_key"] = key
                df["_unidad_regional"] = get_ur_from_key(key)
                logger.debug("Lectura exitosa de %s con encoding detectado '%s'", key, encoding_detectado)
                return df
            except Exception as exc:
                intentos_descartados.append({"encoding": encoding_detectado, "motivo": type(exc).__name__})

        # --- Paso 2: Fallback clásico con encodings conocidos ---
        for enc in _ENCODINGS:
            if enc == encoding_detectado:
                continue  # Ya lo intentamos en paso 1
            try:
                gdf = self._read_geofile(full_path, key, encoding=enc)
                if gdf is None:
                    intentos_descartados.append({"encoding": enc, "motivo": "warning-conversion"})
                    continue
                df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
                # Reparar mojibake residual con ftfy en vez de rechazar
                df = reparar_texto_mojibake(df)
                df["_shapefile_key"] = key
                df["_unidad_regional"] = get_ur_from_key(key)
                if intentos_descartados:
                    self._registrar_fallback_encoding(key, full_path, enc, intentos_descartados)
                return df
            except Exception as exc:
                intentos_descartados.append({"encoding": enc, "motivo": type(exc).__name__})
                continue

        # --- Paso 3: Autodetección sin encoding explícito + ftfy ---
        try:
            gdf = self._read_geofile(full_path, key)
            if gdf is None:
                raise ValueError("advertencia de conversión durante autodetección de encoding")
            df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
            df = reparar_texto_mojibake(df)
            df["_shapefile_key"] = key
            df["_unidad_regional"] = get_ur_from_key(key)
            self._registrar_fallback_encoding(key, full_path, "auto", intentos_descartados)
            return df
        except Exception:
            pass

        # --- Paso 4: Fallback extremo con dbfread (recupera datos sin geometría) ---
        logger.warning("geopandas falló para %s, intentando fallback dbfread...", key)
        df = leer_dbf_como_dataframe(full_path)
        if df is not None and len(df) > 0:
            df["_shapefile_key"] = key
            df["_unidad_regional"] = get_ur_from_key(key)
            self._registrar_fallback_encoding(key, full_path, "dbfread", intentos_descartados)
            return df

        logger.error("No se pudo leer %s con ningún método", key)
        self._errores.append({"key": key, "error": "todos los métodos fallaron"})
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

        # --- FRANJA HORARIA: mantener solo valores válidos; inválidos → SIN_DATOS ---
        if "FRAN_HORAR" in df.columns:
            def _norm_franja(x):
                if pd.notna(x) and str(x).strip() in FRANJAS_HORARIAS:
                    return str(x).strip()
                return "SIN_DATOS"
            df["FRAN_HORAR"] = df["FRAN_HORAR"].apply(_norm_franja)

        # --- DIA HECHO: normalizar; inválidos → sin_datos ---
        if "DIA_HECHO" in df.columns:
            def _norm_dia(x):
                if pd.notna(x) and str(x).strip().lower() in DIAS_SEMANA:
                    return str(x).strip().lower()
                return "sin_datos"
            df["DIA_HECHO"] = df["DIA_HECHO"].apply(_norm_dia)

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

        # --- DELITO: normalizar duplicados y unificar variantes sin prefijo ---
        _DELITO_NORM = {
            "ROBO": "010-ROBO",
            "HURTO": "050-HURTO",
            "ESTAFA": "160-ESTAFA",
        }
        if "DELITO" in df.columns:
            def _normalizar_delito(x):
                if pd.isna(x):
                    return None
                v = str(x).strip()
                if v in VALORES_BASURA:
                    return None
                return _DELITO_NORM.get(v, v)
            df["DELITO"] = df["DELITO"].apply(_normalizar_delito)

        # --- Extraer Año y Mes numérico de FECHA_HECH ---
        if "FECHA_HECH" in df.columns:
            parsed = df["FECHA_HECH"].apply(extraer_anio_mes)
            df["_anio"] = parsed.apply(lambda x: x[0])
            df["_mes_num"] = parsed.apply(lambda x: x[1])
            # Columna de fecha completa para filtro por rango de días
            df["_fecha"] = df["FECHA_HECH"].apply(extraer_fecha)

        # --- Limpiar coordenadas ---
        for col in ["X", "Y"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    # ----- Caché Parquet persistente -----

    @staticmethod
    def _cache_parquet_es_valido() -> bool:
        """
        Verifica si el caché Parquet existe y es más reciente que todos los .shp.
        Si la unidad de red no está disponible, acepta el caché existente.
        """
        if not os.path.exists(CACHE_PARQUET_PATH):
            return False

        cache_mtime = os.path.getmtime(CACHE_PARQUET_PATH)

        # Verificar si la fuente de datos es accesible
        if not os.path.exists(BASE_SHAPEFILE_PATH):
            logger.warning(
                "Unidad de red no disponible (%s). Usando caché Parquet existente.",
                BASE_SHAPEFILE_PATH,
            )
            return True

        # Comparar con el mtime más reciente de los .shp
        for key in _SHAPEFILES:
            try:
                shp_path = get_full_path(key)
                if os.path.exists(shp_path) and os.path.getmtime(shp_path) > cache_mtime:
                    logger.info("Shapefile %s es más reciente que el caché. Se regenerará.", key)
                    return False
            except (KeyError, OSError):
                continue

        return True

    @staticmethod
    def _guardar_cache_parquet(df: pd.DataFrame) -> None:
        """Guarda el DataFrame procesado como Parquet para carga instantánea futura."""
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            df.to_parquet(CACHE_PARQUET_PATH, engine="pyarrow", index=False)
            logger.info("Caché Parquet guardado en %s (%d registros)", CACHE_PARQUET_PATH, len(df))
        except Exception as e:
            logger.warning("No se pudo guardar caché Parquet: %s", e)

    @staticmethod
    def _cargar_cache_parquet() -> Optional[pd.DataFrame]:
        """Carga el DataFrame desde el caché Parquet."""
        try:
            df = pd.read_parquet(CACHE_PARQUET_PATH, engine="pyarrow")
            # Restaurar columna _fecha como date (Parquet la guarda como datetime)
            if "_fecha" in df.columns:
                df["_fecha"] = pd.to_datetime(df["_fecha"], errors="coerce").dt.date
            logger.info("Caché Parquet cargado: %d registros desde %s", len(df), CACHE_PARQUET_PATH)
            return df
        except Exception as e:
            logger.warning("No se pudo leer caché Parquet: %s", e)
            return None

    # ----- Métodos públicos de carga -----

    def cargar_todo(
        self,
        use_cache: bool = True,
        progress_callback=None,
        diagnostic_json_path: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Carga y combina los 132 shapefiles en un único DataFrame normalizado.

        Estrategia de carga (de más rápido a más lento):
        1. Caché en memoria (instantáneo)
        2. Caché Parquet en disco (< 2 segundos)
        3. Lectura paralela de shapefiles con detección inteligente de encoding

        Args:
            use_cache: Si True, intenta devolver datos cacheados.
            progress_callback: Función f(pct, msg) para informar progreso.
            diagnostic_json_path: Ruta opcional para exportar un JSON de diagnóstico.

        Returns:
            DataFrame con todos los registros normalizados.
        """
        # --- Nivel 1: Caché en memoria ---
        if use_cache and self._cache is not None:
            return self._cache

        # --- Nivel 2: Caché Parquet en disco ---
        if use_cache and self._cache_parquet_es_valido():
            if progress_callback:
                progress_callback(10, "Cargando desde caché local...")
            df_cached = self._cargar_cache_parquet()
            if df_cached is not None:
                if progress_callback:
                    progress_callback(100, f"Carga instantánea: {len(df_cached):,} registros desde caché")
                self._cache = df_cached
                return df_cached

        # --- Nivel 3: Lectura paralela desde shapefiles ---
        if progress_callback:
            progress_callback(0, "Iniciando carga desde shapefiles con IA de encoding...")

        frames: list[pd.DataFrame] = []
        keys = list(_SHAPEFILES.keys())
        total = len(keys)
        self._errores = []
        self._encoding_fallbacks = []

        # Lock para progreso thread-safe
        _progress_lock = threading.Lock()
        _completed = [0]  # mutable para closure

        def _procesar_shapefile(key: str) -> Optional[pd.DataFrame]:
            """Carga y normaliza un shapefile individual (ejecutado en thread)."""
            df = self._leer_shapefile(key)
            if df is not None and len(df) > 0:
                df = self._normalizar_esquema(df)
                return df
            return None

        # ThreadPoolExecutor: 4 workers conservadores para I/O de red
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_procesar_shapefile, key): key for key in keys}

            for future in as_completed(futures):
                key = futures[future]
                try:
                    result = future.result()
                    if result is not None:
                        frames.append(result)
                except Exception as exc:
                    logger.error("Error procesando %s: %s", key, exc)
                    self._errores.append({"key": key, "error": str(exc)})

                with _progress_lock:
                    _completed[0] += 1
                    if progress_callback:
                        pct = int((_completed[0] / total) * 95)  # Reservar 5% para post-proceso
                        progress_callback(pct, f"Cargando shapefiles ({_completed[0]}/{total})...")

        if not frames:
            logger.error("No se pudo cargar ningún shapefile.")
            return pd.DataFrame()

        if progress_callback:
            progress_callback(96, "Combinando y limpiando datos...")

        combined = pd.concat(frames, ignore_index=True)
        combined = self._limpiar_datos(combined)

        # Filtrar registros anteriores a FECHA_MINIMA_CARGA
        if FECHA_MINIMA_CARGA and "_fecha" in combined.columns:
            antes = len(combined)
            combined = combined[
                combined["_fecha"].isna() | (combined["_fecha"] >= FECHA_MINIMA_CARGA)
            ]
            descartados = antes - len(combined)
            if descartados > 0:
                logger.info("Descartados %d registros históricos (anteriores a %s)", descartados, FECHA_MINIMA_CARGA)

        if progress_callback:
            progress_callback(98, "Guardando caché para próxima carga instantánea...")

        # Guardar caché Parquet para próxima vez
        self._guardar_cache_parquet(combined)

        if progress_callback:
            progress_callback(100, f"Carga completa: {len(combined):,} registros")

        self._cache = combined

        # --- Diagnóstico de carga ---
        n = len(combined)
        sin_fecha = int(combined["_anio"].isna().sum()) if "_anio" in combined.columns else 0
        sin_franja = int((combined["FRAN_HORAR"] == "SIN_DATOS").sum()) if "FRAN_HORAR" in combined.columns else 0
        sin_dia = int((combined["DIA_HECHO"] == "sin_datos").sum()) if "DIA_HECHO" in combined.columns else 0
        logger.info(
            "Cargados %d registros de %d/%d shapefiles",
            n, len(frames), total,
        )
        logger.info(
            "Diagnóstico: sin_fecha=%d (%.1f%%), sin_franja=%d (%.1f%%), sin_dia=%d (%.1f%%)",
            sin_fecha, (sin_fecha / n * 100) if n else 0,
            sin_franja, (sin_franja / n * 100) if n else 0,
            sin_dia, (sin_dia / n * 100) if n else 0,
        )
        if self._encoding_fallbacks:
            fallback_summary = self._resumen_encoding_fallbacks()
            logger.info(
                "Fallbacks de encoding detectados en %d shapefiles.",
                len(self._encoding_fallbacks),
            )
            logger.info(
                "Resumen estructurado de fallbacks de encoding: %s",
                json.dumps(
                    {
                        "total_fallbacks": fallback_summary["total_fallbacks"],
                        "por_encoding_final": fallback_summary["por_encoding_final"],
                        "shapefiles": fallback_summary["shapefiles"],
                    },
                    ensure_ascii=False,
                ),
            )
        if "_unidad_regional" in combined.columns:
            dist_ur = combined["_unidad_regional"].value_counts().to_dict()
            logger.info("Distribución UR: %s", dist_ur)
        if "DELITO" in combined.columns:
            delitos_unicos = sorted(combined["DELITO"].dropna().unique().tolist())
            logger.info("Valores DELITO únicos (%d): %s", len(delitos_unicos), delitos_unicos)

        if diagnostic_json_path:
            diagnostic_payload = {
                "registros": n,
                "shapefiles_cargados": len(frames),
                "shapefiles_totales": total,
                "diagnostico": {
                    "sin_fecha": sin_fecha,
                    "sin_franja": sin_franja,
                    "sin_dia": sin_dia,
                },
                "errores": self._errores,
                "encoding_fallbacks": self._resumen_encoding_fallbacks(),
            }
            self._exportar_diagnostico_json(diagnostic_json_path, diagnostic_payload)

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

    def invalidar_cache(self, incluir_parquet: bool = False):
        """Invalida el DataFrame cacheado para forzar recarga.

        Args:
            incluir_parquet: Si True, también elimina el caché Parquet en disco.
        """
        self._cache = None
        if incluir_parquet and os.path.exists(CACHE_PARQUET_PATH):
            try:
                os.remove(CACHE_PARQUET_PATH)
                logger.info("Caché Parquet eliminado: %s", CACHE_PARQUET_PATH)
            except OSError as e:
                logger.warning("No se pudo eliminar caché Parquet: %s", e)

    @property
    def errores(self) -> list[dict]:
        """Lista de errores de carga."""
        return self._errores

    @property
    def encoding_fallbacks(self) -> list[dict]:
        """Lista de shapefiles que necesitaron fallback de encoding."""
        return self._encoding_fallbacks

    # ----- Singleton de conveniencia -----

    _instance: Optional["ShapefileLoader"] = None

    @classmethod
    def get_instance(cls) -> "ShapefileLoader":
        """Devuelve una instancia singleton del loader."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
