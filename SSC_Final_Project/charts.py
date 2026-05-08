"""
Chart generation.

Owner: Sam
Job: Build matplotlib figures for the UI. Each function takes assignment
data and returns a Figure that main.py wraps in a FigureCanvasQTAgg.
"""
import matplotlib

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


REQUIRED_CLASSIFICATIONS = ["Partner", "Director", "Manager", "Senior", "Associate"]
MAX_HOURS = 40


def billable_chart(employee_assignments):
    """Pie chart: billable hours vs. unused capacity for one employee."""
    billable = sum(a["hours"] for a in employee_assignments)
    non_billable = max(0, MAX_HOURS - billable)

    fig = Figure(figsize=(4, 3), tight_layout=True)
    ax = fig.add_subplot(111)
    if billable + non_billable == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
    else:
        ax.pie(
            [billable, non_billable],
            labels=["Billable", "Non-billable"],
            autopct="%1.0f%%",
            startangle=90,
        )
    ax.set_title("Billable vs. Non-Billable Hours")
    return fig


def weekly_hours_chart(employee_assignments):
    """Bar chart: hours per project for one employee."""
    projects = [a["project_id"] for a in employee_assignments]
    hours = [a["hours"] for a in employee_assignments]

    fig = Figure(figsize=(4, 3), tight_layout=True)
    ax = fig.add_subplot(111)
    if not projects:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
    else:
        ax.bar([f"Proj {p}" for p in projects], hours)
        ax.set_ylabel("Hours/week")
        ax.set_ylim(0, MAX_HOURS)
    ax.set_title("Weekly Hours Worked")
    return fig


def hours_by_classification_chart(project_assignments):
    """Bar chart: hours per classification on one project."""
    totals = {c: 0 for c in REQUIRED_CLASSIFICATIONS}
    for a in project_assignments:
        totals[a["classification"]] = totals.get(a["classification"], 0) + a["hours"]

    fig = Figure(figsize=(4, 3), tight_layout=True)
    ax = fig.add_subplot(111)
    if not project_assignments:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
    else:
        ax.bar(list(totals.keys()), list(totals.values()))
        ax.set_ylabel("Hours")
        ax.tick_params(axis="x", rotation=30)
    ax.set_title("Hours by Classification")
    return fig
