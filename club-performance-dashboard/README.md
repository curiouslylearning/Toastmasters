# District 95 Dashboard

Interactive, drill-down dashboard for `d95.csv`.

## What it includes
- Filters by Toastmasters year, snapshot date, division, status, and club search.
- Hierarchical drilldown: District -> Division -> Area -> Club.
- Trend view across the selected Toastmasters year.
- Club comparison bubble map and clickable leaderboard.
- Insight cards highlighting momentum and risk signals.

## Run locally
From the repository root:

```powershell
python -m http.server 8080
```

Then open:

`http://localhost:8080/club-performance-dashboard/`

## Notes
- The app reads `../d95.csv` directly, so keep the dashboard folder inside this repository.
- No build step required (plain HTML/CSS/JavaScript).
