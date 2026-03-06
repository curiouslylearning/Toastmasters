from etl.state import build_download_plan
from etl.download import download_from_df
from etl.merge import merge_CSVs
from etl.clean import year_month_from_filename, convert_to_numeric
from etl.upload import create_backup_table, upload_via_staging_table
from etl.sql_connection import sql_engine

#output path for the downloaded CSVs
OUT_DIR = r'C:\CSVs'

#path from where the CSVs are that will be merged
PATH = OUT_DIR

OUTPUT_FILENAME = r'C:\Users\ClaesPalm\OneDrive - ECI Media Management AB\Dokument\Toastmasters\Dataanalyser\1. Project clean files\Output\ClubPerformance_Latest_update.csv'

#Om ClubPerformance-fliken används. Tar med dessa kolumner när DFs mergeas
EXPECTED_COLS = ["District","Division","Area","Club Number","Club Name","Club Status","CSP","Mem. Base",
                       "Active Members","Net Growth","Goals Met","Level 1s","Level 2s","Add. Level 2s","Level 3s",
                       "Level4s, Path Completions, or DTM Awards","Add.Level 4s, Level 5s, or DTM award","New Members",
                       "Add. New Members","Off. Trained Round 1","Off. Trained Round 2","Mem. dues on time Oct","Mem. dues on time Apr",
                       "Off. List On Time","Club Distinguished Status","Level 4s","Level 5s","Level4s, Level 5s, or DTM award","CCs","Add. CCs","ACs","Add. ACs","CL/AL/DTMs","Add. CL/AL/DTMs","Month Year","MonthOf", "AsOf", "AsOfMonth", "AsOfDay","AsOfYear","Club numeric","Filename"]


#Om ClubPerformance-fliken används. Kolumner att ändra till nummerformat
COLUMN_LIST_CONVERT_TYPE = ["Club Number","Mem. Base","Active Members","Net Growth","Goals Met","Level 1s","Level 2s","Add. Level 2s","Level 3s",
                    "Level4s, Path Completions, or DTM Awards","Add.Level 4s, Level 5s, or DTM award","New Members","Add. New Members",
                    "Level 4s","Level 5s","Level4s, Level 5s, or DTM award","CCs","Add. CCs","ACs","Add. ACs","CL/AL/DTMs","Add. CL/AL/DTMs",
                    "AsOfMonth","AsOfDay","AsOfYear","Club numeric","CalendarYear","Month_Num"]



def main():

    #bygger DFen. Skapar en range mellan senaste TM_year och Month i SQL och senaste på hemsida
    #df_state = build_download_plan()

    # download
    # loopar DFen
    # laddar ned via URL

    #download_from_df(df_state, OUT_DIR)


    merged_df = merge_CSVs(PATH, OUTPUT_FILENAME,EXPECTED_COLS)

    # Behöver encoding="utf-16" för att den ska ge åäö i output istället för konstiga tecken)
    merged_df.to_csv(OUTPUT_FILENAME, encoding="utf-16")

    df_year_month_fix = year_month_from_filename(merged_df)

    df_clean = convert_to_numeric(df_year_month_fix, COLUMN_LIST_CONVERT_TYPE)

    #create_backup_table("ClubPerformance")

    upload_via_staging_table("ClubPerformance_staging", df_clean)

    print(df_clean.info())

main()


#merge files to one df

#clean the df

#upload to SQL
#skapa mellantabell
#jämför databasen med mellantabellen. Ta bort dubletter i stora databasen.
#för över nya datan från mellantabellen


