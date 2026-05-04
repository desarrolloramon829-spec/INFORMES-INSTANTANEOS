import streamlit as st
import pandas as pd
from app.src.ai.gemini_assistant import GeminiAssistant
from app.src.data.shapefile_reader import ShapefileReader

def render():
    st.markdown("""
        <div class='editorial-hero'>
            <div class='editorial-kicker'>Inteligencia Artificial</div>
            <h1>Asistente Táctico Gemini</h1>
            <p class='editorial-lead'>Análisis automatizado de datos espaciales y reportes criminales utilizando Google Gemini Pro.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='scene-seq seq-1'>", unsafe_allow_html=True)
    
    # Inicializar componentes
    assistant = GeminiAssistant()
    reader = ShapefileReader()
    
    if not assistant.is_ready():
        import os
        from app.src.ai.gemini_assistant import GEMINI_AVAILABLE, IMPORT_ERROR_MSG
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not GEMINI_AVAILABLE:
            st.warning(f"⚠️ **Faltan Dependencias**: No se detectaron las librerías necesarias. Por favor, aprueba el comando de instalación que el asistente de IA ejecutará en tu terminal. (Error: {IMPORT_ERROR_MSG})")
        elif not api_key:
            st.warning("⚠️ **API Key no encontrada**: No se detectó la clave de API (GEMINI_API_KEY) en el archivo `.env` o en las variables de entorno.")
        else:
            st.warning("⚠️ **Asistente IA No Disponible**: Error desconocido de inicialización.")
        return
        
    st.success("✅ Conectado exitosamente a Google Gemini Pro.")
    
    st.markdown("### Análisis de Shapefiles")
    st.write("Seleccione un archivo Shapefile para que la IA extraiga los datos subyacentes (DBF) y genere un reporte estratégico preliminar.")
    
    shapes_list = reader.get_shapefile_list()
    
    if not shapes_list:
        st.info("No se encontraron rutas de Shapefiles en `rutas_shpbac.txt`. Usando ejemplos de demostración.")
        shapes_list = ["Z:/EJEMPLO/MAPA_DELICTUAL_CRIA_1.shp", "Z:/EJEMPLO/MAPA_DELICTUAL_CRIA_2.shp"]
        
    selected_shape = st.selectbox("Seleccionar Shapefile", options=shapes_list)
    
    contexto_adicional = st.text_area("Contexto adicional para la IA (opcional)", 
                                    placeholder="Ej: Ten en cuenta que esta jurisdicción tuvo un aumento de patrullajes la semana pasada.",
                                    height=100)
    
    if st.button("Generar Análisis Estratégico", type="primary"):
        with st.spinner("Procesando archivo DBF y consultando a Gemini Pro..."):
            # Si es un ejemplo de demostración, simulamos la lectura
            if "EJEMPLO" in selected_shape:
                success = True
                summary = "Total de registros: 120\nColumnas: DELITO, FECHA, HORA, JURISDICCION\nTop 5 DELITO:\n- ROBO_AGRAVADO: 45\n- HURTO_OPORTUNISTA: 30"
                df = pd.DataFrame()
            else:
                success, summary, df = reader.extract_summary_from_shapefile(selected_shape)
                
            if success:
                st.markdown("#### Datos Extraídos")
                with st.expander("Ver resumen de datos enviado a la IA"):
                    st.text(summary)
                    if not df.empty:
                        st.dataframe(df.head(10))
                        
                st.markdown("#### Análisis de la IA")
                # Llamar a Gemini
                respuesta = assistant.generate_shapefile_analysis(selected_shape, summary, contexto_adicional)
                
                st.markdown(f"<div class='scene-stage analysis-stage'>{respuesta}</div>", unsafe_allow_html=True)
            else:
                st.error(f"No se pudieron leer los datos del shapefile: {summary}")
                
    st.markdown("</div>", unsafe_allow_html=True)
