# Streamlit app


#This is to set the folders to path, so I can run outside pyCharm and/or in terminal
from pathlib import Path
import sys
PROJECT_SRC = Path(__file__).resolve().parents[1]
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

import streamlit as st

from data_access.queries import get_full_table, get_table_filter_district, get_table_filter_tm_year

df_district = get_table_filter_district("ClubPerformance", "95")


print(df_district.columns)

#data = df_district[["TM_Year","Active Members", "Club Name"]]

df_pivot = df_district.pivot_table(
    index=["TM_Year"],
    columns="Club Name",
    values="Active Members",
    aggfunc="max",
).sort_index()


#df_pivot = df_pivot.loc[:, df_pivot.max(axis=0) > 55] "klubbar som är större än 55
df_pivot = df_pivot[["Stockholm Toastmaster Club", "Stockholm International", "Ericsson Stockholm Toastmasters", "Stockholm Speakers Club"]]

print(df_pivot)




st.write(df_pivot)
st.line_chart(df_pivot, width=2000, height=250)


df_district_filtered = df_district.loc[df_district["TM_Year"] == "2025-2026"]

df_pivot2 = df_district_filtered.pivot_table(
    index=["Month_Num_Fiscal"],
    columns=["Club Name"],
    values="Active Members",
    aggfunc="max",
).sort_index()

print(df_pivot2)
df_pivot2 = df_pivot2[["Stockholm Toastmaster Club", "Stockholm International", "Ericsson Stockholm Toastmasters", "Stockholm Speakers Club"]]

st.line_chart(df_pivot2, height=250)



tm_year_option = st.selectbox(
    "Which year do you want to see?",
    sorted(df_district["TM_Year"].unique())
)


#st.text_input("Your name", key="name")
# You can access the value at any point with:
#Club_name = st.session_state.name

#This works like an auto-completion almost, when the user starts typing the dropdown alternatives filter auto
Club_name = st.selectbox(
    "Start typing club name",
    sorted(df_district["Club Name"].unique())
)


#df_district = df_district[df_district["Club Name"]=="Stockholm Toastmaster Club"]
df_filtered = df_district[
    (df_district["Club Name"] == Club_name) &
    (df_district["TM_Year"] == tm_year_option)
]

if df_filtered.empty:
    st.warning("No data found for that TM year and club name. Check you spelling of the club name and try again.")
else:
    chart_data = (
        df_filtered.pivot_table(
            index="Month_Num_Fiscal",
            values="Active Members",
            aggfunc="max",
        )
        .sort_index()
    )
    print(chart_data)

    st.line_chart(chart_data, height=250)


# Add a selectbox to the sidebar:
add_selectbox = st.sidebar.selectbox(
    'How would you like to be contacted?',
    ('Email', 'Home phone', 'Mobile phone')
)

# Add a slider to the sidebar:
add_slider = st.sidebar.slider(
    'Select a range of values',
    0.0, 100.0, (25.0, 75.0)
)