"""
Generador de gráficos estilo Power BI para informes del mapa delictual.
Usa Plotly para crear gráficos de barras, tortas, líneas y tablas interactivas.
"""
from __future__ import annotations

from typing import Optional
import textwrap
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

from app.config.settings import CHART_PALETTE, COLORES, TYPOGRAPHY, VISUAL_THEMES


def _palette_by_chart(theme: dict, chart_type: str) -> list[str]:
    base_palette = _get_palette(theme)
    presets = {
        "horizontal": [theme["primary"], "#6ea8fe", "#8cb9ff", theme["accent"], theme["success"]],
        "vertical": [theme["primary"], theme["accent"], theme["warning"], theme["success"], "#9dc2ff"],
        "comparison": [theme["primary"], theme["accent"]],
        "donut": [theme["accent"], theme["primary"], theme["success"], theme["warning"], "#95aee8"],
    }
    preset = presets.get(chart_type, [])
    return preset + [color for color in base_palette if color not in preset]


def _adaptive_height(item_count: int, base: int, per_item: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, base + max(item_count, 0) * per_item))


def _should_show_text(item_count: int, threshold: int) -> bool:
    return item_count <= threshold


def _trim_ticktext(values: list, max_chars: int = 22) -> list[str]:
    labels = []
    for value in values:
        text = str(value)
        labels.append(text if len(text) <= max_chars else f"{text[:max_chars - 1]}…")
    return labels


def _wrap_ticktext(values: list, width: int = 16, max_lines: int = 2) -> list[str]:
    labels = []
    for value in values:
        text = str(value).strip()
        if not text:
            labels.append("")
            continue

        parts = textwrap.wrap(text, width=width, break_long_words=False)
        if len(parts) > max_lines:
            visible = parts[:max_lines]
            last = visible[-1]
            visible[-1] = last if len(last) <= width - 1 else last[:width - 1]
            visible[-1] = f"{visible[-1]}…"
            parts = visible
        labels.append("<br>".join(parts))
    return labels


def _wrap_title(text: str, width: int = 28) -> str:
    raw = str(text or "").strip()
    if len(raw) <= width:
        return raw
    return "<br>".join(textwrap.wrap(raw, width=width, break_long_words=False))


def _apply_axis_density(fig: go.Figure, categories: list, axis: str = "x") -> None:
    count = len(categories)
    if count == 0:
        return

    if axis == "x":
        fig.update_xaxes(
            tickmode="array",
            tickvals=categories,
            ticktext=_trim_ticktext(categories, max_chars=18 if count > 18 else 24),
            tickangle=-45 if count > 10 else 0,
            automargin=True,
        )
    else:
        fig.update_yaxes(
            tickmode="array",
            tickvals=categories,
            ticktext=_trim_ticktext(categories, max_chars=26),
            automargin=True,
        )


def _apply_trace_transitions(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        hoverdistance=40,
    )
    return fig


def _resolve_default_color(color: str, fallback: str) -> str:
    legacy_defaults = {COLORES["bar_blue"], COLORES["bar_red"], COLORES["bar_green"], COLORES["bar_purple"]}
    return fallback if color in legacy_defaults else color


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string to RGB tuple."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _relative_luminance(r: int, g: int, b: int) -> float:
    """Compute relative luminance (0=black, 1=white) per WCAG."""
    def _linear(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def _interpolate_colorscale(value: float, colorscale: list[list]) -> str:
    """Interpolate a hex color from a Plotly-style colorscale at a given 0-1 value."""
    if value <= colorscale[0][0]:
        return str(colorscale[0][1])
    if value >= colorscale[-1][0]:
        return str(colorscale[-1][1])
    for i in range(len(colorscale) - 1):
        lo_pos, lo_color = colorscale[i][0], str(colorscale[i][1])
        hi_pos, hi_color = colorscale[i + 1][0], str(colorscale[i + 1][1])
        if lo_pos <= value <= hi_pos:
            t = (value - lo_pos) / (hi_pos - lo_pos) if hi_pos != lo_pos else 0.0
            r1, g1, b1 = _hex_to_rgb(lo_color)
            r2, g2, b2 = _hex_to_rgb(hi_color)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            return f"#{r:02x}{g:02x}{b:02x}"
    return str(colorscale[-1][1])


def _adaptive_text_colors(z_values, colorscale: list[list], dark_text: str = "#11213c", light_text: str = "#f5f8ff") -> list[list[str]]:
    """Build a 2D list of text colors (dark/light) based on cell background luminance."""
    import numpy as np
    z_arr = np.array(z_values, dtype=float)
    z_min = float(z_arr.min()) if z_arr.size > 0 else 0.0
    z_max = float(z_arr.max()) if z_arr.size > 0 else 1.0
    z_range = z_max - z_min if z_max != z_min else 1.0

    result: list[list[str]] = []
    for row in z_arr:
        row_colors: list[str] = []
        for val in row:
            norm = (float(val) - z_min) / z_range
            bg_hex = _interpolate_colorscale(norm, colorscale)
            lum = _relative_luminance(*_hex_to_rgb(bg_hex))
            row_colors.append(dark_text if lum > 0.35 else light_text)
        result.append(row_colors)
    return result


def _themed_colorscale(theme: dict) -> list[list[float | str]]:
    if theme["label"] == "Claro Institucional":
        return [
            [0.0, "#edf3ff"],
            [0.2, "#c9dcff"],
            [0.45, "#8db5ff"],
            [0.7, theme["primary"]],
            [1.0, theme["accent"]],
        ]
    return [
        [0.0, "#152238"],
        [0.2, "#1d3658"],
        [0.45, theme["primary"]],
        [0.7, "#7aa7ff"],
        [1.0, theme["warning"]],
    ]

def _get_active_theme() -> dict:
    try:
        theme_key = st.session_state.get("app_theme", "oscuro")
    except Exception:
        theme_key = "oscuro"
    return VISUAL_THEMES.get(theme_key, VISUAL_THEMES["oscuro"])


def _get_palette(theme: dict) -> list[str]:
    base = [theme["primary"], theme["accent"], theme["success"], theme["warning"]]
    extra = [color for color in CHART_PALETTE if color not in base]
    return base + extra


def _build_layout_base(theme: dict) -> dict:
    return dict(
        font=dict(family=TYPOGRAPHY["ui"], size=13, color=theme["text"]),
        paper_bgcolor=theme["surface"],
        plot_bgcolor=theme["surface_alt"],
        margin=dict(l=60, r=30, t=68, b=60),
        hoverlabel=dict(bgcolor=theme["surface_alt"], font_size=12, font_color=theme["text"]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=theme["text"]),
        ),
        xaxis=dict(
            gridcolor=theme["border"],
            zerolinecolor=theme["border"],
            tickfont=dict(color=theme["text"]),
            title_font=dict(color=theme["text"]),
        ),
        yaxis=dict(
            gridcolor=theme["border"],
            zerolinecolor=theme["border"],
            tickfont=dict(color=theme["text"]),
            title_font=dict(color=theme["text"]),
        ),
    )


def _apply_base_layout(fig: go.Figure, title: str = "", height: int = 450) -> go.Figure:
    """Aplica el estilo base a cualquier figura Plotly."""
    from datetime import datetime
    theme = _get_active_theme()
    
    fecha_actual = datetime.now().strftime("%d/%m")
    
    fig.update_layout(
        **_build_layout_base(theme),
        title=dict(text=title, x=0.5, font=dict(family=TYPOGRAPHY["editorial"], size=18, color=theme["heading"])),
        height=height,
        bargap=0.22,
        bargroupgap=0.08,
    )
    
    fig.add_annotation(
        text=f"Fecha: {fecha_actual}",
        xref="paper", yref="paper",
        x=1.0, y=1.1,
        xanchor="right", yanchor="bottom",
        showarrow=False,
        font=dict(size=12, color=theme.get("text_muted", "#888888"))
    )
    
    return _apply_trace_transitions(fig)


# ====================================================================
# Gráficos principales
# ====================================================================

class ChartGenerator:
    """
    Genera gráficos Plotly estilizados para cada tipo de informe.

    Uso:
        charts = ChartGenerator()
        fig = charts.barras_horizontal(df_stats, "Delitos por Modalidad")
    """

    # ---- Barras horizontales (ideal para modalidades, jurisdicciones) ----

    @staticmethod
    def barras_horizontal(
        df: pd.DataFrame,
        titulo: str = "",
        color: str = COLORES["bar_blue"],
        col_cat: str = "categoria_label",
        col_val: str = "cantidad",
        col_pct: str = "porcentaje",
        height: int = 500,
    ) -> go.Figure:
        """Gráfico de barras horizontales con etiquetas de valor y %."""
        theme = _get_active_theme()
        df_plot = df.copy()
        if col_cat in df_plot.columns:
            df_plot = df_plot.sort_values(col_val, ascending=True)
        height = _adaptive_height(len(df_plot), base=170, per_item=34, minimum=340, maximum=920)
        palette = _palette_by_chart(theme, "horizontal")
        color = _resolve_default_color(color, palette[0])
        show_text = _should_show_text(len(df_plot), 14)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=df_plot[col_cat],
            x=df_plot[col_val],
            orientation="h",
            marker_color=color,
            marker_line=dict(color=theme["border"], width=1),
            text=df_plot.apply(
                lambda r: f"{int(r[col_val]):,}  ({r[col_pct]:.1f}%)", axis=1
            ) if col_pct in df_plot.columns else df_plot[col_val].apply(lambda value: f"{int(value):,}"),
            textposition="outside",
            textfont=dict(color=theme["text"]),
            hovertemplate="<b>%{y}</b><br>Cantidad: %{x:,}<extra></extra>",
            cliponaxis=False,
            insidetextanchor="middle",
        ))

        fig.update_layout(
            xaxis_title="Cantidad",
            yaxis_title="",
            showlegend=False,
        )

        _apply_axis_density(fig, df_plot[col_cat].tolist(), axis="y")

        return _apply_base_layout(fig, titulo, height=height)

    # ---- Barras verticales (ideal para días, meses, franjas) ----

    @staticmethod
    def barras_vertical(
        df: pd.DataFrame,
        titulo: str = "",
        color: str = COLORES["bar_blue"],
        col_cat: str = "categoria_label",
        col_val: str = "cantidad",
        col_pct: str = "porcentaje",
        height: int | None = None,
        highlight_max: bool = True,
    ) -> go.Figure:
        """Gráfico de barras verticales con resaltado del valor máximo."""
        theme = _get_active_theme()
        df_plot = df.copy()
        categories = df_plot[col_cat].astype(str).tolist()
        palette = _palette_by_chart(theme, "vertical")
        base_color = _resolve_default_color(color, palette[0])
        show_text = _should_show_text(len(df_plot), 12)
        max_label_length = max((len(label) for label in categories), default=0)
        use_wrapped_ticks = max_label_length > 14
        if height is None:
            height = _adaptive_height(
                len(df_plot),
                base=300 if use_wrapped_ticks else 260,
                per_item=18,
                minimum=420 if use_wrapped_ticks else 360,
                maximum=760,
            )

        colors = [base_color] * len(df_plot)
        if highlight_max and len(df_plot) > 0:
            max_idx = df_plot[col_val].idxmax()
            pos = df_plot.index.get_loc(max_idx)
            colors[pos] = palette[1]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_plot[col_cat],
            y=df_plot[col_val],
            marker_color=colors,
            marker_line=dict(color=theme["border"], width=1),
            text=df_plot[col_val].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            textfont=dict(color=theme["text"]),
            hovertemplate="<b>%{x}</b><br>Cantidad: %{y:,}<extra></extra>",
            cliponaxis=False,
        ))

        fig.update_layout(
            xaxis_title="",
            yaxis_title="Cantidad",
            showlegend=False,
        )

        _apply_axis_density(fig, df_plot[col_cat].tolist(), axis="x")
        if use_wrapped_ticks:
            fig.update_xaxes(
                tickmode="array",
                tickvals=categories,
                ticktext=_wrap_ticktext(categories, width=16, max_lines=2),
                tickangle=-18,
                tickfont=dict(size=11, color=theme["text"]),
                automargin=True,
            )

        fig = _apply_base_layout(fig, titulo, height)
        if use_wrapped_ticks:
            fig.update_layout(margin=dict(l=60, r=30, t=68, b=110))
        return fig

    # ---- Gráfico de torta / dona ----

    @staticmethod
    def dona(
        df: pd.DataFrame,
        titulo: str = "",
        col_cat: str = "categoria_label",
        col_val: str = "cantidad",
        hole: float = 0.45,
        height: int = 450,
    ) -> go.Figure:
        """Gráfico de dona (donut) con porcentajes."""
        theme = _get_active_theme()
        df_plot = df[[col_cat, col_val]].copy()
        df_plot = df_plot[df_plot[col_val].fillna(0) > 0]
        df_plot = df_plot.sort_values(col_val, ascending=False).reset_index(drop=True)

        if df_plot.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="Sin datos disponibles",
                showarrow=False,
                font=dict(size=16, color=theme["text_muted"]),
            )
            fig.update_layout(showlegend=False)
            return _apply_base_layout(fig, titulo, height)

        original_count = len(df_plot)
        max_visible_slices = 7
        if original_count > max_visible_slices:
            top_df = df_plot.head(max_visible_slices).copy()
            otros_valor = float(df_plot.iloc[max_visible_slices:][col_val].sum())
            if otros_valor > 0:
                top_df.loc[len(top_df)] = {
                    col_cat: "Otros",
                    col_val: otros_valor,
                }
            df_plot = top_df

        palette = _palette_by_chart(theme, "donut")
        item_count = len(df_plot)
        compact_labels = item_count > 4
        show_legend = original_count > 4
        text_threshold = 0.02
        fig = go.Figure()

        pie_domain_x = [0.05, 0.60] if show_legend else [0.10, 0.90]
        pie_domain_y = [0.05, 0.88]

        fig.add_trace(go.Pie(
            labels=df_plot[col_cat],
            values=df_plot[col_val],
            hole=hole,
            marker=dict(colors=palette[:item_count], line=dict(color=theme["surface"], width=2)),
            textinfo="percent" if compact_labels else "label+percent",
            textposition="inside" if compact_labels else "outside",
            texttemplate="%{percent}" if compact_labels else "%{label}<br>%{percent}",
            textfont=dict(color=theme["heading"], size=12),
            insidetextorientation="horizontal",
            automargin=True,
            hovertemplate="<b>%{label}</b><br>Cantidad: %{value:,}<br>%{percent}<extra></extra>",
            sort=False,
            pull=[0.03 if idx == 0 else 0 for idx in range(item_count)],
            direction="clockwise",
            rotation=90,
            domain=dict(x=pie_domain_x, y=pie_domain_y),
        ))

        fig.update_traces(
            selector=dict(type="pie"),
            textfont_size=12,
            textposition="inside" if compact_labels else "outside",
            texttemplate=(
                "%{percent}" if compact_labels else "%{label}<br>%{percent}"
            ),
        )

        if compact_labels:
            fig.data[0].update(
                texttemplate=[f"%{{percent}}" if (value / df_plot[col_val].sum()) >= text_threshold else "" for value in df_plot[col_val]],
            )

        total = df[col_val].sum()
        center_x = (pie_domain_x[0] + pie_domain_x[1]) / 2
        center_y = (pie_domain_y[0] + pie_domain_y[1]) / 2
        fig.add_annotation(
            text=f"<b>{int(total):,}</b><br>Total",
            showarrow=False,
            font=dict(size=16, color=theme["heading"]),
            x=center_x,
            y=center_y,
            xanchor="center",
            yanchor="middle",
        )

        wrapped_title = _wrap_title(titulo, width=26 if show_legend else 34)
        fig = _apply_base_layout(fig, wrapped_title, height)
        fig.update_layout(
            showlegend=show_legend,
            title=dict(
                x=0.5,
                xanchor="center",
                y=0.98,
                yanchor="top",
                font=dict(family=TYPOGRAPHY["editorial"], size=18, color=theme["heading"]),
            ),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.88,
                xanchor="left",
                x=0.66,
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=11, color=theme["text"]),
                itemwidth=30,
                tracegroupgap=6,
            ),
            margin=dict(l=28, r=220 if show_legend else 28, t=60, b=28),
        )

        return fig

    # ---- Gráfico de líneas (ideal para tendencias mensuales) ----

    @staticmethod
    def lineas_comparativo(
        df: pd.DataFrame,
        titulo: str = "",
        col_x: str = "mes_label",
        col_y1: str = "cantidad_anterior",
        col_y2: str = "cantidad_actual",
        label_y1: str = "Año anterior",
        label_y2: str = "Año actual",
        height: int = 450,
        mostrar_texto: bool = True,
        xaxis_title: str = "Periodo",
    ) -> go.Figure:
        """Gráfico de líneas comparando dos períodos."""
        theme = _get_active_theme()
        # Excluir fila TOTAL si existe
        df_plot = df[df[col_x] != "TOTAL"].copy()
        point_count = len(df_plot)
        show_text = mostrar_texto and _should_show_text(point_count, 12)
        if point_count > 18:
            height = max(height, 560)
        elif point_count > 10:
            height = max(height, 500)

        text_y1 = df_plot[col_y1].apply(lambda x: f"{int(x):,}")
        text_y2 = df_plot[col_y2].apply(lambda x: f"{int(x):,}")
        mode = "lines+markers+text"

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_plot[col_x],
            y=df_plot[col_y1],
            name=label_y1,
            mode=mode,
            line=dict(color=theme["primary"], width=3, shape="spline", smoothing=0.55),
            marker=dict(size=9, color=theme["primary"], line=dict(width=1, color=theme["surface"])),
            text=text_y1,
            textposition="top center",
            textfont=dict(size=10, color=theme["text"]),
            hovertemplate=f"<b>{label_y1}</b><br>%{{x}}: %{{y:,}}<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
            x=df_plot[col_x],
            y=df_plot[col_y2],
            name=label_y2,
            mode=mode,
            line=dict(color=theme["accent"], width=3, shape="spline", smoothing=0.55),
            marker=dict(size=9, color=theme["accent"], line=dict(width=1, color=theme["surface"])),
            text=text_y2,
            textposition="bottom center",
            textfont=dict(size=10, color=theme["text"]),
            hovertemplate=f"<b>{label_y2}</b><br>%{{x}}: %{{y:,}}<extra></extra>",
        ))

        fig.update_layout(
            xaxis_title=xaxis_title,
            yaxis_title="Cantidad de Delitos",
            hovermode="x unified",
        )

        _apply_axis_density(fig, df_plot[col_x].tolist(), axis="x")
        fig.update_yaxes(rangemode="tozero")
        fig.update_xaxes(showspikes=True, spikecolor=theme["border"], spikethickness=1)
        fig = _apply_base_layout(fig, titulo, height)
        fig.update_layout(
            margin=dict(l=60, r=30, t=78, b=110 if point_count > 10 else 70),
        )
        return fig

    # ---- Barras agrupadas comparativas ----

    @staticmethod
    def barras_comparativo(
        df: pd.DataFrame,
        titulo: str = "",
        col_cat: str = "categoria",
        col_y1: str = "cantidad_anterior",
        col_y2: str = "cantidad_actual",
        label_y1: str = "Año anterior",
        label_y2: str = "Año actual",
        height: int = 500,
    ) -> go.Figure:
        """Gráfico de barras agrupadas comparando dos períodos."""
        theme = _get_active_theme()
        df_plot = df[df[col_cat] != "TOTAL"].copy()
        palette = _palette_by_chart(theme, "comparison")
        show_text = _should_show_text(len(df_plot), 10)
        item_count = len(df_plot)
        height = _adaptive_height(item_count, base=320, per_item=24, minimum=420, maximum=980)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name=label_y1,
            x=df_plot[col_cat],
            y=df_plot[col_y1],
            marker_color=palette[0],
            marker_line=dict(color=theme["border"], width=1),
            text=df_plot[col_y1].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            textfont=dict(color=theme["text"]),
            cliponaxis=False,
        ))

        fig.add_trace(go.Bar(
            name=label_y2,
            x=df_plot[col_cat],
            y=df_plot[col_y2],
            marker_color=palette[1],
            marker_line=dict(color=theme["border"], width=1),
            text=df_plot[col_y2].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            textfont=dict(color=theme["text"]),
            cliponaxis=False,
        ))

        fig.update_layout(barmode="group")
        _apply_axis_density(fig, df_plot[col_cat].tolist(), axis="x")
        fig = _apply_base_layout(fig, titulo, height)
        fig.update_layout(
            margin=dict(l=60, r=30, t=78, b=120 if item_count > 10 else 80),
        )
        return fig

    @staticmethod
    def barras_horizontal_comparativo(
        df: pd.DataFrame,
        titulo: str = "",
        col_cat: str = "categoria",
        col_y1: str = "cantidad_anterior",
        col_y2: str = "cantidad_actual",
        label_y1: str = "Serie 1",
        label_y2: str = "Serie 2",
        height: int | None = None,
    ) -> go.Figure:
        """Gráfico de barras horizontales agrupadas para comparar dos series."""
        theme = _get_active_theme()
        df_plot = df.copy()
        palette = _palette_by_chart(theme, "comparison")
        show_text = _should_show_text(len(df_plot), 12)
        if height is None:
            height = _adaptive_height(len(df_plot), base=230, per_item=28, minimum=380, maximum=940)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name=label_y1,
            y=df_plot[col_cat],
            x=df_plot[col_y1],
            orientation="h",
            marker_color=palette[0],
            marker_line=dict(color=theme["border"], width=1),
            text=df_plot[col_y1].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            textfont=dict(color=theme["text"]),
            cliponaxis=False,
            hovertemplate=f"<b>{label_y1}</b><br>%{{y}}: %{{x:,}}<extra></extra>",
        ))

        fig.add_trace(go.Bar(
            name=label_y2,
            y=df_plot[col_cat],
            x=df_plot[col_y2],
            orientation="h",
            marker_color=palette[1],
            marker_line=dict(color=theme["border"], width=1),
            text=df_plot[col_y2].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            textfont=dict(color=theme["text"]),
            cliponaxis=False,
            hovertemplate=f"<b>{label_y2}</b><br>%{{y}}: %{{x:,}}<extra></extra>",
        ))

        fig.update_layout(
            barmode="group",
            xaxis_title="Cantidad",
            yaxis_title="",
            hovermode="y unified",
        )

        _apply_axis_density(fig, df_plot[col_cat].tolist(), axis="y")

        return _apply_base_layout(fig, titulo, height)

    # ---- Tabla estilizada (Power BI style) ----

    @staticmethod
    def tabla_estilizada(
        df: pd.DataFrame,
        titulo: str = "",
        height: int = 500,
        columnas: Optional[list[str]] = None,
        header_color: str = COLORES["header_red"],
    ) -> go.Figure:
        """Tabla interactiva estilo Power BI con encabezados de color."""
        theme = _get_active_theme()
        if columnas:
            df_plot = df[columnas].copy()
        else:
            df_plot = df.copy()

        # Formatear números
        for col in df_plot.select_dtypes(include=["float64", "float32"]).columns:
            df_plot[col] = df_plot[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
        for col in df_plot.select_dtypes(include=["int64", "int32"]).columns:
            df_plot[col] = df_plot[col].apply(lambda x: f"{x:,}")

        # Colores alternados en filas — tema oscuro
        n_rows = len(df_plot)
        fill_colors = [
            [theme["surface"] if i % 2 == 0 else theme["surface_alt"] for i in range(n_rows)]
            for _ in df_plot.columns
        ]

        # Resaltar fila TOTAL si existe
        for col_idx, col in enumerate(df_plot.columns):
            for row_idx in range(n_rows):
                val = str(df_plot.iloc[row_idx][df_plot.columns[0]])
                if "TOTAL" in val.upper():
                    fill_colors[col_idx][row_idx] = COLORES["total_yellow"]

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=[f"<b>{c}</b>" for c in df_plot.columns],
                fill_color=theme["accent"] if header_color == COLORES["header_red"] else header_color,
                font=dict(color="white", size=13),
                align="center",
                height=35,
            ),
            cells=dict(
                values=[df_plot[c].tolist() for c in df_plot.columns],
                fill_color=fill_colors,
                font=dict(size=12, color=theme["text"]),
                align=["left"] + ["center"] * (len(df_plot.columns) - 1),
                height=28,
            ),
        )])

        return _apply_base_layout(fig, titulo, height)

    # ---- Mapa de calor (heatmap) ----

    @staticmethod
    def heatmap(
        df_pivot: pd.DataFrame,
        titulo: str = "",
        height: int = 500,
        colorscale: str = "YlOrRd",
    ) -> go.Figure:
        """Heatmap para matrices de datos (ej: delito x mes)."""
        theme = _get_active_theme()
        row_count, col_count = df_pivot.shape
        adaptive_height = _adaptive_height(row_count, base=250, per_item=34, minimum=320, maximum=920)
        height = max(height, adaptive_height)
        show_text = True
        text_size = 10 if row_count > 6 or col_count > 6 else 11
        x_labels = df_pivot.columns.tolist()
        y_labels = df_pivot.index.tolist()

        active_colorscale = _themed_colorscale(theme) if colorscale == "YlOrRd" else colorscale

        fig = go.Figure(data=go.Heatmap(
            z=df_pivot.values,
            x=x_labels,
            y=y_labels,
            colorscale=active_colorscale,
            hovertemplate="<b>%{y}</b> - %{x}<br>Cantidad: %{z:,}<extra></extra>",
            xgap=2,
            ygap=2,
            colorbar=dict(outlinewidth=0, tickfont=dict(color=theme["text"])),
        ))

        # Add per-cell annotations: white text in dark mode, black text in light mode
        if show_text:
            cell_color = "#ffffff" if theme["label"] != "Claro Institucional" else "#000000"
            annotations = []
            for i, y_val in enumerate(y_labels):
                for j, x_val in enumerate(x_labels):
                    val = df_pivot.values[i][j]
                    annotations.append(dict(
                        x=x_val,
                        y=y_val,
                        text=f"{int(val):,}",
                        showarrow=False,
                        font=dict(size=text_size, color=cell_color),
                        xref="x",
                        yref="y",
                    ))
            fig.update_layout(annotations=annotations)

        fig.update_layout(
            xaxis_title="",
            yaxis_title="",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=118 if row_count > 6 else 80, r=30, t=68, b=96 if col_count > 5 else 60),
        )

        _apply_axis_density(fig, x_labels, axis="x")
        _apply_axis_density(fig, y_labels, axis="y")
        fig.update_xaxes(tickangle=-35 if col_count > 4 else 0)

        return _apply_base_layout(fig, titulo, height)

    # ---- KPI Cards (indicadores) ----

    @staticmethod
    def kpi_card(
        valor: int | float | str,
        titulo: str = "",
        subtitulo: str = "",
        delta: Optional[float] = None,
        height: int = 180,
        width: int = 300,
    ) -> go.Figure:
        """Indicador numérico estilo KPI card de Power BI."""
        fig = go.Figure()
        theme = _get_active_theme()

        fig.add_trace(go.Indicator(
            mode="number+delta" if delta is not None else "number",
            value=valor if isinstance(valor, (int, float)) else 0,
            title=dict(text=f"<b>{titulo}</b><br><span style='font-size:12px;color:{theme['text_muted']}'>{subtitulo}</span>"),
            delta=dict(
                reference=valor - delta if delta else None,
                valueformat=",.0f",
                increasing=dict(color=theme["success"]),
                decreasing=dict(color=theme["accent"]),
            ) if delta is not None else None,
            number=dict(
                valueformat=",",
                font=dict(size=40, color=theme["heading"]),
            ),
        ))

        fig.update_layout(
            height=height,
            width=width,
            paper_bgcolor=theme["surface"],
            font=dict(family=TYPOGRAPHY["ui"], color=theme["text"]),
            margin=dict(l=20, r=20, t=60, b=20),
        )

        return fig
