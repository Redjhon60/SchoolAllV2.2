"""
Theme & Style Configuration
===========================
Centralized color palette, fonts and style constants used
throughout the UI, inspired by modern ERP dashboards.
"""

import customtkinter as ctk

# ----------------------------------------------------------------------
# Color Palette
# ----------------------------------------------------------------------
COLORS = {
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "secondary": "#3B82F6",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "background_light": "#F8FAFC",
    "background_dark": "#0F172A",
    "card_light": "#FFFFFF",
    "card_dark": "#1E293B",
    "text_light": "#1E293B",
    "text_dark": "#F1F5F9",
    "muted_light": "#64748B",
    "muted_dark": "#94A3B8",
    "border_light": "#E2E8F0",
    "border_dark": "#334155",
    "sidebar_light": "#1E293B",
    "sidebar_dark": "#0F172A",
    "sidebar_active": "#2563EB",
    "sidebar_text": "#CBD5E1",
}

# Chart color sequence
CHART_COLORS = ["#2563EB", "#3B82F6", "#22C55E", "#F59E0B", "#EF4444",
                "#8B5CF6", "#EC4899", "#14B8A6", "#F97316", "#6366F1"]

# ----------------------------------------------------------------------
# Fonts
# ----------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"


def font_title():
    return ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold")


def font_subtitle():
    return ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold")


def font_body():
    return ctk.CTkFont(family=FONT_FAMILY, size=13)


def font_small():
    return ctk.CTkFont(family=FONT_FAMILY, size=11)


def font_kpi_value():
    return ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold")


def font_kpi_label():
    return ctk.CTkFont(family=FONT_FAMILY, size=12)


def font_button():
    return ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")


# ----------------------------------------------------------------------
# Layout constants
# ----------------------------------------------------------------------
SIDEBAR_WIDTH_EXPANDED = 220
SIDEBAR_WIDTH_COLLAPSED = 70
CARD_CORNER_RADIUS = 14
BUTTON_CORNER_RADIUS = 8


def get_color(name: str):
    """Return color hex appropriate for current appearance mode."""
    mode = ctk.get_appearance_mode()  # "Light" or "Dark"
    light_dark_map = {
        "background": (COLORS["background_light"], COLORS["background_dark"]),
        "card": (COLORS["card_light"], COLORS["card_dark"]),
        "text": (COLORS["text_light"], COLORS["text_dark"]),
        "muted": (COLORS["muted_light"], COLORS["muted_dark"]),
        "border": (COLORS["border_light"], COLORS["border_dark"]),
    }
    if name in light_dark_map:
        light, dark = light_dark_map[name]
        return light if mode == "Light" else dark
    return COLORS.get(name, "#000000")
