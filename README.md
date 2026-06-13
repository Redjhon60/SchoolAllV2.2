# Le Schéma SGS — Private School Management System

A modern, professional desktop application for managing a private school,
built with **Python 3.12**, **CustomTkinter**, **SQLite**, **Pandas/OpenPyXL**
and **Matplotlib**, following an **MVC architecture**.

---

## ✨ Features

- **Modern ERP-style dashboard** with KPI cards and 5 dynamic charts
  (students per class, monthly registrations, re-inscription progress,
  departures by month, transport users by class).
- **Collapsible animated sidebar** with icons and active-page highlighting.
- **Gestion Élèves**: searchable, sortable, paginated table with
  view / edit / delete / print actions, Excel import & export.
- **Nouvelle Inscription**: modern registration form with auto matricule
  generation, validation and instant save.
- **Réinscription**: select students from the current year and generate
  next-year records in one click, preserving all data.
- **Gestion des Paiements**: search/select students, view color-coded
  monthly payment status (Payé / Non payé / Non inscrit), automatic
  next-unpaid-month detection, register payments (Inscription, Mensualité,
  Transport), and auto-generate PDF receipts with unique receipt numbers.
- **Dark / Light mode** with persisted preference.
- **Automatic database backup** from the Settings page.
- **Printable student cards** (PDF) via ReportLab.
- **Toast notifications**, **confirmation dialogs**, and **loading spinners**
  for a polished UX.

---

## 🗂️ Project Structure

```
school_app/
├── main.py                     # Application entry point
├── init_db.py                  # Database initialization / seed script
├── requirements.txt
├── README.md
├── database/
│   └── db_manager.py           # SQLite connection & schema
├── models/
│   ├── student.py              # Student CRUD operations
│   ├── dashboard_model.py       # Dashboard statistics queries
│   ├── payment_student.py       # Payment-module student records & month statuses
│   └── payment.py                # Payment records, receipts, financial KPIs
├── views/
│   ├── sidebar.py               # Collapsible animated sidebar
│   ├── dashboard_page.py        # Dashboard (KPIs + charts)
│   ├── gestion_eleves_page.py   # Student management table
│   ├── nouvelle_inscription_page.py  # Registration form
│   ├── reinscription_page.py    # Re-inscription workflow
│   ├── gestion_paiements_page.py # Payment management module (table view)
│   ├── payment_student_detail_dialog.py # Payment student detail popup
│   ├── settings_page.py         # Settings (theme, school year, backup)
│   ├── student_profile_dialog.py # Student profile modal
│   └── widgets.py                # KPI cards, dialogs, toasts, spinner
├── utils/
│   ├── theme.py                  # Colors, fonts, layout constants
│   ├── excel_handler.py          # Student Excel import/export logic
│   ├── payment_excel_handler.py  # Payment Excel import logic
│   ├── payment_constants.py      # Month list, status colors/labels
│   ├── validators.py             # Form validation helpers
│   ├── card_printer.py           # PDF student card generator
│   ├── receipt_generator.py      # PDF payment receipt generator
│   └── printer.py                # Sends generated PDFs to the default printer
├── assets/
│   ├── sample/                   # Sample & template Excel files
│   └── exports/                  # Generated PDFs/exports (runtime)
└── data/                          # SQLite database & backups (created at runtime)
```

---

## 🚀 Installation

See `INSTALL.md` for full setup instructions. Quick start:

```bash
pip install -r requirements.txt
python init_db.py --sample   # optional: seed with sample students
python main.py
```

---

## 📊 Database Schema

Table `students`:

| Column          | Type | Description                          |
|------------------|------|---------------------------------------|
| matricule        | TEXT | Unique student ID (auto-generated)     |
| eleve_nom        | TEXT | Last name                              |
| eleve_prenom     | TEXT | First name                             |
| mere / pere      | TEXT | Parents' names                         |
| date_of_birth    | TEXT | Date of birth (YYYY-MM-DD)             |
| city_of_birth    | TEXT | City of birth                          |
| adresse          | TEXT | Address                                |
| pere_telephone   | TEXT | Father's phone                         |
| mere_telephone   | TEXT | Mother's phone                         |
| classe           | TEXT | Class                                  |
| inscription      | TEXT | Registration date                      |
| transport_yn     | TEXT | "Y" or "N"                              |
| transport        | REAL | Transport fee                          |
| mensualite       | REAL | Monthly tuition fee                    |
| note_date        | TEXT | Free-text note / date                  |
| annee_scolaire   | TEXT | School year (e.g. "2025/2026")         |
| date_creation    | TEXT | Record creation timestamp              |
| statut           | TEXT | "Actif" or "Parti"                     |

Table `settings`: simple key/value store (theme, school name, school years).

Payment module tables:

- `payment_students`: one row per (matricule, classe, année scolaire) from
  the payments import — matricule, nom, prénom, classe, inscription,
  transport, mensualité, total à payer, note/date, année scolaire.
- `month_status`: one row per (payment_student, month, année scolaire) with
  status `PAYE`, `UNPAID`, or `NAN`.
- `payments`: full payment history — type, month, amount, date, notes,
  unique receipt number. Remains intact across re-imports.
- `receipts`: receipt metadata linking receipt numbers to generated PDF files.

---

## 📥 Excel Import Format

The import expects the same columns as `assets/sample/template_eleves.xlsx`:

`Matricule, Eleve Nom, Eleve Prénom, Mere, Père, Date of birth, City of birth,
Adress, Père telephone, Mere telephone, Classe, Inscription,
Transport (Y/N), Transport, Mensualité, Note/Date`

Rows missing `Eleve Nom`, `Eleve Prénom` or `Classe` are rejected with an
error message. Existing students (matched by matricule + school year) are
updated; new ones are inserted with an auto-generated matricule if blank.

---

## 💰 Gestion des Paiements Module

### Excel Import Format

The payment import expects the columns from `assets/sample/template_paiements.xlsx`:

`Matricule, Nom, Prénom, Classe, Inscription, Transport, Mensualité,
Total a payé, Note/Date, Year, Septembre, Octobre, Novembre, Décembre,
Janvier, Février, Mars, Avril, Mai, Juin`

Each monthly column accepts one of three values:

| Value      | Meaning                          | Color  |
|------------|-----------------------------------|--------|
| `Payé`     | Paid for that month                | Green  |
| *(empty)*  | Enrolled, not yet paid             | Red    |
| `NAN`      | Not enrolled that month             | Gray   |

### Next Payment Detection

The app automatically suggests the next payment month by scanning
Septembre → Juin in order, skipping months marked `NAN` or `Payé`, and
proposing the first month marked unpaid.

### Student List & Detail Popup

**Gestion des Paiements** displays a searchable, sortable, paginated table
of all students (same UX as Gestion des Élèves), with columns for
Matricule, Nom, Prénom, Classe, Mensualité, Total Payé, and the next due
month (highlighted green "À jour" or red with the month name if a payment
is due).

Clicking any row (or the "Détails / Paiement" action) opens a popup
showing:

- Full student information (matricule, classe, année scolaire,
  inscription, transport, mensualité, total à payer, total payé, notes).
- **Statut Mensuel** — color-coded chips for Septembre → Juin
  (green = Payé, red = Non payé, gray = Non inscrit).
- An **Ajouter Paiement** form, pre-filled with the suggested month and
  amount.
- Complete **payment history** table (type, month, amount, date, receipt
  number, notes).

### Registering a Payment

From the student detail popup, fill in:

- **Payment Type**: Inscription, Mensualité, or Transport
- **Month** (auto-suggested for Mensualité)
- **Amount**, **Payment Date**, **Notes**

Clicking **Enregistrer Paiement**:

1. Saves the payment record (with a unique receipt number `REC-YYYY-NNNNNN`).
2. Marks the corresponding month as **Payé** (for Mensualité payments).
3. Updates the student's total paid amount — reflected immediately in the
   popup and in the table after closing.
4. Generates a PDF receipt in `assets/exports/receipts/`.
5. **Automatically sends the receipt to the default printer** (Windows:
   via the registered "print" handler; macOS/Linux: via `lp`/CUPS if
   available). If silent printing isn't possible on the current system,
   a toast notification indicates the PDF was generated for manual printing.
6. Refreshes the Dashboard's financial KPIs and charts automatically.

### Dashboard Additions

- **Total Inscription Revenue** — sum of all "Inscription" payments for the
  selected year/class.
- **Monthly Student Income** — total income collected during the selected
  month (recalculates with year/class/month filters).
- **Évolution des revenus mensuels** — line chart of Inscription,
  Mensualité, and Transport revenue per school month.
- **Répartition des statuts de paiement** — pie chart of Payé / Non payé /
  Non inscrit counts.
- **Revenus par classe** — bar chart of total revenue per class.

---

## 🏗️ Building a Windows .exe (CI/CD)

This repo includes a GitHub Actions workflow at
`.github/workflows/build-exe.yml` that automatically builds a standalone
Windows executable using **PyInstaller**.

**How it works:**

- On every push to `main`/`master` (and on pull requests), the workflow
  runs on `windows-latest`, installs dependencies, and runs:
  ```bash
  pyinstaller schema_sgs.spec
  ```
- The resulting `LeSchemaSGS.exe`, plus `assets/`, `README.md` and
  `INSTALL.md`, are uploaded as a build artifact (**Actions → workflow run
  → Artifacts**).
- When you push a tag like `v1.0.0`, the workflow additionally zips the
  bundle and attaches it to a **GitHub Release**.

**To trigger a release:**

```bash
git tag v1.0.0
git push origin v1.0.0
```

**To build locally on Windows:**

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller schema_sgs.spec
```

The `.exe` will be in `dist/LeSchemaSGS.exe`. Place it alongside the
`assets/` folder (a `data/` folder will be created automatically next to
the `.exe` on first run for the database).

---

## 🎨 Design

| Token        | Color     |
|--------------|-----------|
| Primary      | `#2563EB` |
| Secondary    | `#3B82F6` |
| Success      | `#22C55E` |
| Warning      | `#F59E0B` |
| Background   | `#F8FAFC` |

Cards use rounded corners (14px), subtle borders, and hover highlighting.
