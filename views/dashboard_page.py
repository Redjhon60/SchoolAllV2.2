"""
Dashboard Page
==============
Main landing page showing KPI cards and analytical charts
(students per class, registrations, re-inscriptions, departures,
transport usage). All charts update dynamically with filters.
"""

import customtkinter as ctk
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from utils.theme import COLORS, CHART_COLORS, font_title, font_subtitle, font_body
from models.dashboard_model import DashboardModel
from models.student import Student
from database.db_manager import DatabaseManager


class DashboardPage(ctk.CTkFrame):

    MONTHS_FR = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
        7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=("#F8FAFC", "#0F172A"), **kwargs)

        self.db = DatabaseManager()
        self.current_year = self.db.get_setting("current_school_year", "2025/2026")
        self.next_year = self.db.get_setting("next_school_year", "2026/2027")

        self.selected_year = ctk.StringVar(value=self.current_year)
        self.selected_class = ctk.StringVar(value="Toutes")
        now = datetime.now()
        self.selected_month_num = now.month
        self.selected_month = ctk.StringVar(value=self.MONTHS_FR[now.month])

        self.kpi_cards = {}
        self.chart_frames = {}

        self._build_header()
        self._build_filters()
        self._build_kpi_section()
        self._build_charts_section()

        self.refresh()

    # ------------------------------------------------------------------
    # Header & Filters
    # ------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 5))

        ctk.CTkLabel(header, text="📊 Dashboard", font=font_title()).pack(side="left")

    def _build_filters(self):
        filter_frame = ctk.CTkFrame(
            self, fg_color=("white", COLORS["card_dark"]), corner_radius=12,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        filter_frame.pack(fill="x", padx=25, pady=10)

        inner = ctk.CTkFrame(filter_frame, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)

        # School Year filter
        ctk.CTkLabel(inner, text="Année scolaire:", font=font_body()).pack(side="left", padx=(0, 8))
        years = [self.current_year, self.next_year]
        self.year_menu = ctk.CTkOptionMenu(
            inner, values=years, variable=self.selected_year,
            command=lambda v: self.refresh(), fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"], width=130,
        )
        self.year_menu.pack(side="left", padx=(0, 20))

        # Class filter
        ctk.CTkLabel(inner, text="Classe:", font=font_body()).pack(side="left", padx=(0, 8))
        self.class_menu = ctk.CTkOptionMenu(
            inner, values=["Toutes"], variable=self.selected_class,
            command=lambda v: self.refresh(), fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"], width=130,
        )
        self.class_menu.pack(side="left", padx=(0, 20))

        # Month filter
        ctk.CTkLabel(inner, text="Mois:", font=font_body()).pack(side="left", padx=(0, 8))
        month_values = [self.MONTHS_FR[m] for m in range(1, 13)]
        self.month_menu = ctk.CTkOptionMenu(
            inner, values=month_values, variable=self.selected_month,
            command=self._on_month_change, fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"], width=130,
        )
        self.month_menu.pack(side="left", padx=(0, 20))

        # Refresh button
        ctk.CTkButton(
            inner, text="🔄 Actualiser", fg_color=COLORS["secondary"],
            hover_color=COLORS["primary_hover"], command=self.refresh, width=120,
        ).pack(side="right")

    def _on_month_change(self, value):
        for num, name in self.MONTHS_FR.items():
            if name == value:
                self.selected_month_num = num
                break
        self.refresh()

    # ------------------------------------------------------------------
    # KPI Cards
    # ------------------------------------------------------------------
    def _build_kpi_section(self):
        from views.widgets import KPICard

        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=25, pady=10)

        for i in range(4):
            kpi_frame.grid_columnconfigure(i, weight=1)

        self.kpi_cards["enrolled"] = KPICard(
            kpi_frame, "Élèves inscrits (année actuelle)", "0",
            icon="🎓", color=COLORS["primary"],
        )
        self.kpi_cards["enrolled"].grid(row=0, column=0, padx=8, pady=5, sticky="nsew")

        self.kpi_cards["pre_registered"] = KPICard(
            kpi_frame, "Pré-inscrits (année prochaine)", "0",
            icon="📋", color=COLORS["secondary"],
        )
        self.kpi_cards["pre_registered"].grid(row=0, column=1, padx=8, pady=5, sticky="nsew")

        self.kpi_cards["new_this_month"] = KPICard(
            kpi_frame, "Nouvelles inscriptions ce mois", "0",
            icon="✨", color=COLORS["success"],
        )
        self.kpi_cards["new_this_month"].grid(row=0, column=2, padx=8, pady=5, sticky="nsew")

        self.kpi_cards["transport"] = KPICard(
            kpi_frame, "Élèves utilisant le transport", "0",
            icon="🚌", color=COLORS["warning"],
        )
        self.kpi_cards["transport"].grid(row=0, column=3, padx=8, pady=5, sticky="nsew")

        # Second row: financial KPIs
        for i in range(4):
            kpi_frame.grid_rowconfigure(1, weight=1)

        self.kpi_cards["inscription_revenue"] = KPICard(
            kpi_frame, "Total Inscription Revenue", "0 DH",
            icon="💵", color=COLORS["success"],
        )
        self.kpi_cards["inscription_revenue"].grid(row=1, column=0, padx=8, pady=5, sticky="nsew")

        self.kpi_cards["monthly_income"] = KPICard(
            kpi_frame, "Monthly Student Income", "0 DH",
            icon="📈", color=COLORS["primary"],
        )
        self.kpi_cards["monthly_income"].grid(row=1, column=1, padx=8, pady=5, sticky="nsew")

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------
    def _build_charts_section(self):
        self.charts_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.charts_container.pack(fill="both", expand=True, padx=25, pady=10)

        for i in range(2):
            self.charts_container.grid_columnconfigure(i, weight=1)

        # Row 1: students per class (bar), monthly registrations (line)
        self.chart_frames["per_class"] = self._make_chart_card(self.charts_container, "Élèves par classe")
        self.chart_frames["per_class"].grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_frames["monthly_reg"] = self._make_chart_card(self.charts_container, "Inscriptions mensuelles")
        self.chart_frames["monthly_reg"].grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        # Row 2: reinscription progress (donut), departures (line)
        self.chart_frames["reinscription"] = self._make_chart_card(self.charts_container, "Progression des réinscriptions")
        self.chart_frames["reinscription"].grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_frames["departures"] = self._make_chart_card(self.charts_container, "Départs par mois")
        self.chart_frames["departures"].grid(row=1, column=1, padx=8, pady=8, sticky="nsew")

        # Row 3: transport by class (pie) - full width
        self.chart_frames["transport_class"] = self._make_chart_card(self.charts_container, "Élèves transport par classe")
        self.chart_frames["transport_class"].grid(row=2, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

        # Row 4: Monthly income evolution (line), Payment status distribution (pie)
        self.chart_frames["income_evolution"] = self._make_chart_card(self.charts_container, "Évolution des revenus mensuels")
        self.chart_frames["income_evolution"].grid(row=3, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_frames["payment_status"] = self._make_chart_card(self.charts_container, "Répartition des statuts de paiement")
        self.chart_frames["payment_status"].grid(row=3, column=1, padx=8, pady=8, sticky="nsew")

        # Row 5: income by class (bar) - full width
        self.chart_frames["income_by_class"] = self._make_chart_card(self.charts_container, "Revenus par classe")
        self.chart_frames["income_by_class"].grid(row=4, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

    def _make_chart_card(self, parent, title):
        card = ctk.CTkFrame(
            parent, corner_radius=14, fg_color=("white", COLORS["card_dark"]),
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
            height=340,
        )
        ctk.CTkLabel(card, text=title, font=font_subtitle()).pack(anchor="w", padx=18, pady=(15, 5))

        canvas_holder = ctk.CTkFrame(card, fg_color="transparent")
        canvas_holder.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        card.canvas_holder = canvas_holder
        card.canvas_widget = None
        return card

    def _render_chart(self, card, fig):
        """Embed a matplotlib figure inside a chart card, replacing previous one."""
        if card.canvas_widget is not None:
            card.canvas_widget.get_tk_widget().destroy()
        canvas = FigureCanvasTkAgg(fig, master=card.canvas_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        card.canvas_widget = canvas
        plt.close(fig)

    def _empty_fig(self, message="Aucune donnée disponible"):
        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=11, color="#94A3B8")
        ax.axis("off")
        return fig

    # ------------------------------------------------------------------
    # Refresh / Data loading
    # ------------------------------------------------------------------
    def refresh(self):
        year = self.selected_year.get()

        # Update class filter options
        classes = ["Toutes"] + Student.get_distinct_classes(year)
        self.class_menu.configure(values=classes)
        if self.selected_class.get() not in classes:
            self.selected_class.set("Toutes")

        self._update_kpis(year)
        self._update_charts(year)

    def _update_kpis(self, year):
        enrolled = DashboardModel.kpi_current_year_count(year)
        pre_registered = DashboardModel.kpi_pre_registered_next_year(self.next_year)
        now = datetime.now()
        new_this_month = DashboardModel.kpi_new_registrations_this_month(
            year, now.year, self.selected_month_num
        )
        transport = DashboardModel.kpi_transport_users(year)

        self.kpi_cards["enrolled"].update_value(enrolled)
        self.kpi_cards["pre_registered"].update_value(pre_registered)
        self.kpi_cards["new_this_month"].update_value(new_this_month)
        self.kpi_cards["transport"].update_value(transport)

        # Financial KPIs
        from models.payment import Payment
        classe = self.selected_class.get()

        inscription_revenue = Payment.total_inscription_revenue(year, classe)
        self.kpi_cards["inscription_revenue"].update_value(f"{inscription_revenue:,.0f} DH")

        # Determine calendar year/month for the selected school-year month
        from utils.payment_constants import MONTH_CALENDAR_MAP
        start_year = int(year.split("/")[0])
        end_year = int(year.split("/")[1])
        selected_month_name = self.selected_month.get()
        if selected_month_name in MONTH_CALENDAR_MAP:
            cal_month, offset = MONTH_CALENDAR_MAP[selected_month_name]
            cal_year = start_year if offset == 0 else end_year
        else:
            cal_month, cal_year = self.selected_month_num, now.year

        monthly_income = Payment.monthly_income(year, cal_year, cal_month, classe)
        self.kpi_cards["monthly_income"].update_value(f"{monthly_income:,.0f} DH")

    def _update_charts(self, year):
        # 1. Students per class - Bar Chart
        data = DashboardModel.students_per_class(year)
        if self.selected_class.get() != "Toutes":
            data = [(c, n) for c, n in data if c == self.selected_class.get()]
        self._render_bar_chart(self.chart_frames["per_class"], data)

        # 2. Monthly registrations - Line Chart
        data = DashboardModel.monthly_registrations(year)
        self._render_line_chart(self.chart_frames["monthly_reg"], data, COLORS["primary"])

        # 3. Reinscription progress - Donut Chart
        reinscribed, eligible = DashboardModel.reinscription_progress(year, self.next_year)
        self._render_donut_chart(self.chart_frames["reinscription"], reinscribed, eligible)

        # 4. Departures by month - Line Chart
        data = DashboardModel.departures_by_month(year)
        self._render_line_chart(self.chart_frames["departures"], data, COLORS["danger"])

        # 5. Transport users by class - Pie Chart
        data = DashboardModel.transport_users_by_class(year)
        self._render_pie_chart(self.chart_frames["transport_class"], data)

        # 6. Monthly income evolution - Line Chart (3 series)
        from models.payment import Payment
        classe = self.selected_class.get()
        income_data = Payment.monthly_income_evolution(year, classe)
        self._render_income_evolution_chart(self.chart_frames["income_evolution"], income_data)

        # 7. Payment status distribution - Pie Chart
        status_data = Payment.payment_status_distribution(year, classe)
        self._render_payment_status_chart(self.chart_frames["payment_status"], status_data)

        # 8. Income by class - Bar Chart
        income_by_class = Payment.income_by_class(year)
        self._render_income_by_class_chart(self.chart_frames["income_by_class"], income_by_class)

    # ------------------------------------------------------------------
    # Chart renderers
    # ------------------------------------------------------------------
    def _render_bar_chart(self, card, data):
        if not data:
            self._render_chart(card, self._empty_fig())
            return
        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        bars = ax.bar(labels, values, color=COLORS["primary"], width=0.55)
        ax.bar_label(bars, padding=2, fontsize=8)
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_line_chart(self, card, data, color):
        if not data:
            self._render_chart(card, self._empty_fig())
            return
        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.plot(labels, values, marker="o", color=color, linewidth=2)
        ax.fill_between(range(len(values)), values, alpha=0.1, color=color)
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_donut_chart(self, card, reinscribed, eligible):
        remaining = max(eligible - reinscribed, 0)
        if eligible == 0:
            self._render_chart(card, self._empty_fig())
            return

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        values = [reinscribed, remaining]
        labels = ["Réinscrits", "En attente"]
        colors = [COLORS["success"], COLORS["border_light"]]
        wedges, texts, autotexts = ax.pie(
            values, labels=None, autopct=lambda p: f"{p:.0f}%" if p > 0 else "",
            colors=colors, startangle=90, wedgeprops=dict(width=0.4),
        )
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
        ax.text(0, 0, f"{reinscribed}/{eligible}", ha="center", va="center", fontsize=14, fontweight="bold")
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_pie_chart(self, card, data):
        if not data:
            self._render_chart(card, self._empty_fig())
            return
        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        fig = Figure(figsize=(8, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        colors = CHART_COLORS[: len(values)]
        ax.pie(values, labels=labels, autopct="%1.0f%%", colors=colors, startangle=90,
               textprops={"fontsize": 8})
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_income_evolution_chart(self, card, data):
        """data: list of dicts {month, inscription, mensualite, transport, total}"""
        if not data or all(d["total"] == 0 for d in data):
            self._render_chart(card, self._empty_fig())
            return

        labels = [d["month"] for d in data]
        inscription = [d["inscription"] for d in data]
        mensualite = [d["mensualite"] for d in data]
        transport = [d["transport"] for d in data]

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.plot(labels, inscription, marker="o", label="Inscription", color=COLORS["secondary"], linewidth=2)
        ax.plot(labels, mensualite, marker="o", label="Mensualité", color=COLORS["success"], linewidth=2)
        ax.plot(labels, transport, marker="o", label="Transport", color=COLORS["warning"], linewidth=2)
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax.legend(fontsize=8)
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_payment_status_chart(self, card, status_data):
        """status_data: {'PAYE': n, 'UNPAID': n, 'NAN': n}"""
        from utils.payment_constants import STATUS_PAYE, STATUS_UNPAID, STATUS_NAN, STATUS_LABELS, STATUS_COLORS

        values = [status_data.get(STATUS_PAYE, 0), status_data.get(STATUS_UNPAID, 0), status_data.get(STATUS_NAN, 0)]
        if sum(values) == 0:
            self._render_chart(card, self._empty_fig())
            return

        labels = [STATUS_LABELS[STATUS_PAYE], STATUS_LABELS[STATUS_UNPAID], STATUS_LABELS[STATUS_NAN]]
        colors = [STATUS_COLORS[STATUS_PAYE], STATUS_COLORS[STATUS_UNPAID], STATUS_COLORS[STATUS_NAN]]

        # Filter out zero-value slices to avoid clutter
        filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
        labels, values, colors = zip(*filtered)

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.pie(values, labels=labels, autopct="%1.0f%%", colors=colors, startangle=90,
               textprops={"fontsize": 8})
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_income_by_class_chart(self, card, data):
        """data: list of (classe, total_revenue)"""
        data = [(c, v) for c, v in data if v > 0]
        if not data:
            self._render_chart(card, self._empty_fig())
            return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        fig = Figure(figsize=(10, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        bars = ax.bar(labels, values, color=COLORS["success"], width=0.6)
        ax.bar_label(bars, padding=2, fontsize=7, fmt="%.0f")
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        fig.tight_layout()
        self._render_chart(card, fig)
