"""
Staffing optimizer.

Owner: George
Job: Assign staff to projects to minimize total cost, subject to:
  - No staff member exceeds 40 hours per week total
  - Every project has all 5 required classifications staffed
  - Only staff with the matching classification fill a slot
Returns a list of assignment dicts (see CONTRACTS.md §3).
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


def optimize(staff, projects, hours, rates):
    """
    Parameters
    ----------
    staff : list of {id, name, classification, base_rate}
    projects : list of {id, name, industry, revenue}
    hours : {project_id: {classification: hours_required}}
    rates : {classification: rate}

    Returns
    -------
    list of {project_id, staff_id, classification, hours, cost}
    """
    prob = LpProblem("ssc_staffing", LpMinimize)

    # Decision variable: hours[s,p,c] = hours person s works on project p in role c
    x = {}
    for s in staff:
        for p in projects:
            c = s["classification"]
            need = hours.get(p["id"], {}).get(c, 0)
            if need > 0:
                x[(s["id"], p["id"], c)] = LpVariable(
                    f"x_{s['id']}_{p['id']}_{c}",
                    lowBound=0,
                    upBound=need,
                    cat=LpInteger,
                )

    # Objective: minimize total cost
    prob += lpSum(
        x[k] * rates.get(k[2], 0) for k in x
    )

    # Constraint: each project's classification hours must be met
    for p in projects:
        for c in REQUIRED_CLASSIFICATIONS:
            need = hours.get(p["id"], {}).get(c, 0)
            if need > 0:
                prob += (
                    lpSum(x[(s["id"], p["id"], c)]
                          for s in staff
                          if s["classification"] == c
                          and (s["id"], p["id"], c) in x) == need,
                    f"need_{p['id']}_{c}",
                )

    # Constraint: each staff member's total hours <= 40
    for s in staff:
        prob += (
            lpSum(x[k] for k in x if k[0] == s["id"]) <= MAX_HOURS_PER_WEEK,
            f"cap_{s['id']}",
        )

    # Solve
    status = prob.solve(PULP_CBC_CMD(msg=False))
    if LpStatus[status] != "Optimal":
        raise RuntimeError(
            f"Optimizer could not find a valid assignment ({LpStatus[status]})."
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
                "cost": h * rates.get(cls, 0),
            })
    return assignments


def validate(assignments, staff, projects, hours):
    """Sanity check: no one over 40 hours, every project's needs met."""
    # 40-hour check
    by_staff = {}
    for a in assignments:
        by_staff[a["staff_id"]] = by_staff.get(a["staff_id"], 0) + a["hours"]
    over = [sid for sid, h in by_staff.items() if h > MAX_HOURS_PER_WEEK]
    assert not over, f"Staff over 40 hours: {over}"

    # Coverage check
    for p in projects:
        for c in REQUIRED_CLASSIFICATIONS:
            need = hours.get(p["id"], {}).get(c, 0)
            got = sum(a["hours"] for a in assignments
                      if a["project_id"] == p["id"] and a["classification"] == c)
            assert got == need, f"Project {p['id']} {c}: need {need}, got {got}"
    return True
