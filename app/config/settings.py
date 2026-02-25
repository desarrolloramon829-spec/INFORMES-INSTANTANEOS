"""
Configuración general de la aplicación Mapa Delictual.
"""
import os

# ============================================================
# RUTAS
# ============================================================
BASE_SHAPEFILE_PATH = r"Z:\MAPA DEL DELITO\MAPAS DEL DELITO POR JURISDICCIONES"

# ============================================================
# MAPEO DE COLUMNAS: nombre dBASE (10 chars) → nombre legible
# ============================================================
COLUMN_MAP = {
    "ID_N_SRIO": "id_sumario",
    "JURIS_HECH": "jurisdiccion",
    "DPCIA_INT": "dependencia_interviniente",
    "DPCIA_CARG": "dependencia_carga",
    "FECHA_HECH": "fecha_hecho",
    "DIA_HECHO": "dia_semana",
    "HORA_HECH": "hora_hecho",
    "FRAN_HORAR": "franja_horaria",
    "PRDA_URBAN": "perdida_urbana",
    "DIREC_HECH": "direccion_hecho",
    "LUGR_HECHO": "ambito",
    "DET_LUG_HE": "detalle_lugar",
    "DELITO": "delito",
    "MODUS_OPER": "modus_operandi",
    "VEHIC_UTIL": "movilidad",
    "DET_VEHIC": "detalle_vehiculo",
    "ARMA_UTILI": "arma",
    "DET_ARMA": "detalle_arma",
    "ELEMN_SUST": "elementos_sustraidos",
    "DET_ELE_SU": "detalle_elementos",
    "RESEN_HECH": "resena_hecho",
    "SEXO_VICTI": "sexo_victima",
    "EDAD_VICTI": "edad_victima",
    "AP_NOM_VIC": "nombre_victima",
    "DNI_VICTIM": "dni_victima",
    "DIREC_VICT": "direccion_victima",
    "VIN_DE_VIC": "vinculo_victima",
    "AP_NOM_DEN": "nombre_denunciante",
    "DNI_DENUNC": "dni_denunciante",
    "SEXO_DENUN": "sexo_denunciante",
    "EDAD_DENUN": "edad_denunciante",
    "DIREC_DENU": "direccion_denunciante",
    "AP_NOM_CAU": "nombre_causante",
    "SEXO_CAUS": "sexo_causante",
    "EDAD_CAUSA": "edad_causante",
    "DNI_CAUSAN": "dni_causante",
    "DIREC_CAUS": "direccion_causante",
    "DESC_CAUS": "descripcion_causante",
    "HECH_RESUE": "hecho_resuelto",
    "MES_DENU": "mes",
    "SITUA_CAUS": "situacion_causante",
    "ELEM_SECU": "elementos_secuestrados",
    "DET_EL_SE1": "detalle_secuestro_1",
    "DET_EL_SE2": "detalle_secuestro_2",
    "DET_EL_SE3": "detalle_secuestro_3",
    "X": "longitud",
    "Y": "latitud",
}

# ============================================================
# CAMPOS CLAVE PARA REPORTES (nombres originales del shapefile)
# ============================================================
CAMPO_DELITO = "DELITO"
CAMPO_FECHA = "FECHA_HECH"
CAMPO_HORA = "HORA_HECH"
CAMPO_FRANJA = "FRAN_HORAR"
CAMPO_DIA = "DIA_HECHO"
CAMPO_MES = "MES_DENU"
CAMPO_MOVILIDAD = "VEHIC_UTIL"
CAMPO_ARMA = "ARMA_UTILI"
CAMPO_AMBITO = "LUGR_HECHO"
CAMPO_JURISDICCION = "JURIS_HECH"
CAMPO_MODUS = "MODUS_OPER"
CAMPO_HECHO_RESUELTO = "HECH_RESUE"
CAMPO_X = "X"
CAMPO_Y = "Y"

# ============================================================
# FRANJAS HORARIAS VÁLIDAS
# ============================================================
FRANJAS_HORARIAS = [
    "MADRUGADA_(00:00-04:59)",
    "MANANA_(05:00-08:59)",
    "VESPERTINA_(09:00-12:59)",
    "SIESTA_(13:00-16:59)",
    "TARDE_(17:00-19:59)",
    "NOCHE_(20:00-23:59)",
]

FRANJAS_LABELS = {
    "MADRUGADA_(00:00-04:59)": "Madrugada\n00:00 - 04:59",
    "MANANA_(05:00-08:59)": "Mañana\n05:00 - 08:59",
    "VESPERTINA_(09:00-12:59)": "Vespertina\n09:00 - 12:59",
    "SIESTA_(13:00-16:59)": "Siesta\n13:00 - 16:59",
    "TARDE_(17:00-19:59)": "Tarde\n17:00 - 19:59",
    "NOCHE_(20:00-23:59)": "Noche\n20:00 - 23:59",
}

# ============================================================
# DÍAS DE LA SEMANA (orden correcto)
# ============================================================
DIAS_SEMANA = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
DIAS_LABELS = {
    "lunes": "Lunes",
    "martes": "Martes",
    "miercoles": "Miércoles",
    "jueves": "Jueves",
    "viernes": "Viernes",
    "sabado": "Sábado",
    "domingo": "Domingo",
}

# ============================================================
# MESES (orden correcto)
# ============================================================
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MESES_LABELS = {
    "enero": "Enero", "febrero": "Febrero", "marzo": "Marzo",
    "abril": "Abril", "mayo": "Mayo", "junio": "Junio",
    "julio": "Julio", "agosto": "Agosto", "septiembre": "Septiembre",
    "octubre": "Octubre", "noviembre": "Noviembre", "diciembre": "Diciembre",
}

# ============================================================
# UNIDADES REGIONALES
# ============================================================
UNIDADES_REGIONALES = {
    "URC": "Unidad Regional Capital",
    "URN": "Unidad Regional Norte",
    "URO": "Unidad Regional Oeste",
    "URE": "Unidad Regional Este",
    "URS": "Unidad Regional Sur",
    "ESPECIAL": "Shapes Especiales",
}

# ============================================================
# CATEGORÍAS DE DELITO (simplificadas desde códigos)
# ============================================================
DELITO_CATEGORIAS = {
    "010-ROBO": "Robo",
    "020-TENTATIVAS_DE_ROBO": "Tent. de Robo",
    "030-ROBO_AGRAVADO": "Robo Agravado",
    "040-TENTATIVA_DE_ROBO_AGRAVADO": "Tent. Robo Agrav.",
    "050-HURTO": "Hurto",
    "060-TENTATIVA_DE_HURTO": "Tent. de Hurto",
    "070-189_bis": "Art. 189 bis",
    "120-HALLAZGO": "Hallazgo",
    "160-ESTAFA": "Estafa",
    "170-TENTATIVA_DE_ESTAFA": "Tent. de Estafa",
    "ROBO": "Robo",
    "HURTO": "Hurto",
    "ESTAFA": "Estafa",
    "#NO_CONSTA": "No Consta",
    "NO CONSTA": "No Consta",
}

# ============================================================
# VALORES A EXCLUIR/LIMPIAR
# ============================================================
VALORES_BASURA = {"zzz", "", "None", "NULL", "null"}

# ============================================================
# COLORES ESTILO POWER BI
# ============================================================
COLORES = {
    "primary": "#2563EB",
    "secondary": "#DC2626",
    "accent": "#F59E0B",
    "success": "#16A34A",
    "purple": "#7C3AED",
    "orange": "#EA580C",
    "cyan": "#0891B2",
    "dark_blue": "#1E3A5F",
    "light_gray": "#F5F5F5",
    "header_red": "#CC0000",
    "header_blue": "#0000FF",
    "total_yellow": "#FFFF00",
    "bar_blue": "#4472C4",
    "bar_red": "#ED7D31",
    "bar_green": "#70AD47",
    "bar_purple": "#9B59B6",
}

CHART_PALETTE = [
    "#4472C4", "#ED7D31", "#A5A5A5", "#FFC000", "#5B9BD5",
    "#70AD47", "#264478", "#9B59B6", "#FF6384", "#36A2EB",
    "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#C9CBCF",
]

# ============================================================
# COMISARÍAS POR UNIDAD REGIONAL (nombres exactos para filtros)
# ============================================================
COMISARIAS_POR_REGION: dict[str, list[str]] = {
    "URC": [
        "Comisaria 1a", "Comisaria 2a", "Comisaria 3a", "Comisaria 4a",
        "Comisaria 5a", "Comisaria 6a", "Comisaria 7a", "Comisaria 8a",
        "Comisaria 9a", "Comisaria 10a", "Comisaria 11a", "Comisaria 12a",
        "Comisaria 13a", "Comisaria 14a", "Comisaria 15a",
    ],
    "URE": [
        "Cria. Burruyacu", "Cria. El Cajon", "Cria. Villa B. Araoz",
        "Cria. El Puestito", "Cria. Chilcas", "Cria. 7 de Abril",
        "Cria. El Chañar", "Cria. La Ramada", "Cria. Garmendia",
        "Cria. El Timbo", "Cria. El Naranjo", "Cria. Piedrabuena",
        "Cria. Villa P. Monti", "Cria. Banda del Rio Sali",
        "Cria. Lastenia", "Cria. Guemes", "Cria. Alderetes",
        "Cria. Pozo del Alto", "Cria. Ranchillos", "Cria. Los Ralos",
        "Cria. Delfin Gallo", "Cria. Colombres", "Cria. La Florida",
        "Cria. San Andres", "Cria. El Bracho", "Cria. Las Cejas",
        "Cria. Los Bulacios", "Cria. Bella Vista", "Cria. Romera Pozo",
        "Cria. Santa Rosa de Leales", "Cria. Quilmes",
        "Cria. Ingenio Leales", "Cria. Los Sueldos",
        "Cria. Estacion Araoz", "Cria. Villa de Leales",
        "Cria. Rio Colorado", "Cria. Esquina", "Cria. Mancopa",
        "Cria. Agua Dulce", "Cria. Los Gomez", "Cria. Los Puestos",
        "Cria. Los Herrera", "Cria. El Mojon", "Cria. Campo El Quimil",
    ],
    "URO": [
        "Cria. Tafi del Valle", "Cria. El Mollar",
        "Cria. Amaicha del Valle", "Cria. Colalao del Valle",
        "Cria. Lules", "Cria. La Reducción", "Cria. El Manantial",
        "Cria. San Pablo", "Cria. V. Nougues", "Cria. Los Aguirre",
        "Cria. Famailla", "Cria. Tte. Berdina", "Cria. Monteros",
        "Cria. Santa Lucía", "Cria. Acheral", "Cria. Río Seco",
        "Cria. Villa Quinteros", "Cria. León Rouges",
        "Cria. Capitán Cáceres",
        "Cria. Los Sosa y Soldado Maldonado",
        "Cria. Amberes", "Cria. Sargento Moya",
    ],
    "URS": [
        "Cria. de Concepción", "Sub. Cria. Alto Verde",
        "Cria. Arcadia", "Cria. Alpachiri", "Cria. Medinas",
        "Cria. La Trinidad", "Cria. Aguilares", "Sub. Cria. El Polear",
        "Cria. Sta. Ana", "Cria. Los Sarmientos", "Cria. Sta. Cruz",
        "Cria. Monteagudo", "Cria. Villa Chicligasta",
        "Cria. Graneros", "Cria. Atahona", "Cria. Simoca",
        "Cria. Manuela Pedraza", "Cria. Taco Ralo",
        "Cria. Villa Belgrano", "Cria. Lamadrid",
        "Cria. J. B. Alberdi", "Cria. Escaba", "Cria. La Invernada",
        "Cria. Los Juarez", "Cria. Juan Posse", "Cria. Rio Chico",
        "Cria. Pampa Mayo",
    ],
    "URN": [
        "Cria. de Trancas", "Cria. Chuscha", "Cria. Choromoro",
        "Cria. Vipos", "Sub Cria. de Tapia",
        "Cria. San Pedro de Colalao", "Cria. Yerba Buena",
        "Cria. Marti Coll", "Cria. San José", "Cria. El Corte",
        "Cria. San Javier", "Cria. Villa Carmela", "Cria. Raco",
        "Cria. Los Nogales", "Cria. El Cadillal", "Cria. Las Talitas",
        "Cria. V. Mariano Moreno", "Cria. El Colmenar",
        "Cria. Los Pocitos", "Cria. Lomas de Tafi",
        "Cria. Villa Obrera", "Cria. Tafi Viejo",
    ],
}
