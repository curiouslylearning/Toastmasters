"""
Dashboard-datan tvättas:

- December får korrekt år
- Juni får korrekt år
- Skapar kolumn med nummer av månad
- Skapar TM-år, tex "2025-2026"

"""

from etl.utils_dates import MONTH_MAP
import pandas as pd


def year_month_from_filename(df: pd.DataFrame):
    #NB! Only use this on data downloaded with URL that has the date info in the filename

    # Regex drar ut TM-Year och månad från filnamnet (som jag började spara med år angivet redan vid nedladdning (när jag började använda URL hösten 2025))
    # Fick hjälp av ChatGPT med denna

    df2 = df

    # 1) Extrahera TM_Year (t.ex. 2016-2017)
    df2["TM_Year"] = df["Filename"].str.extract(r'((?:19|20)\d{2}-(?:19|20)\d{2})')[0]

    # 2) Extrahera månadstexten direkt efter TM_Year_ (t.ex. Jun i 2016-2017_Jun_...)
    df2["MonthTxt"] = (
        df2["Filename"]
        .str.extract(r'(?:19|20)\d{2}-(?:19|20)\d{2}_([A-Za-z]{3})')[0]
        .str.title()
    )

    # 3) Mappa månadstext -> månadnummer

    df2["Month_Num"] = df2["MonthTxt"].map(MONTH_MAP)
    df2["Month_Num"] = pd.to_numeric(df2["Month_Num"]).astype("Int64")

    # 4) Dela TM_Year i start och slutår (heltal)
    years = df2["TM_Year"].str.extract(r'(?P<start>\d{4})-(?P<end>\d{4})')
    df2["TM_Year_Start"] = pd.to_numeric(years["start"]).astype("Int64")
    df2["TM_Year_End"] = pd.to_numeric(years["end"]).astype("Int64")

    # 5) Jul-Dec => startår, annars => slutår
    mask = df2["Month_Num"] >= 7
    df2.loc[mask, "CalendarYear"] = df2.loc[mask, "TM_Year_Start"]
    df2.loc[~mask, "CalendarYear"] = df2.loc[~mask, "TM_Year_End"]

    df2.drop(columns=["MonthTxt", "TM_Year_Start", "TM_Year_End"], inplace=True)

    return df2


def convert_to_numeric(df: pd.DataFrame,column_convert_list: list):

# print("Starting to convert string values in selected columns to integer values")
    for c in column_convert_list:

        print("Converting data type in column: " + str(c))

    # Finns med möjlighet att skriva "NA" på de som inte går att konvertera (men jag vill ha error). I så fall: df2[c] = (pd.to_numeric(df2[c], errors="coerce").astype("Int64"))
    # Förutsätter att det egentligen bara är heltal i dessa CSVer. (Varning i andra kontexter att "." skulle kunna vara amerikansk 1000 avskiljare, det måste tydligen kontexten avgöra)
        df[c] = pd.to_numeric(df[c]).astype("Int64")

    return df


