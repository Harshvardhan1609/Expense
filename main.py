import sqlite3
import streamlit as st
import io
from io import BytesIO
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Function to create the SQLite database and table
def create_table():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Create the expenses table if it doesn't exist
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    cursor.execute(''' 
        INSERT INTO expenses (amount, purpose, purchase_date, bill_image) 
        VALUES (?, ?, ?, ?)
    ''', (amount, purpose, purchase_date, bill_image))
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

                # Show 'Show Bill' button if a bill exists
                if expense[4]:  # Check if the bill is not None (there is a bill image)
                    if st.button(f"Show Bill for Expense ID {expense[0]}", key=expense[0]):
                        try:
                            # If bill exists, convert the binary data to an image
                            bill_image = BytesIO(expense[4])  # Convert BLOB data to image
                            st.image(bill_image, caption="Bill Image", use_column_width=True)
                        except Exception as e:
                            st.error(f"Error displaying bill: {e}")
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
    
    if st.button("Download Report"):
        expenses = get_expenses()
        df = pd.DataFrame(expenses, columns=["ID", "Date", "Amount", "Purpose", "Purchase Date", "Bill"])
        st.download_button("Download as CSV", df.to_csv(index=False), file_name="expense_report.csv")
