import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# Denna ser enklare ut än de andra, jag skrev den till stor del själv (förutom första blocket som jag kopierade
# Men regex skrev jag, borde vara tillräckligt säkert genom kombinationen med option, ser i html koden att det inte förekommer på annan plats i denna kombo

def get_years_from_page():
    url = "https://dashboards.toastmasters.org/Club.aspx?id=01"
    headers = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    #print(soup)
    extract = re.compile(r'\d\d\d\d-\d\d\d\d</option>') #söker efter 4 siffror sen "-" sen 4 siffror och </option>
    mo = extract.findall(str(soup))
    #print(mo)

    extract2 = re.compile(r'\d\d\d\d-\d\d\d\d')
    mo1 = extract2.findall(str(mo))
    print(mo1)

    return mo1
#ctl00$cpContent$TopControls1$ddlProgramYear



# Denna ser enklare ut än de andra, jag skrev den till stor del själv (förutom första blocket som jag kopierade
# Men regex skrev jag, borde vara tillräckligt säkert genom kombinationen med option, ser i html koden att det inte förekommer på annan plats i denna kombo

def get_months_from_page():
    url = "https://dashboards.toastmasters.org/Club.aspx?id=01"
    headers = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    #print(soup)
    #extract = re.compile(r'>[A-Za-z]{3}</option>')
    extract = re.compile(r'>[A-Z]{1}[a-z]{2}</option>') #söker efter 1 första stor bokstav, sen 2 små bokstäver och </option>
    mo = extract.findall(str(soup))
   #print(mo)

    extract2 = re.compile(r'[A-Z]{1}[a-z]{2}')
    mo1 = extract2.findall(str(mo))
    #print(mo1)

    return mo1
#ctl00$cpContent$TopControls1$ddlProgramYear


# Hitta districts från dropdown och spara i df



#Sätter district_id till default "01". Det distriktet kommer alltid vara med
def get_districts_from_page(year, month, district_id="01"):
    url = f"https://dashboards.toastmasters.org/{year}/Club.aspx?id={district_id}&month={month}"
    headers = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Hitta dropdownen som innehåller District-alternativ
    #    (vi letar efter en <select> som har minst en <option> med text som börjar med "District ")
    district_select = None
    for sel in soup.find_all("select"):
        opts = sel.find_all("option")
        if any((opt.get_text(strip=True) or "").startswith("District ") for opt in opts):
            district_select = sel
            #print("District dropdown id/name:", district_select.get("id"), district_select.get("name"))

            break

    if district_select is None:
        raise ValueError("Hittade ingen District-dropdown (<select>) på sidan. Layouten kan ha ändrats.")

    # 2) Extrahera District-koder från option-texterna
    #    Stödjer: District 01, District 95, District F, District U, etc.
    codes = []
    for opt in district_select.find_all("option"):
        text = (opt.get_text(strip=True) or "")

        # Ignorera placeholder som t.ex. "Select a District"
        if not text.startswith("District "):
            continue

        m = re.fullmatch(r"District\s+([A-Za-z0-9]+)", text)
        if not m:
            continue

        code = m.group(1)

        # Pad för numeriska så 1 -> 01 (om dropdown råkar innehålla "District 1")
        if code.isdigit():
            code = code.zfill(2) #zfill lägger till nollor till vänster tills dess det når en viss bredd.

        codes.append(code)

    if not codes:
        raise ValueError("Hittade inga District-koder i dropdownen.")

    # 3) Unika i ordning (ingen 'sammanhängande'-logik → vi tillåter hopp som 08→10)
    seen = set()
    final = []
    for c in codes:
        if c in seen:
            continue
        seen.add(c)
        final.append(c)

    dfDistricts = pd.DataFrame({"District code": final, "District": [f"District {x}" for x in final]})
    return dfDistricts



#Hitta senaste AsOf datum i dropdown. Först spara alla i lista. Sen ta fram översta, dvs senaste.
#För att filen inte ska bli tom kan senaste inte vara dagens, funkar bara manuellt, så ta -1 dag om det är dagens


def get_asof_list_from_page(year, month, district_id="01"):
#def get_asof_list_from_page(year, district_id, month):
    """
    Hämtar en lista av 'As of DD-Mmm-YYYY' från dropdownen på sidan (utan Selenium)
    och returnerar en pandas DataFrame.

    Exempel: 'As of 11-Jun-2024'
    """
    url = f"https://dashboards.toastmasters.org/{year}/district.aspx?id={district_id}&month={month}"
    headers = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Hitta dropdownen (<select>) som innehåller "As of ..."
    asof_select = None
    for sel in soup.find_all("select"):
        opts = sel.find_all("option")
        if any(((opt.get_text(strip=True) or "").startswith("As of ")) for opt in opts):
            asof_select = sel
            #print("AsOf dropdown id/name:", asof_select.get("id"), asof_select.get("name"))
            break

    if asof_select is None:
        raise ValueError("Hittade ingen As-of dropdown (<select>) på sidan. Layouten kan ha ändrats.")

    # 2) Extrahera As-of från option-texterna
    #    Vi tar bara de som verkligen följer formatet "As of 11-Jun-2024"
    asof_dates = []
    for opt in asof_select.find_all("option"):
        text = (opt.get_text(strip=True) or "")

        m = re.fullmatch(r"As of (\d{1,2}-[A-Za-z]{3}-\d{4})", text)
        if not m:
            continue

        asof_dates.append(m.group(1))  # bara datumdelen (t.ex. 11-Jun-2024)

    if not asof_dates:
        raise ValueError("Hittade inga giltiga 'As of DD-Mmm-YYYY' i dropdownen.")

    # 3) Unika i ordning (behåller ordningen från sidan)
    seen = set()
    asof_unique = []
    for d in asof_dates:
        if d in seen:
            continue
        seen.add(d)
        asof_unique.append(d)

    df = pd.DataFrame({
        "AsOfText": [f"As of {d}" for d in asof_unique],
        "AsOfDate": pd.to_datetime(asof_unique, format="%d-%b-%Y", errors="coerce")
    })

    return df

