"""Dump raw API responses so we can see what's really in there."""
import json
import api_client


def show(label, data, limit=3):
    print("\n" + "=" * 60)
    print(label)
    print("=" * 60)
    if data is None:
        print("  (no data — endpoint failed)")
        return
    if isinstance(data, list):
        for item in data[:limit]:
            print(json.dumps(item, indent=2))
            print("-" * 40)
        print(f"\nTotal records: {len(data)}")
    else:
        print(json.dumps(data, indent=2))


# Raw responses
show("STAFF (first 3)", api_client._try_api("/project/Staff"))
show("PROJECTS (first 3)", api_client._try_api("/project/Projects"))
show("PROJECT HOURS (first 5)", api_client._try_api("/project/ProjectHours"), limit=5)
show("STAFF RATES (first 5)", api_client._try_api("/project/StaffRates"), limit=5)

# Week analysis
print("\n" + "=" * 60)
print("WEEK ANALYSIS")
print("=" * 60)
hours_data = api_client._try_api("/project/ProjectHours")
if hours_data:
    # Find the week field, whatever it's named
    sample = hours_data[0]
    week_field = next((k for k in sample if "week" in k.lower()), None)
    print(f"Week field appears to be: {week_field!r}")
    if week_field:
        weeks = sorted(set(e[week_field] for e in hours_data if week_field in e))
        print(f"Number of unique weeks: {len(weeks)}")
        print(f"Week range: {weeks[0]} to {weeks[-1]}")

# Rate magnitude check
print("\n" + "=" * 60)
print("RATE COMPARISON")
print("=" * 60)
staff = api_client._try_api("/project/Staff")
rates = api_client._try_api("/project/StaffRates")
if staff:
    base_rates = [s.get("baseRate", 0) for s in staff]
    print(f"BASE rates (from Staff endpoint): ${min(base_rates)} - ${max(base_rates)}, avg ${sum(base_rates)/len(base_rates):.0f}")
if rates:
    project_rates = [r.get("rate", 0) for r in rates]
    print(f"PROJECT rates (from StaffRates):  ${min(project_rates)} - ${max(project_rates)}, avg ${sum(project_rates)/len(project_rates):.0f}")