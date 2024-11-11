import streamlit as st
import sqlite3

# Create a connection to the SQLite database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Function to validate the login credentials
def check_credentials(username, password):
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    return user

# UI for login page
st.title("Login to SIN Expense Tracker")

# Input fields for username and password
username = st.text_input("Username")
password = st.text_input("Password", type="password")

# Attempt login
if st.button("Login"):
    if check_credentials(username, password):
        # Set session state as logged in
        st.session_state.logged_in = True
        st.session_state.username = username  # Store the username
        st.success("Logged in successfully!")
        st.experimental_rerun()  # Redirect to main page
    else:
        st.error("Invalid credentials, please try again.")
