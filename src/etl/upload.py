#Functions to upload to postgresSQL

from datetime import datetime
from sqlalchemy import text
import pandas as pd

from etl.sql_connection import sql_engine

def create_backup_table(db_table: str):
    """
    A backup table of the main table is created, named after todays date
    """
    
    starttime = datetime.now()

    engine = sql_engine()

    backup_name = f'{db_table}_backup_{datetime.now():%Y_%m_%d}'

    with engine.begin() as conn:
        conn.execute(text(f'''
            CREATE TABLE "{backup_name}" AS
            SELECT * FROM "{db_table}";
        '''))

    print("Backup skapad:", backup_name)

    endtime = datetime.now()
    timediff = endtime - starttime
    print("Backupscriptet tog : " + str(timediff))


def create_table_and_upload(main_table: str, df: pd.DataFrame):
    #Use this for the first time, if there is no table yet. Or if you want to overwrite an existing one

    # För uppladdning första gången
    # Obs! Tog 13 minuter att ladda upp 1,7 GB senast. Du kan i pgAdmin kolla på dashboard-fliken att det rör sig

    print("Uppladdning till databas påbörjas")

    starttime = datetime.now()

    engine = sql_engine()

    df.to_sql(
        # name="FindAClub",
        name=f"{main_table}",
        con=engine,
        schema="public",
        if_exists="replace",  # eller append. Varning! Replace tar bort hela och lägger in ny
        index=False,
        chunksize=50_00,  # 5000
        # method="multi" #Innebär att den gör en enda stor Insert, alla rader på en gång typ (i chunksize) tog bort denna, hänger sig. Men ska vara effektivt ibland.
    )

    endtime = datetime.now()
    timediff = endtime - starttime
    print("Scriptet att ladda upp till databas tog : " + str(timediff))



def upload_via_staging_table(main_table: str, staging_table: str, df: pd.DataFrame) -> None:

    """Uploads latest df to main table, via a staging table that it creates.
     Duplicates are handled through checking versus the staging table.
     The duplicates are deleted from the main table, and then the staging table is transfered
     to the main table"""

    print("Uppladdning till databas påbörjas")

    starttime = datetime.now()

    engine = sql_engine()

    schema = "public"
    chunksize = 5000

    df.to_sql(
        name=staging_table,
        con=engine,
        schema=schema,
        if_exists="replace",
        index=False,
        chunksize=chunksize,
    )

    # 2-3) i en transaktion: ta bort gamla månader som ingår i staging, och fyll på med nya
    sql = f"""
    BEGIN;

    -- ta bort befintliga rader för de månader/år som finns i staging
    DELETE FROM public."{main_table}" cp
    USING (
      SELECT DISTINCT "TM_Year", "Month_Num"
      FROM public."{staging_table}"
    ) s
    WHERE cp."TM_Year"  = s."TM_Year"
      AND cp."Month_Num" = s."Month_Num";

    -- lägg in nya versionen
    INSERT INTO public."{main_table}"
    SELECT * FROM public."{staging_table}";

    COMMIT;
    """

    with engine.begin() as conn:
        conn.execute(text(sql))

    endtime = datetime.now()
    timediff = endtime - starttime
    print("Scriptet att ladda upp data till SQL tog : " + str(timediff))