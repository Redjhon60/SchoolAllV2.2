"""
Student Profile Dialog
=======================
Modal window showing full student information with
Modify / Save / Print / Delete actions.
"""

import customtkinter as ctk
from utils.theme import COLORS, font_title, font_subtitle, font_body, font_button
from utils.validators import validate_student_form, normalize_date
from models.student import Student
from views.widgets import ConfirmDialog, ToastNotification


FIELD_LABELS = [
    ("matricule", "Matricule"),
    ("eleve_nom", "Nom"),
    ("eleve_prenom", "Prénom"),
    ("mere", "Mère"),
    ("pere", "Père"),
    ("date_of_birth", "Date de naissance"),
    ("city_of_birth", "Lieu de naissance"),
    ("adresse", "Adresse"),
    ("pere_telephone", "Téléphone père"),
    ("mere_telephone", "Téléphone mère"),
    ("classe", "Classe"),
    ("inscription", "Date d'inscription"),
    ("transport_yn", "Transport (Y/N)"),
    ("transport", "Montant transport"),
    ("mensualite", "Mensualité"),
    ("note_date", "Note / Date"),
]


class StudentProfileDialog(ctk.CTkToplevel):

    def __init__(self, master, student_id, on_change=None):
        super().__init__(master)
        self.title("Profil de l'élève")
        self.geometry("620x700")
        self.minsize(500, 500)
        self.grab_set()
        self.transient(master)

        self.student_id = student_id
        self.on_change = on_change
        self.editable = False
        self.entries = {}

        self.student = Student.get_by_id(student_id)
        if not self.student:
            ctk.CTkLabel(self, text="Élève introuvable.", font=font_subtitle()).pack(pady=40)
            return

        self._build_ui()
        self._center_on_parent(master)

    def _center_on_parent(self, master):
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=80)
        header.pack(fill="x")
        full_name = f"{self.student['eleve_nom']} {self.student['eleve_prenom']}"
        ctk.CTkLabel(
            header, text=f"👤  {full_name}", font=font_title(), text_color="white",
        ).pack(side="left", padx=25, pady=20)
        ctk.CTkLabel(
            header, text=f"Matricule: {self.student['matricule']}", font=font_body(),
            text_color="white",
        ).pack(side="right", padx=25)

        # Scrollable form
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)

        for idx, (field, label) in enumerate(FIELD_LABELS):
            row, col = divmod(idx, 2)
            frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
            frame.grid(row=row, column=col, sticky="ew", padx=8, pady=6)

            ctk.CTkLabel(frame, text=label, font=font_body(), anchor="w").pack(anchor="w")
            entry = ctk.CTkEntry(frame, font=font_body())
            entry.insert(0, str(self.student.get(field) or ""))
            entry.configure(state="disabled")
            entry.pack(fill="x", pady=(2, 0))
            self.entries[field] = entry

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.modify_btn = ctk.CTkButton(
            btn_frame, text="✏️ Modifier", font=font_button(),
            fg_color=COLORS["secondary"], hover_color=COLORS["primary_hover"],
            command=self._toggle_edit, width=130,
        )
        self.modify_btn.pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(
            btn_frame, text="💾 Enregistrer", font=font_button(),
            fg_color=COLORS["success"], hover_color="#16A34A",
            command=self._save, width=130, state="disabled",
        )
        self.save_btn.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🖨️ Imprimer", font=font_button(),
            fg_color=COLORS["warning"], hover_color="#D97706",
            command=self._print, width=130,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🗑️ Supprimer", font=font_button(),
            fg_color=COLORS["danger"], hover_color="#DC2626",
            command=self._delete, width=130,
        ).pack(side="right", padx=5)

    # ------------------------------------------------------------------
    # Edit / Save
    # ------------------------------------------------------------------
    def _toggle_edit(self):
        self.editable = not self.editable
        state = "normal" if self.editable else "disabled"
        for field, entry in self.entries.items():
            if field == "matricule":
                continue  # matricule never editable
            entry.configure(state=state)
        self.save_btn.configure(state="normal" if self.editable else "disabled")
        self.modify_btn.configure(text="✖️ Annuler" if self.editable else "✏️ Modifier")

    def _save(self):
        data = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            data[field] = value

        if data.get("date_of_birth"):
            data["date_of_birth"] = normalize_date(data["date_of_birth"])
        if data.get("inscription"):
            data["inscription"] = normalize_date(data["inscription"])

        # numeric coercion
        for num_field in ("transport", "mensualite"):
            try:
                data[num_field] = float(data.get(num_field) or 0)
            except ValueError:
                data[num_field] = 0

        errors = validate_student_form(data)
        if errors:
            ToastNotification(self, message=errors[0], success=False)
            return

        Student.update(self.student_id, data)
        ToastNotification(self, message="Modifications enregistrées avec succès.", success=True)
        self._toggle_edit()
        self.student = Student.get_by_id(self.student_id)
        if self.on_change:
            self.on_change()

    # ------------------------------------------------------------------
    # Delete / Print
    # ------------------------------------------------------------------
    def _delete(self):
        def do_delete():
            Student.delete(self.student_id)
            ToastNotification(self.master, message="Élève supprimé.", success=True)
            if self.on_change:
                self.on_change()
            self.destroy()

        ConfirmDialog(
            self, title="Supprimer l'élève",
            message=f"Voulez-vous vraiment supprimer {self.student['eleve_nom']} "
                    f"{self.student['eleve_prenom']} ? Cette action est irréversible.",
            on_confirm=do_delete,
        )

    def _print(self):
        from utils.card_printer import generate_student_card
        try:
            path = generate_student_card(self.student)
            ToastNotification(self, message=f"Fiche générée: {path}", success=True)
        except Exception as e:
            ToastNotification(self, message=f"Erreur d'impression: {e}", success=False)
