"""
Payment Receipt Generator
==========================
Generates a professional PDF receipt for a registered payment,
using reportlab.
"""

import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from database.db_manager import DatabaseManager


def _get_export_dir():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "assets", "exports", "receipts")


EXPORT_DIR = _get_export_dir()


def generate_receipt_pdf(payment: dict, student: dict, remaining_amount: float = None,
                          logo_path: str = None) -> str:
    """
    Generate a PDF receipt for a payment and return its file path.

    `payment` keys: receipt_number, payment_type, month, amount,
                     payment_date, notes, annee_scolaire
    `student` keys: matricule, nom, prenom, classe
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)
    db = DatabaseManager()
    school_name = db.get_setting("school_name", "Ecole Privee")

    filename = f"{payment['receipt_number']}.pdf".replace("/", "-")
    path = os.path.join(EXPORT_DIR, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # Header bar
    c.setFillColor(colors.HexColor("#2563EB"))
    c.rect(0, height - 40 * mm, width, 40 * mm, fill=True, stroke=False)

    # Logo (optional)
    text_x = 20 * mm
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 15 * mm, height - 37 * mm, width=28 * mm, height=28 * mm,
                         preserveAspectRatio=True, mask="auto")
            text_x = 50 * mm
        except Exception:
            pass

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(text_x, height - 18 * mm, school_name)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(text_x, height - 28 * mm, "REÇU DE PAIEMENT")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 15 * mm, height - 18 * mm, f"N° {payment['receipt_number']}")
    c.drawRightString(width - 15 * mm, height - 26 * mm, f"Date: {payment['payment_date']}")

    # Body
    c.setFillColor(colors.black)
    y = height - 55 * mm
    line_height = 8 * mm

    full_name = f"{student.get('nom', '')} {student.get('prenom', '')}".strip()

    fields = [
        ("Matricule", student.get("matricule", "")),
        ("Nom et Prenom", full_name),
        ("Classe", student.get("classe", "")),
        ("Annee scolaire", payment.get("annee_scolaire", "")),
        ("Type de paiement", payment.get("payment_type", "")),
    ]
    if payment.get("month"):
        fields.append(("Mois concerne", payment.get("month")))

    for label, value in fields:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(75 * mm, y, str(value or "-"))
        y -= line_height

    # Amount box
    y -= 5 * mm
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.roundRect(20 * mm, y - 18 * mm, width - 40 * mm, 18 * mm, 3 * mm, fill=True, stroke=False)
    c.setFillColor(colors.HexColor("#22C55E"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(25 * mm, y - 12 * mm, "Montant paye:")
    c.drawRightString(width - 25 * mm, y - 12 * mm, f"{payment.get('amount', 0):.2f} DH")
    y -= 24 * mm

    if remaining_amount is not None:
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Montant restant:")
        c.setFont("Helvetica", 11)
        c.drawString(75 * mm, y, f"{remaining_amount:.2f} DH")
        y -= line_height

    # Notes
    if payment.get("notes"):
        y -= 4 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Remarques:")
        y -= line_height
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, str(payment.get("notes"))[:100])
        y -= line_height

    # Signature area
    sig_y = 35 * mm
    c.setFont("Helvetica", 10)
    c.line(25 * mm, sig_y, 85 * mm, sig_y)
    c.drawString(25 * mm, sig_y - 5 * mm, "Signature du parent")

    c.line(width - 85 * mm, sig_y, width - 25 * mm, sig_y)
    c.drawString(width - 85 * mm, sig_y - 5 * mm, "Signature et cachet de l'ecole")

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawString(
        20 * mm, 15 * mm,
        f"Recu genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}"
    )

    c.showPage()
    c.save()
    return path
