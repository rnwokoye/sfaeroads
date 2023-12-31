# streamlit_app.py
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from random import randint
import hmac
import streamlit as st
from sqlalchemy import (
    text,
    Table,
    MetaData,
    Column,
    Integer,
    String,
    Date,
    insert,
    create_engine,
)

import admin_page

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
            st.session_state["name"] = st.secrets["credentials"]["names"][
                st.session_state["username"]
            ]
            del st.session_state["password"]  # Don't store the username or password.
            st.session_state.session_data["username"] = st.session_state["username"]
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


## Added this for new offense df
def get_offense_type(csv_file):
    offense_df = pd.read_csv(csv_file).set_index("Description")
    return offense_df


def select_offense_df(df: pd.DataFrame):
    selected_offense = st.selectbox(
        "Choose an offense Description to start:",
        options=list(df.index),
        placeholder="Choose option",
    )
    if selected_offense is not None:
        st.write("You selected: ", selected_offense)
        fine_amount = df.loc[selected_offense]["Fine_Amount"].replace(",", "")
        st.write(fine_amount)
    return selected_offense, fine_amount


def log_out():
    for key in st.session_state.keys():
        del st.session_state[key]


# Enter Form Details
def create_offense() -> pd.DataFrame:
    # Get the offence info
    offense, fine = select_offense_df(get_offense_type("violations_list.csv"))

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


def run_program(logged_on_officer: str) -> dict:
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

        if st.button("log_out", type="primary", on_click=log_out):
            log_out()
    try:
        return my_df
    except UnboundLocalError as e:
        st.stop()
        return


# New Testing Starts Here
def insert_offense(offense_details: pd.DataFrame):
    # Hard coded because data_frame columns are different form actual table columns

    offense_details = offense_details.astype(
        {"Fine Amount": "int", "Date Issued": "str", "Due Date": "str"}
    )
    # Rename df cols to match db cols because of insert staement mapping
    ren_cols = {
        "First Name": "first_name",
        "Last Name": "last_name",
        "Offense": "offence_type",
        "Fine Amount": "fine_amount",
        "License Plate": "license_plate",
        "Date Issued": "date_issued",
        "Due Date": "due_date",
        "Phone Number": "phone_number",
        "Location": "location",
        "Description": "description",
        "Officer Name": "officer_name",
    }

    offense_details = offense_details.rename(columns=ren_cols)

    offense_details = offense_details.to_dict(orient="records")[0]
    query = text(
        """
    INSERT INTO traffic_tickets (tkt_number, first_name, last_name, phone_number, offence_type, fine_amount, license_plate, date_issued, due_date, location, description, officer_name)
    VALUES (:tkt_number, :first_name, :last_name, :phone_number, :offence_type, :fine_amount, :license_plate, :date_issued, :due_date, :location, :description, :officer_name);
    """
    )

    # execute the query
    with conn.session as s:
        s.execute(query, offense_details)
        s.commit()
    return True


def main():
    check_password()
    username = st.session_state.session_data.get("username")
    name = st.session_state.name
    if username:
        st.write(f"Welcome {name}")
        if st.button("log_out", on_click=log_out):
            log_out()
        # Check if the username is an admin or a regular user
        if is_admin(username):
            admin_page.display_data()
        else:
            insert_offense(run_program(username))


if __name__ == "__main__":
    main()
