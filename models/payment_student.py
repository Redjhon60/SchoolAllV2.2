"""
Payment Student Model
======================
Represents a student record within the payment module
(payment_students table) and provides CRUD + lookup helpers.
"""

from datetime import datetime
from database.db_manager import DatabaseManager
from utils.payment_constants import SCHOOL_MONTHS, STATUS_UNPAID, STATUS_NAN, STATUS_PAYE


class PaymentStudent:

    COLUMNS = [
        "matricule", "nom", "prenom", "classe", "inscription",
        "transport", "mensualite", "total_a_payer", "note_date",
        "annee_scolaire", "date_creation",
    ]

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @staticmethod
    def create(data: dict) -> int:
        db = DatabaseManager()
        data = dict(data)
        data.setdefault("date_creation", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        columns = [c for c in PaymentStudent.COLUMNS if c in data]
        placeholders = ", ".join(["?"] * len(columns))
        values = [data.get(c) for c in columns]

        query = f"INSERT INTO payment_students ({', '.join(columns)}) VALUES ({placeholders})"
        cursor = db.execute(query, values)
        return cursor.lastrowid

    @staticmethod
    def update(student_id: int, data: dict):
        db = DatabaseManager()
        columns = [c for c in PaymentStudent.COLUMNS if c in data]
        set_clause = ", ".join([f"{c} = ?" for c in columns])
        values = [data.get(c) for c in columns]
        values.append(student_id)
        query = f"UPDATE payment_students SET {set_clause} WHERE id = ?"
        db.execute(query, values)

    @staticmethod
    def get_by_id(student_id: int):
        db = DatabaseManager()
        return db.fetchone("SELECT * FROM payment_students WHERE id = ?", (student_id,))

    @staticmethod
    def get_by_key(matricule: str, classe: str, annee_scolaire: str):
        db = DatabaseManager()
        return db.fetchone(
            "SELECT * FROM payment_students WHERE matricule = ? AND classe = ? AND annee_scolaire = ?",
            (str(matricule), classe, annee_scolaire),
        )

    @staticmethod
    def search(annee_scolaire: str = None, classe: str = None, search: str = None):
        """Search payment students with optional filters."""
        db = DatabaseManager()
        query = "SELECT * FROM payment_students WHERE 1=1"
        params = []

        if annee_scolaire:
            query += " AND annee_scolaire = ?"
            params.append(annee_scolaire)
        if classe and classe != "Toutes":
            query += " AND classe = ?"
            params.append(classe)
        if search:
            query += " AND (nom LIKE ? OR prenom LIKE ? OR matricule LIKE ? OR classe LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like, like, like])

        query += " ORDER BY nom ASC, prenom ASC"
        return db.fetchall(query, params)

    @staticmethod
    def get_distinct_classes(annee_scolaire: str = None):
        db = DatabaseManager()
        if annee_scolaire:
            rows = db.fetchall(
                "SELECT DISTINCT classe FROM payment_students WHERE annee_scolaire = ? "
                "AND classe IS NOT NULL AND classe != '' ORDER BY classe",
                (annee_scolaire,),
            )
        else:
            rows = db.fetchall(
                "SELECT DISTINCT classe FROM payment_students WHERE classe IS NOT NULL "
                "AND classe != '' ORDER BY classe"
            )
        return [r["classe"] for r in rows]

    @staticmethod
    def count_all(annee_scolaire: str = None) -> int:
        db = DatabaseManager()
        if annee_scolaire:
            row = db.fetchone(
                "SELECT COUNT(*) as cnt FROM payment_students WHERE annee_scolaire = ?",
                (annee_scolaire,),
            )
        else:
            row = db.fetchone("SELECT COUNT(*) as cnt FROM payment_students")
        return row["cnt"] if row else 0

    # ------------------------------------------------------------------
    # Month status helpers
    # ------------------------------------------------------------------
    @staticmethod
    def get_month_statuses(payment_student_id: int, annee_scolaire: str) -> dict:
        """Return {month_name: status} for all 10 school months."""
        db = DatabaseManager()
        rows = db.fetchall(
            "SELECT month, status FROM month_status WHERE payment_student_id = ? AND annee_scolaire = ?",
            (payment_student_id, annee_scolaire),
        )
        statuses = {r["month"]: r["status"] for r in rows}
        # Ensure all months present (default UNPAID if missing)
        for m in SCHOOL_MONTHS:
            statuses.setdefault(m, STATUS_UNPAID)
        return statuses

    @staticmethod
    def set_month_status(payment_student_id: int, annee_scolaire: str, month: str, status: str):
        db = DatabaseManager()
        db.execute(
            "INSERT INTO month_status (payment_student_id, annee_scolaire, month, status) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(payment_student_id, annee_scolaire, month) DO UPDATE SET status = excluded.status",
            (payment_student_id, annee_scolaire, month, status),
        )

    @staticmethod
    def get_next_unpaid_month(payment_student_id: int, annee_scolaire: str):
        """
        Return the first month (in chronological order) with status UNPAID,
        ignoring NAN and PAYE months. Returns None if all months are paid/NAN.
        """
        statuses = PaymentStudent.get_month_statuses(payment_student_id, annee_scolaire)
        for month in SCHOOL_MONTHS:
            if statuses.get(month) == STATUS_UNPAID:
                return month
        return None

    # ------------------------------------------------------------------
    # Total paid
    # ------------------------------------------------------------------
    @staticmethod
    def get_total_paid(payment_student_id: int, annee_scolaire: str) -> float:
        db = DatabaseManager()
        row = db.fetchone(
            "SELECT COALESCE(SUM(amount), 0) as total FROM payments "
            "WHERE payment_student_id = ? AND annee_scolaire = ?",
            (payment_student_id, annee_scolaire),
        )
        return row["total"] if row else 0.0
