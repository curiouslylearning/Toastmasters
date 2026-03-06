"""
Bokeh dashboard app (PowerBI-ish cross-filter):

- Left: District "slicer" bar chart (click a bar to filter)
- Right: Multi-line chart (one line per club)
    X = TM_Year
    Y = Active Members

Snapshot rule (your requirement):
- Pick ONE snapshot month based on:
    "latest month within the latest TM_Year" (TM-year ordering Jul..Jun)
- Then use THAT SAME Month_Num for ALL TM_Years
- For each (Club numeric, TM_Year) in that snapshot month: take MAX(Active Members)
- Missing values = GAP (NaN) => Bokeh breaks the line

Run:
    bokeh serve --show dashboard_app.py

Data columns required:
    District, Club numeric, TM_Year, Month_Num, Active Members

Data loading:
- Uses DATABASE_URL environment variable for SQLAlchemy.
  Example (Windows cmd):
      set DATABASE_URL=postgresql+psycopg2://<USER>:<PASSWORD>@127.0.0.1:5432/<DB>
"""

from __future__ import annotations

import os
from itertools import cycle

import pandas as pd

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, HoverTool, Div
from bokeh.palettes import Turbo256
from bokeh.plotting import figure
from bokeh.models import DataTable, TableColumn



# ---------------------------------------------------------------------
# CONFIG (your exact column names)
# ---------------------------------------------------------------------
DISTRICT_COL = "District"
CLUB_ID_COL = "Club numeric"
TM_YEAR_COL = "TM_Year"
MONTH_NUM_COL = "Month_Num"
ACTIVE_MEMBERS_COL = "Active Members"

TOP_N_CLUBS = 30  # reduce if the line chart gets too heavy

MONTH_ABBR = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}


# ---------------------------------------------------------------------
# DATA LOADING (SQL)
# ---------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    from sqlalchemy import create_engine, text
    from etl.sql_connection import sql_engine
    engine = sql_engine()

    #db_url = os.environ.get("DATABASE_URL")
    #if not db_url:
     #   raise RuntimeError(
      #      "DATABASE_URL env var not set.\n"
       #     "Example:\n"
        #    "  set DATABASE_URL=postgresql+psycopg2://<USER>:<PASSWORD>@127.0.0.1:5432/<DB>\n"
        #)

    #engine = create_engine(db_url, connect_args={"connect_timeout": 10})

    # Select only the columns we need
    sql = text(f"""
        SELECT
            "{DISTRICT_COL}"        AS "{DISTRICT_COL}",
            "{CLUB_ID_COL}"         AS "{CLUB_ID_COL}",
            "{TM_YEAR_COL}"         AS "{TM_YEAR_COL}",
            "{MONTH_NUM_COL}"       AS "{MONTH_NUM_COL}",
            "{ACTIVE_MEMBERS_COL}"  AS "{ACTIVE_MEMBERS_COL}"
        FROM "ClubPerformance"
    """)

    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def tm_month_order(month_num: pd.Series) -> pd.Series:
    """
    Convert calendar month (1..12) to Toastmasters TM-year order (Jul..Jun):
      Jul=1, Aug=2, ... Dec=6, Jan=7, ... Jun=12
    Formula: ((month + 5) % 12) + 1
    """
    return ((month_num + 5) % 12) + 1


def compute_snapshot_month(dff: pd.DataFrame) -> tuple[str, int]:
    """
    Snapshot month selection rule:
      - find latest TM_Year present (by start year in 'YYYY-YYYY')
      - inside that TM_Year, pick latest month in TM-year sense (Jul..Jun)
      - return (latest_tm_year, snapshot_month_num)
    """
    dff = dff.copy()
    dff["_tm_start"] = dff[TM_YEAR_COL].str.slice(0, 4).astype(int)

    latest_tm_year = dff.loc[dff["_tm_start"].idxmax(), TM_YEAR_COL]

    latest_year_df = dff[dff[TM_YEAR_COL] == latest_tm_year].copy()
    latest_year_df["_tm_month_order"] = tm_month_order(latest_year_df[MONTH_NUM_COL])

    snapshot_tm_order = int(latest_year_df["_tm_month_order"].max())

    # Inverse mapping back to calendar Month_Num:
    # month = ((tm_order + 5) % 12) + 1
    snapshot_month_num = int(((snapshot_tm_order + 5) % 12) + 1)

    return latest_tm_year, snapshot_month_num


def compute_club_series_snapshot_month(dff: pd.DataFrame) -> tuple[pd.DataFrame, str, int]:
    """
    Returns:
      series_df: columns = [Club numeric, TM_Year, active_members]
      latest_tm_year, snapshot_month_num

    Logic:
      - Choose snapshot month based on latest TM_Year (global)
      - Filter ALL years to that Month_Num
      - Aggregate max Active Members per (club, TM_Year)
    """
    latest_tm_year, snapshot_month_num = compute_snapshot_month(dff)

    snap = dff[dff[MONTH_NUM_COL] == snapshot_month_num].copy()

    series_df = (
        snap.groupby([CLUB_ID_COL, TM_YEAR_COL], as_index=False)
            .agg(active_members=(ACTIVE_MEMBERS_COL, "max"))
    )

    return series_df, latest_tm_year, snapshot_month_num


def pick_top_clubs(series_df: pd.DataFrame, latest_tm_year: str) -> list[str]:
    """
    Choose clubs to draw to keep the chart readable.
    Rank by snapshot value in the latest TM_Year.
    """
    latest = series_df[series_df[TM_YEAR_COL] == latest_tm_year].copy()
    if latest.empty:
        best = (
            series_df.groupby(CLUB_ID_COL, as_index=False)["active_members"]
            .max()
            .sort_values("active_members", ascending=False)
        )
        return best[CLUB_ID_COL].head(TOP_N_CLUBS).astype(str).tolist()

    best = latest.sort_values("active_members", ascending=False)
    return best[CLUB_ID_COL].head(TOP_N_CLUBS).astype(str).tolist()


# ---------------------------------------------------------------------
# Build app
# ---------------------------------------------------------------------
df_raw = load_data()

# Normalize types
df = df_raw.copy()
df[DISTRICT_COL] = df[DISTRICT_COL].astype(str)
df[CLUB_ID_COL] = df[CLUB_ID_COL].astype(str)
df[TM_YEAR_COL] = df[TM_YEAR_COL].astype(str)
df[MONTH_NUM_COL] = pd.to_numeric(df[MONTH_NUM_COL], errors="coerce")
df[ACTIVE_MEMBERS_COL] = pd.to_numeric(df[ACTIVE_MEMBERS_COL], errors="coerce")

df = df.dropna(subset=[MONTH_NUM_COL, ACTIVE_MEMBERS_COL, TM_YEAR_COL, DISTRICT_COL, CLUB_ID_COL])
df[MONTH_NUM_COL] = df[MONTH_NUM_COL].astype(int)

# TM_Year ordering for x-axis
df["_tm_start"] = df[TM_YEAR_COL].str.slice(0, 4).astype(int)
tm_year_order = (
    df[[TM_YEAR_COL, "_tm_start"]]
    .drop_duplicates()
    .sort_values("_tm_start")[TM_YEAR_COL]
    .tolist()
)

# ---------------------------------------------------------------------
# Left: District slicer table (click row to filter)
# ---------------------------------------------------------------------
district_list = (
    df[[DISTRICT_COL]]
    .drop_duplicates()
    .sort_values(DISTRICT_COL)
    .reset_index(drop=True)
)

district_source = ColumnDataSource(district_list)

district_table = DataTable(
    source=district_source,
    columns=[TableColumn(field=DISTRICT_COL, title="District")],
    selectable=True,
    index_position=None,  # hide row index column
    height=520,
    width=450,
)

# ---------------------------------------------------------------------
# Right: Multi-line clubs (snapshot month, missing=gaps)
# ---------------------------------------------------------------------
title_div = Div(text="<b>Filter:</b> All districts", styles={"font-size": "14px"})

p_lines = figure(
    title="Active Members by TM-Year (one line per club)",
    x_range=tm_year_order,
    height=520,
    width=920,
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location="above",
)
p_lines.xaxis.axis_label = "TM-Year"
p_lines.yaxis.axis_label = "Active Members"
p_lines.xgrid.grid_line_color = None

club_renderers: list = []

hover = HoverTool(
    tooltips=[
        ("Club numeric", "@club_id"),
        ("TM-Year", "@TM_Year"),
        ("Active Members", "@active_members{0,0}"),
    ],
    mode="mouse",
)
p_lines.add_tools(hover)


def clear_club_lines() -> None:
    global club_renderers
    for r in club_renderers:
        try:
            p_lines.renderers.remove(r)
        except ValueError:
            pass
    club_renderers = []
    p_lines.legend.items = []


def render_multiline_for_district(district: str | None) -> None:
    clear_club_lines()

    dff = df if not district else df[df[DISTRICT_COL] == district].copy()
    if dff.empty:
        title_div.text = "<b>Filter:</b> (no data)"
        return

    series_df, latest_tm_year, snapshot_month_num = compute_club_series_snapshot_month(dff)

    snap_month_abbr = MONTH_ABBR.get(snapshot_month_num, str(snapshot_month_num))
    filter_text = "All districts" if not district else f"District {district}"
    title_div.text = f"<b>Filter:</b> {filter_text} — <b>Snapshot month:</b> {snap_month_abbr} (from {latest_tm_year})"

    keep_clubs = pick_top_clubs(series_df, latest_tm_year)
    series_df = series_df[series_df[CLUB_ID_COL].isin(keep_clubs)].copy()

    # Pivot WITHOUT fill => NaN => gaps
    pivot = (
        series_df.pivot_table(
            index=TM_YEAR_COL,
            columns=CLUB_ID_COL,
            values="active_members",
            aggfunc="max",
            dropna=False,
        )
        .reindex(tm_year_order)
    )

    color_cycle = cycle(Turbo256)

    for club in pivot.columns.tolist():
        color = next(color_cycle)
        y_vals = pivot[club].astype(float).tolist()  # NaNs preserved

        src = ColumnDataSource(
            data={
                "TM_Year": tm_year_order,
                "active_members": y_vals,
                "club_id": [club] * len(tm_year_order),
            }
        )

        r_line = p_lines.line(
            x="TM_Year",
            y="active_members",
            source=src,
            line_width=2,
            color=color,
            alpha=0.85,
            legend_label=str(club),
        )
        r_pts = p_lines.circle(
            x="TM_Year",
            y="active_members",
            source=src,
            size=6,
            color=color,
            alpha=0.9,
        )

        club_renderers.extend([r_line, r_pts])

    p_lines.legend.click_policy = "hide"
    p_lines.legend.location = "top_left"
    p_lines.legend.label_text_font_size = "9pt"


def on_district_selected(attr: str, old, new) -> None:
    sel = district_source.selected.indices
    if not sel:
        render_multiline_for_district(None)
        return

    i = sel[0]
    district = district_source.data[DISTRICT_COL][i]
    render_multiline_for_district(district)


district_source.selected.on_change("indices", on_district_selected)

# initial render
render_multiline_for_district(None)

curdoc().add_root(
    column(
        Div(text="<h2>Bokeh Dashboard</h2>"),
        row(district_table, column(title_div, p_lines)),
    )
)
curdoc().title = "Bokeh Cross-Filter Dashboard"
