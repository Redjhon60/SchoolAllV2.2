"""
Database Manager
=================
Handles SQLite database connection, schema creation and provides
a simple interface for executing queries throughout the application.
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime


def _get_app_data_dir():
    """
    Return a writable directory for storing the database and backups.

    - When running from source: a 'data' folder next to the project root.
    - When running as a frozen PyInstaller .exe: a 'data' folder next to
      the executable (so the database persists across runs and updates).
    """
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data")


DB_DIR = _get_app_data_dir()
DB_PATH = os.path.join(DB_DIR, "school.db")
BACKUP_DIR = os.path.join(DB_DIR, "backups")


class DatabaseManager:
    """Singleton-style manager for the SQLite database connection."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        os.makedirs(DB_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._initialized = True

    # ------------------------------------------------------------------
    # Schema creation
    # ------------------------------------------------------------------
    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricule TEXT UNIQUE NOT NULL,
                eleve_nom TEXT NOT NULL,
                eleve_prenom TEXT NOT NULL,
                mere TEXT,
                pere TEXT,
                date_of_birth TEXT,
                city_of_birth TEXT,
                adresse TEXT,
                pere_telephone TEXT,
                mere_telephone TEXT,
                classe TEXT,
                inscription TEXT,
                transport_yn TEXT DEFAULT 'N',
                transport REAL DEFAULT 0,
                mensualite REAL DEFAULT 0,
                note_date TEXT,
                annee_scolaire TEXT,
                date_creation TEXT,
                statut TEXT DEFAULT 'Actif'
            )
        """)

        # Index to speed up lookups by school year / class / matricule
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_annee ON students(annee_scolaire)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_classe ON students(classe)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_matricule ON students(matricule)")

        # Settings table (key/value store for app settings, e.g. theme, current year)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # ------------------------------------------------------------
        # Payment Module Tables
        # ------------------------------------------------------------

        # payment_students: a dedicated record per (matricule, classe, annee_scolaire)
        # combination as found in the payments Excel file. This is intentionally
        # decoupled from `students` because payment matricules may not follow the
        # same numbering scheme and the same matricule can map to several
        # children/classes in the source spreadsheet.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricule TEXT NOT NULL,
                nom TEXT NOT NULL,
                prenom TEXT,
                classe TEXT,
                inscription TEXT,
                transport REAL DEFAULT 0,
                mensualite REAL DEFAULT 0,
                total_a_payer REAL DEFAULT 0,
                note_date TEXT,
                annee_scolaire TEXT NOT NULL,
                date_creation TEXT,
                UNIQUE (matricule, classe, annee_scolaire)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pay_students_annee ON payment_students(annee_scolaire)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pay_students_classe ON payment_students(classe)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pay_students_matricule ON payment_students(matricule)")

        # month_status: one row per (payment_student, month, annee_scolaire)
        # status is one of 'PAYE', 'UNPAID', 'NAN'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS month_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_student_id INTEGER NOT NULL,
                annee_scolaire TEXT NOT NULL,
                month TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'UNPAID',
                FOREIGN KEY (payment_student_id) REFERENCES payment_students(id) ON DELETE CASCADE,
                UNIQUE (payment_student_id, annee_scolaire, month)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_month_status_student ON month_status(payment_student_id)")

        # payments: full payment history (traceable even after re-import)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_student_id INTEGER NOT NULL,
                annee_scolaire TEXT NOT NULL,
                payment_type TEXT NOT NULL,
                month TEXT,
                amount REAL NOT NULL DEFAULT 0,
                payment_date TEXT NOT NULL,
                notes TEXT,
                receipt_number TEXT UNIQUE,
                date_creation TEXT,
                FOREIGN KEY (payment_student_id) REFERENCES payment_students(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(payment_student_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_annee ON payments(annee_scolaire)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_month ON payments(month)")

        # receipts: receipt metadata (kept separate for easy lookups / numbering)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_number TEXT UNIQUE NOT NULL,
                payment_id INTEGER NOT NULL,
                file_path TEXT,
                date_creation TEXT,
                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

        # Insert default settings if missing
        defaults = {
            "current_school_year": "2025/2026",
            "next_school_year": "2026/2027",
            "theme": "Light",
            "school_name": "Ecole Privee",
            "last_receipt_seq": "0",
        }
        for k, v in defaults.items():
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def execute(self, query, params=()):
        """Execute an INSERT/UPDATE/DELETE statement and commit."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetchall(self, query, params=()):
        """Run a SELECT query and return all rows as a list of dicts."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def fetchone(self, query, params=()):
        """Run a SELECT query and return a single row as a dict (or None)."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------
    def get_setting(self, key, default=None):
        row = self.fetchone("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------
    def backup_database(self):
        """Create a timestamped copy of the database file in the backups folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"school_backup_{timestamp}.db")
        self.conn.commit()
        shutil.copy2(DB_PATH, backup_path)
        return backup_path

    def close(self):
        self.conn.close()
