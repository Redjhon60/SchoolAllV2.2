"""
Sidebar Component
==================
A collapsible animated sidebar with navigation menu and
active page highlighting.
"""

import customtkinter as ctk
from utils.theme import COLORS, font_subtitle, font_body, SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED


class Sidebar(ctk.CTkFrame):
    """
    Collapsible sidebar. Calls `on_navigate(page_key)` when a menu
    item is clicked, and `on_toggle(is_collapsed)` when toggled.
    """

    MENU_ITEMS = [
        ("dashboard", "🏠", "Dashboard"),
        ("eleves", "🎓", "Gestion Élèves"),
        ("inscription", "📝", "Nouvelle Inscription"),
        ("reinscription", "🔄", "Réinscription"),
        ("paiements", "💰", "Gestion des Paiements"),
        ("settings", "⚙️", "Paramètres"),
    ]

    def __init__(self, master, on_navigate, on_toggle=None, **kwargs):
        super().__init__(
            master,
            width=SIDEBAR_WIDTH_EXPANDED,
            corner_radius=0,
            fg_color=COLORS["sidebar_light"],
            **kwargs,
        )
        self.on_navigate = on_navigate
        self.on_toggle = on_toggle
        self.collapsed = False
        self.active_page = "dashboard"
        self.menu_buttons = {}
        self._animation_steps = 8
        self._animating = False

        self.grid_propagate(False)
        self.pack_propagate(False)

        self._build_header()
        self._build_menu()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=70)
        self.header_frame.pack(fill="x", padx=10, pady=(15, 10))

        self.logo_label = ctk.CTkLabel(
            self.header_frame, text="🏫  Le Schéma SGS",
            font=font_subtitle(), text_color="white", anchor="w",
        )
        self.logo_label.pack(side="left", padx=5)

        self.toggle_btn = ctk.CTkButton(
            self.header_frame, text="☰", width=32, height=32,
            fg_color="transparent", hover_color=COLORS["sidebar_active"],
            command=self.toggle, font=font_subtitle(),
        )
        self.toggle_btn.pack(side="right")

    def _build_menu(self):
        self.menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.menu_frame.pack(fill="both", expand=True, padx=8, pady=5)

        for key, icon, label in self.MENU_ITEMS:
            btn = ctk.CTkButton(
                self.menu_frame,
                text=f"  {icon}   {label}",
                anchor="w",
                height=44,
                corner_radius=8,
                fg_color="transparent",
                hover_color=COLORS["primary_hover"],
                text_color=COLORS["sidebar_text"],
                font=font_body(),
                command=lambda k=key: self._handle_click(k),
            )
            btn.pack(fill="x", pady=3)
            self.menu_buttons[key] = (btn, icon, label)

        self.set_active("dashboard")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _handle_click(self, key):
        self.set_active(key)
        if self.on_navigate:
            self.on_navigate(key)

    def set_active(self, key):
        """Highlight the active page in the sidebar."""
        self.active_page = key
        for k, (btn, icon, label) in self.menu_buttons.items():
            if k == key:
                btn.configure(fg_color=COLORS["sidebar_active"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["sidebar_text"])

    # ------------------------------------------------------------------
    # Collapse / Expand animation
    # ------------------------------------------------------------------
    def toggle(self):
        if self._animating:
            return
        self._animating = True
        if self.collapsed:
            self._animate_width(SIDEBAR_WIDTH_COLLAPSED, SIDEBAR_WIDTH_EXPANDED)
        else:
            self._animate_width(SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED)
        self.collapsed = not self.collapsed

    def _animate_width(self, start, end):
        step = (end - start) / self._animation_steps
        widths = [int(start + step * i) for i in range(1, self._animation_steps + 1)]
        widths[-1] = end
        self._do_animation_step(widths, 0, end)

    def _do_animation_step(self, widths, index, final_width):
        if index >= len(widths):
            self._animating = False
            self._on_animation_complete(final_width)
            return
        w = widths[index]
        self.configure(width=w)
        self.after(12, lambda: self._do_animation_step(widths, index + 1, final_width))

    def _on_animation_complete(self, final_width):
        is_collapsed = final_width == SIDEBAR_WIDTH_COLLAPSED
        # Update labels/visibility for collapsed state
        if is_collapsed:
            self.logo_label.configure(text="🏫")
            for k, (btn, icon, label) in self.menu_buttons.items():
                btn.configure(text=f" {icon}")
        else:
            self.logo_label.configure(text="🏫  Le Schéma SGS")
            for k, (btn, icon, label) in self.menu_buttons.items():
                btn.configure(text=f"  {icon}   {label}")

        if self.on_toggle:
            self.on_toggle(is_collapsed)
