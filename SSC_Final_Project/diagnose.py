"""Figure out why the optimizer says 'infeasible'."""
import api_client
from collections import defaultdict

REQUIRED = ["Partner", "Director", "Manager", "Senior", "Associate"]
MAX_HOURS = 40

staff = api_client.get_staff()
projects = api_client.get_projects()
hours = api_client.get_hours()

# Count staff per classification
by_class = defaultdict(list)
for s in staff:
    by_class[s["classification"]].append(s["name"])

print("Staff supply:")
print("-" * 60)
for cls in REQUIRED:
    people = by_class.get(cls, [])
    capacity = len(people) * MAX_HOURS
    print(f"  {cls:10s}: {len(people):2} people  ->  {capacity}h/week capacity")
print()

# Sum hours needed across all projects, by classification
needed = defaultdict(int)
for pid, cls_hours in hours.items():
    for cls, h in cls_hours.items():
        needed[cls] += h

print("Hours demand vs supply:")
print("-" * 60)
for cls in REQUIRED:
    demand = needed.get(cls, 0)
    capacity = len(by_class.get(cls, [])) * MAX_HOURS
    flag = "OK" if demand <= capacity else f"!! SHORT by {demand - capacity}h"
    print(f"  {cls:10s}: needs {demand:4}h  |  have {capacity:4}h  |  {flag}")
print()

# Catch classification name mismatches
staff_classes = set(s["classification"] for s in staff)
hour_classes = set()
for cls_hours in hours.values():
    hour_classes.update(cls_hours.keys())

unexpected_staff = staff_classes - set(REQUIRED)
unexpected_hours = hour_classes - set(REQUIRED)

if unexpected_staff:
    print(f"⚠ Unexpected classifications in STAFF data: {unexpected_staff}")
if unexpected_hours:
    print(f"⚠ Unexpected classifications in HOURS data: {unexpected_hours}")
if not unexpected_staff and not unexpected_hours:
    print("✓ All classification names match REQUIRED list")