"""
=============================================================================
SCRIPT DE EXPLORACIÓN DE SHAPEFILES - MAPA DELICTUAL
=============================================================================
Este script explora la estructura de los archivos .shp para documentar:
- Columnas disponibles en cada shapefile
- Tipos de datos
- Valores únicos por campo
- Cantidad de registros
- Sistema de coordenadas (CRS)
- Comparación de esquemas entre shapefiles

Ejecutar: python explorar_shapefiles.py
Resultado: genera un archivo 'reporte_exploracion.txt' con toda la info
=============================================================================
"""

import os
import sys
import json
from datetime import datetime
from collections import defaultdict

# ---- Verificar dependencias ----
try:
    import geopandas as gpd
    import pandas as pd
except ImportError:
    print("=" * 60)
    print("ERROR: Faltan dependencias. Ejecutar:")
    print("  pip install geopandas pandas fiona pyshp shapely")
    print("=" * 60)
    sys.exit(1)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

BASE_PATH = r"Z:\MAPA DEL DELITO\MAPAS DEL DELITO POR JURISDICCIONES"

# Registro completo de shapefiles organizados por categoría
SHAPEFILES = {
    # --- SHAPES ESPECIALES ---
    "CARGA_FINCAS": r"CARGA FINCAS - copia1\CARGA FINCAS Copia1\CARGA FINCAS Copia1.shp",
    "CARGA_ABIGEATO": r"CARGA ABIGEATO - copia1\CARGA ABIGEATO - copia1\CARGA ABIGEATO - copia1.shp",

    # --- URC (Unidad Regional Capital) ---
    "URC_CRIA1":  r"CRIA1-URC- 2020\MAPA DELICTUAL CRIA1-URC-2020\MAPA DELICTUAL CRIA1-URC-2020.shp",
    "URC_CRIA2":  r"CRIA2-URC-2020\MAPA DELICTUAL CRIA 2-URC\MAPA DELICTUAL CRIA2-URC-2020.shp",
    "URC_CRIA3":  r"CRIA3-URC-2020\MAPA DELICTUAL CRIA3-URC-2020\MAPA DELICTUAL CRIA3-URC-2020.shp",
    "URC_CRIA4":  r"CRIA4-URC-2020\MAPA DELICTUAL CRIA4-URC-2020\MAPA DELICTUAL CRIA4-URC-2020.shp",
    "URC_CRIA5":  r"CRIA5-URC-2020\MAPA DELICTUAL CRIA5-URC-2020\MAPA DELICTUAL CRIA5-URC-2020.shp",
    "URC_CRIA6":  r"CRIA6-URC-2020\MAPA DELICTUAL CRIA6-URC-2020\MAPA DELICTUAL CRIA6-URC-2020.shp",
    "URC_CRIA7":  r"CRIA7-URC-2020\MAPA DELICTUAL CRIA7-URC-2019\MAPA DELICTUAL CRIA7-URC-2019.shp",
    "URC_CRIA8":  r"CRIA8-URC-2020\MAPA DELICTUAL CRIA8-URC-2020\MAPA DELICTUAL CRIA8-URC-2020.shp",
    "URC_CRIA9":  r"CRIA9-URC-2020\MAPA DELICTUAL CRIA9-URC-2020\MAPA DELICTUAL CRIA9-URC-2020.shp",
    "URC_CRIA10": r"CRIA10-URC-2020\MAPA DELICTUAL CRIA10-URC-2020\MAPA DELICTUAL CRIA10-URC-2020.shp",
    "URC_CRIA11": r"CRIA11-URC-2020\MAPA DELICTUAL CRIA11-URC-2020\MAPA DELICTUAL CRIA11-URC-2020.shp",
    "URC_CRIA12": r"CRIA12-URC-2020\MAPA DELICTUAL CRIA12-URC-2020\MAPA DELICTUAL CRIA12-URC-2020.shp",
    "URC_CRIA13": r"CRIA13-URC-2020\MAPA DELICTUAL CRIA13-URC-2020\MAPA DELICTUAL CRIA13-URC-2020.shp",
    "URC_CRIA14": r"CRIA14-URC-2020\MAPA DELICTUAL CRIA14-URC-2020\MAPA DELICTUAL CRIA14-URC-2020.shp",
    "URC_CRIA15": r"CRIA15-URC-2020\MAPA DELICTUAL CRIA15-URC-2020\MAPA DELICTUAL CRIA15-URC-2020.shp",

    # --- URE (Unidad Regional Este) - muestra representativa ---
    "URE_BURRUYACU":       r"CRIA BURRUYACU-URE-2024\MAPA DELICTUAL CRIA BURRUYACU-URE\MAPA DELICTUAL CRIA BURRUYACU-URE.shp",
    "URE_BANDA_RIO_SALI":  r"CRIA BANDA DEL RIO SALI-URE\MAPA DELICTUAL CRIA BANDA DEL RIO SALI - URE\MAPA DELICTUAL CRIA BANDA DEL RIO SALI - URE.shp",
    "URE_ALDERETES":       r"CRIA ALDERETES-URE\MAPA DELICTUAL CRIA ALDERETES-URE\MAPA DELICTUAL CRIA ALDERETES-URE.shp",
    "URE_LASTENIA":        r"CRIA LASTENIA-URE\MAPA DELICTUAL CRIA LASTENIA - URE\MAPA DELICTUAL CRIA LASTENIA - URE.shp",
    "URE_GUEMES":          r"CRIA GUEMES-URE\MAPA DELICTUAL CRIA GUEMES-URE-2020\MAPA DELICTUAL CRIA GUEMES-URE-2020.shp",
    "URE_LAS_CEJAS":       r"CRIA LAS CEJAS-URE\MAPA DELICTUAL CRIA LAS CEJAS-URE\MAPA DELICTUAL CRIA LAS CEJAS-URE.shp",
    "URE_BELLA_VISTA":     r"CRIA BELLA VISTA-URE\MAPA DELICTUAL CRIA BELLA VISTA-URE\MAPA DELICTUAL CRIA BELLA VISTA-URE.shp",
    "URE_COLOMBRES":       r"CRIA COLOMBRES-URE\MAPA DELICTUAL CRIA COLOMBRES-URE\MAPA DELICTUAL CRIA COLOMBRES-URE.shp",
    "URE_EL_CHANIAR":      r"CRIA EL CHAÑAR-URE\MAPA DELICTUAL CRIA EL CHAÑAR-URE\MAPA DELICTUAL CRIA EL CHAÑAR-URE.shp",
    "URE_GARMENDIA":       r"CRIA GARMENDIA-URE-2024\MAPA DELICTUAL CRIA GARMENDIA-URE\MAPA DELICTUAL CRIA GARMENDIA-URE.shp",
    "URE_CHILCAS":         r"CRIA CHILCAS-URE-2024\MAPA DELICTUAL CRIA CHILCAS-URE\MAPA DELICTUAL CRIA CHILCAS-URE.shp",
    "URE_RANCHILLOS":      r"CRIA RANCHILLOS-URE\MAPA DELICTUAL CRIA DE RANCHILLOS-URE\MAPA DELICTUAL CRIA DE RANCHILLOS-URE.shp",
    "URE_LOS_RALOS":       r"CRIA LOS RALOS-URE\MAPA DELICTUAL CRIA LOS RALOS-URE\MAPA DELICTUAL CRIA LOS RALOS-URE.shp",
    "URE_DELFIN_GALLO":    r"CRIA DELFIN GALLO-URE\MAPA DELICTUAL CRIA DELFIN GALLO-URE\MAPA DELICTUAL CRIA DELFIN GALLO-URE.shp",
    "URE_LA_FLORIDA":      r"CRIA LA FLORIDA-URE\MAPA DELICTUAL CRIA LA FLORIDA-URE\MAPA DELICTUAL CRIA LA FLORIDA-URE.shp",
    "URE_SAN_ANDRES":      r"CRIA SAN ANDRES-URE\MAPA DELICTUAL CRIA SAN ANDRES-URE\MAPA DELICTUAL CRIA SAN ANDRES-URE.shp",
    "URE_EL_BRACHO":       r"CRIA EL BRACHO-URE\MAPA DELICTUAL CRIA EL BRACHO-URE\MAPA DELICTUAL CRIA EL BRACHO-URE.shp",
    "URE_POZO_ALTO":       r"CRIA POZO DEL ALTO-URE\MAPA DELICTUAL CRIA POZO DEL ALTO-URE\MAPA DELICTUAL CRIA POZO DEL ALTO-URE.shp",
    "URE_EL_NARANJO":      r"CRIA EL NARANJO-URE-2024\MAPA DELICTUAL CRIA EL NARANJO-URE\MAPA DELICTUAL CRIA EL NARANJO-URE.shp",
    "URE_PIEDRABUENA":     r"CRIA GOB PIEDRABUENA-URE-2024\MAPA DELICTUAL CRIA GOB PIEDRABUENA-URE\MAPA DELICTUAL CRIA GOB PIEDRABUENA-URE.shp",
    "URE_PADRE_MONTI":     r"CRIA VILLA PADRE MONTI-URE-2024\MAPA DELICTUAL CRIA VILLA PADRE MONTI-URE\MAPA DELICTUAL CRIA VILLA PADRE MONTI-URE.shp",
    "URE_EL_TIMBO":        r"CRIA EL TIMBO-URE\MAPA DELICTUAL CRIA EL TIMBO-URE\MAPA DELICTUAL CRIA EL TIMBO-URE.shp",
    "URE_LA_RAMADA":       r"CRIA LA RAMADA-URE-2024\MAPA DELICTUAL CRIA LA RAMADA-URE\MAPA DELICTUAL CRIA LA RAMADA-URE.shp",
    "URE_EL_CAJON":        r"CRIA EL CAJON-URE-2024\MAPA DELICTUAL CRIA EL CAJON-URE\MAPA DELICTUAL CRIA EL CAJON-URE.shp",
    "URE_VILLA_B_ARAOZ":   r"CRIA VILLA BENJAMIN ARAOZ-URE-2024\MAPA DELICTUAL CRIA VILLA BENJAMIN ARAOZ-URE\MAPA DELICTUAL CRIA VILLA BENJAMIN ARAOZ-URE.shp",
    "URE_EL_PUESTITO":     r"CRIA EL PUESTITO-URE-2024\MAPA DELICTUAL CRIA EL PUESTITO-URE\MAPA DELICTUAL CRIA EL PUESTITO-URE.shp",
    "URE_7_DE_ABRIL":      r"CRIA 7 DE ABRIL-URE-2024\MAPA DELICTUAL CRIA 7 DE ABRIL-URE\MAPA DELICTUAL CRIA 7 DE ABRIL-URE.shp",
    "URE_ROMERA_POZO":     r"CRIA ROMERA POZO-URE\MAPA DELICTUAL CRIA ROMERA POZO-URE\MAPA DELICTUAL CRIA ROMERA POZO-URE.shp",
    "URE_STA_ROSA_LEALES": r"CRIA SANTA ROSA DE LEALES-URE\MAPA DELICTUAL CRIA SANTA ROSA DE LEALES-URE\MAPA DELICTUAL CRIA SANTA ROSA DE LEALES-URE.shp",
    "URE_QUILMES":         r"CRIA QUILMES-URE\MAPA DELICTUAL CRIA QUILMES-URE\MAPA DELICTUAL CRIA QUILMES-URE.shp",
    "URE_INGENIO_LEALES":  r"CRIA INGENIO LEALES-URE\MAPA DELICTUAL CRIA INGENIO LEALES-URE\MAPA DELICTUAL CRIA INGENIO LEALES-URE.shp",
    "URE_LOS_SUELDOS":     r"CRIA LOS SUELDOS-URE\MAPA DELICTUAL CRIA LOS SUELDOS-URE\MAPA DELICTUAL CRIA LOS SUELDOS-URE.shp",
    "URE_ESTACION_ARAOZ":  r"CRIA ESTACION ARAOZ-URE-2024\MAPA DELICTUAL CRIA ESTACION ARAOZ-URE\MAPA DELICTUAL CRIA ESTACION ARAOZ-URE.shp",
    "URE_VILLA_LEALES":    r"CRIA VILLA DE LEALES-URE\MAPA DELICTUAL CRIA VILLA DE LEALES-URE\MAPA DELICTUAL CRIA VILLA DE LEALES-URE.shp",
    "URE_RIO_COLORADO":    r"CRIA RIO COLORADO-URE\MAPA DELICTUAL CRIA RIO COLORADO-URE\MAPA DELICTUAL CRIA RIO COLORADO-URE.shp",
    "URE_ESQUINA":         r"CRIA ESQUINA-URE\SHAPES_CRIA ESQUINA-URE\MAPA DELICTUAL CRIA ESQUINA-URE.shp",
    "URE_MANCOPA":         r"CRIA MANCOPA-URE\MAPA DELICTUAL CRIA MANCOPA - URE\MAPA DELICTUAL CRIA MANCOPA - URE.shp",
    "URE_AGUA_DULCE":      r"CRIA AGUA DULCE-URE-2024\MAPA DELICTUAL CRIA AGUA DULCE-URE\MAPA DELICTUAL CRIA AGUA DULCE-URE.shp",
    "URE_LOS_GOMES":       r"CRIA LOS GOMES-URE\MAPA DELICTUAL CRIA LOS GOMES-URE\MAPA DELICTUAL CRIA LOS GOMES-URE.shp",
    "URE_LOS_PUESTOS":     r"CRIA LOS PUESTOS-URE\MAPA DELICTUAL CRIA LOS PUESTOS-URE\MAPA DELICTUAL CRIA LOS PUESTOS-URE.shp",
    "URE_LOS_HERRERA":     r"CRIA LOS HERRERA-URE\MAPA DELICTUAL CRIA LOS HERRERA-URE\MAPA DELICTUAL CRIA LOS HERRERA-URE.shp",
    "URE_EL_MOJON":        r"CRIA EL MOJON-URE-2024\MAPA DELICTUAL CRIA EL MOJON-URE\MAPA DELICTUAL CRIA EL MOJON-URE.shp",
    "URE_CAMPO_QUIMIL":    r"CRIA CAMPO QUIMIL-URE-2024\MAPA DELICTUAL CRIA CAMPO QUIMIL-URE\MAPA DELICTUAL CRIA CAMPO QUIMIL-URE.shp",
    "URE_LOS_BULACIOS":    r"CRIA LOS BULACIOS-URE\MAPA DELICTUAL CRIA LOS BULACIOS-URE\MAPA DELICTUAL CRIA LOS BULACIOS-URE.shp",

    # --- URO (Unidad Regional Oeste) ---
    "URO_TAFI_VALLE":      r"CRIA TAFI DEL VALLE-URO\MAPA DELICTUAL CRIA  TAFI DEL VALLE-URO\MAPA DELICTUAL CRIA TAFI DEL VALLE-URO.shp",
    "URO_EL_MOLLAR":       r"CRIA EL MOLLAR-URO\MAPA DELICTUAL CRIA EL MOLLAR-URO\MAPA DELICTUAL CRIA EL MOLLAR-URO.shp",
    "URO_AMAICHA":         r"CRIA AMAICHA DEL VALLE-URO\MAPA DELICTUAL CRIA  AMAICHA DEL VALLE-URO\MAPA DELICTUAL CRIA AMAICHA DEL VALLE-URO.shp",
    "URO_COLALAO":         r"CRIA COLALAO DEL VALLE-URO-2024\MAPA DELICTUAL CRIA COLALAO DEL VALLE-URO\MAPA DELICTUAL CRIA COLALAO DEL VALLE-URO.shp",
    "URO_LULES":           r"CRIA LULES-URO\MAPA DELICTUAL CRIA LULES-URO\MAPA DELICTUAL CRIA LULES-URO.shp",
    "URO_LA_REDUCCION":    r"CRIA LA REDUCCION-URO\MAPA DELICTUAL CRIA LA REDUCCION-URO\MAPA DELICTUAL CRIA LA REDUCCION-URO.shp",
    "URO_EL_MANANTIAL":    r"CRIA EL MANANTIAL-URO\MAPA DELICTUAL CRIA EL MANANTIAL-URO\MAPA DELICTUAL CRIA EL MANANTIAL-URO.shp",
    "URO_SAN_PABLO":       r"CRIA SAN PABLO-URO\MAPA DELICTUAL CRIA SAN PABLO-URO-2020\MAPA DELICTUAL CRIA SAN PABLO-URO-2020.shp",
    "URO_VILLA_NOUGUES":   r"CRIA VILLA NOUGUES-URO\MAPA DELICTUAL CRIA VILLA NOUGUES-URO\MAPA DELICTUAL CRIA VILLA NOUGUES-URO.shp",
    "URO_LOS_AGUIRRE":     r"CRIA LOS AGUIRRE-URO\MAPA DELICTUAL CRIA LOS AGUIRRE-URO-2020\MAPA DELICTUAL CRIA LOS AGUIRRE-URO-2020.shp",
    "URO_FAMAILLA":        r"CRIA FAMAILLA-URO\MAPA DELICTUAL CRIA FAMAILLA-URO\MAPA DELICTUAL CRIA FAMAILLA-URO.shp",
    "URO_TTE_BERDINA":     r"CRIA TENIENTE BERDINA-URO-2024\MAPA DELICTUAL CRIA TENIENTE BERDINA-URO\MAPA DELICTUAL CRIA TENIENTE BERDINA-URO.shp",
    "URO_MONTEROS":        r"CRIA MONTEROS-URO\MAPA DELICTUAL CRIA MONTEROS-URO\MAPA DELICTUAL CRIA MONTEROS-URO.shp",
    "URO_SANTA_LUCIA":     r"CRIA SANTA LUCIA-URO-2024\MAPA DELICTUAL CRIA SANTA LUCIA-URO\MAPA DELICTUAL CRIA SANTA LUCIA-URO.shp",
    "URO_ACHERAL":         r"CRIA ACHERAL-URO-2024\MAPA DELICTUAL CRIA ACHERAL-URO\MAPA DELICTUAL CRIA ACHERAL-URO.shp",
    "URO_RIO_SECO":        r"CRIA RIO SECO-URO-2024\MAPA DELICTUAL CRIA RIO SECO-URO\MAPA DELICTUAL CRIA RIO SECO-URO.shp",
    "URO_VILLA_QUINTEROS": r"CRIA VILLA QUINTEROS-URO\MAPA DELICTUAL CRIA VILLA QUINTEROS-URO\MAPA DELICTUAL CRIA VILLA QUINTEROS-URO.shp",
    "URO_LEON_ROUGES":     r"CRIA LEON ROUGES-URO-2024\MAPA DELICTUAL CRIA LEON ROUGES-URO\MAPA DELICTUAL CRIA LEON ROUGES-URO.shp",
    "URO_CAPITAN_CACERES": r"CRIA CAPITAN CACERES-URO-2024\MAPA DELICTUAL CRIA CAPITAN CACERES-URO\MAPA DELICTUAL CRIA CAPITAN CACERES-URO.shp",
    "URO_LOS_SOSA":        r"CRIA LOS SOSA Y SOLDADO MALDONADO-URO-2024\MAPA DELICTUAL CRIA LOS SOSA Y SOLDADO MALDONADO-URO\MAPA DELICTUAL CRIA LOS SOSA Y SOLDADO MALDONADO-URO.shp",
    "URO_AMBERES":         r"CRIA AMBERES-URO-2024\MAPA DELICTUAL CRIA AMBERES-URO\MAPA DELICTUAL CRIA AMBERES-URO.shp",
    "URO_SGTO_MOYA":       r"CRIA SARGENTO MOYA-URO-2024\MAPA DELICTUAL CRIA SARGENTO MOYA-URO\MAPA DELICTUAL CRIA SARGENTO MOYA-URO.shp",

    # --- URS (Unidad Regional Sur) ---
    "URS_CONCEPCION":      r"CRIA CONCEPCION-URS\MAPA DELICTUAL CRIA CONCEPCION-URS\MAPA DELICTUAL CRIA CONCEPCION-URS.shp",
    "URS_ALTO_VERDE":      r"CRIA ALTO VERDE-URS\CRIA ALTO VERDE-URS\CRIA ALTO VERDE-URS.shp",
    "URS_ARCADIA":         r"CRIA ARCADIA-URS-2024\MAPA DELICTUAL CRIA ARCADIA-URS\MAPA DELICTUAL CRIA ARCADIA-URS.shp",
    "URS_ALPACHIRI":       r"CRIA ALPACHIRI-URS-2024\MAPA DELICTUAL CRIA ALPACHIRI URS\MAPA DELICTUAL CRIA ALPACHIRI URS.shp",
    "URS_MEDINAS":         r"CRIA MEDINAS -URS-2024\MAPA DELICTUAL CRIA MEDINAS URS\MAPA DELICTUAL CRIA MEDINAS URS.shp",
    "URS_LA_TRINIDAD":     r"CRIA LA TRINIDAD-URS\MAPA DELICTUAL CRIA LA TRINIDAD-URS\MAPA DELICTUAL CRIA LA TRINIDAD-URS.shp",
    "URS_AGUILARES":       r"CRIA AGUILARES-URS\MAPA DELICTUAL CRIA AGUILARES-URS\MAPA DELICTUAL CRIA AGUILARES-URS.shp",
    "URS_EL_POLEAR":       r"DESTACAMENTO EL POLEAR URS-2024\MAPA DELICTUAL DESTACAMENTO EL POLEAR -URS\MAPA DELICTUAL DESTACAMENTO EL POLEAR  URS.shp",
    "URS_SANTA_ANA":       r"CRIA SANTA ANA -URS-2024\MAPA DELICTUAL CRIA SANTA ANA URS\MAPA DELICTUAL CRIA SANTA ANA-URS.shp",
    "URS_LOS_SARMIENTOS":  r"CRIA LOS SARMIENTOS-URS\MAPA DELICTUAL CRIA LOS SARMIENTOS-URS\MAPA DELICTUAL CRIA LOS SARMIENTOS-URS.shp",
    "URS_STA_CRUZ_TUNA":   r"CRIA DE SANTA CRUZ Y LA TUNA-URS-2024\MAPA DELICTUAL CRIA DE SANTA CRUZ Y LA TUNA-URS\MAPA DELICTUAL CRIA DE SANTA CRUZ Y LA TUNA-URS.shp",
    "URS_MONTEAGUDO":      r"CRIA DE MONTEAGUDO-URS-2024\MAPA DELICTUAL CRIA DE MONTEAGUDO-URS\MAPA DELICTUAL CRIA DE MONTEAGUDO-URS.shp",
    "URS_CHICLIGASTA":     r"CRIA DE VILLA DE CHICLIGASTA-URS-2024\MAPA DELICTUAL CRIA DE VILLA DE CHICLIGASTA-URS\MAPA DELICTUAL CRIA DE VILLA DE CHICLIGASTA-URS.shp",
    "URS_GRANEROS":        r"CRIA GRANEROS-URS\MAPA DELICTUAL CRIA GRANEROS-URS\MAPA DELICTUAL CRIA GRANEROS-URS.shp",
    "URS_ATAHONA":         r"CRIA ATAHONA-URS-2024\MAPA DELICTUAL CRIA ATAHONA-URS\MAPA DELICTUAL CRIA ATAHONA-URS.shp",
    "URS_SIMOCA":          r"CRIA SIMOCA-URS\MAPA DELICTUAL CRIA SIMOCA-URS\MAPA DELICTUAL CRIA SIMOCA-URS.shp",
    "URS_TACO_RALO":       r"CRIA DE TACO RALO-URS-2024\MAPA DELICTUAL CRIA DE TACO RALO-URS\MAPA DELICTUAL CRIA DE TACO RALO-URS.shp",
    "URS_VILLA_BELGRANO":  r"CRIA DE VILLA BELGRANO-URS-2024\MAPA DELICTUAL CRIA DE VILLA BELGRANO-URS\MAPA DELICTUAL CRIA DE VILLA BELGRANO-URS.shp",
    "URS_LAMADRID":        r"CRIA DE LAMADRID-URS-2024\MAPA DELICTUAL CRIA DE LAMADRID-URS\MAPA DELICTUAL CRIA DE LAMADRID-URS.shp",
    "URS_ALBERDI":         r"CRIA ALBERDI-URS\MAPA DELICTUAL CRIA CRIA ALBERDI-URS\MAPA DELICTUAL CRIA ALBERDI-URS.shp",
    "URS_ESCABA":          r"CRIA ESCABA-URS\MAPA DELICTUAL CRIA ESCABA-URS\MAPA DELICTUAL CRIA ESCABA-URS.shp",
    "URS_LA_INVERNADA":    r"CRIA LA INVERNADA-URS-2024\MAPA DELICTUAL CRIA LA INVERNADA-URS\MAPA DELICTUAL CRIA LA INVERNADA-URS.shp",
    "URS_LA_COCHA":        r"CRIA LA COCHA-URS\MAPA DELICTUAL CRIA LA COCHA-URS\MAPA DELICTUAL CRIA LA COCHA-URS.shp",
    "URS_SAN_IGNACIO":     r"CRIA SAN IGNACIO-URS-2024\MAPA DELICTUAL CRIA SAN IGNACIO-URS\MAPA DELICTUAL CRIA SAN IGNACIO-URS.shp",
    "URS_RUMIPUNCO":       r"CRIA RUMIPUNCO-URS-2024\MAPA DELICTUAL CRIA RUMIPUNCO-URS\MAPA DELICTUAL CRIA RUMIPUNCO-URS.shp",
    "URS_ARBOLES_GRANDES": r"CRIA ARBOLES GRANDES-URS-2024\MAPA DELICTUAL CRIA ARBOLES GRANDES-URS\MAPA DELICTUAL CRIA ARBOLES GRANDES-URS.shp",
    "URS_HUASA_PAMPA":     r"CRIA DE HUASA PAMPA-URS-2024\MAPA DELICTUAL CRIA DE HUASA PAMPA-URS\MAPA DELICTUAL CRIA DE HUASA PAMPA-URS.shp",

    # --- URN (Unidad Regional Norte) ---
    "URN_TRANCAS":         r"CRIA TRANCAS -URN\MAPA DELICTUAL CRIA TRANCAS-URN\MAPA DELICTUAL CRIA TRANCAS-URN.shp",
    "URN_CHUSCHA":         r"CRIA CHUSCHA-URN-2024\MAPA DELICTUAL CRIA CHUSCHA\MAPA DELICTUAL CRIA DE CHUSCHA.shp",
    "URN_CHOROMORO":       r"CRIA CHOROMORO-URN-2024\MAPA DELICTUAL CRIA CHOROMORO\MAPA DELICTUAL CRIA DE CHOROMORO.shp",
    "URN_VIPOS":           r"CRIA VIPOS-URN\MAPA DELICTUAL CRIA VIPOS-URN\MAPA DELICTUAL CRIA VIPOS-URN.shp",
    "URN_TAPIA":           r"SUBCOMISARIA DE TAPIA-URN-2024\MAPA DELICTUAL SUBCOMISARIA DE TAPIA-URN\MAPA DELICTUAL SUBCOMISARIA DE TAPIA-URN.shp",
    "URN_SAN_PEDRO":       r"CRIA SAN PEDRO-URN\MAPA DELICTUAL CRIA SAN PEDRO-URN\MAPA DELICTUAL CRIA SAN PEDRO-URN.shp",
    "URN_YERBA_BUENA":     r"CRIA YERBA BUENA-URN\SHAPES_CRIA YERBA BUENA-URN\MAPA DELICTUAL CRIA YERBA BUENA-URN.shp",
    "URN_MARTI_COLL":      r"CRIA MARTI COLL-URN\SHAPES_CRIA MARTI COLL-URN\MAPA DELICTUAL CRIA MARTI COLL-URN.shp",
    "URN_SAN_JOSE":        r"CRIA SAN JOSE-URN\MAPA DELICTUAL CRIA SAN JOSE-URN-2020\MAPA DELICTUAL CRIA SAN JOSE-URN-2020.shp",
    "URN_EL_CORTE":        r"CRIA EL CORTE-URN\MAPA DELICTUAL CRIA EL CORTE-URN\MAPA DELICTUAL CRIA EL CORTE-URN.shp",
    "URN_SAN_JAVIER":      r"CRIA SAN JAVIER-URN\MAPA DELICTUAL CRIA SAN JAVIER-URN\MAPA DELICTUAL CRIA SAN JAVIER-URN.shp",
    "URN_VILLA_CARMELA":   r"CRIA VILLA CARMELA-URN-URC-2020\MAPA DELICTUAL CRIA VILLA CARMELA-URN-2020\MAPA DELICTUAL CRIA VILLA CARMELA.shp",
    "URN_RACO":            r"CRIA RACO-URN\MAPA DELICTUAL CRIA RACO-URN\MAPA DELICTUAL CRIA RACO-URN.shp",
    "URN_LOS_NOGALES":     r"CRIA LOS NOGALES-URN\MAPA DELICTUAL CRIA LOS NOGALES-URN\MAPA DELICTUAL CRIA LOS NOGALES-URN.shp",
    "URN_EL_CADILLAL":     r"CRIA EL CADILLAL-URN\MAPA DELICTUAL CRIA EL CADILLAL-URN\MAPA DELICTUAL CRIA EL CADILLAL-URN.shp",
    "URN_LAS_TALITAS":     r"CRIA LAS TALITAS-URN\MAPA DELICTUAL CRIA LAS TALITAS-URN\MAPA DELICTUAL CRIA LAS TALITAS-URN.shp",
    "URN_MARIANO_MORENO":  r"CRIA VILLA MARIANO MORENO-URN\MAPA DELICTUAL CRIA VILLA MARIANO MORENO-URN\MAPA DELICTUAL CRIA VILLA MARIANO MORENO-URN.shp",
    "URN_EL_COLMENAR":     r"CRIA EL COLMENAR-URN\MAPA DELICTUAL CRIA EL COLMENAR-URN\MAPA DELICTUAL CRIA VILLA EL COLMENAR URN.shp",
    "URN_LOS_POCITOS":     r"CRIA LOS POCITOS-URN\MAPA DELICTUAL CRIA LOS POCITOS-URN\MAPA DELICTUAL CRIA LOS POCITOS-URN.shp",
    "URN_LOMAS_TAFI":      r"CRIA LOMAS DE TAFI-URN\SHAPES_CRIA_LOMAS_DE_TAFI-URN\MAPA DELICTUAL CRIA LOMAS DE TAFI-URN.shp",
    "URN_VILLA_OBRERA":    r"CRIA VILLA OBRERA--URN\MAPA DELICTUAL CRIA VILLA OBRERA-URN\MAPA DELICTUAL CRIA VILLA OBRERA-URN.shp",
    "URN_TAFI_VIEJO_CENTRO": r"CRIA TAFI VIEJO CENTRO-URN\MAPA DELICTUAL CRIA TAFI VIEJO CENTRO-URN\MAPA DELICTUAL CRIA TAFI VIEJO CENTRO-URN.shp",
}

# Encodings a probar
ENCODINGS_TO_TRY = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']

# ============================================================================
# FUNCIONES
# ============================================================================

def print_header(text, char="="):
    """Imprime un encabezado formateado"""
    line = char * 70
    return f"\n{line}\n{text}\n{line}\n"


def try_read_shapefile(full_path):
    """Intenta leer un shapefile probando distintos encodings"""
    for enc in ENCODINGS_TO_TRY:
        try:
            gdf = gpd.read_file(full_path, encoding=enc)
            return gdf, enc
        except Exception:
            continue
    # Último intento sin especificar encoding
    try:
        gdf = gpd.read_file(full_path)
        return gdf, "default"
    except Exception as e:
        return None, str(e)


def explore_single_shapefile(name, full_path):
    """Explora un shapefile individual y retorna un dict con la info"""
    result = {
        "nombre": name,
        "ruta": full_path,
        "existe": False,
        "error": None,
        "encoding": None,
        "registros": 0,
        "crs": None,
        "columnas": [],
        "tipos_datos": {},
        "valores_unicos": {},
        "muestra": None,
    }

    # Verificar existencia
    if not os.path.exists(full_path):
        result["error"] = "ARCHIVO NO ENCONTRADO"
        # Verificar si la carpeta padre existe
        parent = os.path.dirname(full_path)
        if not os.path.exists(parent):
            result["error"] += f" (carpeta padre tampoco existe: {parent})"
        return result

    result["existe"] = True

    # Verificar archivos complementarios
    base = full_path.replace('.shp', '')
    for ext in ['.dbf', '.shx', '.prj']:
        if not os.path.exists(base + ext):
            result.setdefault("archivos_faltantes", []).append(ext)

    # Leer el shapefile
    gdf, enc = try_read_shapefile(full_path)

    if gdf is None:
        result["error"] = f"ERROR AL LEER: {enc}"
        return result

    result["encoding"] = enc
    result["registros"] = len(gdf)
    result["crs"] = str(gdf.crs) if gdf.crs else "SIN CRS"

    # Columnas (excluyendo geometry)
    cols = [c for c in gdf.columns if c != 'geometry']
    result["columnas"] = cols

    # Tipos de datos
    result["tipos_datos"] = {col: str(gdf[col].dtype) for col in cols}

    # Valores únicos (máx 30 por campo)
    for col in cols:
        try:
            unicos = gdf[col].dropna().unique()
            n_unicos = len(unicos)
            if n_unicos <= 30:
                result["valores_unicos"][col] = {
                    "total": n_unicos,
                    "valores": sorted([str(v) for v in unicos])
                }
            else:
                muestra = sorted([str(v) for v in unicos[:20]])
                result["valores_unicos"][col] = {
                    "total": n_unicos,
                    "valores": muestra,
                    "nota": f"(mostrando 20 de {n_unicos})"
                }
        except Exception:
            result["valores_unicos"][col] = {"total": 0, "valores": [], "error": "no se pudo leer"}

    # Muestra de datos (primeras 3 filas)
    try:
        result["muestra"] = gdf[cols].head(3).to_string()
    except Exception:
        result["muestra"] = "No se pudo obtener muestra"

    return result


def format_result(result):
    """Formatea el resultado de exploración para el reporte"""
    lines = []
    lines.append(f"\n{'─' * 70}")
    lines.append(f"📁 {result['nombre']}")
    lines.append(f"   Ruta: {result['ruta']}")

    if not result["existe"]:
        lines.append(f"   ❌ {result['error']}")
        return "\n".join(lines)

    if result["error"]:
        lines.append(f"   ❌ {result['error']}")
        return "\n".join(lines)

    lines.append(f"   ✅ Leído correctamente | Encoding: {result['encoding']}")
    lines.append(f"   📊 Registros: {result['registros']}")
    lines.append(f"   🌐 CRS: {result['crs']}")

    if result.get("archivos_faltantes"):
        lines.append(f"   ⚠️  Archivos faltantes: {result['archivos_faltantes']}")

    lines.append(f"   📋 Columnas ({len(result['columnas'])}):")
    for col in result["columnas"]:
        tipo = result["tipos_datos"].get(col, "?")
        uinfo = result["valores_unicos"].get(col, {})
        n_unicos = uinfo.get("total", "?")
        lines.append(f"      • {col} ({tipo}) - {n_unicos} valores únicos")

        valores = uinfo.get("valores", [])
        if valores and len(valores) <= 15:
            for v in valores:
                lines.append(f"          → {v}")
        elif valores:
            for v in valores[:10]:
                lines.append(f"          → {v}")
            nota = uinfo.get("nota", "")
            lines.append(f"          ... {nota}")

    lines.append(f"\n   📄 Muestra de datos (primeras 3 filas):")
    lines.append(f"   {result['muestra']}")

    return "\n".join(lines)


def compare_schemas(results):
    """Compara los esquemas de todos los shapefiles leídos exitosamente"""
    lines = []
    lines.append(print_header("COMPARACIÓN DE ESQUEMAS ENTRE SHAPEFILES"))

    # Agrupar por conjunto de columnas
    schema_groups = defaultdict(list)
    for r in results:
        if r["existe"] and not r["error"]:
            key = tuple(sorted(r["columnas"]))
            schema_groups[key].append(r["nombre"])

    lines.append(f"Se encontraron {len(schema_groups)} esquemas diferentes:\n")

    for i, (cols, names) in enumerate(schema_groups.items(), 1):
        lines.append(f"  ESQUEMA {i} ({len(names)} shapefiles):")
        lines.append(f"    Columnas: {list(cols)}")
        lines.append(f"    Shapefiles:")
        for n in names:
            lines.append(f"      - {n}")
        lines.append("")

    # Columnas comunes a todos
    if schema_groups:
        all_col_sets = [set(k) for k in schema_groups.keys()]
        common = set.intersection(*all_col_sets) if all_col_sets else set()
        all_cols = set.union(*all_col_sets) if all_col_sets else set()

        lines.append(f"\n  COLUMNAS COMUNES A TODOS: {sorted(common)}")
        lines.append(f"  COLUMNAS QUE SOLO EXISTEN EN ALGUNOS: {sorted(all_cols - common)}")

    return "\n".join(lines)


def summary_statistics(results):
    """Genera estadísticas resumen globales"""
    lines = []
    lines.append(print_header("RESUMEN ESTADÍSTICO GLOBAL"))

    total = len(results)
    existentes = sum(1 for r in results if r["existe"])
    leidos_ok = sum(1 for r in results if r["existe"] and not r["error"])
    total_registros = sum(r["registros"] for r in results if r["existe"] and not r["error"])

    lines.append(f"  Total shapefiles en registro: {total}")
    lines.append(f"  Archivos encontrados: {existentes}")
    lines.append(f"  Archivos NO encontrados: {total - existentes}")
    lines.append(f"  Leídos correctamente: {leidos_ok}")
    lines.append(f"  Errores de lectura: {existentes - leidos_ok}")
    lines.append(f"  Total de registros combinados: {total_registros}")

    # CRS encontrados
    crs_set = set(r["crs"] for r in results if r["crs"])
    lines.append(f"\n  Sistemas de coordenadas encontrados:")
    for crs in crs_set:
        count = sum(1 for r in results if r.get("crs") == crs)
        lines.append(f"    - {crs}: {count} shapefiles")

    # Archivos no encontrados
    not_found = [r for r in results if not r["existe"]]
    if not_found:
        lines.append(f"\n  ⚠️  ARCHIVOS NO ENCONTRADOS ({len(not_found)}):")
        for r in not_found:
            lines.append(f"    - {r['nombre']}: {r['ruta']}")

    # Valores únicos globales por campos comunes
    lines.append(f"\n  VALORES ÚNICOS GLOBALES (campos principales):")
    # Recopilar todos los valores por campo
    global_values = defaultdict(set)
    for r in results:
        if r["existe"] and not r["error"]:
            for col, info in r["valores_unicos"].items():
                for v in info.get("valores", []):
                    global_values[col].add(v)

    for col in sorted(global_values.keys()):
        vals = sorted(global_values[col])
        lines.append(f"\n    {col} ({len(vals)} valores únicos globales):")
        for v in vals[:50]:
            lines.append(f"      → {v}")
        if len(vals) > 50:
            lines.append(f"      ... y {len(vals) - 50} más")

    return "\n".join(lines)


# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reporte_exploracion.txt")
    json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reporte_exploracion.json")

    print(print_header(f"EXPLORACIÓN DE SHAPEFILES - MAPA DELICTUAL\nFecha: {timestamp}"))

    # Verificar acceso a ruta base
    print(f"Verificando acceso a: {BASE_PATH}")
    if not os.path.exists(BASE_PATH):
        print(f"❌ ERROR: No se puede acceder a {BASE_PATH}")
        print("   Verifique que la unidad Z:\\ esté mapeada y accesible.")
        print("   Si la ruta es diferente, modifique BASE_PATH en el script.")

        # Intentar listar la unidad Z:
        if os.path.exists("Z:\\"):
            print("\n   La unidad Z:\\ existe. Contenido:")
            try:
                for item in os.listdir("Z:\\"):
                    print(f"     - {item}")
            except Exception as e:
                print(f"     Error al listar: {e}")
        else:
            print("   La unidad Z:\\ NO está disponible.")
        return

    print(f"✅ Ruta base accesible")
    print(f"   Explorando {len(SHAPEFILES)} shapefiles...\n")

    # Explorar cada shapefile
    results = []
    report_lines = []
    report_lines.append(print_header(f"REPORTE DE EXPLORACIÓN DE SHAPEFILES\nMapa Delictual - Provincia de Tucumán\nFecha: {timestamp}"))

    for i, (name, rel_path) in enumerate(SHAPEFILES.items(), 1):
        full_path = os.path.join(BASE_PATH, rel_path)
        print(f"  [{i}/{len(SHAPEFILES)}] Explorando: {name}...", end=" ")

        result = explore_single_shapefile(name, full_path)
        results.append(result)

        if result["existe"] and not result["error"]:
            print(f"✅ ({result['registros']} registros)")
        elif not result["existe"]:
            print(f"❌ No encontrado")
        else:
            print(f"⚠️ Error: {result['error']}")

        report_lines.append(format_result(result))

    # Comparar esquemas
    report_lines.append(compare_schemas(results))

    # Resumen estadístico
    report_lines.append(summary_statistics(results))

    # Guardar reporte TXT
    full_report = "\n".join(report_lines)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_report)
    print(f"\n✅ Reporte guardado en: {output_file}")

    # Guardar datos en JSON (para uso posterior)
    json_data = []
    for r in results:
        # Convertir a formato serializable
        json_r = {k: v for k, v in r.items() if k != "muestra"}
        json_data.append(json_r)

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Datos JSON guardados en: {json_file}")

    # Mostrar resumen en consola
    print(summary_statistics(results))


if __name__ == "__main__":
    main()
