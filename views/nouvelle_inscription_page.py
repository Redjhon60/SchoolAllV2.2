"""
Nouvelle Inscription Page
==========================
Modern registration form with auto matricule generation,
validation, required field checks, and instant save.
"""

import customtkinter as ctk
from datetime import datetime

from utils.theme import COLORS, font_title, font_subtitle, font_body, font_button
from utils.validators import validate_student_form, normalize_date
from models.student import Student
from database.db_manager import DatabaseManager
from views.widgets import ToastNotification


CLASSES = [
    "Maternelle 1", "Maternelle 2", "Maternelle 3",
    "CP1", "CP2", "CE1", "CE2", "CM1", "CM2",
    "1AC", "2AC", "3AC", "1BAC", "2BAC",
]


class NouvelleInscriptionPage(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=("#F8FAFC", "#0F172A"), **kwargs)

        self.db = DatabaseManager()
        self.current_year = self.db.get_setting("current_school_year", "2025/2026")

        self.fields = {}

        self._build_header()
        self._build_form()

    # ------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 5))
        ctk.CTkLabel(header, text="📝 Nouvelle Inscription", font=font_title()).pack(side="left")

    def _build_form(self):
        card = ctk.CTkScrollableFrame(
            self, fg_color=("white", COLORS["card_dark"]), corner_radius=14,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        card.pack(fill="both", expand=True, padx=25, pady=10)

        for i in range(2):
            card.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(card, text="Informations de l'élève", font=font_subtitle()).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10)
        )

        # Matricule (auto-generated, read-only with regenerate option)
        self._add_matricule_field(card, row=1)

        layout = [
            ("eleve_nom", "Nom *", "entry", 2, 0),
            ("eleve_prenom", "Prénom *", "entry", 2, 1),
            ("mere", "Mère", "entry", 3, 0),
            ("pere", "Père", "entry", 3, 1),
            ("date_of_birth", "Date de naissance (AAAA-MM-JJ)", "entry", 4, 0),
            ("city_of_birth", "Lieu de naissance", "entry", 4, 1),
            ("adresse", "Adresse", "entry", 5, 0),
            ("pere_telephone", "Téléphone père", "entry", 5, 1),
            ("mere_telephone", "Téléphone mère", "entry", 6, 0),
            ("classe", "Classe *", "classe", 6, 1),
            ("inscription", "Date d'inscription (AAAA-MM-JJ)", "entry", 7, 0),
            ("transport_yn", "Transport", "transport", 7, 1),
            ("transport", "Montant transport (DH)", "entry", 8, 0),
            ("mensualite", "Mensualité (DH)", "entry", 8, 1),
            ("note_date", "Note / Remarques", "entry", 9, 0),
        ]

        for field, label, kind, row_offset, col in layout:
            self._add_field(card, field, label, kind, row_offset, col)

        # Default inscription date = today
        self.fields["inscription"].insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Action buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=10, column=0, columnspan=2, sticky="ew", padx=15, pady=25)

        ctk.CTkButton(
            btn_frame, text="✅ Enregistrer l'inscription", font=font_button(),
            fg_color=COLORS["success"], hover_color="#16A34A",
            height=44, command=self._save,
        ).pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(
            btn_frame, text="🔄 Réinitialiser", font=font_button(),
            fg_color="gray", hover_color="#475569",
            height=44, command=self._reset,
        ).pack(side="left", padx=5)

    def _add_matricule_field(self, parent, row):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=15, pady=6)

        ctk.CTkLabel(frame, text="Matricule (généré automatiquement)", font=font_body(), anchor="w").pack(anchor="w")
        sub = ctk.CTkFrame(frame, fg_color="transparent")
        sub.pack(fill="x", pady=(2, 0))

        entry = ctk.CTkEntry(sub, font=font_body())
        entry.insert(0, Student.generate_matricule(self.current_year))
        entry.pack(side="left", fill="x", expand=True)
        self.fields["matricule"] = entry

        ctk.CTkButton(
            sub, text="🔄", width=40,
            fg_color=COLORS["secondary"], hover_color=COLORS["primary_hover"],
            command=self._regenerate_matricule,
        ).pack(side="left", padx=(8, 0))

    def _regenerate_matricule(self):
        self.fields["matricule"].delete(0, "end")
        self.fields["matricule"].insert(0, Student.generate_matricule(self.current_year))

    def _add_field(self, parent, field, label, kind, row, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="ew", padx=15, pady=6)

        ctk.CTkLabel(frame, text=label, font=font_body(), anchor="w").pack(anchor="w")

        if kind == "entry":
            widget = ctk.CTkEntry(frame, font=font_body())
            widget.pack(fill="x", pady=(2, 0))
        elif kind == "classe":
            widget = ctk.CTkOptionMenu(
                frame, values=CLASSES, fg_color=COLORS["primary"],
                button_color=COLORS["primary_hover"],
            )
            widget.set(CLASSES[0])
            widget.pack(fill="x", pady=(2, 0))
        elif kind == "transport":
            widget = ctk.CTkOptionMenu(
                frame, values=["Non", "Oui"], fg_color=COLORS["primary"],
                button_color=COLORS["primary_hover"],
            )
            widget.set("Non")
            widget.pack(fill="x", pady=(2, 0))

        self.fields[field] = widget

    # ------------------------------------------------------------------
    # Save / Reset
    # ------------------------------------------------------------------
    def _collect_data(self):
        data = {}
        for field, widget in self.fields.items():
            if isinstance(widget, ctk.CTkEntry):
                data[field] = widget.get().strip()
            else:
                data[field] = widget.get()

        # transport conversion
        data["transport_yn"] = "Y" if data.get("transport_yn") == "Oui" else "N"

        for num_field in ("transport", "mensualite"):
            try:
                data[num_field] = float(data.get(num_field) or 0)
            except ValueError:
                data[num_field] = 0

        if data.get("date_of_birth"):
            data["date_of_birth"] = normalize_date(data["date_of_birth"])
        if data.get("inscription"):
            data["inscription"] = normalize_date(data["inscription"])

        data["annee_scolaire"] = self.current_year
        data["statut"] = "Actif"
        return data

    def _save(self):
        data = self._collect_data()
        errors = validate_student_form(data)
        if errors:
            ToastNotification(self, message=errors[0], success=False)
            return

        # Ensure matricule uniqueness
        existing = Student.get_by_matricule(data["matricule"], self.current_year)
        if existing:
            data["matricule"] = Student.generate_matricule(self.current_year)

        Student.create(data)
        ToastNotification(
            self, message=f"Élève {data['eleve_nom']} {data['eleve_prenom']} inscrit avec succès !",
            success=True,
        )
        self._reset()

    def _reset(self):
        for field, widget in self.fields.items():
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
            elif field == "transport_yn":
                widget.set("Non")
            elif field == "classe":
                widget.set(CLASSES[0])

        self.fields["matricule"].insert(0, Student.generate_matricule(self.current_year))
        self.fields["inscription"].insert(0, datetime.now().strftime("%Y-%m-%d"))
