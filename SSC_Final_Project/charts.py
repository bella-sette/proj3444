"""
Chart generation. Dark theme, grayscale palette.
Owner: Sam
"""
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.figure import Figure


REQUIRED_CLASSIFICATIONS = ["Partner", "Director", "Manager", "Senior", "Associate"]
MAX_HOURS = 40

# Theme
BG = "#111111"
TEXT = "#FAFAFA"
MUTED = "#A1A1AA"
BORDER = "#27272A"
GREY_PALETTE = ["#FAFAFA", "#A1A1AA", "#71717A", "#52525B", "#3F3F46"]


def _style(fig, ax):
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.tick_params(colors=MUTED, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.title.set_color(TEXT)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def billable_chart(employee_assignments):
    billable = sum(a["hours"] for a in employee_assignments)
    non_billable = max(0, MAX_HOURS - billable)

    fig = Figure(figsize=(4, 3), tight_layout=True, facecolor=BG)
    ax = fig.add_subplot(111)
    _style(fig, ax)

    if billable + non_billable == 0 or billable == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                color=MUTED, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        wedges, texts, autotexts = ax.pie(
            [billable, non_billable],
            labels=["Billable", "Non-billable"],
            autopct="%1.0f%%",
            startangle=90,
            colors=["#FAFAFA", "#3F3F46"],
            wedgeprops={"edgecolor": BG, "linewidth": 2},
        )
        for t in texts:
            t.set_color(TEXT)
        for t in autotexts:
            t.set_color("#0A0A0A")
            t.set_fontweight("bold")
    ax.set_title("Billable vs. Non-Billable Hours", color=TEXT, fontsize=11)
    return fig


def weekly_hours_chart(employee_assignments):
    projects = [f"P{a['project_id']}" for a in employee_assignments]
    hours = [a["hours"] for a in employee_assignments]

    fig = Figure(figsize=(4, 3), tight_layout=True, facecolor=BG)
    ax = fig.add_subplot(111)
    _style(fig, ax)

    if not projects:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                color=MUTED, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.bar(projects, hours, color="#FAFAFA", edgecolor=BORDER)
        ax.set_ylabel("Hours/week")
        ax.set_ylim(0, MAX_HOURS)
    ax.set_title("Weekly Hours Worked", color=TEXT, fontsize=11)
    return fig


def hours_by_classification_chart(project_assignments):
    totals = {c: 0 for c in REQUIRED_CLASSIFICATIONS}
    for a in project_assignments:
        totals[a["classification"]] = totals.get(a["classification"], 0) + a["hours"]

    fig = Figure(figsize=(4, 3), tight_layout=True, facecolor=BG)
    ax = fig.add_subplot(111)
    _style(fig, ax)

    if not project_assignments:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                color=MUTED, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.bar(list(totals.keys()), list(totals.values()),
               color=GREY_PALETTE, edgecolor=BORDER)
        ax.set_ylabel("Hours")
        ax.tick_params(axis="x", rotation=30)
    ax.set_title("Hours by Classification", color=TEXT, fontsize=11)
    return fig