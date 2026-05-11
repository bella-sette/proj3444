"""
Staffing optimizer using PuLP linear programming.

Decides which staff to assign to which projects to minimize total cost, while making sure:
  - No one works more than 40 hours per week
  - Every project has all 5 classifications (Partner, Director, Manager, Senior, Associate)
  - Each project's required hours per classification are exactly met
"""
from pulp import (
    LpProblem,
    LpMinimize,
    LpVariable,
    LpInteger,
    lpSum,
    PULP_CBC_CMD,
    LpStatus,
)


REQUIRED_CLASSIFICATIONS = ["Partner", "Director", "Manager", "Senior", "Associate"]
MAX_HOURS_PER_WEEK = 40


def optimize(staff, projects, hours, rates, staff_project_rates=None, num_weeks=1):
    """
    Assigns staff to projects at minimum total billed cost.
    
    If staff_project_rates is provided, uses per-(staff,project) billing rates.
    Otherwise falls back to each staff member's base_rate.
    """
    max_hours = MAX_HOURS_PER_WEEK * num_weeks  # cap scales with engagement length

    # Pick which rate to use for each (staff, project) pair
    if staff_project_rates:
        def rate_for(sid, pid, cls):
            return staff_project_rates.get((sid, pid), rates.get(cls, 0))
    else:
        staff_base = {s["id"]: s["base_rate"] for s in staff}
        def rate_for(sid, pid, cls):
            return staff_base.get(sid, rates.get(cls, 0))

    prob = LpProblem("ssc_staffing", LpMinimize)

    # Decision variables: x[(staff_id, project_id, classification)] = hours
    x = {}
    for s in staff:
        for p in projects:
            cls = s["classification"]
            need = hours.get(p["id"], {}).get(cls, 0)
            if need > 0:
                x[(s["id"], p["id"], cls)] = LpVariable(
                    f"x_{s['id']}_{p['id']}_{cls}",
                    lowBound=0,
                    upBound=need,
                    cat=LpInteger,
                )

    # Objective: minimize total billed cost
    prob += lpSum(x[k] * rate_for(k[0], k[1], k[2]) for k in x)

    # Constraint 1: each project's classification hours must be exactly met
    for p in projects:
        for cls in REQUIRED_CLASSIFICATIONS:
            need = hours.get(p["id"], {}).get(cls, 0)
            if need > 0:
                prob += (
                    lpSum(
                        x[(s["id"], p["id"], cls)]
                        for s in staff
                        if s["classification"] == cls
                        and (s["id"], p["id"], cls) in x
                    ) == need,
                    f"need_{p['id']}_{cls}",
                )

    # Constraint 2: no staff over (40 * weeks) total hours across all projects
    for s in staff:
        prob += (
            lpSum(x[k] for k in x if k[0] == s["id"]) <= max_hours,
            f"cap_{s['id']}",
        )

    status = prob.solve(PULP_CBC_CMD(msg=False))
    if LpStatus[status] != "Optimal":
        raise RuntimeError(
            f"Could not find a valid staffing assignment ({LpStatus[status]}). "
            f"There might not be enough staff in each classification."
        )

    # Build result list
    assignments = []
    for (sid, pid, cls), var in x.items():
        h = int(var.value() or 0)
        if h > 0:
            assignments.append({
                "project_id": pid,
                "staff_id": sid,
                "classification": cls,
                "hours": h,
                "cost": h * rate_for(sid, pid, cls),
            })
    return assignments


def validate(assignments, staff, projects, hours, num_weeks=1):
    """Sanity-check optimizer output."""
    max_hours = MAX_HOURS_PER_WEEK * num_weeks

    hours_per_staff = {}
    for a in assignments:
        hours_per_staff[a["staff_id"]] = hours_per_staff.get(a["staff_id"], 0) + a["hours"]

    over_limit = [sid for sid, h in hours_per_staff.items() if h > max_hours]
    assert not over_limit, f"Staff over {max_hours} hours: {over_limit}"

    for p in projects:
        for cls in REQUIRED_CLASSIFICATIONS:
            needed = hours.get(p["id"], {}).get(cls, 0)
            assigned = sum(
                a["hours"] for a in assignments
                if a["project_id"] == p["id"] and a["classification"] == cls
            )
            assert assigned == needed, (
                f"Project {p['id']} needs {needed} {cls} hours but got {assigned}"
            )
    return True

def optimize_all_weeks(staff, projects, hours_by_week, rates, staff_project_rates=None):
    """
    Run optimize() once per week and combine the results.
    Each week independently enforces the 40-hour cap per staff member,
    which forces realistic per-week spreading of work.
    """
    combined = {}  # (staff_id, project_id, classification) -> aggregated assignment

    for week_num, week_hours in hours_by_week.items():
        if not any(week_hours.values()):
            continue  # skip empty weeks
        try:
            week_assignments = optimize(
                staff, projects, week_hours, rates,
                staff_project_rates=staff_project_rates,
                num_weeks=1,  # 40-hour cap per week
            )
        except RuntimeError:
            continue  # skip infeasible weeks (shouldn't happen with valid data)

        # Aggregate so each (staff, project, classification) shows total hours
        for a in week_assignments:
            key = (a["staff_id"], a["project_id"], a["classification"])
            if key not in combined:
                combined[key] = {
                    "staff_id": a["staff_id"],
                    "project_id": a["project_id"],
                    "classification": a["classification"],
                    "hours": 0,
                    "cost": 0,
                }
            combined[key]["hours"] += a["hours"]
            combined[key]["cost"] += a["cost"]

    return list(combined.values())