"""
Réinscription Page
====================
Prepares the next academic year by allowing selection of current
students and generating re-inscription records that preserve all
information while updating the school year.
"""

import customtkinter as ctk
from tkinter import ttk

from utils.theme import COLORS, font_title, font_subtitle, font_body, font_button
from models.student import Student
from database.db_manager import DatabaseManager
from views.widgets import ConfirmDialog, ToastNotification, LoadingSpinner


class ReinscriptionPage(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=("#F8FAFC", "#0F172A"), **kwargs)

        self.db = DatabaseManager()
        self.current_year = self.db.get_setting("current_school_year", "2025/2026")
        self.next_year = self.db.get_setting("next_school_year", "2026/2027")

        self.search_var = ctk.StringVar()
        self.selected_ids = set()
        self.all_students = []

        self._build_header()
        self._build_stats()
        self._build_toolbar()
        self._build_table()
        self._build_action_bar()

        self.refresh()

    # ------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 5))
        ctk.CTkLabel(header, text="🔄 Réinscription", font=font_title()).pack(side="left")

        ctk.CTkLabel(
            header, text=f"{self.current_year}  →  {self.next_year}",
            font=font_subtitle(), text_color=COLORS["primary"],
        ).pack(side="right")

    def _build_stats(self):
        stats_frame = ctk.CTkFrame(
            self, fg_color=("white", COLORS["card_dark"]), corner_radius=12,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        stats_frame.pack(fill="x", padx=25, pady=10)

        inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        for i in range(3):
            inner.grid_columnconfigure(i, weight=1)

        self.eligible_label = self._stat_widget(inner, "Total éligibles", "0", COLORS["primary"], 0)
        self.selected_label = self._stat_widget(inner, "Sélectionnés", "0", COLORS["warning"], 1)
        self.reinscribed_label = self._stat_widget(inner, "Déjà réinscrits", "0", COLORS["success"], 2)

    def _stat_widget(self, parent, title, value, color, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, sticky="ew", padx=10)

        value_label = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=26, weight="bold"), text_color=color)
        value_label.pack(anchor="w")
        ctk.CTkLabel(frame, text=title, font=font_body(), text_color=("#64748B", "#94A3B8")).pack(anchor="w")
        return value_label

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(
            self, fg_color=("white", COLORS["card_dark"]), corner_radius=12,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        toolbar.pack(fill="x", padx=25, pady=(0, 10))

        inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)

        self.search_entry = ctk.CTkEntry(
            inner, placeholder_text="🔍 Rechercher un élève...",
            textvariable=self.search_var, width=300, font=font_body(),
        )
        self.search_entry.pack(side="left", padx=(0, 12))
        self.search_var.trace_add("write", lambda *a: self.refresh())

        ctk.CTkButton(
            inner, text="☑️ Sélectionner tout", font=font_button(),
            fg_color=COLORS["secondary"], hover_color=COLORS["primary_hover"],
            command=self._select_all,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            inner, text="☐ Désélectionner tout", font=font_button(),
            fg_color="gray", hover_color="#475569",
            command=self._deselect_all,
        ).pack(side="left", padx=6)

    def _build_table(self):
        table_card = ctk.CTkFrame(
            self, fg_color=("white", COLORS["card_dark"]), corner_radius=12,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        table_card.pack(fill="both", expand=True, padx=25, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Reins.Treeview", background="#FFFFFF", foreground="#1E293B",
            rowheight=32, fieldbackground="#FFFFFF", borderwidth=0, font=("Segoe UI", 10),
        )
        style.configure(
            "Reins.Treeview.Heading", background="#2563EB", foreground="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
        )

        tree_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=12, pady=12)

        columns = ["select", "matricule", "eleve_nom", "eleve_prenom", "classe", "mensualite"]
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            style="Reins.Treeview", selectmode="none",
        )

        headers = {
            "select": ("✓", 50),
            "matricule": ("Matricule", 100),
            "eleve_nom": ("Nom", 150),
            "eleve_prenom": ("Prénom", 150),
            "classe": ("Classe", 100),
            "mensualite": ("Mensualité", 100),
        }
        for key, (label, width) in headers.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self._on_tree_click)

    def _build_action_bar(self):
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=25, pady=(0, 20))

        self.generate_btn = ctk.CTkButton(
            action_frame, text="🚀 Générer la Réinscription", font=font_button(),
            fg_color=COLORS["success"], hover_color="#16A34A", height=46,
            command=self._confirm_generate,
        )
        self.generate_btn.pack(fill="x")

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def refresh(self):
        search = self.search_var.get().strip() or None
        self.all_students = Student.get_all(
            annee_scolaire=self.current_year, search=search, statut="Actif"
        )

        for item in self.tree.get_children():
            self.tree.delete(item)

        for s in self.all_students:
            checked = "☑" if s["id"] in self.selected_ids else "☐"
            self.tree.insert(
                "", "end", iid=str(s["id"]),
                values=(checked, s["matricule"], s["eleve_nom"], s["eleve_prenom"],
                        s["classe"], f"{s.get('mensualite', 0):.0f}")
            )

        self._update_stats()

    def _update_stats(self):
        eligible = Student.count_all(annee_scolaire=self.current_year, statut="Actif")
        reinscribed = Student.count_all(annee_scolaire=self.next_year)

        self.eligible_label.configure(text=str(eligible))
        self.selected_label.configure(text=str(len(self.selected_ids)))
        self.reinscribed_label.configure(text=str(reinscribed))

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------
    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item or column != "#1":
            return

        student_id = int(item)
        if student_id in self.selected_ids:
            self.selected_ids.remove(student_id)
        else:
            self.selected_ids.add(student_id)

        checked = "☑" if student_id in self.selected_ids else "☐"
        values = list(self.tree.item(item, "values"))
        values[0] = checked
        self.tree.item(item, values=values)
        self._update_stats()

    def _select_all(self):
        for s in self.all_students:
            self.selected_ids.add(s["id"])
        self.refresh()

    def _deselect_all(self):
        self.selected_ids.clear()
        self.refresh()

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def _confirm_generate(self):
        if not self.selected_ids:
            ToastNotification(self, message="Veuillez sélectionner au moins un élève.", success=False)
            return

        ConfirmDialog(
            self, title="Générer la réinscription",
            message=f"Confirmer la réinscription de {len(self.selected_ids)} élève(s) "
                    f"pour l'année {self.next_year} ?",
            on_confirm=self._generate,
        )

    def _generate(self):
        spinner = LoadingSpinner(self, "Génération en cours...")
        self.update_idletasks()

        created = 0
        skipped = 0
        try:
            for student_id in list(self.selected_ids):
                student = Student.get_by_id(student_id)
                if not student:
                    continue

                # Check if already re-inscribed
                existing = Student.get_by_matricule(student["matricule"], self.next_year)
                if existing:
                    skipped += 1
                    continue

                new_data = dict(student)
                new_data.pop("id", None)
                new_data["annee_scolaire"] = self.next_year
                new_data["statut"] = "Actif"
                Student.create(new_data)
                created += 1

            spinner.close()
            self.selected_ids.clear()
            self.refresh()
            ToastNotification(
                self,
                message=f"{created} élève(s) réinscrit(s), {skipped} déjà existant(s).",
                success=True,
            )
        except Exception as e:
            spinner.close()
            ToastNotification(self, message=f"Erreur: {e}", success=False)
