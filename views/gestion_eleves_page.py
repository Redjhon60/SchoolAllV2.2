"""
Gestion Élèves Page
====================
Professional table view of all students with search, multi-filter,
sorting, pagination, import/export, and row actions (view, edit,
delete, print).
"""

import customtkinter as ctk
from tkinter import ttk, filedialog
import os

from utils.theme import COLORS, font_title, font_body, font_subtitle, font_button
from models.student import Student
from database.db_manager import DatabaseManager
from views.widgets import ConfirmDialog, ToastNotification, LoadingSpinner
from views.student_profile_dialog import StudentProfileDialog


PAGE_SIZE = 15

TABLE_COLUMNS = [
    ("matricule", "Matricule", 90),
    ("eleve_nom", "Nom", 110),
    ("eleve_prenom", "Prénom", 110),
    ("classe", "Classe", 70),
    ("pere_telephone", "Tél. Père", 100),
    ("mere_telephone", "Tél. Mère", 100),
    ("transport_yn", "Transport", 80),
    ("mensualite", "Mensualité", 90),
    ("statut", "Statut", 80),
]


class GestionElevesPage(ctk.CTkFrame):

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
        self.sort_column = "eleve_nom"
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
        ctk.CTkLabel(header, text="🎓 Gestion des Élèves", font=font_title()).pack(side="left")

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

        # Status filter
        ctk.CTkOptionMenu(
            row1, values=["Tous", "Actif", "Parti"], variable=self.status_filter_var,
            command=lambda v: self._on_filter_change(), width=100,
            fg_color=COLORS["primary"], button_color=COLORS["primary_hover"],
        ).pack(side="left", padx=6)

        # Right side: action buttons
        row2 = ctk.CTkFrame(toolbar, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkButton(
            row2, text="📥 Importer Excel", font=font_button(),
            fg_color=COLORS["secondary"], hover_color=COLORS["primary_hover"],
            command=self._import_excel, width=150,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row2, text="📤 Exporter Excel", font=font_button(),
            fg_color=COLORS["success"], hover_color="#16A34A",
            command=self._export_excel, width=150,
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
            "Modern.Treeview",
            background="#FFFFFF", foreground="#1E293B", rowheight=32,
            fieldbackground="#FFFFFF", borderwidth=0, font=("Segoe UI", 10),
        )
        style.configure(
            "Modern.Treeview.Heading",
            background="#2563EB", foreground="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
        )
        style.map("Modern.Treeview.Heading", background=[("active", "#1D4ED8")])
        style.map("Modern.Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", "#1E293B")])

        tree_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=12, pady=12)

        columns = [c[0] for c in TABLE_COLUMNS] + ["actions"]
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            style="Modern.Treeview", selectmode="browse",
        )

        for key, label, width in TABLE_COLUMNS:
            self.tree.heading(key, text=label, command=lambda k=key: self._sort_by(k))
            self.tree.column(key, width=width, anchor="center")

        self.tree.heading("actions", text="Actions")
        self.tree.column("actions", width=160, anchor="center")

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
        classes = ["Toutes"] + Student.get_distinct_classes(year)
        self.class_menu.configure(values=classes)
        if self.class_filter_var.get() not in classes:
            self.class_filter_var.set("Toutes")

        statut = None if self.status_filter_var.get() == "Tous" else self.status_filter_var.get()
        search = self.search_var.get().strip() or None
        classe = self.class_filter_var.get()

        self.all_rows = Student.get_all(
            annee_scolaire=year, classe=classe, search=search, statut=statut
        )
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
            if col == "mensualite":
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
            transport_display = "✅" if str(row.get("transport_yn", "")).upper() in ("Y", "O") else "❌"
            values = [
                row.get("matricule", ""),
                row.get("eleve_nom", ""),
                row.get("eleve_prenom", ""),
                row.get("classe", ""),
                row.get("pere_telephone", "") or "-",
                row.get("mere_telephone", "") or "-",
                transport_display,
                f"{row.get('mensualite', 0):.0f}" if row.get("mensualite") is not None else "0",
                row.get("statut", ""),
                "👁️ Voir   ✏️ Éditer   🗑️",
            ]
            self.tree.insert("", "end", iid=str(row["id"]), values=values)

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
            self._open_profile(int(item))

    def _on_tree_click(self, event):
        """Detect clicks on the 'actions' column to trigger view/edit/delete."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item:
            return
        col_index = int(column.replace("#", "")) - 1
        col_keys = [c[0] for c in TABLE_COLUMNS] + ["actions"]
        if col_index >= len(col_keys) or col_keys[col_index] != "actions":
            return

        # Determine which sub-action based on x position within the cell
        bbox = self.tree.bbox(item, column)
        if not bbox:
            return
        rel_x = event.x - bbox[0]
        cell_width = bbox[2]
        third = cell_width / 3

        student_id = int(item)
        if rel_x < third:
            self._open_profile(student_id)
        elif rel_x < 2 * third:
            self._open_profile(student_id)
        else:
            self._delete_student(student_id)

    def _open_profile(self, student_id):
        StudentProfileDialog(self, student_id, on_change=self.refresh)

    def _delete_student(self, student_id):
        student = Student.get_by_id(student_id)
        if not student:
            return

        def do_delete():
            Student.delete(student_id)
            ToastNotification(self, message="Élève supprimé.", success=True)
            self.refresh()

        ConfirmDialog(
            self, title="Supprimer l'élève",
            message=f"Voulez-vous vraiment supprimer "
                    f"{student['eleve_nom']} {student['eleve_prenom']} ?",
            on_confirm=do_delete,
        )

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------
    def _import_excel(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier Excel",
            filetypes=[("Fichiers Excel", "*.xlsx *.xls")],
        )
        if not file_path:
            return

        spinner = LoadingSpinner(self, "Importation en cours...")
        self.update_idletasks()

        try:
            from utils.excel_handler import import_excel
            year = self.year_filter_var.get()
            result = import_excel(file_path, year)
            spinner.close()

            msg = f"Importé: {result['inserted']} ajoutés, {result['updated']} mis à jour."
            if result["errors"]:
                msg += f" {len(result['errors'])} erreur(s)."
            ToastNotification(self, message=msg, success=len(result["errors"]) == 0)
            self.refresh()
        except Exception as e:
            spinner.close()
            ToastNotification(self, message=f"Erreur d'importation: {e}", success=False)

    def _export_excel(self):
        file_path = filedialog.asksaveasfilename(
            title="Exporter vers Excel",
            defaultextension=".xlsx",
            filetypes=[("Fichiers Excel", "*.xlsx")],
            initialfile="export_eleves.xlsx",
        )
        if not file_path:
            return

        try:
            from utils.excel_handler import export_excel
            export_excel(self.all_rows, file_path)
            ToastNotification(self, message=f"Exporté avec succès vers {os.path.basename(file_path)}", success=True)
        except Exception as e:
            ToastNotification(self, message=f"Erreur d'exportation: {e}", success=False)
