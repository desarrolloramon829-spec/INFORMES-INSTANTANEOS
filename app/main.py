"""
Aplicación principal Streamlit - Informes del Mapa Delictual
Punto de entrada: streamlit run app/main.py
"""
import streamlit as st
import sys
import os

from app.config.settings import TYPOGRAPHY, VISUAL_THEMES

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de página (DEBE ser la primera llamada de Streamlit)
st.set_page_config(
    page_title="Mapa Delictual - Informes",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


from app.src.ui.pages import home, delitos, temporal, caracteristicas, geografico, comparativo, robos_hurtos
from app.src.ui.shared import render_boton_regenerar


def inject_visual_system(theme_key: str):
    """Inyecta el sistema visual base según el tema seleccionado."""
    theme = VISUAL_THEMES.get(theme_key, VISUAL_THEMES["oscuro"])

    st.markdown(
        f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:wght@600;700&display=swap');

    :root {{
        --app-page-bg: {theme['page_bg']};
        --app-page-gradient: {theme['page_gradient']};
        --app-surface: {theme['surface']};
        --app-surface-alt: {theme['surface_alt']};
        --app-sidebar: {theme['surface_sidebar']};
        --app-border: {theme['border']};
        --app-text: {theme['text']};
        --app-text-muted: {theme['text_muted']};
        --app-heading: {theme['heading']};
        --app-accent: {theme['accent']};
        --app-accent-soft: {theme['accent_soft']};
        --app-primary: {theme['primary']};
        --app-primary-soft: {theme['primary_soft']};
        --app-success: {theme['success']};
        --app-warning: {theme['warning']};
        --app-metric-bg: {theme['metric_bg']};
        --app-shadow: {theme['shadow']};
        --font-ui: {TYPOGRAPHY['ui']};
        --font-editorial: {TYPOGRAPHY['editorial']};
    }}

    html, body, [class*="css"] {{
        font-family: var(--font-ui);
    }}

    body, [data-testid="stAppViewContainer"] {{
        background: var(--app-page-gradient);
        color: var(--app-text);
    }}

    [data-testid="stAppViewContainer"] > .main {{
        background: transparent;
    }}

    .main .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2.4rem;
        max-width: 1440px;
    }}

    .main .block-container > div {{
        animation: fadeUp 0.45s ease-out;
    }}

    .main .block-container [data-testid="column"]:nth-of-type(1) > div,
    .main .block-container [data-testid="column"]:nth-of-type(1) [data-testid="stPlotlyChart"],
    .main .block-container [data-testid="column"]:nth-of-type(1) [data-testid="stDataFrame"] {{
        animation-delay: 0.04s;
    }}

    .main .block-container [data-testid="column"]:nth-of-type(2) > div,
    .main .block-container [data-testid="column"]:nth-of-type(2) [data-testid="stPlotlyChart"],
    .main .block-container [data-testid="column"]:nth-of-type(2) [data-testid="stDataFrame"] {{
        animation-delay: 0.1s;
    }}

    .main .block-container [data-testid="column"]:nth-of-type(3) > div,
    .main .block-container [data-testid="column"]:nth-of-type(3) [data-testid="stPlotlyChart"],
    .main .block-container [data-testid="column"]:nth-of-type(3) [data-testid="stDataFrame"] {{
        animation-delay: 0.16s;
    }}

    .main .block-container [data-testid="column"]:nth-of-type(4) > div,
    .main .block-container [data-testid="column"]:nth-of-type(4) [data-testid="stPlotlyChart"],
    .main .block-container [data-testid="column"]:nth-of-type(4) [data-testid="stDataFrame"] {{
        animation-delay: 0.22s;
    }}

    @keyframes fadeUp {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes cardFloatIn {{
        from {{ opacity: 0; transform: translateY(12px) scale(0.985); }}
        to {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}

    @keyframes chartGlowIn {{
        from {{ opacity: 0; transform: translateY(10px); filter: saturate(0.92); }}
        to {{ opacity: 1; transform: translateY(0); filter: saturate(1); }}
    }}

    h1, h2, h3 {{
        letter-spacing: -0.02em;
    }}

    h1 {{
        font-family: var(--font-editorial) !important;
        color: var(--app-heading) !important;
        font-size: 2.1rem !important;
        margin-bottom: 0.25rem !important;
    }}

    h2 {{
        font-family: var(--font-editorial) !important;
        color: var(--app-heading) !important;
        border-bottom: 1px solid var(--app-border);
        padding-bottom: 0.4rem;
        margin-top: 1.2rem !important;
    }}

    h3 {{
        color: var(--app-primary) !important;
        font-weight: 700 !important;
    }}

    p, li, label, [data-testid="stMarkdownContainer"] {{
        color: var(--app-text);
    }}

    .stCaption, [data-testid="stCaptionContainer"], small {{
        color: var(--app-text-muted) !important;
    }}

    [data-testid="stMetric"] {{
        background: var(--app-metric-bg);
        border: 1px solid var(--app-border);
        border-radius: 18px;
        padding: 0.95rem 1rem;
        box-shadow: var(--app-shadow);
        backdrop-filter: blur(8px);
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        animation: cardFloatIn 0.42s ease both;
    }}

    [data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        border-color: rgba(79, 140, 255, 0.3);
        box-shadow: 0 18px 34px rgba(8, 15, 30, 0.22);
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--app-text-muted) !important;
        font-size: 0.82rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600 !important;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--app-heading) !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
    }}

    [data-testid="stMetricDelta"] {{
        font-weight: 600;
    }}

    .stAlert {{
        border-radius: 16px !important;
        border: 1px solid var(--app-border) !important;
        box-shadow: var(--app-shadow);
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: transparent;
        border-bottom: 1px solid var(--app-border);
        padding-bottom: 0.35rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        background: var(--app-surface-alt);
        border: 1px solid var(--app-border);
        border-radius: 999px;
        color: var(--app-text-muted);
        padding: 0.4rem 0.95rem;
        font-weight: 600;
        transition: transform 0.16s ease, background 0.16s ease, border-color 0.16s ease;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        transform: translateY(-1px);
        border-color: rgba(79, 140, 255, 0.28);
    }}

    .stTabs [aria-selected="true"] {{
        background: var(--app-primary-soft) !important;
        color: var(--app-heading) !important;
        border-color: rgba(79, 140, 255, 0.35) !important;
    }}

    .stButton > button, .stDownloadButton > button {{
        border-radius: 999px;
        border: 1px solid var(--app-border);
        background: linear-gradient(180deg, var(--app-surface-alt) 0%, var(--app-surface) 100%);
        color: var(--app-heading);
        font-weight: 600;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        box-shadow: var(--app-shadow);
    }}

    .stButton > button:hover, .stDownloadButton > button:hover {{
        transform: translateY(-1px);
        border-color: rgba(79, 140, 255, 0.35);
    }}

    [data-testid="stSidebar"] {{
        background: var(--app-sidebar);
        border-right: 1px solid var(--app-border);
    }}

    [data-testid="stSidebar"] .block-container {{
        padding-top: 1.15rem;
    }}

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stCaption {{
        color: var(--app-text) !important;
    }}

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    .stDateInput > div > div,
    .stMultiSelect > div > div {{
        background: var(--app-surface-alt) !important;
        border: 1px solid var(--app-border) !important;
        border-radius: 14px !important;
        color: var(--app-text) !important;
    }}

    .stRadio [role="radiogroup"] label,
    .stCheckbox label {{
        color: var(--app-text) !important;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid var(--app-border);
        border-radius: 18px;
        overflow: hidden;
        box-shadow: var(--app-shadow);
        animation: chartGlowIn 0.5s ease both;
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        background: linear-gradient(180deg, var(--app-surface-alt) 0%, var(--app-surface) 100%);
    }}

    [data-testid="stDataFrame"]:hover {{
        transform: translateY(-2px);
        border-color: rgba(79, 140, 255, 0.3);
        box-shadow: 0 22px 44px rgba(8, 15, 30, 0.22);
    }}

    [data-testid="stPlotlyChart"] {{
        border-radius: 22px;
        overflow: hidden;
        border: 1px solid var(--app-border);
        background: linear-gradient(180deg, var(--app-surface-alt) 0%, var(--app-surface) 100%);
        box-shadow: var(--app-shadow);
        padding: 0.3rem 0.35rem 0.15rem 0.35rem;
        animation: chartGlowIn 0.56s ease both;
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease, background 0.22s ease;
    }}

    [data-testid="stPlotlyChart"]:hover {{
        transform: translateY(-3px);
        border-color: rgba(79, 140, 255, 0.34);
        box-shadow: 0 24px 48px rgba(8, 15, 30, 0.24);
        background: linear-gradient(180deg, var(--app-primary-soft) 0%, var(--app-surface) 100%);
    }}

    [data-testid="stPlotlyChart"] > div {{
        border-radius: 18px;
        overflow: hidden;
    }}

    .editorial-hero,
    .editorial-panel {{
        animation: cardFloatIn 0.42s ease both;
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    }}

    .scene-seq {{
        animation: cardFloatIn 0.48s ease both;
    }}

    .scene-seq.seq-1 {{ animation-delay: 0.02s; }}
    .scene-seq.seq-2 {{ animation-delay: 0.12s; }}
    .scene-seq.seq-3 {{ animation-delay: 0.22s; }}
    .scene-seq.seq-4 {{ animation-delay: 0.32s; }}
    .scene-seq.seq-5 {{ animation-delay: 0.42s; }}
    .scene-seq.seq-6 {{ animation-delay: 0.52s; }}
    .scene-seq.seq-7 {{ animation-delay: 0.62s; }}
    .scene-seq.seq-8 {{ animation-delay: 0.72s; }}

    .editorial-section-heading {{
        margin-bottom: 0.7rem;
    }}

    .editorial-section-heading h2 {{
        margin: 0 !important;
        border-bottom: none;
        padding-bottom: 0;
        font-size: 1.45rem !important;
    }}

    .editorial-section-heading p {{
        margin: 0.25rem 0 0 0;
        color: var(--app-text-muted);
        max-width: 880px;
    }}

    .scene-stage {{
        border: 1px solid var(--app-border);
        border-radius: 24px;
        background: linear-gradient(180deg, var(--app-surface-alt) 0%, var(--app-surface) 100%);
        box-shadow: var(--app-shadow);
        padding: 1rem 1rem 0.85rem 1rem;
        margin: 0.4rem 0 1rem 0;
        animation: cardFloatIn 0.48s ease both;
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    }}

    .scene-stage:hover {{
        transform: translateY(-2px);
        border-color: rgba(79, 140, 255, 0.28);
        box-shadow: 0 22px 44px rgba(8, 15, 30, 0.22);
    }}

    .scene-stage.analysis-stage {{
        background: linear-gradient(180deg, var(--app-primary-soft) 0%, var(--app-surface) 100%);
    }}

    .scene-stage.export-stage {{
        background: linear-gradient(180deg, var(--app-accent-soft) 0%, var(--app-surface) 100%);
    }}

    .scene-stage .editorial-kicker {{
        margin-bottom: 0.3rem;
    }}

    .scene-stage h3 {{
        margin-bottom: 0.3rem;
    }}

    .scene-stage p {{
        color: var(--app-text-muted);
        margin-bottom: 0.8rem;
    }}

    .editorial-hero:hover,
    .editorial-panel:hover {{
        transform: translateY(-2px);
        border-color: rgba(79, 140, 255, 0.28);
        box-shadow: 0 20px 40px rgba(8, 15, 30, 0.2);
    }}

    .styled-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.92rem;
        background: var(--app-surface);
        border-radius: 12px;
        overflow: hidden;
    }}

    .styled-table thead tr {{
        background: var(--app-accent);
        color: #ffffff;
    }}

    .styled-table th, .styled-table td {{
        padding: 10px 14px;
        text-align: center;
        color: var(--app-text);
        border-bottom: 1px solid var(--app-border);
    }}

    .styled-table tbody tr:nth-of-type(odd) {{
        background: var(--app-surface-alt);
    }}

    .styled-table tbody tr:nth-of-type(even) {{
        background: var(--app-surface);
    }}

    .styled-table tbody tr:hover {{
        background: var(--app-primary-soft);
        transition: background-color 0.15s;
    }}

    .styled-table .total-row {{
        background: rgba(231, 184, 75, 0.18) !important;
        font-weight: 700;
    }}

    .styled-table .total-row td {{
        color: var(--app-heading) !important;
    }}

    hr {{
        border-color: var(--app-border);
    }}

    .editorial-hero {{
        position: relative;
        overflow: hidden;
        padding: 1.4rem 1.5rem;
        border-radius: 26px;
        border: 1px solid var(--app-border);
        background: linear-gradient(145deg, var(--app-surface) 0%, var(--app-surface-alt) 100%);
        box-shadow: var(--app-shadow);
        margin-bottom: 1rem;
    }}

    .editorial-hero::after {{
        content: "";
        position: absolute;
        inset: auto -8% -30% auto;
        width: 240px;
        height: 240px;
        border-radius: 50%;
        background: radial-gradient(circle, var(--app-primary-soft) 0%, rgba(255,255,255,0) 70%);
        pointer-events: none;
    }}

    .editorial-kicker {{
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
        color: var(--app-accent);
        margin-bottom: 0.5rem;
    }}

    .editorial-hero h1,
    .editorial-panel h3 {{
        margin: 0;
    }}

    .editorial-lead {{
        margin-top: 0.45rem;
        max-width: 920px;
        color: var(--app-text-muted);
        line-height: 1.55;
        font-size: 1.01rem;
    }}

    .editorial-meta-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1rem;
    }}

    .editorial-chip {{
        padding: 0.38rem 0.8rem;
        border-radius: 999px;
        border: 1px solid var(--app-border);
        background: var(--app-primary-soft);
        color: var(--app-heading);
        font-size: 0.86rem;
        font-weight: 600;
    }}

    .editorial-section-label {{
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
        color: var(--app-text-muted);
        margin: 0.35rem 0 0.55rem 0;
    }}

    .editorial-panel {{
        height: 100%;
        padding: 1rem 1.05rem;
        border-radius: 20px;
        border: 1px solid var(--app-border);
        background: linear-gradient(180deg, var(--app-surface-alt) 0%, var(--app-surface) 100%);
        box-shadow: var(--app-shadow);
    }}

    .editorial-panel p {{
        margin: 0.35rem 0 0 0;
        color: var(--app-text-muted);
        line-height: 1.5;
    }}

    .editorial-panel strong {{
        color: var(--app-heading);
    }}

    .editorial-panel.accent {{
        background: linear-gradient(180deg, var(--app-primary-soft) 0%, var(--app-surface) 100%);
    }}

    .editorial-panel.alert {{
        background: linear-gradient(180deg, rgba(231, 184, 75, 0.15) 0%, var(--app-surface) 100%);
    }}

    .editorial-panel.success {{
        background: linear-gradient(180deg, rgba(93, 194, 154, 0.14) 0%, var(--app-surface) 100%);
    }}

    .editorial-panel.panel-match-heatmap {{
        min-height: 458px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }}

    @media (max-width: 900px) {{
        .editorial-panel.panel-match-heatmap {{
            min-height: auto;
        }}
    }}

    footer {{ visibility: hidden; }}
</style>
        """,
        unsafe_allow_html=True,
    )


# ====================================================================
# Sidebar – Navegación y filtros
# ====================================================================

def render_sidebar():
    """Renderiza el menú lateral de navegación y filtros globales."""
    with st.sidebar:
        tema_actual = st.session_state.get("app_theme", "oscuro")
        st.image(
            "https://img.icons8.com/fluency/96/detective.png",
            width=64,
        )
        st.title("Mapa Delictual")
        st.caption("Sistema de Informes Estadísticos")
        tema_label = VISUAL_THEMES[tema_actual]["label"]
        st.caption(f"Tema activo: {tema_label}")

        def _on_theme_change():
            st.session_state["app_theme"] = st.session_state["_theme_radio"]

        temas_keys = list(VISUAL_THEMES.keys())
        st.radio(
            "Tema visual",
            options=temas_keys,
            index=temas_keys.index(tema_actual),
            format_func=lambda key: VISUAL_THEMES[key]["label"],
            horizontal=False,
            key="_theme_radio",
            on_change=_on_theme_change,
        )
        st.divider()

        # Navegación
        PAGINAS = [
            "🏠 Inicio",
            "📋 Delitos por Modalidad",
            "🔫 Robos y Hurtos",
            "📅 Análisis Temporal",
            "🔍 Características",
            "🗺️ Análisis Geográfico",
            "📈 Comparativo",
        ]
        pagina_guardada = st.session_state.get("app_pagina", "🏠 Inicio")
        idx_actual = PAGINAS.index(pagina_guardada) if pagina_guardada in PAGINAS else 0

        pagina = st.radio(
            "📊 Navegación",
            PAGINAS,
            index=idx_actual,
            key="app_pagina",
            label_visibility="collapsed",
        )

        render_boton_regenerar()

        st.caption("v1.0 — Policía de Tucumán")

        return pagina


# ====================================================================
# Router de páginas
# ====================================================================

def main():
    if "app_theme" not in st.session_state:
        st.session_state["app_theme"] = "oscuro"
    if "app_pagina" not in st.session_state:
        st.session_state["app_pagina"] = "🏠 Inicio"

    inject_visual_system(st.session_state["app_theme"])
    pagina = render_sidebar()

    if "🏠 Inicio" in pagina:
        home.render()
    elif "Delitos por Modalidad" in pagina:
        delitos.render()
    elif "Robos y Hurtos" in pagina:
        robos_hurtos.render()
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
