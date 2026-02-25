"""
Generador de gráficos estilo Power BI para informes del mapa delictual.
Usa Plotly para crear gráficos de barras, tortas, líneas y tablas interactivas.
"""
from __future__ import annotations

from typing import Optional
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from app.config.settings import COLORES, CHART_PALETTE

# ====================================================================
# Configuración base de estilo
# ====================================================================

_LAYOUT_BASE = dict(
    font=dict(family="Segoe UI, Arial, sans-serif", size=13, color="#333"),
    paper_bgcolor="white",
    plot_bgcolor="#FAFAFA",
    margin=dict(l=60, r=30, t=60, b=60),
    hoverlabel=dict(bgcolor="white", font_size=12, font_color="black"),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
)


def _apply_base_layout(fig: go.Figure, title: str = "", height: int = 450) -> go.Figure:
    """Aplica el estilo base a cualquier figura Plotly."""
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text=title, x=0.5, font=dict(size=18, color=COLORES["dark_blue"])),
        height=height,
    )
    return fig


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
        df_plot = df.copy()
        if col_cat in df_plot.columns:
            df_plot = df_plot.sort_values(col_val, ascending=True)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=df_plot[col_cat],
            x=df_plot[col_val],
            orientation="h",
            marker_color=color,
            text=df_plot.apply(
                lambda r: f"{int(r[col_val]):,}  ({r[col_pct]:.1f}%)", axis=1
            ),
            textposition="outside",
            textfont=dict(color="black"),
            hovertemplate="<b>%{y}</b><br>Cantidad: %{x:,}<extra></extra>",
        ))

        fig.update_layout(
            xaxis_title="Cantidad",
            yaxis_title="",
            showlegend=False,
        )

        return _apply_base_layout(fig, titulo, height=max(height, len(df_plot) * 35 + 100))

    # ---- Barras verticales (ideal para días, meses, franjas) ----

    @staticmethod
    def barras_vertical(
        df: pd.DataFrame,
        titulo: str = "",
        color: str = COLORES["bar_blue"],
        col_cat: str = "categoria_label",
        col_val: str = "cantidad",
        col_pct: str = "porcentaje",
        height: int = 450,
        highlight_max: bool = True,
    ) -> go.Figure:
        """Gráfico de barras verticales con resaltado del valor máximo."""
        df_plot = df.copy()

        colors = [color] * len(df_plot)
        if highlight_max and len(df_plot) > 0:
            max_idx = df_plot[col_val].idxmax()
            pos = df_plot.index.get_loc(max_idx)
            colors[pos] = COLORES["secondary"]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_plot[col_cat],
            y=df_plot[col_val],
            marker_color=colors,
            text=df_plot[col_val].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            textfont=dict(color="black"),
            hovertemplate="<b>%{x}</b><br>Cantidad: %{y:,}<extra></extra>",
        ))

        fig.update_layout(
            xaxis_title="",
            yaxis_title="Cantidad",
            showlegend=False,
        )

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
        fig = go.Figure()

        fig.add_trace(go.Pie(
            labels=df[col_cat],
            values=df[col_val],
            hole=hole,
            marker=dict(colors=CHART_PALETTE[:len(df)]),
            textinfo="label+percent",
            textposition="outside",
            textfont=dict(color="black"),
            hovertemplate="<b>%{label}</b><br>Cantidad: %{value:,}<br>%{percent}<extra></extra>",
        ))

        total = df[col_val].sum()
        fig.add_annotation(
            text=f"<b>{int(total):,}</b><br>Total",
            showarrow=False,
            font=dict(size=16, color=COLORES["dark_blue"]),
        )

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
    ) -> go.Figure:
        """Gráfico de líneas comparando dos períodos."""
        # Excluir fila TOTAL si existe
        df_plot = df[df[col_x] != "TOTAL"].copy()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_plot[col_x],
            y=df_plot[col_y1],
            name=label_y1,
            mode="lines+markers+text",
            line=dict(color=COLORES["bar_blue"], width=2.5),
            marker=dict(size=8),
            text=df_plot[col_y1].apply(lambda x: f"{int(x):,}"),
            textposition="top center",
            textfont=dict(size=10, color="black"),
        ))

        fig.add_trace(go.Scatter(
            x=df_plot[col_x],
            y=df_plot[col_y2],
            name=label_y2,
            mode="lines+markers+text",
            line=dict(color=COLORES["bar_red"], width=2.5),
            marker=dict(size=8),
            text=df_plot[col_y2].apply(lambda x: f"{int(x):,}"),
            textposition="bottom center",
            textfont=dict(size=10, color="black"),
        ))

        fig.update_layout(
            xaxis_title="Mes",
            yaxis_title="Cantidad de Delitos",
            hovermode="x unified",
        )

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
        df_plot = df[df[col_cat] != "TOTAL"].copy()

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name=label_y1,
            x=df_plot[col_cat],
            y=df_plot[col_y1],
            marker_color=COLORES["bar_blue"],
            text=df_plot[col_y1].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            textfont=dict(color="black"),
        ))

        fig.add_trace(go.Bar(
            name=label_y2,
            x=df_plot[col_cat],
            y=df_plot[col_y2],
            marker_color=COLORES["bar_red"],
            text=df_plot[col_y2].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            textfont=dict(color="black"),
        ))

        fig.update_layout(barmode="group")

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
        if columnas:
            df_plot = df[columnas].copy()
        else:
            df_plot = df.copy()

        # Formatear números
        for col in df_plot.select_dtypes(include=["float64", "float32"]).columns:
            df_plot[col] = df_plot[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
        for col in df_plot.select_dtypes(include=["int64", "int32"]).columns:
            df_plot[col] = df_plot[col].apply(lambda x: f"{x:,}")

        # Colores alternados en filas
        n_rows = len(df_plot)
        fill_colors = [
            ["#F2F2F2" if i % 2 == 0 else "white" for i in range(n_rows)]
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
                fill_color=header_color,
                font=dict(color="white", size=13),
                align="center",
                height=35,
            ),
            cells=dict(
                values=[df_plot[c].tolist() for c in df_plot.columns],
                fill_color=fill_colors,
                font=dict(size=12),
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
        fig = go.Figure(data=go.Heatmap(
            z=df_pivot.values,
            x=df_pivot.columns.tolist(),
            y=df_pivot.index.tolist(),
            colorscale=colorscale,
            text=df_pivot.values,
            texttemplate="%{text:,}",
            hovertemplate="<b>%{y}</b> - %{x}<br>Cantidad: %{z:,}<extra></extra>",
        ))

        fig.update_layout(
            xaxis_title="",
            yaxis_title="",
            yaxis=dict(autorange="reversed"),
        )

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

        fig.add_trace(go.Indicator(
            mode="number+delta" if delta is not None else "number",
            value=valor if isinstance(valor, (int, float)) else 0,
            title=dict(text=f"<b>{titulo}</b><br><span style='font-size:12px;color:gray'>{subtitulo}</span>"),
            delta=dict(
                reference=valor - delta if delta else None,
                valueformat=",.0f",
                increasing=dict(color=COLORES["success"]),
                decreasing=dict(color=COLORES["secondary"]),
            ) if delta is not None else None,
            number=dict(
                valueformat=",",
                font=dict(size=40, color=COLORES["dark_blue"]),
            ),
        ))

        fig.update_layout(
            height=height,
            width=width,
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        return fig
