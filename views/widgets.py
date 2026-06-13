"""
Reusable Widgets
=================
Common UI components: KPI cards, confirmation dialogs,
toast notifications, and loading spinners.
"""

import customtkinter as ctk
from utils.theme import COLORS, font_kpi_value, font_kpi_label, font_subtitle, font_body, CARD_CORNER_RADIUS


class KPICard(ctk.CTkFrame):
    """A rounded card displaying a KPI value, label and icon."""

    def __init__(self, master, title, value, icon="📊", color=None, **kwargs):
        super().__init__(
            master,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=("white", COLORS["card_dark"]),
            border_width=1,
            border_color=("#E2E8F0", COLORS["border_dark"]),
            **kwargs,
        )
        self.color = color or COLORS["primary"]

        # Top row: icon badge
        icon_frame = ctk.CTkFrame(
            self, width=46, height=46, corner_radius=10, fg_color=self.color
        )
        icon_frame.pack(anchor="w", padx=18, pady=(18, 6))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon, font=ctk.CTkFont(size=20)).place(relx=0.5, rely=0.5, anchor="center")

        # Value
        self.value_label = ctk.CTkLabel(self, text=str(value), font=font_kpi_value(), anchor="w")
        self.value_label.pack(anchor="w", padx=18, pady=(2, 0))

        # Title
        self.title_label = ctk.CTkLabel(
            self, text=title, font=font_kpi_label(), anchor="w",
            text_color=("#64748B", "#94A3B8"),
        )
        self.title_label.pack(anchor="w", padx=18, pady=(0, 18))

        # Hover effect
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        self.configure(border_color=self.color)

    def _on_leave(self, event):
        self.configure(border_color=("#E2E8F0", COLORS["border_dark"]))

    def update_value(self, value):
        self.value_label.configure(text=str(value))


class ConfirmDialog(ctk.CTkToplevel):
    """Modal confirmation dialog with Yes/No buttons."""

    def __init__(self, master, title="Confirmation", message="Êtes-vous sûr ?", on_confirm=None):
        super().__init__(master)
        self.title(title)
        self.geometry("380x180")
        self.resizable(False, False)
        self.grab_set()
        self.on_confirm = on_confirm

        self.transient(master)
        self.lift()

        ctk.CTkLabel(self, text=message, font=font_body(), wraplength=320, justify="center").pack(
            expand=True, padx=20, pady=(30, 10)
        )

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame, text="Annuler", width=110, fg_color="gray",
            command=self.destroy,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="Confirmer", width=110, fg_color=COLORS["danger"],
            hover_color="#DC2626", command=self._confirm,
        ).pack(side="left", padx=8)

        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _confirm(self):
        if self.on_confirm:
            self.on_confirm()
        self.destroy()


class ToastNotification(ctk.CTkToplevel):
    """A temporary toast notification that auto-closes after a delay."""

    def __init__(self, master, message="", success=True, duration=2200):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        color = COLORS["success"] if success else COLORS["danger"]
        icon = "✅" if success else "❌"

        frame = ctk.CTkFrame(self, fg_color=color, corner_radius=10)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            frame, text=f"{icon}  {message}", text_color="white",
            font=font_body(), padx=20, pady=14,
        ).pack()

        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        master.update_idletasks()
        x = master.winfo_x() + master.winfo_width() - width - 30
        y = master.winfo_y() + 50

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.after(duration, self.destroy)


class LoadingSpinner(ctk.CTkToplevel):
    """A simple modal loading overlay with an indeterminate progress bar."""

    def __init__(self, master, message="Chargement..."):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.grab_set()

        frame = ctk.CTkFrame(self, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(frame, text=message, font=font_subtitle()).pack(padx=40, pady=(25, 10))
        self.progress = ctk.CTkProgressBar(frame, mode="indeterminate", width=220)
        self.progress.pack(padx=40, pady=(0, 25))
        self.progress.start()

        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        master.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (width // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def close(self):
        self.progress.stop()
        self.grab_release()
        self.destroy()
