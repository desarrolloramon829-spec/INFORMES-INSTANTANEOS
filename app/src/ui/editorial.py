"""Helpers visuales editoriales reutilizables para las páginas Streamlit."""

from html import escape
import pandas as pd
import streamlit as st


def render_hero(kicker: str, titulo: str, cuerpo: str, chips: list[str] | None = None, seq: int = 1):
    chips_html = ""
    if chips:
        chips_html = "".join(
            f'<span class="editorial-chip">{escape(chip)}</span>'
            for chip in chips
        )

    st.markdown(
        f"""
        <section class="editorial-hero scene-seq seq-{seq}">
            <div class="editorial-kicker">{escape(kicker)}</div>
            <h1>{escape(titulo)}</h1>
            <p class="editorial-lead">{escape(cuerpo)}</p>
            <div class="editorial-meta-row">{chips_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(seq: int, kicker: str, titulo: str, cuerpo: str):
    st.markdown(
        f"""
        <section class="editorial-section-heading scene-seq seq-{seq}">
            <div class="editorial-kicker">{escape(kicker)}</div>
            <h2>{escape(titulo)}</h2>
            <p>{escape(cuerpo)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_panel(seq: int, kicker: str, titulo: str, cuerpo: str, tone: str = ""):
    tone_class = f" {tone}" if tone else ""
    st.markdown(
        f"""
        <section class="editorial-panel scene-seq seq-{seq}{tone_class}">
            <div class="editorial-kicker">{escape(kicker)}</div>
            <h3>{escape(titulo)}</h3>
            <p>{escape(cuerpo)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def open_stage(seq: int, kicker: str, titulo: str, cuerpo: str, stage_class: str = ""):
    extra_class = f" {stage_class}" if stage_class else ""
    st.markdown(
        f"""
        <section class="scene-stage scene-seq seq-{seq}{extra_class}">
            <div class="editorial-kicker">{escape(kicker)}</div>
            <h3>{escape(titulo)}</h3>
            <p>{escape(cuerpo)}</p>
        """,
        unsafe_allow_html=True,
    )


def close_stage():
    st.markdown("</section>", unsafe_allow_html=True)


def render_dataframe_as_html_table(df: pd.DataFrame, height: int | None = None):
    """
    Renderiza un DataFrame de pandas como una tabla HTML estilizada (.styled-table)
    que respeta el tema claro/oscuro de la aplicación.
    """
    import pandas as pd
    rows = ""
    for _, row in df.iterrows():
        rows += "<tr>"
        for i, val in enumerate(row):
            align = "left" if i == 0 else "center"
            weight = "500" if i == 0 else "normal"
            rows += f'<td style="text-align:{align}; font-weight:{weight};">{val}</td>'
        rows += "</tr>"

    headers = ""
    for i, col in enumerate(df.columns):
        align = "left" if i == 0 else "center"
        headers += f'<th style="text-align:{align}; position: sticky; top: 0; z-index: 1; background-color: #000000;">{col}</th>'

    html = f"""
    <table class="styled-table" style="margin: 0;">
        <thead>
            <tr>{headers}</tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """
    
    if height:
        html = f'<div style="max-height: {height}px; overflow-y: auto; border-radius: 12px; border: 1px solid var(--app-border);">{html}</div>'
    else:
        html = f'<div style="overflow-x: auto; border-radius: 12px; border: 1px solid var(--app-border);">{html}</div>'

    st.markdown(html, unsafe_allow_html=True)