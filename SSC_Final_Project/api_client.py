"""
API client — pulls staff, project, hours, and rates data.

Returns clean Python dicts in the formats expected by main.py and the optimizer.
If the live API is unavailable, falls back to sample_data.json.
Caches responses so we don't hit the network more than once per endpoint.
"""
import json
from collections import defaultdict
from pathlib import Path

import requests

API_BASE = "https://bit-coursework-api.azurewebsites.net"
SAMPLE_PATH = Path(__file__).parent / "sample_data.json"

# Cache so we only hit the API (or load the sample file) once per session
_api_cache = {}
_sample_cache = None


def _load_sample():
    """Load sample_data.json once and reuse it."""
    global _sample_cache
    if _sample_cache is None:
        with open(SAMPLE_PATH) as f:
            _sample_cache = json.load(f)
    return _sample_cache


def _try_api(endpoint):
    """Hit the API once per endpoint, then cache the result (success or None)."""
    if endpoint not in _api_cache:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            response.raise_for_status()
            _api_cache[endpoint] = response.json()
        except requests.RequestException:
            _api_cache[endpoint] = None
    return _api_cache[endpoint]


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
    """Returns {classification: avg_rate}. Averages all rates per classification."""
    rates_data = _try_api("/project/StaffRates")
    staff_data = _try_api("/project/Staff")

    # Need both endpoints to compute rates; fall back if either is missing
    if rates_data is None or staff_data is None:
        return _load_sample()["rates"]

    # Build staff_id -> classification map from the Staff endpoint
    staff_cls = {
        s["staffID"]: s["staffClassification"]["classification"]
        for s in staff_data
    }

    # Group rates by classification and average them
    by_class = defaultdict(list)
    for entry in rates_data:
        cls = staff_cls.get(entry["staffID"])
        if cls:
            by_class[cls].append(entry["rate"])
    return {cls: sum(vals) / len(vals) for cls, vals in by_class.items()}


def get_rates_for_staff(staff_id, project_id):
    return _try_api(f"/project/StaffRates/{staff_id}/{project_id}")


# --- Project Hours ---

def get_hours():
    """Returns {project_id: {classification: avg_hours_per_week}}.
    
    The API gives per-week entries; the optimizer thinks per-week
    (40-hour cap is weekly), so we average across the weeks of data.
    """
    data = _try_api("/project/ProjectHours")
    if data is None:
        sample = _load_sample()["hours"]
        return {int(pid): h for pid, h in sample.items()}

    # Group every weekly entry by (project, classification)
    grouped = defaultdict(lambda: defaultdict(list))
    for entry in data:
        pid = entry["project"]["id"]
        cls = entry["classification"]["classification"]
        grouped[pid][cls].append(entry["numberHours"])

    # Average across weeks and round to whole hours
    return {
        pid: {cls: round(sum(vals) / len(vals)) for cls, vals in cls_hours.items()}
        for pid, cls_hours in grouped.items()
    }


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
    """Get a single project by ID."""
    data = _try_api(f"/project/Projects/{project_id}")
    if data is None:
        return None
    return {
        "id": data["id"],
        "name": data["companyName"],
        "industry": data["industry"],
        "revenue": data["revenue"],
    }