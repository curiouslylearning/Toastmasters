#Queries to SQL to get data to dataframes for visualization and analysis

import pandas as pd
from etl.sql_connection import sql_engine
from sqlalchemy import text
from datetime import datetime


def get_full_table(table_name:str) -> pd.DataFrame:
    """Retrieve full table from SQL database"""

    engine = sql_engine()

    sql = text(
        f"""
    SELECT *
    FROM "{table_name}"
    """)


    df_all = pd.read_sql(sql, engine)

    return df_all

def get_table_filter_district(table_name: str, district: str) -> pd.DataFrame:
    """Retrieve rows from a SQL table filtered by district."""

    engine = sql_engine()

    sql = text(
        f"""
        SELECT *
        FROM "{table_name}"
        WHERE "District" = :district
        """
    )

    return pd.read_sql(sql, engine, params={"district": district})

def get_table_filter_tm_year(table_name: str, tm_year: str) -> pd.DataFrame:
    """Retrieve rows from a SQL table filtered by district."""

    engine = sql_engine()

    sql = text(
        f"""
        SELECT *
        FROM "{table_name}"
        WHERE "TM_Year" = :tm_year
        """
    )

    return pd.read_sql(sql, engine, params={"tm_year": tm_year})



if __name__ == "__main__":
    #df_all = get_full_table("DistrictPerformance")
    #print(df_all.head(5))

    #df_CP_d95 = get_table_filter_district("DistrictPerformance", "95")
    #print(df_CP_d95.head(5))

    df_tm_year = get_table_filter_tm_year("DistrictPerformance", "2025-2026")
    print(df_tm_year.head(5))
    print(df_tm_year.columns)