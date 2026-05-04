import os
import json
import logging
from typing import Dict, Any, List

# Intentar importar google-generativeai. Si no está, se manejará el error en la UI.
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    
    # Cargar variables de entorno desde la ruta absoluta del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    env_path = os.path.join(base_dir, '.env')
    load_dotenv(env_path)
    
    # Configurar API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        
    GEMINI_AVAILABLE = True
    IMPORT_ERROR_MSG = ""
except ImportError as e:
    GEMINI_AVAILABLE = False
    IMPORT_ERROR_MSG = str(e)
    logging.warning(f"Faltan dependencias: {e}")

class GeminiAssistant:
    def __init__(self, model_name: str = 'gemini-1.5-pro'):
        self.model_name = model_name
        self.is_available = GEMINI_AVAILABLE and bool(os.getenv("GEMINI_API_KEY"))
        
        if self.is_available:
            try:
                # Usar el modelo especificado
                self.model = genai.GenerativeModel(model_name)
            except Exception as e:
                logging.error(f"Error al inicializar el modelo Gemini: {e}")
                self.is_available = False

    def is_ready(self) -> bool:
        """Verifica si el asistente está listo para usarse (librerías instaladas y API Key configurada)"""
        return self.is_available

    def generate_shapefile_analysis(self, shape_name: str, records_summary: str, extra_context: str = "") -> str:
        """
        Genera un análisis geoespacial básico a partir del resumen de los datos del Shapefile.
        """
        if not self.is_ready():
            return "El asistente IA no está disponible. Verifique que la API Key esté configurada y las dependencias instaladas."

        prompt = f"""
Actúa como un analista criminal táctico y experto en SIG (Sistemas de Información Geográfica).
He procesado un archivo Shapefile (.shp) de la provincia de Tucumán que contiene información delictual.

Nombre de la Jurisdicción/Shapefile: {shape_name}

Resumen de los datos extraídos (Atributos):
{records_summary}

Contexto Adicional:
{extra_context}

Por favor, proporciona un análisis estructurado de estos datos. Identifica:
1. Las modalidades de delitos predominantes.
2. Franjas horarias o días más críticos (si están en los datos).
3. Recomendaciones preliminares basadas en esta muestra.
Mantén un tono profesional, institucional y analítico.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error al generar contenido con Gemini: {e}")
            return f"Error al generar el análisis: {str(e)}"
