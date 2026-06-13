"""
Student Card Printer
=====================
Generates a printable PDF "student card" with key information,
using reportlab.
"""

import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def _get_export_dir():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "assets", "exports")


EXPORT_DIR = _get_export_dir()


def generate_student_card(student: dict) -> str:
    """Generate a PDF student card and return the file path."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    filename = f"fiche_{student['matricule']}.pdf".replace("/", "-")
    path = os.path.join(EXPORT_DIR, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # Header bar
    c.setFillColor(colors.HexColor("#2563EB"))
    c.rect(0, height - 40 * mm, width, 40 * mm, fill=True, stroke=False)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20 * mm, height - 20 * mm, "FICHE ELEVE")
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, height - 30 * mm, "Ecole Privee - Gestion Scolaire")

    # Body
    c.setFillColor(colors.black)
    y = height - 55 * mm
    line_height = 8 * mm

    fields = [
        ("Matricule", student.get("matricule", "")),
        ("Nom", student.get("eleve_nom", "")),
        ("Prenom", student.get("eleve_prenom", "")),
        ("Mere", student.get("mere", "")),
        ("Pere", student.get("pere", "")),
        ("Date de naissance", student.get("date_of_birth", "")),
        ("Lieu de naissance", student.get("city_of_birth", "")),
        ("Adresse", student.get("adresse", "")),
        ("Telephone pere", student.get("pere_telephone", "")),
        ("Telephone mere", student.get("mere_telephone", "")),
        ("Classe", student.get("classe", "")),
        ("Date d'inscription", student.get("inscription", "")),
        ("Transport", "Oui" if str(student.get("transport_yn", "")).upper() in ("Y", "O") else "Non"),
        ("Montant transport", str(student.get("transport", 0))),
        ("Mensualite", str(student.get("mensualite", 0))),
        ("Annee scolaire", student.get("annee_scolaire", "")),
        ("Statut", student.get("statut", "")),
    ]

    c.setFont("Helvetica-Bold", 11)
    for label, value in fields:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(70 * mm, y, str(value or "-"))
        y -= line_height

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawString(
        20 * mm, 15 * mm,
        f"Document genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}"
    )

    c.showPage()
    c.save()
    return path
