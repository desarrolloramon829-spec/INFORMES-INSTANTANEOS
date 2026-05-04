import os
import dbfread
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple

class ShapefileReader:
    def __init__(self, routes_file_path: str = None):
        if not routes_file_path:
            # Default to the known location if not provided
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            routes_file_path = os.path.join(base_dir, "rutas", "rutas_shpbac.txt")
        self.routes_file_path = routes_file_path
        self.available_shapes = self._load_routes()

    def _load_routes(self) -> List[str]:
        """Lee el archivo de texto y extrae las rutas de los shapefiles."""
        routes = []
        if os.path.exists(self.routes_file_path):
            with open(self.routes_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and line.endswith('.shp'):
                        routes.append(line)
        return routes

    def get_shapefile_list(self) -> List[str]:
        """Devuelve la lista de rutas disponibles."""
        return self.available_shapes
        
    def extract_summary_from_shapefile(self, shp_path: str, max_records: int = 50) -> Tuple[bool, str, pd.DataFrame]:
        """
        Intenta leer el archivo .dbf asociado al shapefile para extraer los datos tabulares.
        Retorna: (éxito, mensaje/resumen_texto, dataframe_datos)
        """
        # Convertimos la extensión a .dbf
        dbf_path = shp_path[:-4] + '.dbf'
        
        # Opcional: reemplazar slashes para el sistema operativo actual
        dbf_path = dbf_path.replace('/', os.sep).replace('\\', os.sep)
        
        if not os.path.exists(dbf_path):
            return False, f"Archivo DBF no encontrado en la ruta: {dbf_path}. Asegúrese de tener acceso a la unidad de red.", pd.DataFrame()
            
        try:
            # Leer usando dbfread para evitar dependencias pesadas si geopandas falla,
            # y porque solo necesitamos los atributos para que Gemini los analice.
            table = dbfread.DBF(dbf_path, encoding='latin1', load=True)
            records = list(table)
            
            if not records:
                return True, "El shapefile no contiene registros de atributos.", pd.DataFrame()
                
            df = pd.DataFrame(records)
            
            # Generar un resumen de los datos para enviarlo a Gemini
            total_records = len(df)
            columns = ", ".join(df.columns.tolist())
            
            # Tomar una muestra representativa (por ejemplo, contar valores frecuentes de la primera columna categórica)
            summary_text = f"Total de registros: {total_records}\n"
            summary_text += f"Columnas disponibles: {columns}\n\n"
            
            # Intentar encontrar columnas clave comunes en delitos
            for col in df.columns:
                if 'DELITO' in col.upper() or 'MODALIDAD' in col.upper() or 'HECHO' in col.upper():
                    top_delitos = df[col].value_counts().head(5).to_dict()
                    summary_text += f"Top 5 {col}:\n"
                    for k, v in top_delitos.items():
                        summary_text += f"  - {k}: {v}\n"
                    summary_text += "\n"
                    
            # Si hay demasiados registros, tomar una muestra para no exceder los límites de tokens de Gemini
            sample_df = df.head(max_records)
            summary_text += f"Muestra de los primeros {min(max_records, total_records)} registros:\n"
            
            # Convertir muestra a dict o string
            summary_text += sample_df.to_string(index=False)
            
            return True, summary_text, df
            
        except Exception as e:
            logging.error(f"Error al leer DBF {dbf_path}: {e}")
            return False, f"Error al leer el archivo de atributos: {str(e)}", pd.DataFrame()
