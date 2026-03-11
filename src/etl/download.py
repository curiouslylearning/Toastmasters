#Functions for downloading CSVs' from TMI dashboard Club performance

import os
import time
from datetime import datetime
import requests
import re
import uuid
import pandas as pd


from etl.utils_dates import MONTH_MAP, MONTH_MAP_REV, month_end_mmddyyyy, parse_asof_mmddyyyy



def extract_district_code(district_str: str) -> str:
    s = (district_str or "").strip()
    if not s:
        raise ValueError("District-strängen är tom")

    m = re.search(r"(?i)\bdistrict\b\s*([A-Za-z0-9]+)\b", s)
    if m:
        return m.group(1)

    m = re.fullmatch(r"[A-Za-z0-9]+", s)
    if m:
        return s

    raise ValueError(f"Kunde inte extrahera distriktskod från: {district_str!r}")

    return m.group(1)

#builds the URL
#enklare version än den chatgpt genererade

def build_url(program_year: str, SITE: str, district_code: str, month_end: str, asof_date: str) -> str:
    #return f"http://dashboards.toastmasters.org/{program_year}/export.aspx?type=CSV&report=clubperformance~{district_code}~{month_end}~{asof_date}~{program_year}"

    #ORG_LEVEL = "Club"
    #ORG_LEVEL = "District"

    return f"http://dashboards.toastmasters.org/{program_year}/export.aspx?type=CSV&report={SITE}~{district_code}~{month_end}~{asof_date}~{program_year}"


#Tar bort eventuella otillåtna tecken  och ersätter med "_", samt tar bort mellanslag o punkt osv
def safe_filename(name: str) -> str:
    """
    Gör filnamn Windows-säkert.
    """
    invalid = r'<>:"/\|?*'
    for ch in invalid:
        name = name.replace(ch, "_")
    name = name.replace("\n", " ").replace("\r", " ").strip()
    # Förhindra avslutande punkt/blanksteg
    name = name.rstrip(" .")
    return name


#Test som ska vara mer säker för error
def download_to_file(url: str, final_path: str) -> None:
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    tmp_path = final_path + f".tmp_{uuid.uuid4().hex}"

    TIMEOUT_SECONDS = 60

    tries = 6
    for attempt in range(1, tries + 1):
        try:
            with requests.get(url, stream=True, timeout=TIMEOUT_SECONDS) as r:
                r.raise_for_status()
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 128):
                        if chunk:
                            f.write(chunk)

            os.replace(tmp_path, final_path)
            return

        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ReadTimeout) as e:

            # städa tempfil
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

            if attempt == tries:
                raise

            sleep_s = min(60, 2 ** (attempt - 1))  # 1,2,4,8,16,32
            print(f"⚠️ Nätfel ({type(e).__name__}) försök {attempt}/{tries}. Väntar {sleep_s}s…")
            time.sleep(sleep_s)



def download_from_df(org_level: str, df: pd.DataFrame, out_dir: str) -> pd.DataFrame:
    """
    df måste innehålla kolumnerna: TM-Year, Month, District, AsOf
    Laddar ned 1 fil per rad och sparar som:
      TM-Year_Month_District_AsOf.csv

    Returnerar en liten logg-DF med url + path per rad.
    """

    required = {"TM_Year", "Month", "District", "AsOf"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame saknar kolumner: {sorted(missing)}. Har: {list(df.columns)}")

    log_rows = []

    #loopar df:en

    #iterrows() returnerar en tuple, jag får då fram värdet i en kolumn i den serien genom ange kolumnnamnet i den serien (row).
    # "i" är första delen av den tuplen o returnerar motsvarande rad (serien)
    #alternativt hade jag kunnat använda df.loc men detta ska anses effektivare vid större dataset
    #reset_index används ifall det skulle vara hopp i ordningen på indexet från tex tidigare filtrering
    for i, row in df.reset_index(drop=True).iterrows():
        program_year = str(row["TM_Year"]).strip()
        month_abbr   = str(row["Month"]).strip()
        district_str = str(row["District"]).strip()
        asof_str     = str(row["AsOf"]).strip()

        if month_abbr not in MONTH_MAP:
            raise ValueError(f"Rad {i}: Okänd månad {month_abbr!r} (förväntar t.ex. 'Jul', 'Jun', osv)")

        #tar fram district_code (tex "01" från "District 01"
        district_code = extract_district_code(district_str)

        #tar fram month_end från programår tex "2025-2026" och månad tex "Jan"
        month_end = month_end_mmddyyyy(program_year, month_abbr)
        #asof_date = parse_asof_mmddyyyy(asof_str)

        #The month of today
        today = datetime.today()
        month_num_today = int(today.strftime("%m"))
        month_abbr_today = MONTH_MAP_REV[month_num_today]
        print(month_abbr_today)

        #Jag lägger till att om månaden är Juni så kommer asof_date vara blankt. Det har efter test visat sig att sista AsOfdatum på just Juni månad kommer ge en tom CSV.
        #Vid nedladdning manuellt (eller Sellenium) kommer samma AsOf ge korrekt CSV med värden, men dagens datum. Det har jag tidigare åtgärdat i annat skript när alla CSVs sen mergeas
        #Jag lägger även till att om månaden idag är samma som senaste As of i dropdown, då lämnas As of blankt
        #Eftersom en "bugg" ger en tom fil om jag anger senaste As of trots att den är scrape:ad från dropdownen
        #Tillskillnad från Juni så kommer dock As Of datumet längst ned i varje fil vara korrekt

        if month_abbr == "Jun" or month_abbr == month_abbr_today:
            asof_date = ""
        else:
            asof_date = parse_asof_mmddyyyy(asof_str)

        #bygger URLen
        url = build_url(program_year, org_level, district_code, month_end, asof_date)

        #skapar filnamn
        filename = safe_filename(f"{program_year}_{month_abbr}_{district_str}_{asof_str}.csv")
        final_path = os.path.join(out_dir, filename)

        #laddar ned filen
        print(f"[{i+1}/{len(df)}] Hämtar: {url}")
        download_to_file(url, final_path)
        print(f"    Sparad: {final_path}")

        #lägger till information i en loggbok. Lägger till i lista av dictionaries
        log_rows.append({
            "TM_Year": program_year,
            "Month": month_abbr,
            "District": district_str,
            "AsOf": asof_str,
            "URL": url,
            "SavedPath": final_path
        })

        time.sleep(0.2)   # testa 0.2–1.0

    return pd.DataFrame(log_rows)

