"""
Validators
==========
Simple field validation helpers used by the registration forms.
"""

import re
from datetime import datetime


def is_required(value) -> bool:
    return value is not None and str(value).strip() != ""


def is_valid_date(value: str) -> bool:
    if not value:
        return False
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def is_valid_phone(value: str) -> bool:
    if not value:
        return True  # phone optional
    return bool(re.match(r"^[0-9+\s\-]{6,15}$", str(value)))


def is_valid_number(value) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def normalize_date(value: str) -> str:
    """Normalize a date string to YYYY-MM-DD format if possible."""
    if not value:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value


def validate_student_form(data: dict) -> list:
    """
    Validate a student registration form dict.
    Returns a list of error messages (empty if valid).
    """
    errors = []

    if not is_required(data.get("eleve_nom")):
        errors.append("Le nom de l'élève est obligatoire.")
    if not is_required(data.get("eleve_prenom")):
        errors.append("Le prénom de l'élève est obligatoire.")
    if not is_required(data.get("classe")):
        errors.append("La classe est obligatoire.")

    dob = data.get("date_of_birth")
    if dob and not is_valid_date(dob):
        errors.append("La date de naissance n'est pas valide (format attendu: AAAA-MM-JJ).")

    if not is_valid_phone(data.get("pere_telephone")):
        errors.append("Le numéro de téléphone du père n'est pas valide.")
    if not is_valid_phone(data.get("mere_telephone")):
        errors.append("Le numéro de téléphone de la mère n'est pas valide.")

    if data.get("mensualite") and not is_valid_number(data.get("mensualite")):
        errors.append("La mensualité doit être un nombre.")
    if data.get("transport") and not is_valid_number(data.get("transport")):
        errors.append("Le montant du transport doit être un nombre.")

    return errors
