"""
Database Initialization Script
================================
Run this script once to create the SQLite database and tables.
This is also done automatically the first time the app runs,
but this script can be used to reset / re-create the schema
or to seed it with sample data.

Usage:
    python init_db.py            # create empty database
    python init_db.py --sample   # create database + insert sample students
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager, DB_PATH
from models.student import Student


SAMPLE_STUDENTS = [
    {
        "matricule": "2025-0001", "eleve_nom": "ALAOUI", "eleve_prenom": "IBTISSAM",
        "mere": "FATIMA EZZAHRA", "pere": "MOHAMED", "date_of_birth": "2015-03-12",
        "city_of_birth": "Casablanca", "adresse": "12 Rue Hassan II, Casablanca",
        "pere_telephone": "0612345678", "mere_telephone": "0623456789",
        "classe": "CE1", "inscription": "2025-09-01", "transport_yn": "N",
        "transport": 0, "mensualite": 800, "note_date": "",
        "annee_scolaire": "2025/2026", "statut": "Actif",
    },
    {
        "matricule": "2025-0002", "eleve_nom": "ROUKI", "eleve_prenom": "SAMI",
        "mere": "KHADIJA", "pere": "YOUSSEF", "date_of_birth": "2014-11-05",
        "city_of_birth": "Rabat", "adresse": "5 Avenue Mohammed V, Rabat",
        "pere_telephone": "0698765432", "mere_telephone": "0687654321",
        "classe": "CM1", "inscription": "2025-09-01", "transport_yn": "Y",
        "transport": 400, "mensualite": 2000, "note_date": "",
        "annee_scolaire": "2025/2026", "statut": "Actif",
    },
    {
        "matricule": "2025-0003", "eleve_nom": "FARES", "eleve_prenom": "JAD",
        "mere": "SOUAD", "pere": "KARIM", "date_of_birth": "2016-01-20",
        "city_of_birth": "Marrakech", "adresse": "8 Rue Yacoub El Mansour, Marrakech",
        "pere_telephone": "0611223344", "mere_telephone": "0622334455",
        "classe": "CP1", "inscription": "2025-09-02", "transport_yn": "Y",
        "transport": 300, "mensualite": 1000, "note_date": "",
        "annee_scolaire": "2025/2026", "statut": "Actif",
    },
]


def main():
    db = DatabaseManager()
    print(f"Base de données initialisée: {DB_PATH}")

    if "--sample" in sys.argv:
        for s in SAMPLE_STUDENTS:
            existing = Student.get_by_matricule(s["matricule"], s["annee_scolaire"])
            if not existing:
                Student.create(s)
        print(f"{len(SAMPLE_STUDENTS)} élèves d'exemple ajoutés.")

    print("Terminé.")


if __name__ == "__main__":
    main()
