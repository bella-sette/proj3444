"""
SSC Staffing Optimization Tool — main entry point.

Owner: Bella
Job: Load the UI, populate dropdowns, wire up the Run button, update
labels and charts when the user interacts.
"""
import sys

from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

import api_client
import optimizer
import charts


UI_FILE = "ssc_staffing_tool.ui"  # change if your filename differs


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_FILE, self)

        # Wrap everything in a scroll area
        from PyQt6.QtWidgets import QScrollArea
        old_central = self.takeCentralWidget()
        scroll = QScrollArea()
        scroll.setWidget(old_central)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setCentralWidget(scroll)

        # State
        self.staff = []
        self.projects = []
        self.hours = {}
        self.rates = {}
        self.assignments = []

        # Make sure chart frames have layouts so we can add canvases later
        for frame_name in ("frameEmpChart", "frameEmpHoursChart", "frameProjChart"):
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
            try:
                optimizer.validate(self.assignments, self.staff, self.projects, self.hours)
                print("✓ Optimization output passed validation")

            except AssertionError as e:
                print(f"⚠ Validation failed: {e}")
                QMessageBox.warning(
                    self, "Validation Warning",
                    f"Optimizer output may be invalid:\n{e}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Optimization Error",
                f"Insufficient staff to meet project requirements.\n{e}",
            )
            return

        total_cost = sum(a["cost"] for a in self.assignments)
        self.lblTotalCostValue.setText(f"${total_cost:,}")

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
        # Embed both employee charts
        fig1 = charts.billable_chart(emp_assignments)
        self._embed_chart(self.frameEmpChart, fig1)
        fig2 = charts.weekly_hours_chart(emp_assignments)
        self._embed_chart(self.frameEmpHoursChart, fig2)

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

APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0A0A0A;
    color: #FAFAFA;
    font-family: "Inter", "Segoe UI", "SF Pro Text", sans-serif;
    font-size: 10pt;
}

QLabel {
    color: #FAFAFA;
    background: transparent;
}

#lblHeader {
    font-size: 18pt;
    font-weight: 600;
    color: #FAFAFA;
    padding: 4px 0 12px 0;
}

QGroupBox {
    background-color: #111111;
    border: 1px solid #27272A;
    border-radius: 8px;
    margin-top: 22px;
    padding: 32px 24px 24px 24px;
    font-weight: 500;
    color: #FAFAFA;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 2px 8px;
    background-color: transparent;
    color: #A1A1AA;
    font-size: 9pt;
    font-weight: 500;
}

QPushButton {
    background-color: #FAFAFA;
    color: #0A0A0A;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    font-size: 10pt;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #E4E4E7;
}

QPushButton:pressed {
    background-color: #D4D4D8;
}

QComboBox {
    background-color: #18181B;
    color: #FAFAFA;
    border: 1px solid #27272A;
    border-radius: 6px;
    padding: 6px 20px;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #3F3F46;
}

QComboBox:focus {
    border-color: #52525B;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #71717A;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #18181B;
    color: #FAFAFA;
    border: 1px solid #27272A;
    border-radius: 6px;
    selection-background-color: #27272A;
    selection-color: #FAFAFA;
    padding: 4px;
    outline: none;
}

QFrame#frameEmpChart, QFrame#frameEmpHoursChart, QFrame#frameProjChart {
    background-color: #111111;
    border: 1px solid #27272A;
    border-radius: 8px;
}

QStatusBar {
    background-color: #0A0A0A;
    color: #71717A;
    border-top: 1px solid #27272A;
}

QMessageBox {
    background-color: #18181B;
    color: #FAFAFA;
}

QMessageBox QLabel {
    color: #FAFAFA;
}

QFrame#frameTotalCost {
    background-color: #111111;
    border: 1px solid #27272A;
    border-radius: 8px;
}

#lblTotalCostHeader {
    color: #71717A;
    font-size: 9pt;
    font-weight: 600;
    letter-spacing: 1px;
}

#lblTotalCostValue {
    color: #FAFAFA;
    font-size: 22pt;
    font-weight: 700;
}

QScrollArea {
    border: none;
    background-color: #0A0A0A;
}

QScrollBar:vertical {
    background-color: #0A0A0A;
    width: 10px;
    margin: 4px 2px 4px 0;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #3F3F46;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #52525B;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
"""

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    window = MainApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()