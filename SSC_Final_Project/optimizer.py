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


def optimize(staff, projects, hours, rates):
    """
    Assigns staff to projects at minimum total cost.

    Inputs:
        staff: list of dicts with id, name, classification, base_rate
        projects: list of dicts with id, name, industry, revenue
        hours: dict {project_id: {classification: hours_needed}}
        rates: dict {classification: rate}  -- not actually used here, we
               use each individual's base_rate instead so the model can
               prefer cheaper people within the same classification

    Returns:
        list of assignment dicts {project_id, staff_id, classification, hours, cost}
    """
    # Build a quick lookup so we can find each person's hourly rate by their id.
    # Using base_rate per-person (instead of a flat classification rate) is
    # what makes the optimizer actually pick the cheapest available person.
    staff_rates = {s["id"]: s["base_rate"] for s in staff}

    # Create the LP problem -- we want to MINIMIZE total cost
    prob = LpProblem("ssc_staffing", LpMinimize)

    # Decision variables:
    # x[(staff_id, project_id, classification)] = hours this person works
    # on this project in this role.
    # Only create a variable if the staff member's classification matches
    # what the project needs (a Manager can't fill a Partner slot).
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
                    cat=LpInteger,  # whole hours only
                )

    # Objective function:
    # total cost = sum across all assignments of (hours * that person's rate)
    prob += lpSum(x[k] * staff_rates[k[0]] for k in x)

    # Constraint 1: each project's hours per classification must be EXACTLY met
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

    # Constraint 2: no staff member can work more than 40 hours per week
    # (totaled across all projects they're assigned to)
    for s in staff:
        prob += (
            lpSum(x[k] for k in x if k[0] == s["id"]) <= MAX_HOURS_PER_WEEK,
            f"cap_{s['id']}",
        )

    # Solve using PuLP's built-in CBC solver
    status = prob.solve(PULP_CBC_CMD(msg=False))
    if LpStatus[status] != "Optimal":
        raise RuntimeError(
            f"Could not find a valid staffing assignment ({LpStatus[status]}). "
            f"There might not be enough staff in each classification to cover all projects."
        )

    # Build the result list (only assignments with hours > 0)
    assignments = []
    for (sid, pid, cls), var in x.items():
        h = int(var.value() or 0)
        if h > 0:
            assignments.append({
                "project_id": pid,
                "staff_id": sid,
                "classification": cls,
                "hours": h,
                "cost": h * staff_rates[sid],
            })
    return assignments


def validate(assignments, staff, projects, hours):
    """
    Sanity-checks the optimizer's output before we display it:
      - No staff member is over 40 hours
      - Every project's classification hours are exactly covered

    Raises AssertionError if something is wrong, returns True if all good.
    """
    # Check 1: no one over 40 hours
    hours_per_staff = {}
    for a in assignments:
        hours_per_staff[a["staff_id"]] = hours_per_staff.get(a["staff_id"], 0) + a["hours"]

    over_limit = [sid for sid, h in hours_per_staff.items() if h > MAX_HOURS_PER_WEEK]
    assert not over_limit, f"Staff over 40 hours: {over_limit}"

    # Check 2: every project's classification needs are exactly met
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