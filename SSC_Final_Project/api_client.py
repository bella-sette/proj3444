"""
API client — pulls project hours and projects data.

Owner: George
Job: Return clean Python dicts in the formats specified in CONTRACTS.md.
If the live API is unavailable, fall back to sample_data.json.

Note: Assignments are NOT fetched from the API — they are generated
      dynamically by the optimization model. Per request, we are not using the /Assignments endpoint
"""
import json
import requests
from pathlib import Path

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


# --- Project Hours ---

def get_project_hours():
    return _try_api("/project/ProjectHours") or _load_sample()["hours"]

def get_project_hours_filtered(project_id, classification_id):
    return _try_api(f"/project/ProjectHours/{project_id}/{classification_id}") or _load_sample()["hours"]

def get_project_hours_by_week(project_id, classification_id, week_num):
    return _try_api(f"/project/ProjectHours/{project_id}/{classification_id}/{week_num}") or _load_sample()["hours"]


# --- Projects ---

def get_projects():
    return _try_api("/project/Projects") or _load_sample()["projects"]

def get_project(project_id):
    return _try_api(f"/project/Projects/{project_id}") or _load_sample()["projects"]
