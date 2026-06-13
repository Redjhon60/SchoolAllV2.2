"""
Payment Model
=============
Handles creation and retrieval of payment records, automatic
receipt number generation, and payment history queries.
"""

from datetime import datetime
from database.db_manager import DatabaseManager
from utils.payment_constants import (
    SCHOOL_MONTHS, MONTH_CALENDAR_MAP, STATUS_PAYE, STATUS_UNPAID, STATUS_NAN,
)
from models.payment_student import PaymentStudent


class Payment:

    # ------------------------------------------------------------------
    # Receipt numbering
    # ------------------------------------------------------------------
    @staticmethod
    def generate_receipt_number() -> str:
        """
        Generate a unique, sequential receipt number, e.g. REC-2026-000123.
        Uses a counter stored in settings to guarantee uniqueness even
        across re-imports.
        """
        db = DatabaseManager()
        last_seq = int(db.get_setting("last_receipt_seq", "0") or "0")
        next_seq = last_seq + 1
        db.set_setting("last_receipt_seq", str(next_seq))
        year = datetime.now().year
        return f"REC-{year}-{next_seq:06d}"

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @staticmethod
    def create(data: dict) -> int:
        """
        Insert a payment record. Expected keys:
        payment_student_id, annee_scolaire, payment_type, month (optional),
        amount, payment_date, notes (optional), receipt_number (optional)
        """
        db = DatabaseManager()
        data = dict(data)
        data.setdefault("date_creation", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if not data.get("receipt_number"):
            data["receipt_number"] = Payment.generate_receipt_number()

        columns = [
            "payment_student_id", "annee_scolaire", "payment_type", "month",
            "amount", "payment_date", "notes", "receipt_number", "date_creation",
        ]
        columns = [c for c in columns if c in data]
        placeholders = ", ".join(["?"] * len(columns))
        values = [data.get(c) for c in columns]

        query = f"INSERT INTO payments ({', '.join(columns)}) VALUES ({placeholders})"
        cursor = db.execute(query, values)
        return cursor.lastrowid

    @staticmethod
    def get_by_id(payment_id: int):
        db = DatabaseManager()
        return db.fetchone("SELECT * FROM payments WHERE id = ?", (payment_id,))

    @staticmethod
    def get_history(payment_student_id: int, annee_scolaire: str = None):
        db = DatabaseManager()
        if annee_scolaire:
            return db.fetchall(
                "SELECT * FROM payments WHERE payment_student_id = ? AND annee_scolaire = ? "
                "ORDER BY payment_date DESC, id DESC",
                (payment_student_id, annee_scolaire),
            )
        return db.fetchall(
            "SELECT * FROM payments WHERE payment_student_id = ? ORDER BY payment_date DESC, id DESC",
            (payment_student_id,),
        )

    # ------------------------------------------------------------------
    # Full save workflow: register payment + update month status + total
    # ------------------------------------------------------------------
    @staticmethod
    def register_payment(payment_student_id: int, annee_scolaire: str, payment_type: str,
                          month: str, amount: float, payment_date: str, notes: str = "") -> dict:
        """
        Save a payment, mark the relevant month as PAYE (if applicable),
        and return the created payment record dict (with receipt_number).
        """
        payment_id = Payment.create({
            "payment_student_id": payment_student_id,
            "annee_scolaire": annee_scolaire,
            "payment_type": payment_type,
            "month": month or None,
            "amount": amount,
            "payment_date": payment_date,
            "notes": notes,
        })

        # If this payment corresponds to a monthly fee (Mensualité), mark the
        # month as paid.
        if month and payment_type == "Mensualité":
            PaymentStudent.set_month_status(payment_student_id, annee_scolaire, month, STATUS_PAYE)

        return Payment.get_by_id(payment_id)

    # ------------------------------------------------------------------
    # Aggregations for dashboard
    # ------------------------------------------------------------------
    @staticmethod
    def total_inscription_revenue(annee_scolaire: str, classe: str = None) -> float:
        db = DatabaseManager()
        query = (
            "SELECT COALESCE(SUM(p.amount), 0) as total FROM payments p "
            "JOIN payment_students ps ON p.payment_student_id = ps.id "
            "WHERE p.annee_scolaire = ? AND p.payment_type = 'Inscription'"
        )
        params = [annee_scolaire]
        if classe and classe != "Toutes":
            query += " AND ps.classe = ?"
            params.append(classe)
        row = db.fetchone(query, params)
        return row["total"] if row else 0.0

    @staticmethod
    def monthly_income(annee_scolaire: str, calendar_year: int, calendar_month: int, classe: str = None) -> float:
        """Total income (all payment types) collected during a given calendar month."""
        db = DatabaseManager()
        pattern = f"{calendar_year:04d}-{calendar_month:02d}%"
        query = (
            "SELECT COALESCE(SUM(p.amount), 0) as total FROM payments p "
            "JOIN payment_students ps ON p.payment_student_id = ps.id "
            "WHERE p.annee_scolaire = ? AND p.payment_date LIKE ?"
        )
        params = [annee_scolaire, pattern]
        if classe and classe != "Toutes":
            query += " AND ps.classe = ?"
            params.append(classe)
        row = db.fetchone(query, params)
        return row["total"] if row else 0.0

    @staticmethod
    def monthly_income_evolution(annee_scolaire: str, classe: str = None):
        """
        Returns a list of dicts per school-year month (Sep->Jun):
        {month, inscription, mensualite, transport, total}
        based on payment_date falling in that calendar month.
        """
        db = DatabaseManager()
        start_year = int(annee_scolaire.split("/")[0])
        end_year = int(annee_scolaire.split("/")[1])

        results = []
        for month_name in SCHOOL_MONTHS:
            cal_month, offset = MONTH_CALENDAR_MAP[month_name]
            cal_year = start_year if offset == 0 else end_year
            pattern = f"{cal_year:04d}-{cal_month:02d}%"

            row_data = {"month": month_name}
            for ptype, key in (("Inscription", "inscription"), ("Mensualité", "mensualite"), ("Transport", "transport")):
                query = (
                    "SELECT COALESCE(SUM(p.amount), 0) as total FROM payments p "
                    "JOIN payment_students ps ON p.payment_student_id = ps.id "
                    "WHERE p.annee_scolaire = ? AND p.payment_date LIKE ? AND p.payment_type = ?"
                )
                params = [annee_scolaire, pattern, ptype]
                if classe and classe != "Toutes":
                    query += " AND ps.classe = ?"
                    params.append(classe)
                row = db.fetchone(query, params)
                row_data[key] = row["total"] if row else 0.0

            row_data["total"] = row_data["inscription"] + row_data["mensualite"] + row_data["transport"]
            results.append(row_data)

        return results

    @staticmethod
    def payment_status_distribution(annee_scolaire: str, classe: str = None):
        """
        Returns {'PAYE': n, 'UNPAID': n, 'NAN': n} aggregated counts of
        month_status rows across all students for the given year/class.
        """
        db = DatabaseManager()
        query = (
            "SELECT ms.status, COUNT(*) as cnt FROM month_status ms "
            "JOIN payment_students ps ON ms.payment_student_id = ps.id "
            "WHERE ms.annee_scolaire = ?"
        )
        params = [annee_scolaire]
        if classe and classe != "Toutes":
            query += " AND ps.classe = ?"
            params.append(classe)
        query += " GROUP BY ms.status"

        rows = db.fetchall(query, params)
        result = {STATUS_PAYE: 0, STATUS_UNPAID: 0, STATUS_NAN: 0}
        for r in rows:
            if r["status"] in result:
                result[r["status"]] = r["cnt"]
        return result

    @staticmethod
    def income_by_class(annee_scolaire: str):
        """Returns list of (classe, total_revenue) sorted by class."""
        db = DatabaseManager()
        rows = db.fetchall(
            "SELECT ps.classe as classe, COALESCE(SUM(p.amount), 0) as total "
            "FROM payments p JOIN payment_students ps ON p.payment_student_id = ps.id "
            "WHERE p.annee_scolaire = ? GROUP BY ps.classe ORDER BY ps.classe",
            (annee_scolaire,),
        )
        return [(r["classe"] or "N/A", r["total"]) for r in rows]
