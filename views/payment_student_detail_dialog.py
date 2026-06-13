"""
Payment Student Detail Dialog
===============================
Modal popup shown when a student is selected in "Gestion des
Paiements". Displays full student information, monthly payment
status (color-coded), complete payment history, and an
"Ajouter Paiement" form. Saving a payment updates the monthly
status, refreshes history/totals, generates a PDF receipt and
sends it automatically to the printer.
"""

import customtkinter as ctk
from tkinter import ttk
from datetime import datetime
import os

from utils.theme import COLORS, font_title, font_subtitle, font_body, font_button
from utils.payment_constants import (
    SCHOOL_MONTHS, PAYMENT_TYPES, STATUS_LABELS, STATUS_COLORS, STATUS_UNPAID,
)
from models.payment_student import PaymentStudent
from models.payment import Payment
from database.db_manager import DatabaseManager
from views.widgets import ToastNotification, LoadingSpinner


class PaymentStudentDetailDialog(ctk.CTkToplevel):

    def __init__(self, master, payment_student_id, on_change=None):
        super().__init__(master)
        self.title("Détails de l'élève - Paiements")
        self.geometry("760x800")
        self.minsize(640, 600)
        self.grab_set()
        self.transient(master)

        self.db = DatabaseManager()
        self.payment_student_id = payment_student_id
        self.on_change = on_change

        self.student = PaymentStudent.get_by_id(payment_student_id)
        if not self.student:
            ctk.CTkLabel(self, text="Élève introuvable.", font=font_subtitle()).pack(pady=40)
            return

        # Form state
        self.amount_var = ctk.StringVar()

        self._build_ui()
        self._center_on_parent(master)

    def _center_on_parent(self, master):
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=80)
        header.pack(fill="x")
        full_name = f"{self.student['nom']} {self.student['prenom']}".strip()
        ctk.CTkLabel(
            header, text=f"👤  {full_name}", font=font_title(), text_color="white",
        ).pack(side="left", padx=25, pady=20)
        ctk.CTkLabel(
            header, text=f"Matricule: {self.student['matricule']}  •  {self.student['classe']}  •  "
                         f"{self.student['annee_scolaire']}",
            font=font_body(), text_color="white",
        ).pack(side="right", padx=25)

        # Scrollable body
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        self._build_info_section()
        self._build_month_status_section()
        self._build_payment_form_section()
        self._build_history_section()

    # ------------------------------------------------------------------
    # Student information
    # ------------------------------------------------------------------
    def _build_info_section(self):
        card = ctk.CTkFrame(
            self.scroll, fg_color=("white", COLORS["card_dark"]), corner_radius=14,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        card.pack(fill="x", pady=8)

        ctk.CTkLabel(card, text="ℹ️ Informations de l'élève", font=font_subtitle()).pack(
            anchor="w", padx=18, pady=(15, 5)
        )

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=(0, 15))
        for i in range(3):
            grid.grid_columnconfigure(i, weight=1)

        student = self.student
        total_paid = PaymentStudent.get_total_paid(student["id"], student["annee_scolaire"])

        fields = [
            ("Matricule", student["matricule"]),
            ("Nom", student["nom"]),
            ("Prénom", student.get("prenom") or "-"),
            ("Classe", student["classe"]),
            ("Année scolaire", student["annee_scolaire"]),
            ("Inscription", student.get("inscription") or "-"),
            ("Transport (DH)", f"{student.get('transport', 0):.0f}"),
            ("Mensualité (DH)", f"{student.get('mensualite', 0):.0f}"),
            ("Total à payer (DH)", f"{student.get('total_a_payer', 0):.0f}"),
            ("Note/Date", student.get("note_date") or "-"),
        ]

        self.info_value_labels = {}
        for idx, (label, value) in enumerate(fields):
            r, c = divmod(idx, 3)
            f = ctk.CTkFrame(grid, fg_color="transparent")
            f.grid(row=r, column=c, sticky="w", padx=8, pady=6)
            ctk.CTkLabel(f, text=label, font=font_body(), text_color=("#64748B", "#94A3B8")).pack(anchor="w")
            value_label = ctk.CTkLabel(f, text=str(value), font=font_subtitle())
            value_label.pack(anchor="w")
            self.info_value_labels[label] = value_label

        # Total paid (separate, updated after each payment)
        r, c = divmod(len(fields), 3)
        f = ctk.CTkFrame(grid, fg_color="transparent")
        f.grid(row=r, column=c, sticky="w", padx=8, pady=6)
        ctk.CTkLabel(f, text="Total payé (DH)", font=font_body(), text_color=("#64748B", "#94A3B8")).pack(anchor="w")
        self.total_paid_label = ctk.CTkLabel(f, text=f"{total_paid:.0f}", font=font_subtitle(),
                                              text_color=COLORS["success"])
        self.total_paid_label.pack(anchor="w")

    # ------------------------------------------------------------------
    # Monthly status chips
    # ------------------------------------------------------------------
    def _build_month_status_section(self):
        self.status_card = ctk.CTkFrame(
            self.scroll, fg_color=("white", COLORS["card_dark"]), corner_radius=14,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        self.status_card.pack(fill="x", pady=8)

        ctk.CTkLabel(self.status_card, text="📅 Statut Mensuel", font=font_subtitle()).pack(
            anchor="w", padx=18, pady=(15, 5)
        )

        self.months_row = ctk.CTkFrame(self.status_card, fg_color="transparent")
        self.months_row.pack(fill="x", padx=18, pady=(0, 10))

        self.suggestion_label = ctk.CTkLabel(self.status_card, text="", font=font_body())
        self.suggestion_label.pack(anchor="w", padx=18, pady=(0, 15))

        self._refresh_month_status()

    def _refresh_month_status(self):
        for widget in self.months_row.winfo_children():
            widget.destroy()

        student = self.student
        statuses = PaymentStudent.get_month_statuses(student["id"], student["annee_scolaire"])

        for i, month in enumerate(SCHOOL_MONTHS):
            status = statuses.get(month, STATUS_UNPAID)
            self._add_month_chip(self.months_row, month, status, i)

        next_month = PaymentStudent.get_next_unpaid_month(student["id"], student["annee_scolaire"])
        if next_month:
            self.suggestion_label.configure(
                text=f"💡 Mois suggéré pour le prochain paiement: {next_month}",
                text_color=COLORS["warning"],
            )
            if hasattr(self, "month_menu"):
                self.month_menu.set(next_month)
        else:
            self.suggestion_label.configure(
                text="✅ Tous les mois sont à jour (payés ou non inscrits).",
                text_color=COLORS["success"],
            )

    def _add_month_chip(self, parent, month, status, index):
        color = STATUS_COLORS.get(status, STATUS_COLORS[STATUS_UNPAID])
        label_text = STATUS_LABELS.get(status, "")

        chip = ctk.CTkFrame(parent, fg_color=color, corner_radius=8, width=88, height=58)
        chip.grid(row=0, column=index, padx=4, pady=4, sticky="nsew")
        chip.grid_propagate(False)
        parent.grid_columnconfigure(index, weight=1)

        ctk.CTkLabel(chip, text=month, font=font_body(), text_color="white").pack(pady=(8, 0))
        ctk.CTkLabel(chip, text=label_text, font=ctk.CTkFont(size=10), text_color="white").pack()

    # ------------------------------------------------------------------
    # Payment form ("Ajouter Paiement")
    # ------------------------------------------------------------------
    def _build_payment_form_section(self):
        card = ctk.CTkFrame(
            self.scroll, fg_color=("white", COLORS["card_dark"]), corner_radius=14,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        card.pack(fill="x", pady=8)

        ctk.CTkLabel(card, text="➕ Ajouter Paiement", font=font_subtitle()).pack(
            anchor="w", padx=18, pady=(15, 5)
        )

        form_grid = ctk.CTkFrame(card, fg_color="transparent")
        form_grid.pack(fill="x", padx=18, pady=(0, 10))
        for i in range(2):
            form_grid.grid_columnconfigure(i, weight=1)

        # Payment type
        f1 = ctk.CTkFrame(form_grid, fg_color="transparent")
        f1.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(f1, text="Type de paiement", font=font_body(), anchor="w").pack(anchor="w")
        self.payment_type_menu = ctk.CTkOptionMenu(
            f1, values=PAYMENT_TYPES, fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"], command=self._on_payment_type_change,
        )
        self.payment_type_menu.set("Mensualité")
        self.payment_type_menu.pack(fill="x", pady=(2, 0))

        # Month
        f2 = ctk.CTkFrame(form_grid, fg_color="transparent")
        f2.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(f2, text="Mois", font=font_body(), anchor="w").pack(anchor="w")
        self.month_menu = ctk.CTkOptionMenu(
            f2, values=list(SCHOOL_MONTHS), fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"],
        )
        next_month = PaymentStudent.get_next_unpaid_month(self.student["id"], self.student["annee_scolaire"])
        self.month_menu.set(next_month if next_month else SCHOOL_MONTHS[0])
        self.month_menu.pack(fill="x", pady=(2, 0))

        # Amount
        f3 = ctk.CTkFrame(form_grid, fg_color="transparent")
        f3.grid(row=1, column=0, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(f3, text="Montant (DH)", font=font_body(), anchor="w").pack(anchor="w")
        self.amount_entry = ctk.CTkEntry(f3, textvariable=self.amount_var, font=font_body())
        self.amount_entry.pack(fill="x", pady=(2, 0))

        # Pre-fill amount based on payment type
        self._on_payment_type_change("Mensualité")

        # Payment date
        f4 = ctk.CTkFrame(form_grid, fg_color="transparent")
        f4.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(f4, text="Date de paiement (AAAA-MM-JJ)", font=font_body(), anchor="w").pack(anchor="w")
        self.date_entry = ctk.CTkEntry(f4, font=font_body())
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(fill="x", pady=(2, 0))

        # Notes
        f5 = ctk.CTkFrame(form_grid, fg_color="transparent")
        f5.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(f5, text="Notes", font=font_body(), anchor="w").pack(anchor="w")
        self.notes_entry = ctk.CTkEntry(f5, font=font_body())
        self.notes_entry.pack(fill="x", pady=(2, 0))

        # Save button
        ctk.CTkButton(
            card, text="💾 Enregistrer Paiement", font=font_button(), height=44,
            fg_color=COLORS["success"], hover_color="#16A34A",
            command=self._save_payment,
        ).pack(fill="x", padx=18, pady=(5, 15))

    def _on_payment_type_change(self, value):
        student = self.student
        if value == "Mensualité":
            self.amount_var.set(f"{student.get('mensualite', 0):.0f}")
            self.month_menu.configure(state="normal")
        elif value == "Transport":
            self.amount_var.set(f"{student.get('transport', 0):.0f}")
            self.month_menu.configure(state="disabled")
        elif value == "Inscription":
            self.amount_var.set("")
            self.month_menu.configure(state="disabled")

    # ------------------------------------------------------------------
    # Payment history
    # ------------------------------------------------------------------
    def _build_history_section(self):
        self.history_card = ctk.CTkFrame(
            self.scroll, fg_color=("white", COLORS["card_dark"]), corner_radius=14,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        self.history_card.pack(fill="x", pady=8)

        ctk.CTkLabel(self.history_card, text="🧾 Historique des paiements", font=font_subtitle()).pack(
            anchor="w", padx=18, pady=(15, 5)
        )

        self.history_body = ctk.CTkFrame(self.history_card, fg_color="transparent")
        self.history_body.pack(fill="x", expand=True, padx=18, pady=(0, 15))

        self._refresh_history()

    def _refresh_history(self):
        for widget in self.history_body.winfo_children():
            widget.destroy()

        student = self.student
        history = Payment.get_history(student["id"], student["annee_scolaire"])

        if not history:
            ctk.CTkLabel(self.history_body, text="Aucun paiement enregistré.", font=font_body(),
                          text_color=("#64748B", "#94A3B8")).pack(anchor="w")
            return

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "PayDetail.Treeview", background="#FFFFFF", foreground="#1E293B",
            rowheight=30, fieldbackground="#FFFFFF", borderwidth=0, font=("Segoe UI", 10),
        )
        style.configure(
            "PayDetail.Treeview.Heading", background="#2563EB", foreground="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
        )

        columns = ["payment_type", "month", "amount", "payment_date", "receipt_number", "notes"]
        tree = ttk.Treeview(
            self.history_body, columns=columns, show="headings",
            style="PayDetail.Treeview", height=min(max(len(history), 1), 8),
        )

        headers = {
            "payment_type": ("Type", 100),
            "month": ("Mois", 90),
            "amount": ("Montant (DH)", 100),
            "payment_date": ("Date", 100),
            "receipt_number": ("N° Reçu", 140),
            "notes": ("Notes", 180),
        }
        for key, (label, width) in headers.items():
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor="center")

        for p in history:
            tree.insert("", "end", values=(
                p["payment_type"], p.get("month") or "-", f"{p['amount']:.0f}",
                p["payment_date"], p["receipt_number"], p.get("notes") or "",
            ))

        vsb = ttk.Scrollbar(self.history_body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    # ------------------------------------------------------------------
    # Save payment
    # ------------------------------------------------------------------
    def _save_payment(self):
        student = self.student
        year = student["annee_scolaire"]
        payment_type = self.payment_type_menu.get()
        month = self.month_menu.get() if payment_type == "Mensualité" else None
        date_value = self.date_entry.get().strip()
        notes = self.notes_entry.get().strip()

        try:
            amount = float(self.amount_var.get())
        except ValueError:
            ToastNotification(self, message="Le montant doit être un nombre valide.", success=False)
            return

        if amount <= 0:
            ToastNotification(self, message="Le montant doit être supérieur à 0.", success=False)
            return

        if not date_value:
            ToastNotification(self, message="La date de paiement est obligatoire.", success=False)
            return

        spinner = LoadingSpinner(self, "Enregistrement du paiement...")
        self.update_idletasks()

        try:
            payment = Payment.register_payment(
                payment_student_id=student["id"],
                annee_scolaire=year,
                payment_type=payment_type,
                month=month,
                amount=amount,
                payment_date=date_value,
                notes=notes,
            )

            # Calculate remaining amount
            total_paid = PaymentStudent.get_total_paid(student["id"], year)
            total_due = student.get("total_a_payer", 0) or 0
            remaining = max(total_due - total_paid, 0)

            # Generate receipt PDF
            from utils.receipt_generator import generate_receipt_pdf
            receipt_path = generate_receipt_pdf(
                payment=payment,
                student=student,
                remaining_amount=remaining,
            )

            # Save receipt record
            self.db.execute(
                "INSERT INTO receipts (receipt_number, payment_id, file_path, date_creation) "
                "VALUES (?, ?, ?, ?)",
                (payment["receipt_number"], payment["id"], receipt_path,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )

            # Automatically print the receipt
            from utils.printer import print_pdf
            printed = print_pdf(receipt_path)

            spinner.close()

            # Refresh UI: monthly status, total paid, history
            self.total_paid_label.configure(text=f"{total_paid:.0f}")
            self._refresh_month_status()
            self._refresh_history()

            # Clear notes for next entry
            self.notes_entry.delete(0, "end")

            msg = f"Paiement enregistré ! Reçu: {payment['receipt_number']}"
            if printed:
                msg += " — envoyé à l'imprimante."
            else:
                msg += f" — PDF: {os.path.basename(receipt_path)} (impression manuelle requise)."

            ToastNotification(self, message=msg, success=True)

            # Notify parent (refresh list / dashboard)
            if self.on_change:
                self.on_change()

        except Exception as e:
            spinner.close()
            ToastNotification(self, message=f"Erreur: {e}", success=False)
