import calendar
from datetime import datetime
import re


MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

MONTH_MAP_REV = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}



#Denna delar upp TM-året i första och andra året. Sen avgör den via dictionary:ns månader vilket som är kalenderåret. Månad 7 och över är startåret, under är slutåret
def program_year_to_calendar_year(program_year: str, month_abbr: str) -> int:
    """
    Program year '2015-2016' (Jul->Dec=2015, Jan->Jun=2016)
    """
    start_year, end_year = program_year.split("-")
    start_year, end_year = int(start_year), int(end_year)
    month_num = MONTH_MAP[month_abbr]
    return start_year if month_num >= 7 else end_year


# Tar fram Program_year
# Tar fram en motsatt variant (den andra var calendar till program year) där program_year tas fram från calendar_year (dagens datum)
def calendar_year_program_year(calendar_year: int, month_num: int):  # -> int:
    """
    Calendar year 2016 (Jul->Dec='2016-2017', Jan->Jun='2015-2016')
    """

    if month_num >= 7:
        start_year = calendar_year
        end_year = calendar_year + 1
    else:
        start_year = calendar_year - 1
        end_year = calendar_year

    program_year = f"{start_year}-{end_year}"
    return program_year


# behöver kanske inte denna nu då jag kan formatera via datetime.strptime() direkt, men kan vara tydligt ha kvar för följa logiken i det andra URL skriptet
#Denna gör om formatet på AsOf stringen så att den passar in i URLen
def parse_asof_mmddyyyy(asof_str: str) -> str:
    """
    'As of 21-Jul-2016' -> '07/21/2016'
    """
    s = (asof_str or "").strip()
    s = re.sub(r"^\s*As\s+of\s+", "", s, flags=re.IGNORECASE) #"Tar bort #As of"
    dt = datetime.strptime(s, "%d-%b-%Y")
    return dt.strftime("%m/%d/%Y")



#När jag går via dagens datum så behöver jag egentligen inte MONTH_MAP, kan ta fram month_num direkt ur datetime. Men behåller ända detta
#ifall jag kommer att köra annan lösning än dagens datum senare.

#Tar fram month_end
#Denna returnerar sista datumet i varje månad
def month_end_mmddyyyy(program_year: str, month_abbr: str) -> str:
    year = program_year_to_calendar_year(program_year, month_abbr)
    #year = calendar_year
    month_num = MONTH_MAP[month_abbr]
    last_day = calendar.monthrange(year, month_num)[1]  # hanterar skottår
    dt = datetime(year, month_num, last_day)
    return dt.strftime("%m/%d/%Y")


# Längst ned i varje nedladdad CSV finns en string som innehåller månad, dag och år ihopslaget.
# Denna funktion splittar denna info till separata variabler. Dessa kommer senare att spridas till kolumner istället på varje rad
def splitMonthDayYear(AsOfString: str):

    # Month of Sep, As of 10/15/2022
    AsOf = AsOfString.split("As of ")[1]  # 10/15/2022
    MonthOf = AsOfString[9:12]  # Sep
    AsOfList = AsOf.split("/")

    AsOfMonth = AsOfList[0]  # 10
    AsOfDay = AsOfList[1]  # 15
    AsOfYear = AsOfList[2]  # 2022

    #returns a dictionary
    return {
        "AsOf": AsOf,
        "MonthOf": MonthOf,
        "AsOfMonth": AsOfMonth,
        "AsOfDay": AsOfDay,
        "AsOfYear": AsOfYear
    }