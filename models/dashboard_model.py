"""
Dashboard Model
================
Aggregates statistics and chart data used by the Dashboard view.
"""

from database.db_manager import DatabaseManager


class DashboardModel:

    @staticmethod
    def kpi_current_year_count(annee_scolaire: str) -> int:
        """Number of students enrolled (Actif) for the current school year."""
        db = DatabaseManager()
        row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM students WHERE annee_scolaire = ? AND statut = 'Actif'",
            (annee_scolaire,),
        )
        return row["cnt"] if row else 0

    @staticmethod
    def kpi_pre_registered_next_year(next_year: str) -> int:
        """Number of students pre-registered for next year (created via re-inscription)."""
        db = DatabaseManager()
        row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM students WHERE annee_scolaire = ?",
            (next_year,),
        )
        return row["cnt"] if row else 0

    @staticmethod
    def kpi_new_registrations_this_month(annee_scolaire: str, year: int, month: int) -> int:
        """Count of students whose date_creation falls in the given year/month."""
        db = DatabaseManager()
        pattern = f"{year:04d}-{month:02d}%"
        row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM students WHERE annee_scolaire = ? "
            "AND date_creation LIKE ?",
            (annee_scolaire, pattern),
        )
        return row["cnt"] if row else 0

    @staticmethod
    def kpi_transport_users(annee_scolaire: str) -> int:
        db = DatabaseManager()
        row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM students WHERE annee_scolaire = ? "
            "AND statut = 'Actif' AND (transport_yn = 'Y' OR transport_yn = 'O')",
            (annee_scolaire,),
        )
        return row["cnt"] if row else 0

    @staticmethod
    def students_per_class(annee_scolaire: str):
        """Returns list of (classe, count) for bar chart."""
        db = DatabaseManager()
        rows = db.fetchall(
            "SELECT classe, COUNT(*) as cnt FROM students WHERE annee_scolaire = ? "
            "AND statut = 'Actif' GROUP BY classe ORDER BY classe",
            (annee_scolaire,),
        )
        return [(r["classe"] or "N/A", r["cnt"]) for r in rows]

    @staticmethod
    def monthly_registrations(annee_scolaire: str):
        """
        Returns counts of new registrations per month for the school year
        (Sept -> June). Based on date_creation.
        """
        db = DatabaseManager()
        # School year months mapping: Sep(9) Oct(10) Nov(11) Dec(12) Jan(1)...Jun(6)
        start_year = int(annee_scolaire.split("/")[0])
        end_year = int(annee_scolaire.split("/")[1])
        months = []
        for m in range(9, 13):
            months.append((start_year, m))
        for m in range(1, 7):
            months.append((end_year, m))

        results = []
        for (yr, mo) in months:
            pattern = f"{yr:04d}-{mo:02d}%"
            row = db.fetchone(
                "SELECT COUNT(*) as cnt FROM students WHERE annee_scolaire = ? "
                "AND date_creation LIKE ?",
                (annee_scolaire, pattern),
            )
            results.append((f"{mo:02d}/{yr}", row["cnt"] if row else 0))
        return results

    @staticmethod
    def reinscription_progress(current_year: str, next_year: str):
        """
        Returns (re_inscribed_count, total_eligible_count) for the donut chart.
        Eligible = active students of current_year.
        Re-inscribed = students that exist in next_year with same matricule prefix
        (here: matched by name+matricule existing in next_year table).
        """
        db = DatabaseManager()
        eligible_row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM students WHERE annee_scolaire = ? AND statut = 'Actif'",
            (current_year,),
        )
        eligible = eligible_row["cnt"] if eligible_row else 0

        reinscribed_row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM students WHERE annee_scolaire = ?",
            (next_year,),
        )
        reinscribed = reinscribed_row["cnt"] if reinscribed_row else 0

        return reinscribed, eligible

    @staticmethod
    def departures_by_month(annee_scolaire: str):
        """
        Returns list of (month_label, count) of students marked 'Parti'
        whose note_date falls in each month of the school year.
        """
        db = DatabaseManager()
        start_year = int(annee_scolaire.split("/")[0])
        end_year = int(annee_scolaire.split("/")[1])
        months = []
        for m in range(9, 13):
            months.append((start_year, m))
        for m in range(1, 7):
            months.append((end_year, m))

        results = []
        for (yr, mo) in months:
            pattern = f"{yr:04d}-{mo:02d}%"
            row = db.fetchone(
                "SELECT COUNT(*) as cnt FROM students WHERE annee_scolaire = ? "
                "AND statut = 'Parti' AND note_date LIKE ?",
                (annee_scolaire, pattern),
            )
            results.append((f"{mo:02d}/{yr}", row["cnt"] if row else 0))
        return results

    @staticmethod
    def transport_users_by_class(annee_scolaire: str):
        """Returns list of (classe, count) of transport users for pie chart."""
        db = DatabaseManager()
        rows = db.fetchall(
            "SELECT classe, COUNT(*) as cnt FROM students WHERE annee_scolaire = ? "
            "AND statut = 'Actif' AND (transport_yn = 'Y' OR transport_yn = 'O') "
            "GROUP BY classe ORDER BY classe",
            (annee_scolaire,),
        )
        return [(r["classe"] or "N/A", r["cnt"]) for r in rows if r["cnt"] > 0]
