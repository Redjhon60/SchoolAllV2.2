"""
Student Model
=============
Represents a student record and provides CRUD operations
against the SQLite database via DatabaseManager.
"""

from datetime import datetime
from database.db_manager import DatabaseManager


class Student:
    """Data access object for the `students` table."""

    COLUMNS = [
        "matricule", "eleve_nom", "eleve_prenom", "mere", "pere",
        "date_of_birth", "city_of_birth", "adresse", "pere_telephone",
        "mere_telephone", "classe", "inscription", "transport_yn",
        "transport", "mensualite", "note_date", "annee_scolaire",
        "date_creation", "statut",
    ]

    def __init__(self, **kwargs):
        for col in self.COLUMNS:
            setattr(self, col, kwargs.get(col))
        self.id = kwargs.get("id")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @staticmethod
    def create(data: dict) -> int:
        """Insert a new student record. Returns new row id."""
        db = DatabaseManager()
        data = dict(data)
        data.setdefault("date_creation", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        data.setdefault("statut", "Actif")

        columns = [c for c in Student.COLUMNS if c in data]
        placeholders = ", ".join(["?"] * len(columns))
        values = [data.get(c) for c in columns]

        query = f"INSERT INTO students ({', '.join(columns)}) VALUES ({placeholders})"
        cursor = db.execute(query, values)
        return cursor.lastrowid

    @staticmethod
    def update(student_id: int, data: dict):
        """Update an existing student record by id."""
        db = DatabaseManager()
        columns = [c for c in Student.COLUMNS if c in data]
        set_clause = ", ".join([f"{c} = ?" for c in columns])
        values = [data.get(c) for c in columns]
        values.append(student_id)

        query = f"UPDATE students SET {set_clause} WHERE id = ?"
        db.execute(query, values)

    @staticmethod
    def delete(student_id: int):
        db = DatabaseManager()
        db.execute("DELETE FROM students WHERE id = ?", (student_id,))

    @staticmethod
    def get_by_id(student_id: int):
        db = DatabaseManager()
        return db.fetchone("SELECT * FROM students WHERE id = ?", (student_id,))

    @staticmethod
    def get_by_matricule(matricule: str, annee_scolaire: str = None):
        db = DatabaseManager()
        if annee_scolaire:
            return db.fetchone(
                "SELECT * FROM students WHERE matricule = ? AND annee_scolaire = ?",
                (matricule, annee_scolaire),
            )
        return db.fetchone("SELECT * FROM students WHERE matricule = ?", (matricule,))

    @staticmethod
    def get_all(annee_scolaire: str = None, classe: str = None, search: str = None,
                statut: str = None):
        """Fetch students with optional filters."""
        db = DatabaseManager()
        query = "SELECT * FROM students WHERE 1=1"
        params = []

        if annee_scolaire:
            query += " AND annee_scolaire = ?"
            params.append(annee_scolaire)
        if classe and classe != "Toutes":
            query += " AND classe = ?"
            params.append(classe)
        if statut:
            query += " AND statut = ?"
            params.append(statut)
        if search:
            query += (
                " AND (eleve_nom LIKE ? OR eleve_prenom LIKE ? OR matricule LIKE ?"
                " OR classe LIKE ? OR pere_telephone LIKE ? OR mere_telephone LIKE ?)"
            )
            like = f"%{search}%"
            params.extend([like, like, like, like, like, like])

        query += " ORDER BY eleve_nom ASC, eleve_prenom ASC"
        return db.fetchall(query, params)

    @staticmethod
    def get_distinct_classes(annee_scolaire: str = None):
        db = DatabaseManager()
        if annee_scolaire:
            rows = db.fetchall(
                "SELECT DISTINCT classe FROM students WHERE annee_scolaire = ? "
                "AND classe IS NOT NULL AND classe != '' ORDER BY classe",
                (annee_scolaire,),
            )
        else:
            rows = db.fetchall(
                "SELECT DISTINCT classe FROM students WHERE classe IS NOT NULL "
                "AND classe != '' ORDER BY classe"
            )
        return [r["classe"] for r in rows]

    @staticmethod
    def generate_matricule(annee_scolaire: str) -> str:
        """Generate the next sequential matricule for a given year, e.g. 2025-0001."""
        db = DatabaseManager()
        year_prefix = annee_scolaire.split("/")[0]
        row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM students WHERE matricule LIKE ?",
            (f"{year_prefix}-%",),
        )
        next_num = (row["cnt"] if row else 0) + 1
        return f"{year_prefix}-{next_num:04d}"

    @staticmethod
    def count_all(annee_scolaire: str = None, statut: str = None) -> int:
        db = DatabaseManager()
        query = "SELECT COUNT(*) as cnt FROM students WHERE 1=1"
        params = []
        if annee_scolaire:
            query += " AND annee_scolaire = ?"
            params.append(annee_scolaire)
        if statut:
            query += " AND statut = ?"
            params.append(statut)
        row = db.fetchone(query, params)
        return row["cnt"] if row else 0
