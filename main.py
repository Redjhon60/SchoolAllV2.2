"""
Main Application Window
========================
Sets up the root window, sidebar navigation, and page container.
Handles routing between Dashboard, Gestion Élèves, Nouvelle
Inscription, Réinscription and Settings pages.
"""

import customtkinter as ctk

from views.sidebar import Sidebar
from views.dashboard_page import DashboardPage
from views.gestion_eleves_page import GestionElevesPage
from views.nouvelle_inscription_page import NouvelleInscriptionPage
from views.reinscription_page import ReinscriptionPage
from views.gestion_paiements_page import GestionPaiementsPage
from views.settings_page import SettingsPage
from database.db_manager import DatabaseManager


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Le Schéma SGS - Gestion Scolaire")
        self.geometry("1400x850")
        self.minsize(1100, 700)

        # Apply saved theme
        db = DatabaseManager()
        theme = db.get_setting("theme", "Light")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

        # Root layout: sidebar + content
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self.current_page_key = None

        self._init_pages()
        self.navigate("dashboard")

    def _init_pages(self):
        self.pages["dashboard"] = DashboardPage(self.content_container)
        self.pages["eleves"] = GestionElevesPage(self.content_container)
        self.pages["inscription"] = NouvelleInscriptionPage(self.content_container)
        self.pages["reinscription"] = ReinscriptionPage(self.content_container)
        self.pages["paiements"] = GestionPaiementsPage(self.content_container)
        self.pages["settings"] = SettingsPage(self.content_container, on_theme_change=self._on_theme_change)

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def navigate(self, page_key):
        if page_key not in self.pages:
            return

        page = self.pages[page_key]
        page.tkraise()
        self.current_page_key = page_key

        # Refresh data-driven pages when navigated to
        if page_key == "dashboard":
            page.refresh()
        elif page_key == "eleves":
            page.refresh()
        elif page_key == "reinscription":
            page.refresh()
        elif page_key == "paiements":
            page.refresh()
        elif page_key == "inscription":
            page._reset()

        self.sidebar.set_active(page_key)

    def _on_theme_change(self, theme):
        # Re-render charts on dashboard with new theme colors
        if "dashboard" in self.pages:
            self.pages["dashboard"].refresh()


if __name__ == "__main__":
    app = App()
    app.mainloop()
