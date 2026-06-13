"""
Excel Import / Export Utilities
================================
Handles reading student data from Excel files (matching the
provided template), validating it, detecting duplicates, and
exporting student data back to Excel.
"""

import pandas as pd
from datetime import datetime
from models.student import Student


# Mapping from Excel column names (template) to internal DB columns
EXCEL_TO_DB = {
    "Matricule": "matricule",
    "Eleve Nom": "eleve_nom",
    "Eleve Prénom": "eleve_prenom",
    "Mere": "mere",
    "Père": "pere",
    "Date of birth": "date_of_birth",
    "City of birth": "city_of_birth",
    "Adress": "adresse",
    "Père telephone": "pere_telephone",
    "Mere telephone": "mere_telephone",
    "Classe": "classe",
    "Inscription": "inscription",
    "Transport (Y/N)": "transport_yn",
    "Transport": "transport",
    "Mensualité": "mensualite",
    "Note/Date": "note_date",
}

DB_TO_EXCEL = {v: k for k, v in EXCEL_TO_DB.items()}

REQUIRED_FIELDS = ["eleve_nom", "eleve_prenom", "classe"]


def _clean_value(val):
    """Convert NaN / NaT to None, and stringify cleanly."""
    if pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, float) and val == int(val):
        return int(val)
    return val


def import_excel(file_path: str, annee_scolaire: str):
    """
    Read an Excel file matching the template, validate rows, and
    insert/update students in the database.

    Returns a dict with summary: {
        'inserted': int, 'updated': int, 'errors': list[str]
    }
    """
    df = pd.read_excel(file_path)

    inserted = 0
    updated = 0
    errors = []

    for idx, row in df.iterrows():
        record = {}
        for excel_col, db_col in EXCEL_TO_DB.items():
            if excel_col in df.columns:
                record[db_col] = _clean_value(row[excel_col])
            else:
                record[db_col] = None

        # Convert types/formats
        if record.get("date_of_birth") is not None:
            record["date_of_birth"] = str(record["date_of_birth"])
        if record.get("note_date") is not None:
            record["note_date"] = str(record["note_date"])

        # Normalize transport_yn
        tyn = record.get("transport_yn")
        if tyn is not None:
            tyn = str(tyn).strip().upper()
            record["transport_yn"] = "Y" if tyn in ("Y", "O", "OUI", "YES", "1") else "N"
        else:
            record["transport_yn"] = "N"

        record["transport"] = float(record.get("transport") or 0)
        record["mensualite"] = float(record.get("mensualite") or 0)
        record["annee_scolaire"] = annee_scolaire
        record["statut"] = "Actif"

        # Validate required fields
        missing = [f for f in REQUIRED_FIELDS if not record.get(f)]
        if missing:
            errors.append(f"Ligne {idx + 2}: champs manquants -> {', '.join(missing)}")
            continue

        # Generate matricule if missing
        matricule = record.get("matricule")
        if matricule is None or str(matricule).strip() == "":
            record["matricule"] = Student.generate_matricule(annee_scolaire)
        else:
            record["matricule"] = str(matricule)

        # Detect duplicate (same matricule + annee_scolaire)
        existing = Student.get_by_matricule(record["matricule"], annee_scolaire)
        if existing:
            Student.update(existing["id"], record)
            updated += 1
        else:
            Student.create(record)
            inserted += 1

    return {"inserted": inserted, "updated": updated, "errors": errors}


def export_excel(students: list, file_path: str):
    """Export a list of student dicts to an Excel file using the template column order."""
    rows = []
    for s in students:
        row = {}
        for db_col, excel_col in DB_TO_EXCEL.items():
            row[excel_col] = s.get(db_col)
        rows.append(row)

    df = pd.DataFrame(rows, columns=list(DB_TO_EXCEL.values()))
    df.to_excel(file_path, index=False)
    return file_path


def generate_sample_excel(file_path: str):
    """Generate a sample Excel file matching the template structure."""
    sample_data = [
        {
            "Matricule": "2025-0001",
            "Eleve Nom": "ALAOUI",
            "Eleve Prénom": "IBTISSAM",
            "Mere": "FATIMA EZZAHRA",
            "Père": "MOHAMED",
            "Date of birth": "2015-03-12",
            "City of birth": "Casablanca",
            "Adress": "12 Rue Hassan II, Casablanca",
            "Père telephone": "0612345678",
            "Mere telephone": "0623456789",
            "Classe": "CE1",
            "Inscription": "2025-09-01",
            "Transport (Y/N)": "N",
            "Transport": 0,
            "Mensualité": 800,
            "Note/Date": "",
        },
        {
            "Matricule": "2025-0002",
            "Eleve Nom": "ROUKI",
            "Eleve Prénom": "SAMI",
            "Mere": "KHADIJA",
            "Père": "YOUSSEF",
            "Date of birth": "2014-11-05",
            "City of birth": "Rabat",
            "Adress": "5 Avenue Mohammed V, Rabat",
            "Père telephone": "0698765432",
            "Mere telephone": "0687654321",
            "Classe": "CM1",
            "Inscription": "2025-09-01",
            "Transport (Y/N)": "Y",
            "Transport": 400,
            "Mensualité": 2000,
            "Note/Date": "",
        },
    ]
    df = pd.DataFrame(sample_data)
    df.to_excel(file_path, index=False)
    return file_path
