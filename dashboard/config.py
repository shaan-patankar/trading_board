from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

STRATEGY_FILES = {
    "Momentum": DATA_DIR / "momentum_pnls.csv",
    "Mean Reversion": DATA_DIR / "mean_reversion_pnls.csv",
    "Carry": DATA_DIR / "carry_pnls.csv",
    "Machine Learning": DATA_DIR / "machine_learning_pnls.csv",
    "Short Strangle": DATA_DIR / "short_strangle_pnls.csv",
    "Sprite Pepsi": DATA_DIR / "pepsi_coke.csv",
}

GRAPH_CONFIG = {
    "scrollZoom": True,
    "responsive": True,
    "displaylogo": False,
    "displayModeBar": False,
    "doubleClick": "reset",
    "showTips": True,
}
RANGE_OPTIONS = ["1M", "3M", "YTD", "1Y", "All"]
LAYOUT_OPTIONS = [
    {"label": "Default", "value": "default"},
    {"label": "Focused", "value": "focused"},
    {"label": "Analytics", "value": "analytics"},
]
PANEL_KEYS = ["equity", "custom", "drawdown", "metrics"]
SETTINGS_GEAR_SVG = "data:image/svg+xml;utf8," + quote(
    """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
    stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"
    xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
</svg>
""".strip()
)

BASE_FONT = {
    "family": "Inter, 'Segoe UI', system-ui",
    "color": "#e6e9f0",
}
BASE_BACKGROUND = "rgba(0,0,0,0)"
BASE_HOVERLABEL = {
    "bgcolor": "#151c2c",
    "bordercolor": "#6f7c95",
    "font": {"color": "#e6e9f0", "size": 12, "family": "Inter, 'Segoe UI', system-ui"},
}
LIGHT_FONT = {
    "family": "Inter, 'Segoe UI', system-ui",
    "color": "#1f2a3a",
}
LIGHT_HOVERLABEL = {
    "bgcolor": "#f4f7fb",
    "bordercolor": "#c2cede",
    "font": {"color": "#1f2a3a", "size": 12, "family": "Inter, 'Segoe UI', system-ui"},
}

DEFAULT_INITIAL_CAPITAL = 100.0
DEFAULT_RF = 0.0
DEFAULT_ROLL_WINDOW = 63
