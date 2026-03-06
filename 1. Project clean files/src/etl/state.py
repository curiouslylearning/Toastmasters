#This module has the functions to create a df with the TM-years, months and districts to download
#It is for feeding the URL. Each row in the df contains building blocks for the URL (the API for downloading
#from the TMI dashboard


import pandas as pd
from sqlalchemy import create_engine

from etl.sql_connection import sql_engine
from etl.utils_dates import MONTH_MAP, MONTH_MAP_REV
from etl.utils_dates import program_year_to_calendar_year
from etl.utils_scrape import get_years_from_page, get_months_from_page, get_districts_from_page, get_asof_list_from_page


def get_source_max() -> date:
    """
    1a: Läs senaste 'Calendar Year' och 'Month' från hemsidan/API.
    """
    end_TM_year = get_years_from_page()[0]
    end_month_abbr = get_months_from_page()[0]

    end_year = program_year_to_calendar_year(end_TM_year, end_month_abbr)
    end_month = MONTH_MAP[end_month_abbr]

    return end_year, end_month

def get_sql_max() -> date | None:
    """
    1b: Läs senaste 'Calendar Year' och 'Month' som redan finns i SQL.
    """

    engine = sql_engine()

    sql = """
          SELECT "TM_Year", \
                 "CalendarYear", \
                 "Month_Num", \
                 COUNT(DISTINCT "Club numeric") AS clubs
          FROM "ClubPerformance"
          GROUP BY "TM_Year", "CalendarYear", "Month_Num"
          ORDER BY "TM_Year" ASC, "Month_Num" ASC; \
          """

    df_summary = pd.read_sql(sql, engine)
    df_YearMonth = df_summary.iloc[-1]  # Tar längst ned i den sorterade df, blir en serie

    start_year = df_YearMonth["CalendarYear"]
    start_month = df_YearMonth["Month_Num"]

    return start_year, start_month


def generate_year_month_update_range(start_year: int, start_month: int, end_year: int, end_month: int) -> pd.DataFrame:
    """
    Skapar en DataFrame med:
    - CalendarYear
    - Month_Num
    - TM_Year (Jul–Jun)
    Från angivet startår/månad fram till innevarande månad.
    """
    start_date = pd.Timestamp(start_year, start_month, 1)
    # end_date = pd.Timestamp.today().replace(day=1)
    end_date = pd.Timestamp(end_year, end_month, 1)

    # Skapar en range av datum. Går att loopa och att som nedan skrivas direkt till en dataframe
    dates = pd.date_range(start=start_date, end=end_date,
                          freq="MS")  # freq="MS" betyder month start, alltså första dagen i månaden, den frekvensen

    # print(dates)
    # print(type(dates))

    for i in dates:
        print(i)

    df = pd.DataFrame({
        "CalendarYear": dates.year,
        "Month_Num": dates.month,
        "MonthStart": dates
    })

    # Härled TM_Year
    tm_start_year = df["CalendarYear"].where(
        df["Month_Num"] >= 7,
        df["CalendarYear"] - 1
    )

    df["TM_Year"] = (
            tm_start_year.astype(str)
            + "-"
            + (tm_start_year + 1).astype(str)
    )

#It will generate something like this:
    """  CalendarYear  Month_Num MonthStart    TM_Year
0          2025         12 2025-12-01  2025-2026
1          2026          1 2026-01-01  2025-2026
2          2026          2 2026-02-01  2025-2026"""

    return df[["CalendarYear", "Month_Num", "MonthStart", "TM_Year"]]


def build_download_plan() -> pd.DataFrame:
    """
    1: Skapa df med allt som ska laddas ner (Year, Month, District, AsOf, url, filename)
    """
    # Bygger den stora DF som ska användas för nedladdning.

    end_year, end_month = get_source_max() #outputs end_year, end_month
    start_year, start_month = get_sql_max() #outputs start_year, start_month
    df_year_month_update_range = generate_year_month_update_range(start_year, start_month, end_year, end_month)


    #print(start_year, start_month, end_year, end_month)
    #print(df_year_month_update_range)

    chunks = []
    for i in range(len(df_year_month_update_range)):
        month_num = df_year_month_update_range.loc[i, "Month_Num"]
        program_year = df_year_month_update_range.loc[i, "TM_Year"]

        # hämtar distriktlistan
        dfDistricts = get_districts_from_page(program_year, month_num, district_id="01")

        # hämtar as of listan - sätter district till 01, antar det är samma as of för alla distrikt
        df_asof = get_asof_list_from_page(program_year, month_num, "01")
        # print(df_asof)
        # print("Antal As-of datum:", len(df_asof))

        # tar första as of i listan o omvandlar formatet
        # asof_date = str(df_asof.loc[0, "AsOfDate"].strftime("%m/%d/%y"))

        # hämtar asof_text från As of dataframen
        asof_text = str(df_asof.loc[0, "AsOfText"])

        # df måste innehålla kolumnerna: TM-Year, Month, District, AsOf
        df_chunk = dfDistricts

        # lägger på kolumner från nuvarande steg i df update loopen
        df_chunk["TM_Year"] = program_year
        df_chunk["Month_Num"] = month_num
        # df_chunk["AsOfDate"] = asof_date
        df_chunk["AsOf"] = asof_text

        # Sparar nuvarande df i en lista
        chunks.append(df_chunk)

    # lägger ihop alla dfs i listan
    df_for_download = pd.concat(chunks, ignore_index=True)

    # lägg till månadskolumn i textform. Hade kunnat skippa men för att det ska ändå in i filnamnet senare_
    # och en redan skriven funktion för nedladdning tar det formatet och omvandlar till siffra igen
    df_for_download["Month"] = df_for_download["Month_Num"].map(MONTH_MAP_REV)

    column_names = ["TM_Year", "Month", "District", "AsOf"]

    # Ändrar ordning på kolumner
    df_for_download = df_for_download[column_names]

    print("Printing the head of the df_for_download")
    print(df_for_download)

    #An example of how the DF can look like
    """TM_Year Month      District               AsOf
0    2025-2026   Dec   District 01   As of 8-Jan-2026
1    2025-2026   Dec   District 02   As of 8-Jan-2026
2    2025-2026   Dec   District 03   As of 8-Jan-2026
3    2025-2026   Dec   District 04   As of 8-Jan-2026"""

    return df_for_download



if __name__ == "__main__":
    build_download_plan()