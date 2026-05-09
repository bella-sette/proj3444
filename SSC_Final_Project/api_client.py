"""
API client — pulls staff, project hours, projects, and rates data.

Owner: George
Job: Return clean Python dicts in the formats specified in CONTRACTS.md.
If the live API is unavailable, fall back to sample_data.json.

Note: Assignments are NOT fetched from the API — they are generated
      dynamically by the optimization model.
"""
import json
import requests
from pathlib import Path
from collections import defaultdict

API_BASE = "https://bit-coursework-api.azurewebsites.net"
SAMPLE_PATH = Path(__file__).parent / "sample_data.json"


def _load_sample():
    with open(SAMPLE_PATH) as f:
        return json.load(f)


def _try_api(endpoint):
    try:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


# --- Staff ---

def get_staff():
    """Returns list of {id, name, classification, base_rate}."""
    data = _try_api("/project/Staff")
    if data is None:
        return _load_sample()["staff"]
    return [
        {
            "id": s["staffID"],
            "name": f"{s['firstName']} {s['lastName']}",
            "classification": s["staffClassification"]["classification"],
            "base_rate": s["baseRate"],
        }
        for s in data
    ]

def get_staff_classifications():
    data = _try_api("/project/StaffClassification")
    return data if data is not None else _load_sample().get("classifications", [])


# --- Rates ---

def get_rates():
    """Returns {classification: avg_rate} as expected by the optimizer."""
    data = _try_api("/project/StaffRates")
    if data is None:
        return _load_sample()["rates"]
    # Average billing rate per classification across all staff+project combos
    totals = defaultdict(list)
    for entry in data:
        cls = entry["staff"]["staffClassification"]["classification"] \
              if entry["staff"].get("staffClassification") \
              else None
        if cls:
            totals[cls].append(entry["rate"])
    return {cls: sum(vals) / len(vals) for cls, vals in totals.items()}

def get_rates_for_staff(staff_id, project_id):
    return _try_api(f"/project/StaffRates/{staff_id}/{project_id}")


# --- Project Hours ---

def get_hours():
    """Returns {project_id: {classification: total_hours}} as expected by the optimizer."""
    data = _try_api("/project/ProjectHours")
    if data is None:
        return _load_sample()["hours"]
    # Sum hours across all weeks per project + classification
    hours = defaultdict(lambda: defaultdict(int))
    for entry in data:
        pid = entry["project"]["id"]
        cls = entry["classification"]["classification"]
        hours[pid][cls] += entry["numberHours"]
    return {pid: dict(cls_hours) for pid, cls_hours in hours.items()}

def get_project_hours_filtered(project_id, classification_id):
    return _try_api(f"/project/ProjectHours/{project_id}/{classification_id}")

def get_project_hours_by_week(project_id, classification_id, week_num):
    return _try_api(f"/project/ProjectHours/{project_id}/{classification_id}/{week_num}")


# --- Projects ---

def get_projects():
    """Returns list of {id, name, industry, revenue}."""
    data = _try_api("/project/Projects")
    if data is None:
        return _load_sample()["projects"]
    return [
        {
            "id": p["id"],
            "name": p["companyName"],
            "industry": p["industry"],
            "revenue": p["revenue"],
        }
        for p in data
    ]

def get_project(project_id):
    data = _try_api(f"/project/Projects/{project_id}")
    if data is None:
        return None
    return {
        "id": data["id"],
        "name": data["companyName"],
        "industry": data["industry"],
        "revenue": data["revenue"],
    }