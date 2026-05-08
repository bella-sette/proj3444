"""
API client — pulls staff, project, hours, and rates data.

Owner: Connor
Job: Return clean Python dicts in the formats specified in CONTRACTS.md.
If the live API is unavailable, fall back to sample_data.json.
"""
import json
import os
from pathlib import Path

# import requests   # uncomment when wiring up the real API

API_BASE = "https://api.example.com"  # TODO: replace with real endpoint
SAMPLE_PATH = Path(__file__).parent / "sample_data.json"


def _load_sample():
    with open(SAMPLE_PATH) as f:
        return json.load(f)


def _try_api(endpoint):
    """
    Attempt the live API call. Return parsed JSON on success, or None
    on any failure so callers can fall back to sample data.
    """
    # Example with requests:
    # try:
    #     r = requests.get(f"{API_BASE}/{endpoint}", timeout=5)
    #     r.raise_for_status()
    #     return r.json()
    # except Exception:
    #     return None
    return None


def get_staff():
    """List of staff dicts. See CONTRACTS.md §3."""
    data = _try_api("staff")
    if data is None:
        data = _load_sample()["staff"]
    return data


def get_projects():
    """List of project dicts. See CONTRACTS.md §3."""
    data = _try_api("projects")
    if data is None:
        data = _load_sample()["projects"]
    return data


def get_hours():
    """{project_id: {classification: hours}}. See CONTRACTS.md §3."""
    data = _try_api("hours")
    if data is None:
        data = _load_sample()["hours"]
    # JSON keys are strings — convert project IDs back to ints
    return {int(pid): h for pid, h in data.items()}


def get_rates():
    """{classification: rate}. See CONTRACTS.md §3."""
    data = _try_api("rates")
    if data is None:
        data = _load_sample()["rates"]
    return data
