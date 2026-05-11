# SSC Staffing Optimization Tool

This is our final project for BIT 3444. It's a desktop app that helps SSC figure out
which consultants should be assigned to which projects — automatically, instead of
Sarah doing it by hand in Excel. It pulls real data from an API, runs an optimizer
to find the best assignments, and shows everything in a clean PyQt5 UI with charts.

## Team

- **Bella** 
- **George**
- **Connor** 
- **Sam** 

## What you need to install

Run this one command and you're good:

    pip install -r requirements.txt

Here's what gets installed and why:

| Package | Version | What it's for |
|---------|---------|---------------|
| `PyQt5` | >=5.15 | The desktop UI |
| `matplotlib` | >=3.5 | The charts |
| `PuLP` | >=2.7 | The optimizer that figures out assignments |
| `requests` | >=2.28 | Fetching data from the API |

## How to run it

1. Make sure you have Python 3.9 or newer
2. Install the dependencies (see above)
3. Run this from the project folder:

        python main.py

The app will try to pull live data from the SSC API when it starts. If that
fails for any reason, it automatically uses sample_data.json as a backup
so the app still works.

## How it works

When you hit Run Optimization, the app fetches staff and project data from
the API and hands it to the optimizer. The optimizer finds the cheapest valid
way to assign consultants to projects, making sure:

- Nobody works more than 40 hours a week
- Every project has a Partner, Director, Manager, Senior, and Associate
- Each project gets exactly the hours it needs per classification

Results show up right in the UI — no extra steps needed.

## Files

| File | What it does |
|------|--------------|
| `main.py` | Runs the app and connects the UI to everything else |
| `api_client.py` | Gets staff, project, rate, and hours data from the API |
| `optimizer.py` | Figures out the best staff assignments |
| `charts.py` | Builds the charts shown in the employee and project views |
| `ssc_staffing_tool.ui` | The Qt Designer interface file |
| `sample_data.json` | Backup data in case the API is down |
| `requirements.txt` | Lists the libraries you need to install |

## How to use the app

1. Click Run Optimization to generate staff assignments.
2. Use the Employee dropdown to look up a specific consultant — you'll see
   their classification, base rate, assigned projects, and a pie chart showing
   billable vs. non-billable hours.
3. Use the Project dropdown to see who's assigned to a project, along with
   total cost, profit, and a bar chart breaking down hours by classification.