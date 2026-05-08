# Data Contracts

**Lock these in the kickoff meeting. Do not change without telling everyone.**

This file is the single source of truth for names that have to match
across `main.py`, `api_client.py`, `optimizer.py`, and `charts.py`.

---

## 1. Widget names (in the .ui file)

These names are used by Bella in `main.py` via `self.<name>`.

| Widget | Name |
|--------|------|
| Run button | `btnRunOptimization` |
| Employee dropdown | `cbEmployee` |
| Project dropdown | `cbProject` |
| Employee name label | `lblEmpNameValue` |
| Employee classification label | `lblEmpClassValue` |
| Employee base rate label | `lblEmpRateValue` |
| Employee assigned projects label | `lblEmpProjectsValue` |
| Employee hours label | `lblEmpHoursValue` |
| Project name label | `lblProjNameValue` |
| Project industry label | `lblProjIndustryValue` |
| Project revenue label | `lblProjRevenueValue` |
| Project staff label | `lblProjStaffValue` |
| Project cost label | `lblProjCostValue` |
| Project profit label | `lblProjProfitValue` |
| Employee chart frame | `frameEmpChart` |
| Project chart frame | `frameProjChart` |

---

## 2. Classification names (use these exact strings everywhere)

```
Partner
Director
Manager
Senior
Associate
```

Do **not** use: "Senior Consultant", "Analyst", "Staff", "Sr.", etc.

---

## 3. Data formats

### Staff (returned by `api_client.get_staff()`)

```python
{
    "id": 1,
    "name": "Sarah Beyene",
    "classification": "Manager",
    "base_rate": 95
}
```

### Project (returned by `api_client.get_projects()`)

```python
{
    "id": 101,
    "name": "Project Alpha",
    "industry": "Healthcare",
    "revenue": 250000
}
```

### Project hours (returned by `api_client.get_hours()`)

Hours required per classification per project:

```python
{
    101: {"Partner": 5, "Director": 10, "Manager": 15, "Senior": 20, "Associate": 30}
}
```

### Rates (returned by `api_client.get_rates()`)

Rate per classification (or per staff_id, project_id pair if more
detailed):

```python
{
    "Partner": 250,
    "Director": 175,
    "Manager": 95,
    "Senior": 75,
    "Associate": 55
}
```

### Assignment (returned by `optimizer.optimize(...)`)

```python
{
    "project_id": 101,
    "staff_id": 5,
    "classification": "Associate",
    "hours": 32,
    "cost": 1760
}
```

The optimizer returns a **list of these dicts**.

---

## 4. Cost formula

```
cost      = hours * rate
total     = sum of cost across all assignments for a project
profit    = revenue - total
```

---

## 5. Constraints (optimizer enforces)

- No staff member's total hours across all projects exceeds 40.
- Every project must have at least one staff member assigned per
  required classification.
- Only staff with the matching classification can fill a slot.
- Minimize total cost across all assignments.

---

## 6. Chart function signatures

In `charts.py`:

```python
def billable_chart(employee_assignments) -> Figure
def weekly_hours_chart(employee_assignments) -> Figure
def hours_by_classification_chart(project_assignments) -> Figure
```

Each returns a `matplotlib.figure.Figure` that Bella wraps in
`FigureCanvasQTAgg` and adds to a frame.
