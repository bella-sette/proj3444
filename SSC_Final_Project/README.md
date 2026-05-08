# SSC Staffing Optimization Tool

A Python desktop app that automates staffing assignments for SSC, replacing
Sarah's manual Excel process. Pulls staff and project data, runs an
optimizer to assign consultants to projects under cost and hours
constraints, and displays results in a PyQt UI with charts.

## Team

- **Bella** — Lead programmer (`main.py`, UI integration)
- **George** — Math lead (`optimizer.py`)
- **Connor** — API / data (`api_client.py`)
- **Sam** — Project manager (`charts.py`, README, demo)

## How to run

1. Install Python 3.9+
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. From the project folder:
   ```
   python main.py
   ```

## Files

| File | Purpose |
|------|---------|
| `main.py` | Loads UI, connects buttons, displays results |
| `api_client.py` | Fetches staff, project, rate, and hours data |
| `optimizer.py` | Assigns staff to projects under constraints |
| `charts.py` | Builds matplotlib charts for the UI |
| `ssc_staffing_tool.ui` | Qt Designer interface file |
| `sample_data.json` | Backup data if API is unavailable |
| `CONTRACTS.md` | Agreed widget names, field names, formulas |

## How to use the app

1. Click **Run Optimization** to compute assignments.
2. Pick an employee from the **Employee** dropdown to see their
   classification, rate, assigned projects, and hours.
3. Pick a project from the **Project** dropdown to see assigned staff,
   cost, profit, and hours by classification.

## Constraints

- Each consultant works no more than 40 hours per week.
- Every project must have one of each: Partner, Director, Manager,
  Senior, Associate.
- The optimizer minimizes total staffing cost.
