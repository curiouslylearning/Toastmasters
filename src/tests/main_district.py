from etl.clean import year_month_from_filename, convert_to_numeric
from etl.download import download_from_df
from etl.merge import merge_CSVs
from etl.state import build_download_plan
from etl.upload import upload_via_staging_table, create_table_and_upload
from etl.utils_dates import fiscal_month

#output path for the downloaded CSVs
OUT_DIR = r'C:\CSVs_district'

#path from where the CSVs are that will be merged
PATH = OUT_DIR

URL = "https://dashboards.toastmasters.org/District.aspx?id=01"
ORG_LEVEL = "Districtperformance" #"Clubperformance" or "Districtperformance"
ORG_LEVEL_SHORT = "District" #Club or District

#For SQL
#If you already have a table in SQL. Set to "Yes". Else set to "No"
SQL_TABLE_EXISTS = "Yes"
MAIN_TABLE = "DistrictPerformance"
STAGING_TABLE = "DistrictPerformance_staging"


OUTPUT_FILENAME = r'C:\Users\ClaesPalm\OneDrive - ECI Media Management AB\Dokument\Toastmasters\Dataanalyser\District_Latest_update.csv'


#Om District-fliken används. Tar med dessa kolumner när DFs mergeas
EXPECTED_COLS = ["District","Division","Area","Club","Club Name","New","Late Ren.","Oct. Ren.",
                 "Apr. Ren.","Total Ren.","Total Chart","Total to Date",
                 "Distinguished Status","Charter Date/Suspend Date",
                 "Month Year","MonthOf", "AsOf", "AsOfMonth", "AsOfDay","AsOfYear","Club numeric","Filename"]


#Om District-fliken används. Kolumner att ändra till nummerformat
COLUMN_LIST_CONVERT_TYPE = ["New","Late Ren.","Oct. Ren.","Apr. Ren.","Total Ren.","Total Chart","Total to Date",
                    "AsOfMonth","AsOfDay","AsOfYear","Club numeric","CalendarYear","Month_Num", "Month_Num_Fiscal"]



def main():

    #bygger DFen. Skapar en range mellan senaste TM_year och Month i SQL och senaste på hemsida
    df_state = build_download_plan(ORG_LEVEL_SHORT, URL, MAIN_TABLE, SQL_TABLE_EXISTS)

    #Save to CSV, not necessary
    df_state.to_csv(r'C:\Users\ClaesPalm\OneDrive - ECI Media Management AB\Dokument\Toastmasters\Dataanalyser\1. Project clean files\Output\df_state.csv', encoding="utf-16")

    # download
    # loopar DFen
    # laddar ned via URL

    download_from_df(ORG_LEVEL, df_state, OUT_DIR)


    merged_df = merge_CSVs(PATH, OUTPUT_FILENAME,EXPECTED_COLS, ORG_LEVEL_SHORT)

    # Behöver encoding="utf-16" för att den ska ge åäö i output istället för konstiga tecken)
    merged_df.to_csv(OUTPUT_FILENAME, encoding="utf-16")

    df_year_month_fix = year_month_from_filename(merged_df)

    df_fiscal_month = fiscal_month(df_year_month_fix)

    df_clean = convert_to_numeric(df_fiscal_month, COLUMN_LIST_CONVERT_TYPE)

    #create_backup_table(MAIN_TABLE)

    create_table_and_upload(MAIN_TABLE, df_clean)

    #upload_via_staging_table(MAIN_TABLE, STAGING_TABLE, df_clean)

    print(df_clean.info())

if __name__ == "__main__":
    main()


#merge files to one df

#clean the df

#upload to SQL
#skapa mellantabell
#jämför databasen med mellantabellen. Ta bort dubletter i stora databasen.
#för över nya datan från mellantabellen


