import streamlit as st
import pandas as pd
import numpy as np
import datetime
import streamlit.components.v1 as components


# define connection string
conn = st.connection("cockroachdb", type="sql")

# from db_con import create_connection
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)


def filter_dataframe(res_df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        res_df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return res_df

    res_df = res_df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in res_df.columns:
        if is_object_dtype(res_df[col]):
            try:
                res_df[col] = pd.to_datetime(
                    res_df[col],
                    format="%Y%m%d",
                )
            except Exception:
                pass

        if is_datetime64_any_dtype(res_df[col]):
            res_df[col] = res_df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        # to_filter_columns = st.multiselect("Filter dataframe on", res_df.columns)
        to_filter_columns = st.multiselect(
            "Filter dataframe on",
            ["tkt_number", "last_name", "phone_number", "officer_name"],
        )
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(res_df[column]) or res_df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    res_df[column].unique(),
                    default=list(res_df[column].unique()),
                )
                res_df = res_df[res_df[column].isin(user_cat_input)]
            elif is_numeric_dtype(res_df[column]):
                _min = float(res_df[column].min())
                _max = float(res_df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                res_df = res_df[res_df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(res_df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        res_df[column].min(),
                        res_df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    res_df = res_df.loc[res_df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    res_df = res_df[
                        res_df[column].astype(str).str.contains(user_text_input)
                    ]

    return res_df


def calc_fine(row):
    initial_fine = row["fine_amount"]
    days_lapsed = row.days_lapsed

    if days_lapsed > 30:
        periods_overdue = -(-days_lapsed // 30)  # Ceiling
        return initial_fine * periods_overdue
    else:
        return initial_fine


def style_data_row(val: str = "Overdue"):
    color = "darkred" if val == "Overdue" else "green"
    return f"background-color: {color}"


def set_background_color(df: pd.DataFrame):
    my_status = "Overdue"
    green = "background-color: green"
    red = "background-color: red"
    np.where(df["status"] == my_status, red, green)


def get_tickets() -> pd.DataFrame:
    query = f"""SELECT * FROM traffic_tickets;"""
    today = datetime.datetime.now().date()
    data = conn.query(query)
    res_df = pd.DataFrame(data)
    res_df["days_lapsed"] = pd.to_timedelta(today - res_df["due_date"]).dt.days
    res_df["status"] = np.where(res_df["days_lapsed"] > 30, "Overdue", "Current")
    res_df["penalty_amount"] = res_df.apply(lambda x: calc_fine(x), axis=1)

    return res_df, today


def display_data():
    tab1, tab2 = st.tabs(["Tickets View", "Charts"])
    data, date = get_tickets()
    # data.set_index("tkt_number", inplace=True)

    with tab1:
        st.subheader("A View For All Tickets")
        st.write(f"Today's date is {date}")
        filtered_data = filter_dataframe(data)
        styled_data = filtered_data.style.applymap(style_data_row, subset=["status"])
        st.dataframe(styled_data)

    with tab2:
        st.subheader("Charts")
        st.write(f"Today's date is {date}")
        df2 = pd.DataFrame(data.offence_type.value_counts()).reset_index()
        st.bar_chart(df2, x="offence_type", y="count")
