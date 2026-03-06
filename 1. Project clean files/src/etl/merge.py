#Includes functions for mergeing the downloaded CSVs

import pandas as pd
import glob
from datetime import datetime
import os


from etl.utils_dates import splitMonthDayYear


def read_csv_safe(
        filepath,
        sep=",",
        dtype=str,
        encodings=("utf-8", "utf-16", "latin1", "cp1252"),
        on_bad_lines="error",
):
    """
    Läser CSV robust genom att testa flera encodings.
    Returnerar DataFrame + encoding som fungerade.
    """
    last_error = None

    for enc in encodings:
        try:
            df = pd.read_csv(
                filepath,
                sep=sep,
                dtype=dtype,
                encoding=enc,
                on_bad_lines=on_bad_lines,
            )
            return df, enc
        except UnicodeDecodeError as e:
            last_error = e
            continue

    raise UnicodeDecodeError(
        f"Ingen fungerande encoding för filen: {filepath}"
    ) from last_error


def merge_CSVs(PATH: str, OUTPUT_FILENAME: str, EXPECTED_COLS: list) -> pd.DataFrame:
    # Denna skannar in CSV filerna till en dataframe, sen läggs den till en lista som
    # ackumuleras vid varje scannad CSV, sen mergas denna lista till en dataframe igen

    starttime = datetime.now()

    all_files = sorted(
        glob.glob(PATH + "/*.csv"),
        key=os.path.getmtime,
        reverse=False)

    amount = len(all_files)
    all_df = []
    count = 0
    #seen_schemas = set()  # för logg av olika kolumnvarianter

    for f in all_files:

        # Använder funktionen (read_csv_safe) skriven av ChatGPT som ska kunna hantera olika format såsom Utf-8 eller 16 osv
        # Verkar dock som att alla är Utf-8 i originalen. Sen när jag sparar alla mergeade så använder jag Utf-16 för att få med åäö osv om jag lagt till det
        try:
            df, used_encoding = read_csv_safe(f)
            # print(f"OK: {f} ({used_encoding})")
        except Exception as e:
            # skriv fel på egen rad (så du inte “tappar” felmeddelanden)
            # print(" " * 120, end="\r")  # rensa progressraden. Skriver 120 mellanslag och sen hoppar markören till vänster
            print(f"FEL: {f} → {e}")
            continue  # hoppa till nästa fil

        # För logg av olika varianter av kolumner
        # schema_signature = tuple(df.columns)
        # seen_schemas.add(schema_signature)

        #As of datum tillskrivs en variabel och delas upp i kolumner med funktionen splitMonthDayYear
        maxRow = df.shape[0] - 1  # -1 as columns are excluded from the count in the .iat method below
        maxRowValue = str(df.iat[maxRow, 0]) + str(df.iat[maxRow, 1])  # two columns retrieved as they have a "," in the sentence, makeing the sentence split as its interpreted as a separator above
        df['Month Year'] = maxRowValue

        #print(f"""maxRowValue: {maxRowValue}""")

        #NB! year and month can be incorrect for June and December. This is fixed in with another function
        AsOf_info = splitMonthDayYear(maxRowValue)  # aktiverar funktionen ovan som splittar upp värdet till flera o lägger in en dictionary

        # Fyller här kolumnernas rader med info från dictionarien
        df["MonthOf"] =  AsOf_info["MonthOf"]
        df["AsOf"] = AsOf_info["AsOf"]
        df["AsOfMonth"] = AsOf_info["AsOfMonth"]
        df["AsOfDay"] = AsOf_info["AsOfDay"]
        df["AsOfYear"] = AsOf_info["AsOfYear"]

        df["Club numeric"] = df["Club Number"]

        # Lägger till ny kolumn, denna hamnar i sista kolumn. -1 är att den tar
        # filnamnet som är längst bak i listan som skapats av split och lägger på ALLA rader under den nya kolumnen
        df['Filename'] = f.split(r"\\")[-1]

        # Tvingar fram att bara vissa kolumner tas med,
        # behåll bara relevanta kolumner
        df = df[[c for c in EXPECTED_COLS if c in df.columns]]

        # lägg till saknade kolumner i den nuvarande df:en från den individuella CSVn i loopen. Om CSVn saknar
        # vissa kolumnnamn så läggs dess till i DF, fast med blanka värden på raderna
        for c in EXPECTED_COLS:
            if c not in df.columns:
                df[c] = None

        all_df.append(df.head(-1))  # lägger till df i en lista, men innan det tar bort sista raden (eftersom vi nu lagt den under maxRowValue-kolumnen)
        count += 1

        percent = int(count * 100 / amount)  # eller round(...)
        # print(str(count), " files of ", str(amount), percentageDone, str("% Done"))
        print(f"{count} files of {amount}  {percent}% Done".ljust(60), end="\r", flush=True)

    # print(all_df[1]) #En lista som innehåller en dataframe.
    # print(len(all_df))
    # print(df.shape[0], df.shape[1]) #För att printa antal rader och kolumner vid felsökning

    print("Starting merging of all dataframes from the list to one dataframe")

    merged_df = pd.concat(all_df, axis=0, ignore_index=True, sort=False)

    # Fixar kolumnordningen
    merged_df = merged_df[EXPECTED_COLS]

    return merged_df


    endtime = datetime.now()
    timediff = endtime - starttime
    print("Scriptet tog : " + str(timediff))
