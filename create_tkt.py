# streamlit_app.py
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from random import randint
import hmac
import streamlit as st
from sqlalchemy import text

import admin_page

# from config.app_db_con import create_connection

import psycopg2
from psycopg2.extensions import register_adapter, AsIs

register_adapter(np.int64, AsIs)

conn = st.connection("cockroachdb", type="sql")

# App Title
st.header("Traffice Regulatory System")


def is_admin(username):
    with open("groups_list.json", "r") as admins:
        admins_group = json.load(admins)
        return True if username in admins_group.get("admins") else False


def check_password():
    """Returns `True` if the user had a correct password."""

    if "session_data" not in st.session_state:
        st.session_state.session_data = {}

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets["credentials"][
            "users"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets["credentials"]["passwords"][st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            st.session_state["username"] = st.session_state["username"]
            del st.session_state["password"]  # Don't store the username or password.
            st.session_state.session_data["username"] = st.session_state["username"]

            # return user_name
            # del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False


if not check_password():
    st.stop()


def get_offense_category() -> dict:
    with open("offense_dictionary.json", "r") as f:
        offense_dictionary = json.load(f)
        return offense_dictionary


def select_offence(offence_dict: dict) -> tuple:
    # Use a select box for the offense
    selected_offense = st.selectbox(
        "Choose an offense to begin:",
        options=list(offence_dict.keys()),
        index=0,
        placeholder="Choose option",
        key="selected_offense",
    )
    fine = offence_dict.get(f"{selected_offense}")
    if fine != "":
        st.write(f"${fine}")
    return (selected_offense, fine)


def log_out():
    for key in st.session_state.keys():
        del st.session_state[key]


# Enter Form Details
def create_offense() -> pd.DataFrame:
    # Get the offence info
    offense, fine = select_offence(get_offense_category())

    # Input Offender Forms
    with st.form(key="offense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        # Use a select box for the offense
        with col1:
            first_name = st.text_input("First Name")
            offense_date = st.date_input(
                "Date of Offense", value="today", format="MM/DD/YYYY", disabled=True
            )
            due_date = offense_date + timedelta(days=30)
            st.date_input(
                "Pay By Due Date", value=due_date, format="MM/DD/YYYY", disabled=True
            )
        with col2:
            last_name = st.text_input("Last Name")
            plate_number = st.text_input("Plate Number")
            phone_number = st.text_input("Mobile_no")
        location = st.text_input("Location")
        offense_description = st.text_area("Ticket Details")
        submit_button = st.form_submit_button("create ticket", type="primary")

    if submit_button:
        if not first_name or not last_name or not plate_number or not phone_number:
            st.error("Please fill in all the required fields.")
            st.stop()
        else:
            st.write(
                f"Fine of ${fine} for offense of {offense} has been submited for {first_name}"
            )
        tkt_attributes = {
            "First Name": first_name,
            "Last Name": last_name,
            "Offense": offense,
            "Fine Amount": fine,
            "License Plate": plate_number,
            "Date Issued": offense_date,
            "Due Date": due_date,
            "Phone Number": phone_number,
            "Location": location,
            "Description": offense_description,
        }
        df = pd.DataFrame(tkt_attributes, index=[0])
        st.write("Ticket Submitted")
        return df


def run_program(logged_on_officer: str) -> pd.DataFrame:
    # Make sure Officer is logged on
    if logged_on_officer:
        tkt_issued = create_offense()
        if tkt_issued is not None:
            n = 6
            my_df = pd.DataFrame(tkt_issued)
            my_df["Officer Name"] = logged_on_officer
            my_df["tkt_number"] = "".join(
                ["{}".format(randint(0, 9)) for num in range(0, n)]
            )
        else:
            st.warning("Select a ticket to begin")
            st.stop()

        # if st.button("log_out", type="primary", on_click=log_out):
        #     log_out()
    try:
        return my_df
    except UnboundLocalError as e:
        # st.write("Logged out")
        st.stop()
        return


def insert_offense(offense_details: pd.DataFrame):
    # Hard coded because data_frame columns are different form actual table columns
    cols = [
        "first_name",
        "last_name",
        "offence_type",
        "fine_amount",
        "license_plate",
        "date_issued",
        "due_date",
        "phone_number",
        "location",
        "description",
        "officer_name",
        "tkt_number",
    ]

    placeholders = ", ".join(["%s"] * len(cols))

    query = text(
        f"""INSERT INTO traffic_tickets ({', '.join(cols)}) VALUES ({placeholders});"""
    )
    offense_details["Fine Amount"] = offense_details["Fine Amount"].astype(int)
    values = offense_details.iloc[0].tolist()

    values_tuple = tuple(values)
    values_list = [values_tuple]

    # execute the query
    with conn.session as s:
        s.execute(query, values_list)
        s.commit()
    return True


def main():
    check_password()
    username = st.session_state.session_data.get("username")
    if username:
        st.write(f"Welcome {username}")
        if st.button("log_out", on_click=log_out):
            log_out()
        # Check if the username is an admin or a regular user
        if is_admin(username):
            admin_page.display_data()
        else:
            insert_offense(run_program(username))


if __name__ == "__main__":
    main()
