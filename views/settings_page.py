"""
Settings Page
=============
App configuration: theme (dark/light), school name, school year
configuration, database backup.
"""

import customtkinter as ctk

from utils.theme import COLORS, font_title, font_subtitle, font_body, font_button
from database.db_manager import DatabaseManager
from views.widgets import ToastNotification, ConfirmDialog


class SettingsPage(ctk.CTkFrame):

    def __init__(self, master, on_theme_change=None, **kwargs):
        super().__init__(master, fg_color=("#F8FAFC", "#0F172A"), **kwargs)

        self.db = DatabaseManager()
        self.on_theme_change = on_theme_change

        self._build_header()
        self._build_general_settings()
        self._build_school_year_settings()
        self._build_backup_section()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 5))
        ctk.CTkLabel(header, text="⚙️ Paramètres", font=font_title()).pack(side="left")

    def _section_card(self, title):
        card = ctk.CTkFrame(
            self, fg_color=("white", COLORS["card_dark"]), corner_radius=14,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        card.pack(fill="x", padx=25, pady=10)
        ctk.CTkLabel(card, text=title, font=font_subtitle()).pack(anchor="w", padx=20, pady=(15, 10))
        return card

    # ------------------------------------------------------------------
    def _build_general_settings(self):
        card = self._section_card("Général")

        # School name
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(row, text="Nom de l'école", font=font_body(), width=200, anchor="w").pack(side="left")
        self.school_name_entry = ctk.CTkEntry(row, font=font_body(), width=300)
        self.school_name_entry.insert(0, self.db.get_setting("school_name", "Ecole Privee"))
        self.school_name_entry.pack(side="left", padx=10)

        # Theme switch
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(row2, text="Apparence", font=font_body(), width=200, anchor="w").pack(side="left")

        current_theme = self.db.get_setting("theme", "Light")
        self.theme_switch = ctk.CTkSegmentedButton(
            row2, values=["Light", "Dark"], command=self._on_theme_change,
        )
        self.theme_switch.set(current_theme)
        self.theme_switch.pack(side="left", padx=10)

        # Save general
        ctk.CTkButton(
            card, text="💾 Enregistrer", font=font_button(),
            fg_color=COLORS["success"], hover_color="#16A34A",
            command=self._save_general, width=150,
        ).pack(anchor="w", padx=20, pady=(8, 18))

    def _on_theme_change(self, value):
        ctk.set_appearance_mode(value)
        self.db.set_setting("theme", value)
        if self.on_theme_change:
            self.on_theme_change(value)

    def _save_general(self):
        self.db.set_setting("school_name", self.school_name_entry.get().strip())
        ToastNotification(self, message="Paramètres généraux enregistrés.", success=True)

    # ------------------------------------------------------------------
    def _build_school_year_settings(self):
        card = self._section_card("Année scolaire")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(row, text="Année actuelle", font=font_body(), width=200, anchor="w").pack(side="left")
        self.current_year_entry = ctk.CTkEntry(row, font=font_body(), width=150)
        self.current_year_entry.insert(0, self.db.get_setting("current_school_year", "2025/2026"))
        self.current_year_entry.pack(side="left", padx=10)

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(row2, text="Année suivante", font=font_body(), width=200, anchor="w").pack(side="left")
        self.next_year_entry = ctk.CTkEntry(row2, font=font_body(), width=150)
        self.next_year_entry.insert(0, self.db.get_setting("next_school_year", "2026/2027"))
        self.next_year_entry.pack(side="left", padx=10)

        ctk.CTkButton(
            card, text="💾 Enregistrer", font=font_button(),
            fg_color=COLORS["success"], hover_color="#16A34A",
            command=self._save_years, width=150,
        ).pack(anchor="w", padx=20, pady=(8, 18))

    def _save_years(self):
        self.db.set_setting("current_school_year", self.current_year_entry.get().strip())
        self.db.set_setting("next_school_year", self.next_year_entry.get().strip())
        ToastNotification(
            self, message="Années scolaires mises à jour. Redémarrez l'application pour appliquer partout.",
            success=True,
        )

    # ------------------------------------------------------------------
    def _build_backup_section(self):
        card = self._section_card("Sauvegarde de la base de données")

        ctk.CTkLabel(
            card, text="Créez une copie de sauvegarde de la base de données locale.",
            font=font_body(), text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkButton(
            card, text="💼 Créer une sauvegarde maintenant", font=font_button(),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._do_backup, width=250,
        ).pack(anchor="w", padx=20, pady=(0, 18))

    def _do_backup(self):
        try:
            path = self.db.backup_database()
            ToastNotification(self, message=f"Sauvegarde créée: {path}", success=True)
        except Exception as e:
            ToastNotification(self, message=f"Erreur de sauvegarde: {e}", success=False)
