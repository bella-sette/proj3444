"""
SSC Staffing Optimization Tool — main entry point.

Owner: Bella
Job: Load the UI, populate dropdowns, wire up the Run button, update
labels and charts when the user interacts.
"""
import sys

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import api_client
import optimizer
import charts


UI_FILE = "ssc_staffing_tool.ui"  # change if your filename differs


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_FILE, self)

        # State
        self.staff = []
        self.projects = []
        self.hours = {}
        self.rates = {}
        self.assignments = []

        # Make sure chart frames have layouts so we can add canvases later
        for frame_name in ("frameEmpChart", "frameProjChart"):
            frame = getattr(self, frame_name, None)
            if frame is not None and frame.layout() is None:
                frame.setLayout(QVBoxLayout())

        # Wire up signals
        self.btnRunOptimization.clicked.connect(self.run_optimization)
        self.cbEmployee.currentIndexChanged.connect(self.show_employee)
        self.cbProject.currentIndexChanged.connect(self.show_project)

        # Load data on startup
        self.load_data()

    # ------------------------------------------------------------------ #
    # Data loading
    # ------------------------------------------------------------------ #
    def load_data(self):
        try:
            self.staff = api_client.get_staff()
            self.projects = api_client.get_projects()
            self.hours = api_client.get_hours()
            self.rates = api_client.get_rates()
        except Exception as e:
            QMessageBox.warning(
                self, "Data Error", f"API data could not be loaded.\n{e}"
            )
            return

        self.cbEmployee.clear()
        self.cbEmployee.addItems([s["name"] for s in self.staff])

        self.cbProject.clear()
        self.cbProject.addItems([p["name"] for p in self.projects])

    # ------------------------------------------------------------------ #
    # Run optimization
    # ------------------------------------------------------------------ #
    def run_optimization(self):
        if not self.staff or not self.projects:
            QMessageBox.warning(self, "No Data", "No data loaded.")
            return

        try:
            self.assignments = optimizer.optimize(
                self.staff, self.projects, self.hours, self.rates
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Optimization Error",
                f"Insufficient staff to meet project requirements.\n{e}",
            )
            return

        QMessageBox.information(self, "Done", "Optimization complete.")
        self.show_employee()
        self.show_project()

    # ------------------------------------------------------------------ #
    # Employee view
    # ------------------------------------------------------------------ #
    def show_employee(self):
        name = self.cbEmployee.currentText()
        if not name:
            return

        emp = next((s for s in self.staff if s["name"] == name), None)
        if not emp:
            return

        emp_assignments = [
            a for a in self.assignments if a["staff_id"] == emp["id"]
        ]
        project_names = [
            next(p["name"] for p in self.projects if p["id"] == a["project_id"])
            for a in emp_assignments
        ]
        total_hours = sum(a["hours"] for a in emp_assignments)

        self.lblEmpNameValue.setText(emp["name"])
        self.lblEmpClassValue.setText(emp["classification"])
        self.lblEmpRateValue.setText(f"${emp['base_rate']}/hr")
        self.lblEmpProjectsValue.setText(", ".join(project_names) or "—")
        self.lblEmpHoursValue.setText(f"{total_hours} hrs/week")

        # Embed billable chart
        fig = charts.billable_chart(emp_assignments)
        self._embed_chart(self.frameEmpChart, fig)

    # ------------------------------------------------------------------ #
    # Project view
    # ------------------------------------------------------------------ #
    def show_project(self):
        name = self.cbProject.currentText()
        if not name:
            return

        proj = next((p for p in self.projects if p["name"] == name), None)
        if not proj:
            return

        proj_assignments = [
            a for a in self.assignments if a["project_id"] == proj["id"]
        ]
        total_cost = sum(a["cost"] for a in proj_assignments)
        profit = proj["revenue"] - total_cost

        staff_lines = []
        for a in proj_assignments:
            person = next((s for s in self.staff if s["id"] == a["staff_id"]), None)
            if person:
                staff_lines.append(f"{person['name']} ({a['classification']})")

        self.lblProjNameValue.setText(proj["name"])
        self.lblProjIndustryValue.setText(proj["industry"])
        self.lblProjRevenueValue.setText(f"${proj['revenue']:,}")
        self.lblProjStaffValue.setText("\n".join(staff_lines) or "—")
        self.lblProjCostValue.setText(f"${total_cost:,}")
        self.lblProjProfitValue.setText(f"${profit:,}")

        # Embed hours-by-classification chart
        fig = charts.hours_by_classification_chart(proj_assignments)
        self._embed_chart(self.frameProjChart, fig)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _embed_chart(self, frame, fig):
        """Replace the contents of a frame with a matplotlib canvas."""
        layout = frame.layout()
        # Clear existing widgets
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
