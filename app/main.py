"""
Aplicación principal Streamlit - Informes del Mapa Delictual
Punto de entrada: streamlit run app/main.py
"""
import streamlit as st
import sys
import os

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de página (DEBE ser la primera llamada de Streamlit)
st.set_page_config(
    page_title="Mapa Delictual - Informes",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inyectar CSS personalizado
st.markdown("""
<style>
    /* Estilo general */
    .main .block-container { padding-top: 1rem; max-width: 1400px; }
    
    /* Cards métricas */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #666 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #1E3A5F !important;
    }
    
    /* Encabezados */
    h1 { color: #CC0000 !important; }
    h2 { color: #1E3A5F !important; border-bottom: 2px solid #CC0000; padding-bottom: 0.3rem; }
    h3 { color: #2563EB !important; }
    
    /* Tabla personalizada */
    .styled-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .styled-table thead tr { background-color: #CC0000; color: white; }
    .styled-table th, .styled-table td { padding: 8px 12px; text-align: center; }
    .styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
    .styled-table .total-row { background-color: #FFFF00 !important; font-weight: bold; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1E3A5F; }
    [data-testid="stSidebar"] .stMarkdown { color: white; }
    
    /* Ocultar footer */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


from app.src.ui.pages import home, delitos, temporal, caracteristicas, geografico, comparativo


# ====================================================================
# Sidebar – Navegación y filtros
# ====================================================================

def render_sidebar():
    """Renderiza el menú lateral de navegación y filtros globales."""
    with st.sidebar:
        st.image(
            "https://img.icons8.com/fluency/96/detective.png",
            width=64,
        )
        st.title("Mapa Delictual")
        st.caption("Sistema de Informes Estadísticos")
        st.divider()

        # Navegación
        pagina = st.radio(
            "📊 Navegación",
            [
                "🏠 Inicio",
                "📋 Delitos por Modalidad",
                "📅 Análisis Temporal",
                "🔍 Características",
                "🗺️ Análisis Geográfico",
                "📈 Comparativo",
            ],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("v1.0 — Policía de Tucumán")

        return pagina


# ====================================================================
# Router de páginas
# ====================================================================

def main():
    pagina = render_sidebar()

    if "🏠 Inicio" in pagina:
        home.render()
    elif "Delitos por Modalidad" in pagina:
        delitos.render()
    elif "Análisis Temporal" in pagina:
        temporal.render()
    elif "Características" in pagina:
        caracteristicas.render()
    elif "Análisis Geográfico" in pagina:
        geografico.render()
    elif "Comparativo" in pagina:
        comparativo.render()


if __name__ == "__main__":
    main()
