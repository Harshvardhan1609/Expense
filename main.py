import sqlite3
import streamlit as st
import io
from io import BytesIO
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import os
import pytz


# Function to create the SQLite database and table
def create_table():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Create the expenses table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP,
            amount REAL NOT NULL,
            purpose TEXT NOT NULL,
            bill_image BLOB,
            purchase_date DATE
        )
    ''')
    
    # Commit changes and close the connection
    conn.commit()
    conn.close()

# Function to insert a new expense record into the database
def insert_expense(amount, purpose, purchase_date, bill_image):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get the current time in IST (Indian Standard Time)
    india_timezone = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(india_timezone).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO expenses (date, amount, purpose, purchase_date, bill_image) 
        VALUES (?, ?, ?, ?, ?)
    ''', (current_time, amount, purpose, purchase_date, bill_image))
    conn.commit()
    conn.close()

# Function to retrieve all expenses
def get_expenses():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    records = cursor.fetchall()
    conn.close()
    return records

# Function to retrieve the last 5 expenses
def get_recent_expenses():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC LIMIT 5")
    records = cursor.fetchall()
    conn.close()
    return records

# Function to search expenses by purpose or date range
def search_expenses(purpose=None, start_date=None, end_date=None):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    query = "SELECT id, date, amount, purpose, bill_image, purchase_date FROM expenses WHERE 1=1"
    params = []

    if purpose:
        query += " AND purpose LIKE ?"
        params.append(f"%{purpose}%")

    if start_date:
        query += " AND purchase_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND purchase_date <= ?"
        params.append(end_date)

    cursor.execute(query, tuple(params))
    records = cursor.fetchall()
    conn.close()
    return records

# Function to update an expense
def update_expense(expense_id, amount, purpose, purchase_date, bill_image):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(''' 
        UPDATE expenses 
        SET amount = ?, purpose = ?, purchase_date = ?, bill_image = ? 
        WHERE id = ? 
    ''', (amount, purpose, purchase_date, bill_image, expense_id))
    conn.commit()
    conn.close()

# Function to retrieve expenses within the given date range
def get_expenses_by_date_range(start_date, end_date):
    print("sql called")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE purchase_date BETWEEN ? AND ?", (start_date, end_date))
    records = cursor.fetchall()
    conn.close()
    return records

# Function to generate PDF report

def download_expense_report_as_excel(expenses):
    # Check if expenses are passed correctly
    # print(f"Expenses passed to the function: {expenses}")

    # Check if there are any records
    if not expenses:
        print("No expenses found.")
        return None  # Return None if no expenses are available

    # Convert the expenses data to a pandas DataFrame
    df = pd.DataFrame(data=expenses,columns=["ID", "Date", "Amount", "Purpose", "Purchase Date","BILL"])

    # Check if DataFrame is populated correctly
    # print(f"DataFrame before date conversion: {df.head()}")

    # Convert 'Purchase Date' to datetime (handling any invalid or missing dates)
    # df["Purchase Date"] = pd.to_datetime(df["Purchase Date"], errors='coerce', dayfirst=True)

    # # Check after conversion
    # print(f"DataFrame after date conversion: {df.head()}")

    # # Handle any NaT (Not a Time) values in 'Purchase Date'
    # df = df.dropna(subset=["Purchase Date"])

    # # Remove the "Bill" column if you don't want to include the binary data (images)
    df = df.drop(["Purchase Date","BILL"],axis=1)

    # Save the DataFrame to an Excel file in-memory using openpyxl engine
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    # Rewind the buffer to the beginning before downloading
    excel_file.seek(0)

    return excel_file

# Create the table when the script is run
create_table()

# Streamlit UI Setup
st.set_page_config(page_title="SIN Education and Technology - Expense Tracker", layout="wide")
st.title("SIN Education and Technology - Expense Tracker")
st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        .header {
            font-size: 40px;
            color: #2c3e50;
            font-weight: bold;
        }
        .section-header {
            font-size: 30px;
            color: #2980b9;
        }
        .expense-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            background-color: #fff;
        }
        .expense-card h5 {
            color: #2c3e50;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar for navigation and actions
with st.sidebar:
    st.header("Expense Management")
    st.subheader("Track your expenses in a premium way.")
    st.markdown("Upload bills and track expenses in an interactive and graphical manner.")
    st.markdown("---")
    page = st.selectbox("Navigate to", ["Home", "Add Expense", "Search Expenses", "Modify Expense", "Download Reports"])

# Home Page
if page == "Home":
    st.header("Dashboard Overview")
    
    col1, col2, col3 = st.columns(3)

    # Total Expense Visualization
    with col1:
        expenses = get_expenses()
        total_expense = sum([expense[2] for expense in expenses])
        st.metric("Total Expenses (INR)", f"₹{total_expense:.2f}")

    # Expense Count Visualization
    with col2:
        total_count = len(expenses)
        st.metric("Total Expense Records", total_count)
    
    # Average Expense Visualization
    with col3:
        average_expense = total_expense / total_count if total_count > 0 else 0
        st.metric("Average Expense (INR)", f"₹{average_expense:.2f}")

    # Visualizations (Plotting)
    st.subheader("Expense Breakdown")

    # Create DataFrame for expenses
    expense_df = pd.DataFrame(expenses, columns=["ID", "Date", "Amount", "Purpose", "Purchase Date", "Bill"])
    
    # Plot total expenses by purpose using Plotly
    st.subheader("Total Expenses by Purpose")
    expense_purpose = expense_df.groupby("Purpose")["Amount"].sum().reset_index()
    fig = px.bar(expense_purpose, x="Purpose", y="Amount", title="Total Expenses by Purpose", 
                 labels={"Purpose": "Expense Purpose", "Amount": "Total Amount (INR)"}, 
                 color="Amount", color_continuous_scale="Viridis")
    st.plotly_chart(fig)

    # Plot expense distribution over time using Plotly
    st.subheader("Monthly Expense Trend")
    expense_df["Date"] = pd.to_datetime(expense_df["Date"])

# Group by month (use the period 'M' to group by month) and sum only the 'Amount' column
    monthly_expenses = expense_df.groupby(expense_df["Date"].dt.to_period("M"))["Amount"].sum().reset_index()

# Convert Period to Timestamp for better visualization
    monthly_expenses["Date"] = monthly_expenses["Date"].dt.to_timestamp()

# Create the line plot for monthly expenses
    fig2 = px.line(monthly_expenses, x="Date", y="Amount", title="Monthly Expense Trend", 
                labels={"Date": "Month", "Amount": "Total Amount (INR)"}, markers=True)
    st.plotly_chart(fig2)

# Add Expense Page
elif page == "Add Expense":
    st.header("Add Expense")
    st.markdown("Enter the details of your expense below.")
    
    with st.form("expense_form"):
        amount = st.number_input("Amount (in INR)", min_value=0.0, format="%.2f")
        purpose = st.text_input("Purpose of Expense")
        purchase_date = st.date_input("Date of Purchase", min_value=datetime(2020, 1, 1), value=datetime.today())
        bill_image = st.file_uploader("Upload Bill Image", type=["jpg", "png", "jpeg"])

        submit_button = st.form_submit_button("Submit Expense")
        if submit_button:
            if amount > 0 and purpose and purchase_date and bill_image:
                bill_image_bytes = bill_image.read()
                insert_expense(amount, purpose, purchase_date, bill_image_bytes)
                st.success("Expense submitted successfully!")
            else:
                st.error("Please provide all details.")

# Search Expense Page
elif page == "Search Expenses":
    st.header("Search Expenses")

    # Search Filters
    purpose = st.text_input("Enter Purpose to Search (optional)")
    start_date = st.date_input("Start Date", min_value=datetime(2020, 1, 1), value=datetime.today())
    end_date = st.date_input("End Date", min_value=datetime(2020, 1, 1), value=datetime.today())

    if st.button("Search Expenses"):
        # Fetch expenses based on search criteria
        search_results = search_expenses(purpose, start_date, end_date)

        if search_results:
            # Display search results
            st.subheader("Search Results")
            for expense in search_results:
                st.markdown(f"**ID**: {expense[0]}")
                st.markdown(f"**Date**: {expense[1]}")
                st.markdown(f"**Amount**: ₹{expense[2]}")
                st.markdown(f"**Purpose**: {expense[3]}")
                st.markdown(f"**Purchase Date**: {expense[5]}")

                # Show 'Download Bill' button if a bill exists
                if expense[4]:  # Check if the bill is not None (there is a bill image)
                    bill_image = BytesIO(expense[4])  # Convert BLOB data to image
                    bill_image.seek(0)  # Rewind the image stream to the start
                    st.download_button(
                        label="Download Bill",
                        data=bill_image,
                        file_name=f"bill_expense_{expense[0]}.jpg",  # You can choose a more meaningful filename
                        mime="image/jpeg"  # Set mime type for image
                    )
        else:
            st.warning("No expenses found for the given criteria.")

# Modify Expense Page
elif page == "Modify Expense":
    st.header("Modify Expense")
    
    # Select the expense ID to modify
    expense_id = st.number_input("Enter Expense ID to Modify", min_value=1)
    
    if expense_id:
        expenses = get_expenses()
        expense_to_modify = next((exp for exp in expenses if exp[0] == expense_id), None)
        
        if expense_to_modify:
            st.subheader(f"Modify Expense ID: {expense_to_modify[0]}")
            amount = st.number_input("Amount (in INR)", value=expense_to_modify[2], min_value=0.0, format="%.2f")
            purpose = st.text_input("Purpose of Expense", value=expense_to_modify[3])
            
            if expense_to_modify[5] is None:
                purchase_date = st.date_input("Date of Purchase", value=datetime.today())
            else:
                purchase_date_str = expense_to_modify[5].decode('utf-8') if isinstance(expense_to_modify[5], bytes) else expense_to_modify[5]
                purchase_date = st.date_input("Date of Purchase", value=datetime.strptime(purchase_date_str, '%Y-%m-%d'))
            
            bill_image = st.file_uploader("Upload Bill Image", type=["jpg", "png", "jpeg"])

            if st.button("Update Expense"):
                if amount > 0 and purpose and purchase_date:
                    bill_image_bytes = bill_image.read() if bill_image else expense_to_modify[4]
                    update_expense(expense_id, amount, purpose, purchase_date, bill_image_bytes)
                    st.success("Expense updated successfully!")
                else:
                    st.error("Please provide all details.")

# Download Reports Page
elif page == "Download Reports":
    st.header("Download Expense Reports")

    # Date range for report filtering
    start_date = st.date_input("Start Date", min_value=datetime(2020, 1, 1), value=datetime.today())
    end_date = st.date_input("End Date", min_value=datetime(2020, 1, 1), value=datetime.today())

    # Fetch expenses within the selected date range
    expenses = get_expenses_by_date_range(start_date, end_date)

    if st.button("Download Report"):
        # Ensure there are expenses for the given date range
        if expenses:
            # Generate and download Excel file
            excel_file = download_expense_report_as_excel(expenses)
            st.download_button(
                label="Download as Excel",
                data=excel_file,
                file_name="expense_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No expenses found for the selected date range.")