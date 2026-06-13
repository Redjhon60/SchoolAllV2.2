"""
Payment Excel Import Handler
=============================
Imports the payment Excel template (Matricule, Nom, Prénom, Classe,
Inscription, Transport, Mensualité, Total a payé, Note/Date, Year,
Septembre..Juin) into the payment_students / month_status /
payments tables.
"""

import pandas as pd
from datetime import datetime

from models.payment_student import PaymentStudent
from utils.payment_constants import SCHOOL_MONTHS, parse_month_value, STATUS_PAYE, STATUS_UNPAID, STATUS_NAN
from database.db_manager import DatabaseManager


EXCEL_COLUMNS = [
    "Matricule", "Nom", "Prénom", "Classe", "Inscription", "Transport",
    "Mensualité", "Total a payé", "Note/Date", "Year",
] + SCHOOL_MONTHS


def _clean_value(val):
    if pd.isna(val):
        return None
    if isinstance(val, float) and val == int(val):
        return int(val)
    return val


def _to_float(val, default=0.0):
    """
    Convert a value to float, handling text like 'GRATUIT', '500 AV',
    '200DH AV' etc. by extracting the first numeric token, or 0 for
    non-numeric text such as 'GRATUIT'.
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        try:
            if pd.isna(val):
                return default
        except TypeError:
            pass
        return float(val)

    text = str(val).strip().upper()
    if text in ("", "GRATUIT", "NAN"):
        return default if text != "GRATUIT" else 0.0

    # Extract leading numeric portion (e.g. "500 AV" -> 500, "200DH AV" -> 200)
    import re
    match = re.search(r"[\d]+(\.\d+)?", text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return default
    return default


def import_payments_excel(file_path: str, default_annee_scolaire: str = None):
    """
    Read the payments Excel file and import students, month statuses,
    and create missing payment_students records.

    Returns a summary dict:
    {
        'students_created': int,
        'students_updated': int,
        'months_set': int,
        'errors': list[str],
    }
    """
    df = pd.read_excel(file_path)

    summary = {
        "students_created": 0,
        "students_updated": 0,
        "months_set": 0,
        "errors": [],
    }

    for idx, row in df.iterrows():
        try:
            matricule = _clean_value(row.get("Matricule"))
            nom = _clean_value(row.get("Nom"))
            prenom = _clean_value(row.get("Prénom"))
            classe = _clean_value(row.get("Classe"))
            annee_scolaire = _clean_value(row.get("Year")) or default_annee_scolaire

            if matricule is None or nom is None or annee_scolaire is None:
                summary["errors"].append(f"Ligne {idx + 2}: données obligatoires manquantes (Matricule/Nom/Year).")
                continue

            matricule = str(matricule)

            record = {
                "matricule": matricule,
                "nom": str(nom),
                "prenom": str(prenom) if prenom is not None else "",
                "classe": str(classe) if classe is not None else "",
                "inscription": str(_clean_value(row.get("Inscription")) or ""),
                "transport": _to_float(row.get("Transport"), 0.0),
                "mensualite": _to_float(row.get("Mensualité"), 0.0),
                "total_a_payer": _to_float(row.get("Total a payé"), 0.0),
                "note_date": str(_clean_value(row.get("Note/Date")) or ""),
                "annee_scolaire": str(annee_scolaire),
            }

            existing = PaymentStudent.get_by_key(matricule, record["classe"], record["annee_scolaire"])
            if existing:
                PaymentStudent.update(existing["id"], record)
                ps_id = existing["id"]
                summary["students_updated"] += 1
            else:
                ps_id = PaymentStudent.create(record)
                summary["students_created"] += 1

            # Month statuses
            for month in SCHOOL_MONTHS:
                raw_value = row.get(month)
                status = parse_month_value(raw_value)
                PaymentStudent.set_month_status(ps_id, record["annee_scolaire"], month, status)
                summary["months_set"] += 1

        except Exception as e:
            summary["errors"].append(f"Ligne {idx + 2}: {e}")

    return summary
