from etl.state import build_download_plan


URL = "https://dashboards.toastmasters.org/Club.aspx?id=01"
ORG_LEVEL = "Club"

#For SQL
MAIN_TABLE = "ClubPerformance"


df_state = build_download_plan(ORG_LEVEL, URL, MAIN_TABLE)

print(df_state)


