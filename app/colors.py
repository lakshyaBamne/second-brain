"""Validated categorical/status palette (see dataviz skill references/palette.md).
Colors are assigned by slot order, never hand-picked, so new life aspects stay
CVD-safe automatically.
"""

CATEGORICAL = [
    {"hue": "blue", "light": "#2a78d6", "dark": "#3987e5"},
    {"hue": "orange", "light": "#eb6834", "dark": "#d95926"},
    {"hue": "aqua", "light": "#1baf7a", "dark": "#199e70"},
    {"hue": "yellow", "light": "#eda100", "dark": "#c98500"},
    {"hue": "magenta", "light": "#e87ba4", "dark": "#d55181"},
    {"hue": "green", "light": "#008300", "dark": "#008300"},
    {"hue": "violet", "light": "#4a3aa7", "dark": "#9085e9"},
    {"hue": "red", "light": "#e34948", "dark": "#e66767"},
]

STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

CHROME = {
    "surface_light": "#fcfcfb",
    "surface_dark": "#1a1a19",
    "ink_primary_light": "#0b0b0b",
    "ink_primary_dark": "#ffffff",
    "ink_secondary_light": "#52514e",
    "ink_secondary_dark": "#c3c2b7",
    "ink_muted": "#898781",
    "gridline_light": "#e1e0d9",
    "gridline_dark": "#2c2c2a",
    "baseline_light": "#c3c2b7",
    "baseline_dark": "#383835",
}


def slot_for_order(order: int) -> dict:
    """Deterministic categorical slot for the Nth (0-indexed) life aspect."""
    return CATEGORICAL[order % len(CATEGORICAL)]
