"""Helpers visuales editoriales reutilizables para las páginas Streamlit."""

from html import escape

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