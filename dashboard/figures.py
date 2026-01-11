from __future__ import annotations

import math
from typing import Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import hex_to_rgb

from dashboard.analytics import (
    SeriesPack,
    annualize_factor_from_dates,
    compute_series,
    padded_date_range,
)
from dashboard.config import BASE_BACKGROUND, BASE_FONT, BASE_HOVERLABEL
from dashboard.utils import format_product_label


def base_layout_kwargs(
    title: str, margin: dict, *, include_legend: bool = True, hovermode: str = "x unified"
) -> dict:
    layout = {
        "template": "plotly_dark",
        "title": title,
        "margin": margin,
        "hovermode": hovermode,
        "dragmode": "zoom",
        "hoverlabel": BASE_HOVERLABEL,
        "paper_bgcolor": BASE_BACKGROUND,
        "plot_bgcolor": BASE_BACKGROUND,
        "font": BASE_FONT,
    }
    if include_legend:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    return layout


def color_map(labels: List[str]) -> Dict[str, str]:
    palette = px.colors.qualitative.Plotly
    return {label: palette[idx % len(palette)] for idx, label in enumerate(labels)}


def with_alpha(hex_color: str, alpha: float) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


def equity_figure(
    series_by_label: Dict[str, SeriesPack],
    title: str,
    drawdown_series: Dict[str, SeriesPack] | None = None,
) -> go.Figure:
    fig = go.Figure()

    color_map_by_label = color_map(list(series_by_label.keys()))

    for label, sp in series_by_label.items():
        color = color_map_by_label[label]
        fig.add_trace(
            go.Scatter(
                x=sp.dates,
                y=sp.equity,
                mode="lines",
                name=f"{label} Equity",
                hovertemplate="Equity: %{y:,.2f}<extra></extra>",
                line=dict(color=color, simplify=False),
                hoverlabel=dict(bgcolor=color, bordercolor=color),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=sp.dates,
                y=sp.hwm,
                mode="lines",
                name=f"{label} High Watermark",
                hovertemplate="HWM: %{y:,.2f}<extra></extra>",
                line=dict(width=1, dash="dot", color=color, simplify=False),
                hoverlabel=dict(bgcolor=color, bordercolor=color),
            )
        )

    if drawdown_series:
        for label, sp in drawdown_series.items():
            color = color_map_by_label.get(label) or color_map([label])[label]
            fig.add_trace(
                go.Scatter(
                    x=sp.dates,
                    y=sp.drawdown,
                    mode="lines",
                    name=f"{label} Drawdown",
                    fill="tozeroy",
                    hovertemplate="DD: %{y:.2%}<extra></extra>",
                    line=dict(color=color, width=1, simplify=False),
                    fillcolor=with_alpha(color, 0.16),
                    hoverlabel=dict(bgcolor=color, bordercolor=color),
                    yaxis="y2",
                )
            )

    fig.update_layout(**base_layout_kwargs(title, margin=dict(l=14, r=14, t=40, b=22)))
    fig.update_xaxes(showgrid=False, showspikes=False, hoverformat="%Y-%m-%d")
    fig.update_yaxes(title="Equity", tickformat=",.0f")
    if drawdown_series:
        fig.update_layout(
            yaxis2=dict(
                title="Drawdown",
                tickformat=".0%",
                overlaying="y",
                side="right",
                showgrid=False,
                zeroline=False,
            )
        )
    return fig


def drawdown_figure(series_by_label: Dict[str, SeriesPack], title: str) -> go.Figure:
    fig = go.Figure()

    color_map_by_label = color_map(list(series_by_label.keys()))

    for label, sp in series_by_label.items():
        color = color_map_by_label[label]
        fig.add_trace(
            go.Scatter(
                x=sp.dates,
                y=sp.drawdown,
                mode="lines",
                name=f"{label} Drawdown",
                fill="tozeroy",
                hovertemplate="DD: %{y:.2%}<extra></extra>",
                line=dict(color=color, simplify=False),
                fillcolor=with_alpha(color, 0.2),
                hoverlabel=dict(bgcolor=color, bordercolor=color),
            )
        )

    fig.update_layout(
        **base_layout_kwargs(title, margin=dict(l=14, r=14, t=40, b=22)),
        yaxis=dict(title="Drawdown", tickformat=".0%"),
    )
    fig.update_xaxes(showgrid=False, showspikes=False, hoverformat="%Y-%m-%d")
    return fig


def rolling_correlation_figure(
    df: pd.DataFrame,
    products: List[str],
    window: int,
    title: str,
) -> go.Figure:
    fig = go.Figure()

    if len(products) < 2:
        fig.update_layout(
            **base_layout_kwargs(title, margin=dict(l=18, r=18, t=48, b=56)),
        )
        return fig

    returns_by_product = {}
    for p in products:
        sp = compute_series(df, [p])
        returns_by_product[p] = sp.returns

    returns_df = pd.DataFrame(returns_by_product)
    dates = pd.to_datetime(df["date"])

    corr_labels = []
    for i, p1 in enumerate(products):
        for p2 in products[i + 1 :]:
            corr_labels.append(f"{format_product_label(p1)} vs {format_product_label(p2)}")

    color_map_by_label = color_map(corr_labels)

    for i, p1 in enumerate(products):
        for p2 in products[i + 1 :]:
            roll_corr = returns_df[p1].rolling(window).corr(returns_df[p2])
            label = f"{format_product_label(p1)} vs {format_product_label(p2)}"
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=roll_corr,
                    mode="lines",
                    name=label,
                    hovertemplate="Roll Corr: %{y:.2f}<extra></extra>",
                    line=dict(color=color_map_by_label[label], simplify=False),
                    hoverlabel=dict(bgcolor=color_map_by_label[label], bordercolor=color_map_by_label[label]),
                )
            )

    fig.update_layout(
        **base_layout_kwargs(title, margin=dict(l=18, r=18, t=48, b=56)),
    )
    padded_range = padded_date_range(df["date"])
    fig.update_yaxes(title="Rolling Corr", range=[-1, 1])
    xaxis_kwargs = dict(showgrid=False, showspikes=False, hoverformat="%Y-%m-%d")
    if padded_range is not None:
        xaxis_kwargs["range"] = padded_range
    fig.update_xaxes(**xaxis_kwargs)
    return fig


def rolling_sharpe_figure(
    df: pd.DataFrame,
    products: List[str],
    window: int,
    title: str,
    *,
    include_individuals: bool = True,
    include_aggregate: bool = True,
) -> go.Figure:
    fig = go.Figure()
    ann = annualize_factor_from_dates(df["date"])

    label_order: List[str] = []
    if include_individuals:
        label_order.extend([format_product_label(p) for p in products])
    if include_aggregate and len(products) >= 1:
        label_order.append("ALL (agg)")

    color_map_by_label = color_map(label_order)
    if include_individuals:
        for p in products:
            sp = compute_series(df, [p])
            r = sp.returns
            roll = (r.rolling(window).mean() / (r.rolling(window).std(ddof=1) + 1e-12)) * math.sqrt(ann)
            fig.add_trace(
                go.Scatter(
                    x=sp.dates,
                    y=roll,
                    mode="lines",
                    name=format_product_label(p),
                    hovertemplate="Roll Sharpe: %{y:.2f}<extra></extra>",
                    line=dict(color=color_map_by_label[format_product_label(p)], simplify=False),
                    hoverlabel=dict(
                        bgcolor=color_map_by_label[format_product_label(p)],
                        bordercolor=color_map_by_label[format_product_label(p)],
                    ),
                )
            )

    if include_aggregate and len(products) >= 1:
        sp_all = compute_series(df, products)
        r = sp_all.returns
        roll = (r.rolling(window).mean() / (r.rolling(window).std(ddof=1) + 1e-12)) * math.sqrt(ann)
        fig.add_trace(
            go.Scatter(
                x=sp_all.dates,
                y=roll,
                mode="lines",
                name="ALL (agg)",
                line=dict(width=2, color=color_map_by_label.get("ALL (agg)"), simplify=False),
                hovertemplate="Roll Sharpe: %{y:.2f}<extra></extra>",
                hoverlabel=dict(
                    bgcolor=color_map_by_label.get("ALL (agg)"),
                    bordercolor=color_map_by_label.get("ALL (agg)"),
                ),
            )
        )

    fig.update_layout(
        **base_layout_kwargs(title, margin=dict(l=18, r=18, t=48, b=56)),
    )
    padded_range = padded_date_range(df["date"])
    xaxis_kwargs = dict(showgrid=False, showspikes=False, hoverformat="%Y-%m-%d")
    if padded_range is not None:
        xaxis_kwargs["range"] = padded_range
    fig.update_xaxes(**xaxis_kwargs)
    fig.update_yaxes(title="Sharpe")
    return fig


def seasonality_figure(
    df: pd.DataFrame,
    products: List[str],
    title: str,
) -> go.Figure:
    valid_products = [p for p in products if p in df.columns and p != "date"]
    if len(valid_products) == 0:
        valid_products = [c for c in df.columns if c != "date"]

    tmp = df[["date"] + valid_products].copy()
    tmp["date"] = pd.to_datetime(tmp["date"])
    pnl = tmp[valid_products].sum(axis=1)
    equity = pnl.cumsum()
    eq_series = pd.Series(equity.values, index=tmp["date"])
    monthly_eq = eq_series.resample("M").last()
    monthly_returns = monthly_eq.replace(0, pd.NA).pct_change().dropna()

    heatmap_df = monthly_returns.to_frame(name="ret")
    heatmap_df["year"] = heatmap_df.index.year
    heatmap_df["month"] = heatmap_df.index.month
    pivot = heatmap_df.pivot(index="year", columns="month", values="ret").sort_index()
    pivot = pivot.reindex(columns=range(1, 13))

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            y=pivot.index,
            colorscale=[[0, "#6b0f1a"], [0.5, "#1b1f2a"], [1.0, "#2ed47a"]],
            zmid=0,
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Return: %{z:.2%}<extra></extra>",
            colorbar=dict(
                thickness=8,
                len=0.82,
                y=0.5,
                yanchor="middle",
                x=1.02,
                xanchor="left",
                tickfont=dict(color="#e6e6e6", size=10),
                outlinewidth=0,
            ),
        )
    )
    fig.update_layout(
        **base_layout_kwargs(title, margin=dict(l=28, r=28, t=40, b=40), hovermode="closest"),
    )
    fig.update_xaxes(title=None, constrain="domain", automargin=True)
    fig.update_yaxes(title=None, scaleanchor="x", scaleratio=1, automargin=True)
    return fig


def placeholder_figure(title: str, subtitle: str | None = None) -> go.Figure:
    fig = go.Figure()
    subtitle_html = f"<br><span style='font-size:12px; color:#9ca8b8;'>{subtitle}</span>" if subtitle else ""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_visible=False,
        yaxis_visible=False,
        annotations=[
            dict(
                text=f"<b>{title}</b>{subtitle_html}",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                align="center",
                font=dict(color="#e6e6e6", size=14),
            )
        ],
        margin=dict(l=14, r=14, t=40, b=22),
    )
    return fig
