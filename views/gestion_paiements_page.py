"""
Gestion des Paiements Page
============================
Professional table view of all payment students (same UX as
Gestion des Élèves): search, multi-filter, sorting, pagination,
Excel import, and row click to open a detail popup with full
payment management.
"""

import customtkinter as ctk
from tkinter import ttk, filedialog
import os

from utils.theme import COLORS, font_title, font_body, font_subtitle, font_button
from models.payment_student import PaymentStudent
from database.db_manager import DatabaseManager
from views.widgets import ToastNotification, LoadingSpinner
from views.payment_student_detail_dialog import PaymentStudentDetailDialog


PAGE_SIZE = 15

TABLE_COLUMNS = [
    ("matricule", "Matricule", 90),
    ("nom", "Nom", 120),
    ("prenom", "Prénom", 120),
    ("classe", "Classe", 80),
    ("mensualite", "Mensualité", 90),
    ("total_paye", "Total Payé", 90),
    ("prochain_mois", "Prochain Mois", 110),
]


class GestionPaiementsPage(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=("#F8FAFC", "#0F172A"), **kwargs)

        self.db = DatabaseManager()
        self.current_year = self.db.get_setting("current_school_year", "2025/2026")

        self.search_var = ctk.StringVar()
        self.class_filter_var = ctk.StringVar(value="Toutes")
        self.year_filter_var = ctk.StringVar(value=self.current_year)
        self.status_filter_var = ctk.StringVar(value="Tous")

        self.current_page = 1
        self.all_rows = []
        self.sort_column = "nom"
        self.sort_reverse = False

        self._build_header()
        self._build_toolbar()
        self._build_table()
        self._build_pagination()

        self.refresh()

    # ------------------------------------------------------------------
    # Header & Toolbar
    # ------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 5))
        ctk.CTkLabel(header, text="💰 Gestion des Paiements", font=font_title()).pack(side="left")

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(
            self, fg_color=("white", COLORS["card_dark"]), corner_radius=12,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        toolbar.pack(fill="x", padx=25, pady=10)

        row1 = ctk.CTkFrame(toolbar, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(12, 6))

        # Search
        self.search_entry = ctk.CTkEntry(
            row1, placeholder_text="🔍 Rechercher par nom, prénom, matricule, classe...",
            textvariable=self.search_var, width=320, font=font_body(),
        )
        self.search_entry.pack(side="left", padx=(0, 12))
        self.search_var.trace_add("write", lambda *a: self._on_filter_change())

        # Year filter
        years = [self.current_year, self.db.get_setting("next_school_year", "2026/2027")]
        ctk.CTkOptionMenu(
            row1, values=years, variable=self.year_filter_var,
            command=lambda v: self._on_filter_change(), width=120,
            fg_color=COLORS["primary"], button_color=COLORS["primary_hover"],
        ).pack(side="left", padx=6)

        # Class filter
        self.class_menu = ctk.CTkOptionMenu(
            row1, values=["Toutes"], variable=self.class_filter_var,
            command=lambda v: self._on_filter_change(), width=110,
            fg_color=COLORS["primary"], button_color=COLORS["primary_hover"],
        )
        self.class_menu.pack(side="left", padx=6)

        # Payment status filter (filters by whether "next month" is due/not)
        ctk.CTkOptionMenu(
            row1, values=["Tous", "En retard", "À jour"], variable=self.status_filter_var,
            command=lambda v: self._on_filter_change(), width=110,
            fg_color=COLORS["primary"], button_color=COLORS["primary_hover"],
        ).pack(side="left", padx=6)

        # Right side: action buttons
        row2 = ctk.CTkFrame(toolbar, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkButton(
            row2, text="➕ Ajouter Paiement", font=font_button(),
            fg_color=COLORS["success"], hover_color="#16A34A",
            command=self._add_payment_shortcut, width=170,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row2, text="📥 Importer Excel", font=font_button(),
            fg_color=COLORS["secondary"], hover_color=COLORS["primary_hover"],
            command=self._import_excel, width=150,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            row2, text="🔄 Rafraîchir", font=font_button(),
            fg_color="gray", hover_color="#475569",
            command=self.refresh, width=130,
        ).pack(side="left", padx=8)

        self.count_label = ctk.CTkLabel(row2, text="", font=font_body())
        self.count_label.pack(side="right", padx=10)

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------
    def _build_table(self):
        table_card = ctk.CTkFrame(
            self, fg_color=("white", COLORS["card_dark"]), corner_radius=12,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        table_card.pack(fill="both", expand=True, padx=25, pady=10)

        # Configure ttk style for modern look
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Pay.Treeview",
            background="#FFFFFF", foreground="#1E293B", rowheight=32,
            fieldbackground="#FFFFFF", borderwidth=0, font=("Segoe UI", 10),
        )
        style.configure(
            "Pay.Treeview.Heading",
            background="#2563EB", foreground="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
        )
        style.map("Pay.Treeview.Heading", background=[("active", "#1D4ED8")])
        style.map("Pay.Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", "#1E293B")])

        tree_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=12, pady=12)

        columns = [c[0] for c in TABLE_COLUMNS] + ["actions"]
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            style="Pay.Treeview", selectmode="browse",
        )

        for key, label, width in TABLE_COLUMNS:
            self.tree.heading(key, text=label, command=lambda k=key: self._sort_by(k))
            self.tree.column(key, width=width, anchor="center")

        self.tree.heading("actions", text="Actions")
        self.tree.column("actions", width=160, anchor="center")

        # Tag colors for "next month" highlighting
        self.tree.tag_configure("a_jour", foreground=COLORS["success"])
        self.tree.tag_configure("en_retard", foreground=COLORS["danger"])

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._on_row_double_click)
        self.tree.bind("<Button-1>", self._on_tree_click)

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------
    def _build_pagination(self):
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", padx=25, pady=(0, 15))

        self.prev_btn = ctk.CTkButton(
            self.pagination_frame, text="◀ Précédent", width=110,
            fg_color=COLORS["secondary"], hover_color=COLORS["primary_hover"],
            command=self._prev_page,
        )
        self.prev_btn.pack(side="left", padx=5)

        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Page 1 / 1", font=font_body())
        self.page_label.pack(side="left", padx=15)

        self.next_btn = ctk.CTkButton(
            self.pagination_frame, text="Suivant ▶", width=110,
            fg_color=COLORS["secondary"], hover_color=COLORS["primary_hover"],
            command=self._next_page,
        )
        self.next_btn.pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # Data loading & rendering
    # ------------------------------------------------------------------
    def refresh(self):
        year = self.year_filter_var.get()
        classes = ["Toutes"] + PaymentStudent.get_distinct_classes(year)
        self.class_menu.configure(values=classes)
        if self.class_filter_var.get() not in classes:
            self.class_filter_var.set("Toutes")

        search = self.search_var.get().strip() or None
        classe = self.class_filter_var.get()

        rows = PaymentStudent.search(annee_scolaire=year, classe=classe, search=search)

        # Enrich rows with computed fields: total_paye, prochain_mois
        enriched = []
        for row in rows:
            total_paye = PaymentStudent.get_total_paid(row["id"], row["annee_scolaire"])
            next_month = PaymentStudent.get_next_unpaid_month(row["id"], row["annee_scolaire"])
            row = dict(row)
            row["total_paye"] = total_paye
            row["prochain_mois"] = next_month or "À jour"
            enriched.append(row)

        # Apply payment status filter
        status_filter = self.status_filter_var.get()
        if status_filter == "En retard":
            enriched = [r for r in enriched if r["prochain_mois"] != "À jour"]
        elif status_filter == "À jour":
            enriched = [r for r in enriched if r["prochain_mois"] == "À jour"]

        self.all_rows = enriched
        self._sort_rows()
        self.current_page = 1
        self._render_page()

    def _on_filter_change(self):
        self.refresh()

    def _sort_by(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self._sort_rows()
        self.current_page = 1
        self._render_page()

    def _sort_rows(self):
        col = self.sort_column

        def keyfunc(row):
            val = row.get(col)
            if val is None:
                return ""
            if col in ("mensualite", "total_paye"):
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return 0
            return str(val).lower()

        self.all_rows.sort(key=keyfunc, reverse=self.sort_reverse)

    def _render_page(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total = len(self.all_rows)
        total_pages = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
        if self.current_page > total_pages:
            self.current_page = total_pages

        start = (self.current_page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_rows = self.all_rows[start:end]

        for row in page_rows:
            tag = "a_jour" if row["prochain_mois"] == "À jour" else "en_retard"
            values = [
                row.get("matricule", ""),
                row.get("nom", ""),
                row.get("prenom", "") or "-",
                row.get("classe", ""),
                f"{row.get('mensualite', 0):.0f}",
                f"{row.get('total_paye', 0):.0f}",
                row.get("prochain_mois", ""),
                "👁️ Détails / Paiement",
            ]
            self.tree.insert("", "end", iid=str(row["id"]), values=values, tags=(tag,))

        self.page_label.configure(text=f"Page {self.current_page} / {total_pages}")
        self.count_label.configure(text=f"Total: {total} élève(s)")

        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_page()

    def _next_page(self):
        total_pages = max((len(self.all_rows) + PAGE_SIZE - 1) // PAGE_SIZE, 1)
        if self.current_page < total_pages:
            self.current_page += 1
            self._render_page()

    # ------------------------------------------------------------------
    # Row interactions
    # ------------------------------------------------------------------
    def _on_row_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self._open_detail(int(item))

    def _on_tree_click(self, event):
        """Clicking anywhere on a row (including the actions cell) opens the detail popup."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self._open_detail(int(item))

    def _open_detail(self, payment_student_id):
        PaymentStudentDetailDialog(self, payment_student_id, on_change=self._on_payment_change)

    def _on_payment_change(self):
        """Called after a payment is registered from the detail popup."""
        self.refresh()
        self._refresh_dashboard()

    def _add_payment_shortcut(self):
        """'Ajouter Paiement' button: opens the detail popup for the selected row,
        or guides the user to select a student first."""
        selection = self.tree.selection()
        if selection:
            self._open_detail(int(selection[0]))
        elif self.all_rows:
            ToastNotification(
                self, message="Sélectionnez un élève dans le tableau, puis cliquez sur "
                               "'Détails / Paiement' pour ajouter un paiement.",
                success=True,
            )
        else:
            ToastNotification(self, message="Aucun élève disponible. Importez d'abord vos données.", success=False)

    def _refresh_dashboard(self):
        """Attempt to refresh the dashboard page if the app exposes it."""
        try:
            app = self.winfo_toplevel()
            if hasattr(app, "pages") and "dashboard" in app.pages:
                app.pages["dashboard"].refresh()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Excel import
    # ------------------------------------------------------------------
    def _import_excel(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner le fichier Excel des paiements",
            filetypes=[("Fichiers Excel", "*.xlsx *.xls")],
        )
        if not file_path:
            return

        spinner = LoadingSpinner(self, "Importation des paiements en cours...")
        self.update_idletasks()

        try:
            from utils.payment_excel_handler import import_payments_excel
            summary = import_payments_excel(file_path, self.year_filter_var.get())
            spinner.close()

            msg = (
                f"Import terminé: {summary['students_created']} créés, "
                f"{summary['students_updated']} mis à jour, "
                f"{summary['months_set']} statuts mensuels."
            )
            if summary["errors"]:
                msg += f" {len(summary['errors'])} erreur(s)."

            ToastNotification(self, message=msg, success=len(summary["errors"]) == 0)
            self.refresh()
            self._refresh_dashboard()
        except Exception as e:
            spinner.close()
            ToastNotification(self, message=f"Erreur d'importation: {e}", success=False)
