"""
Generador de gráficos estilo Power BI para informes del mapa delictual.
Usa Plotly para crear gráficos de barras, tortas, líneas y tablas interactivas.
"""
from __future__ import annotations

from typing import Optional
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
        transition=dict(duration=420, easing="cubic-in-out"),
        hoverdistance=40,
    )
    return fig


def _resolve_default_color(color: str, fallback: str) -> str:
    legacy_defaults = {COLORES["bar_blue"], COLORES["bar_red"], COLORES["bar_green"], COLORES["bar_purple"]}
    return fallback if color in legacy_defaults else color


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
    theme = _get_active_theme()
    fig.update_layout(
        **_build_layout_base(theme),
        title=dict(text=title, x=0.5, font=dict(family=TYPOGRAPHY["editorial"], size=18, color=theme["heading"])),
        height=height,
        bargap=0.22,
        bargroupgap=0.08,
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
            ) if show_text and col_pct in df_plot.columns else df_plot[col_val].apply(lambda value: f"{int(value):,}") if show_text else None,
            textposition="outside" if show_text else "none",
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
        palette = _palette_by_chart(theme, "vertical")
        base_color = _resolve_default_color(color, palette[0])
        show_text = _should_show_text(len(df_plot), 12)
        if height is None:
            height = _adaptive_height(len(df_plot), base=260, per_item=18, minimum=360, maximum=760)

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
            text=df_plot[col_val].apply(lambda x: f"{int(x):,}") if show_text else None,
            textposition="outside" if show_text else "none",
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

        return _apply_base_layout(fig, titulo, height)

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
        palette = _palette_by_chart(theme, "donut")
        item_count = len(df)
        compact_labels = item_count > 6
        fig = go.Figure()

        fig.add_trace(go.Pie(
            labels=df[col_cat],
            values=df[col_val],
            hole=hole,
            marker=dict(colors=palette[:len(df)], line=dict(color=theme["surface"], width=2)),
            textinfo="percent" if compact_labels else "label+percent",
            textposition="outside",
            textfont=dict(color=theme["text"]),
            hovertemplate="<b>%{label}</b><br>Cantidad: %{value:,}<br>%{percent}<extra></extra>",
            sort=False,
            pull=[0.03 if idx == 0 else 0 for idx in range(item_count)],
        ))

        total = df[col_val].sum()
        fig.add_annotation(
            text=f"<b>{int(total):,}</b><br>Total",
            showarrow=False,
            font=dict(size=16, color=theme["heading"]),
        )

        fig.update_layout(showlegend=item_count > 5)

        return _apply_base_layout(fig, titulo, height)

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
            height = max(height, 520)

        text_y1 = df_plot[col_y1].apply(lambda x: f"{int(x):,}") if show_text else None
        text_y2 = df_plot[col_y2].apply(lambda x: f"{int(x):,}") if show_text else None
        mode = "lines+markers+text" if show_text else "lines+markers"

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

        return _apply_base_layout(fig, titulo, height)

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
        height = _adaptive_height(len(df_plot), base=290, per_item=22, minimum=380, maximum=860)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name=label_y1,
            x=df_plot[col_cat],
            y=df_plot[col_y1],
            marker_color=palette[0],
            marker_line=dict(color=theme["border"], width=1),
            text=df_plot[col_y1].apply(lambda x: f"{int(x):,}") if show_text else None,
            textposition="outside" if show_text else "none",
            textfont=dict(color=theme["text"]),
            cliponaxis=False,
        ))

        fig.add_trace(go.Bar(
            name=label_y2,
            x=df_plot[col_cat],
            y=df_plot[col_y2],
            marker_color=palette[1],
            marker_line=dict(color=theme["border"], width=1),
            text=df_plot[col_y2].apply(lambda x: f"{int(x):,}") if show_text else None,
            textposition="outside" if show_text else "none",
            textfont=dict(color=theme["text"]),
            cliponaxis=False,
        ))

        fig.update_layout(barmode="group")
        _apply_axis_density(fig, df_plot[col_cat].tolist(), axis="x")

        return _apply_base_layout(fig, titulo, height)

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
            text=df_plot[col_y1].apply(lambda x: f"{int(x):,}") if show_text else None,
            textposition="outside" if show_text else "none",
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
            text=df_plot[col_y2].apply(lambda x: f"{int(x):,}") if show_text else None,
            textposition="outside" if show_text else "none",
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
        show_text = df_pivot.size <= 72
        text_size = 10 if row_count > 6 or col_count > 6 else 11
        x_labels = df_pivot.columns.tolist()
        y_labels = df_pivot.index.tolist()

        fig = go.Figure(data=go.Heatmap(
            z=df_pivot.values,
            x=x_labels,
            y=y_labels,
            colorscale=_themed_colorscale(theme) if colorscale == "YlOrRd" else colorscale,
            text=df_pivot.values,
            texttemplate="%{text:,}" if show_text else None,
            textfont=dict(size=text_size, color=theme["heading"]),
            hovertemplate="<b>%{y}</b> - %{x}<br>Cantidad: %{z:,}<extra></extra>",
            xgap=2,
            ygap=2,
            colorbar=dict(outlinewidth=0, tickfont=dict(color=theme["text"])),
        ))

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
