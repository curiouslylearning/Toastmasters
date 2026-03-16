# Streamlit app


#This is to set the folders to path, so I can run outside pyCharm and/or in terminal
from pathlib import Path
import sys
PROJECT_SRC = Path(__file__).resolve().parents[1]
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

import streamlit as st
import altair as alt

from data_access.queries import get_full_table, get_table_filter_district, get_table_filter_tm_year


st.title("Varmt välkommen! 👋 Här bor Stockholm Toastmasters statistik ")

st.subheader("""
Låt nyfikenheten växa\n
""")

st.markdown("""**Hur många medlemmar är vi i Stockholm Toastmasters?**\n
**Vilket år hade vi flest medlemmar?**\n
**Hur stor andel av medlemmarna förlänger sina medlemskap?**
""", unsafe_allow_html=True)


df_CP_d95 = get_table_filter_district("ClubPerformance", "95")
df_DP_d95 = get_table_filter_district("DistrictPerformance", "95")


print(df_CP_d95.columns)

#data = df_CP_d95[["TM_Year","Active Members", "Club Name"]]


tm_year_option = st.selectbox(
    "Which year do you want to see?",
    sorted(df_CP_d95["TM_Year"].unique())
)


#st.text_input("Your name", key="name")
# You can access the value at any point with:
#Club_name = st.session_state.name

#This works like an auto-completion almost, when the user starts typing the dropdown alternatives filter auto
Club_name = st.selectbox(
    "Start typing club name",
    sorted(df_CP_d95["Club Name"].unique())
)


#df_CP_d95 = df_CP_d95[df_CP_d95["Club Name"]=="Stockholm Toastmaster Club"]

#Filteras efter användarinteraktionen ovan
df_filtered_CP_d95 = df_CP_d95[
    (df_CP_d95["Club Name"] == Club_name) &
    (df_CP_d95["TM_Year"] == tm_year_option)
    ]


#---
df_filtered_sort_DP = df_DP_d95[
    (df_DP_d95["Club Name"] == Club_name) &
    (df_DP_d95["TM_Year"] == tm_year_option)
    ]

#---

#sorterar för att får max månad av senaste kalenderåret
df_filtered_CP_d95 = df_filtered_CP_d95.sort_values(["CalendarYear", "Month_Num_Fiscal"],
                                         ascending=[True, True])

#sorterar för att får max månad av senaste kalenderåret
df_filtered_sort_DP_d95 = df_filtered_sort_DP.sort_values(["CalendarYear", "Month_Num_Fiscal"],
                                         ascending=[True, True])


col1, col2, col3 = st.columns(3)

col1.metric(label= "Medlemmar just nu", value=df_filtered_CP_d95["Active Members"].iloc[-1], delta=df_filtered_CP_d95["Active Members"].iloc[-1] - df_filtered_CP_d95["Active Members"].iloc[-2])

col2.metric(label= "Nya medlemmar", value=df_filtered_sort_DP_d95["New"].iloc[-1], delta=df_filtered_sort_DP_d95["New"].iloc[-1] - df_filtered_sort_DP_d95["New"].iloc[-2])

col3.metric(label= "Avklarade Level1s", value=df_filtered_CP_d95["Level 1s"].iloc[-1], delta=df_filtered_CP_d95["Level 1s"].iloc[-1] - df_filtered_CP_d95["Level 1s"].iloc[-2])



month_order = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]

if df_filtered_CP_d95.empty:
    st.warning("No data found for that TM year and club name. Check you spelling of the club name and try again.")
else:
    chart_data = (
        df_filtered_CP_d95.sort_values("Month_Num_Fiscal")
        .groupby(["Month_Num_Fiscal", "MonthOf"], as_index=False)["Active Members"]
        .max()
    )

    chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("MonthOf:N", sort=month_order, title="Month"),
            y=alt.Y("Active Members:Q", title="Active Members"),
            tooltip=[
                alt.Tooltip("MonthOf:N", title="Month"),
                alt.Tooltip("Active Members:Q", title="Active Members"),
            ],
        )
        .properties(height=250)
    )

    st.altair_chart(chart, use_container_width=True)




if df_filtered_sort_DP.empty:
    st.warning("No data found for that TM year and club name. Check you spelling of the club name and try again.")
else:
    chart_data = (
        df_filtered_sort_DP.sort_values("Month_Num_Fiscal")
        .groupby(["Month_Num_Fiscal", "MonthOf"], as_index=False)["New"]
        .max()
    )

    chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("MonthOf:N", sort=month_order, title="Month"),
            y=alt.Y("New:Q", title="New Members"),
            tooltip=[
                alt.Tooltip("MonthOf:N", title="Month"),
                alt.Tooltip("New Members:Q", title="New Members"),
            ],
        )
        .properties(height=250)
    )

    st.altair_chart(chart, use_container_width=True)



df_district_filtered = df_CP_d95.loc[df_CP_d95["TM_Year"] == tm_year_option]

df_pivot2 = df_district_filtered.pivot_table(
    index=["Month_Num_Fiscal"],
    columns=["Club Name"],
    values="Active Members",
    aggfunc="max",
).sort_index()

print(df_pivot2)
df_pivot2 = df_pivot2[["Stockholm Toastmaster Club", "Stockholm International", "Ericsson Stockholm Toastmasters", "Stockholm Speakers Club"]]

st.line_chart(df_pivot2, height=250)



chart_data2 = (
        df_CP_d95
        .pivot_table(
            index=["Month_Num_Fiscal", "MonthOf"],
            values="Active Members",
            aggfunc="max",
        )
        .sort_index(level="Month_Num_Fiscal")
        .droplevel("Month_Num_Fiscal")
    )
print(f"""printar :" {chart_data2}""")

print(chart_data2)
print(chart_data2.index.duplicated().sum())


max_members = df_CP_d95["Active Members"].max()

add_slider = st.sidebar.slider(
    "Select a range of values",
    0.0, max_members.astype(float), (25.0, 75.0)
)

min_members, max_members = add_slider

club_chart_data = (
    df_CP_d95[df_CP_d95["TM_Year"] == tm_year_option]
    .groupby("Club Name", as_index=False)["Active Members"]
    .max()
    .sort_values("Active Members", ascending=False)
)

club_chart_data = club_chart_data[
    club_chart_data["Active Members"].between(min_members, max_members)
]

chart = (
    alt.Chart(club_chart_data)
    .mark_bar()
    .encode(
        y=alt.Y("Club Name:N", sort="-x", title="Club", axis=alt.Axis(labelLimit=500)),
        x=alt.X("Active Members:Q", title="Active Members"),
        tooltip=[
            alt.Tooltip("Club Name:N", title=""),
            alt.Tooltip("Active Members:Q", title="Active Members"),
        ],
    )
    .properties(height=600)
)


st.altair_chart(chart, use_container_width=True)


df_pivot4 = df_CP_d95.pivot_table(
    index=["TM_Year"],
    values="Active Members",
    aggfunc="mean",
).sort_index()


print(df_pivot4)

chart = (
    alt.Chart(df_pivot4.reset_index())
    .mark_bar()
    .encode(
        y=alt.Y("Active Members:Q", sort="-y", title="Active Members", axis=alt.Axis(labelLimit=500)),
        x=alt.X("TM_Year:N", title="TM_Year"),
        tooltip=[
            alt.Tooltip("Active Members:Q", title="Active Members, Mean"),
            alt.Tooltip("TM_Year:N", title="TM_Year"),
        ],
    )
    .properties(height=600)
)


st.altair_chart(chart, use_container_width=True)



#sorterar för att får max månad av senaste kalenderåret
df_sort = df_CP_d95.sort_values(["CalendarYear", "Month_Num_Fiscal"],
                                ascending=[True, True])

year_max = df_sort["CalendarYear"].iloc[-1]
month_num_fiscal_max = df_sort["Month_Num_Fiscal"].iloc[-1]


df_district_max = df_CP_d95[
    (df_CP_d95["Month_Num_Fiscal"] == month_num_fiscal_max)
]


df_pivot5 = df_district_max.pivot_table(
    index=["TM_Year"],
    values="Active Members",
    aggfunc="sum",
).sort_index()


print(df_pivot5)

chart = (
    alt.Chart(df_pivot5.reset_index())
    .mark_bar()
    .encode(
        y=alt.Y("Active Members:Q", sort="-y", title="Active Members", axis=alt.Axis(labelLimit=500)),
        x=alt.X("TM_Year:N", title="TM_Year"),
        tooltip=[
            alt.Tooltip("Active Members:Q", title="Active Members"),
            alt.Tooltip("TM_Year:N", title="TM_Year"),
        ],
    )
    .properties(height=600)
)


st.altair_chart(chart, use_container_width=True)



#Level1


df_pivot6 = df_district_max.pivot_table(
    index=["TM_Year"],
    values="Level 1s",
    aggfunc="sum",
).sort_index()


print(df_pivot6)

chart_levels = (
    alt.Chart(df_pivot6.reset_index())
    .mark_bar()
    .encode(
        y=alt.Y("Level 1s:Q", sort="-y", title="Level 1s", axis=alt.Axis(labelLimit=500)),
        x=alt.X("TM_Year:N", title="TM_Year"),
        tooltip=[
            alt.Tooltip("Level 1s:Q", title="Level 1s"),
            alt.Tooltip("TM_Year:N", title="TM_Year"),
        ],
    )
    .properties(height=600)
)


st.altair_chart(chart_levels, use_container_width=True)



# Add a selectbox to the sidebar:
add_selectbox = st.sidebar.selectbox(
    'How would you like to be contacted?',
    ('Email', 'Home phone', 'Mobile phone')
)


df_pivot = df_CP_d95.pivot_table(
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




