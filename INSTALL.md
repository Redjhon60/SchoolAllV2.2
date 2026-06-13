# Installation Guide — Le Schéma SGS

## 1. Prerequisites

- **Python 3.12** (or 3.10+) installed and available as `python` / `python3`
- `pip` package manager
- Windows, macOS, or Linux with a desktop environment (Tkinter requires a display)

> On Linux, if `tkinter` is missing, install it first:
> - Debian/Ubuntu: `sudo apt install python3-tk`
> - Fedora: `sudo dnf install python3-tkinter`

---

## 2. Get the project

Unzip the project folder, then open a terminal inside `school_app/`.

---

## 3. Create a virtual environment (recommended)

```bash
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

---

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `customtkinter` — modern UI framework
- `pandas` + `openpyxl` — Excel import/export
- `matplotlib` — dashboard charts
- `reportlab` — PDF student card generation

---

## 5. Initialize the database

```bash
python init_db.py
```

This creates `data/school.db` with the required tables.

To also populate the database with 3 sample students:

```bash
python init_db.py --sample
```

---

## 6. Run the application

```bash
python main.py
```

The application opens in a 1400×850 window. Resize as needed — the layout
is fully responsive.

---

## 7. First steps

1. Go to **Paramètres** to set your school name and confirm the current /
   next school year (defaults: `2025/2026` → `2026/2027`).
2. Go to **Nouvelle Inscription** to register your first students, or
3. Go to **Gestion Élèves → Importer Excel** and select
   `assets/sample/template_eleves.xlsx` (or your own file using the same
   columns) to bulk-import students.
4. View the **Dashboard** to see KPIs and charts update automatically.
5. At the end of the year, use **Réinscription** to roll selected students
   into the next school year.

---

## 8. Backups

From **Paramètres → Sauvegarde**, click "Créer une sauvegarde maintenant" to
copy the database into `data/backups/` with a timestamped filename.

---

## 9. Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named '_tkinter'` | Install the OS Tkinter package (see Prerequisites). |
| Charts not displaying | Ensure `matplotlib` installed correctly; restart the app. |
| Excel import errors | Confirm your file has the exact column headers from `template_eleves.xlsx`. |
| App window too small | Resize manually; minimum size is 1100×700. |
