import sqlite3
import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
import plotly.express as px
import pytz
import io
from io import BytesIO

# Function to create the SQLite database and tables for expenses and users
def create_tables():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Create the expenses table if it doesn't exist
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP,
            amount REAL NOT NULL,
            purpose TEXT NOT NULL,
            description TEXT,
            bill_image BLOB,
            purchase_date DATE,
            company_name TEXT,
            contact_details TEXT
        )
    ''')

    # Create the users table if it doesn't exist
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Add admin user if not exists (username: radha, password: kalki)
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'radha'")
    if cursor.fetchone()[0] == 0:
        hashed_password = hashlib.sha256("kalki".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("radha", hashed_password, "admin"))

    conn.commit()
    conn.close()

# Function to authenticate user
def authenticate_user(username, password):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]  # return role ('admin' or 'user')
    return None  # invalid username/password

def delete_expense(expense_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE ID = ?", (expense_id,))
    conn.commit()
    conn.close()

def get_expenses_by_purpose_and_date_range(purpose, start_date, end_date):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM expenses
        WHERE purchase_date BETWEEN ? AND ?
        AND purpose = ?
    ''', (start_date, end_date, purpose))
    records = cursor.fetchall()
    conn.close()
    return records

# Function to register a new user
def register_user(username, password, role):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
    conn.commit()
    conn.close()


# Function to insert a new expense record into the database
def insert_expense(amount, purpose, description, purchase_date, bill_image, company_name, contact_details):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    india_timezone = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(india_timezone).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(''' 
        INSERT INTO expenses (date, amount, purpose, description, purchase_date, bill_image, company_name, contact_details) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (current_time, amount, purpose, description, purchase_date, bill_image, company_name, contact_details))
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

def update_expense(expense_id, amount, purpose, description, purchase_date, bill_image, company_name, contact_details):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE expenses 
        SET amount = ?, purpose = ?, description = ?, purchase_date = ?, bill_image = ?, company_name = ?, contact_details = ? 
        WHERE id = ? 
    ''', (amount, purpose, description, purchase_date, bill_image, company_name, contact_details, expense_id))
    conn.commit()
    conn.close()

# Function to retrieve expenses within the given date range
def get_expenses_by_date_range(start_date, end_date):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE purchase_date BETWEEN ? AND ?", (start_date, end_date))
    records = cursor.fetchall()
    conn.close()
    return records

def delete_expense(expense_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def download_expense_report_as_excel(expenses):
    # Check if expenses are passed correctly
    # print(f"Expenses passed to the function: {expenses}")

    # Check if there are any records
    if not expenses:
        print("No expenses found.")
        return None  # Return None if no expenses are available

    # Convert the expenses data to a pandas DataFrame
    df = pd.DataFrame(data=expenses, columns=["ID", "Date", "Amount", "Purpose", "Description", "Bill Image", "Purchase Date", "Company Name", "Contact Details"])

    # Check if DataFrame is populated correctly
    # print(f"DataFrame before date conversion: {df.head()}")

    # Convert 'Purchase Date' to datetime (handling any invalid or missing dates)
    # df["Purchase Date"] = pd.to_datetime(df["Purchase Date"], errors='coerce', dayfirst=True)

    # # Check after conversion
    # print(f"DataFrame after date conversion: {df.head()}")

    # # Handle any NaT (Not a Time) values in 'Purchase Date'
    # df = df.dropna(subset=["Purchase Date"])

    # # Remove the "Bill" column if you don't want to include the binary data (images)
    df = df.drop(["Bill Image"], axis=1)

    # Save the DataFrame to an Excel file in-memory using openpyxl engine
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    # Rewind the buffer to the beginning before downloading
    excel_file.seek(0)

    return excel_file

# Streamlit UI Setup
st.set_page_config(page_title="SIN Technologies", layout="wide")
st.title("SIN Technologies")
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
    color: black;
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
    
    if not st.session_state.get("logged_in", False):
        # Show Login and Register options for non-logged-in users
        page = st.selectbox("Navigate to", ["Login", "Register"])
    else:
        # Display user role with color and styling
        user_role = st.session_state.role
        
        # Customize the theme based on the role
        if user_role == "admin":
            role_text = f'<span style="font-weight:bold; color:red;">{user_role}</span>'
            st.markdown(role_text, unsafe_allow_html=True)
            st.markdown('<style>body { background-color: #f8d7da; }</style>', unsafe_allow_html=True)  # Red theme
        elif user_role == "Developer":
            role_text = f'<span style="font-weight:bold; color:yellow;">{user_role}</span>'
            st.markdown(role_text, unsafe_allow_html=True)
            st.markdown('<style>body { background-color: #fff3cd; }</style>', unsafe_allow_html=True)  # Yellow theme
        elif user_role == "Employee":
            role_text = f'<span style="font-weight:bold; color:green;">{user_role}</span>'
            st.markdown(role_text, unsafe_allow_html=True)
            st.markdown('<style>body { background-color: #d4edda; }</style>', unsafe_allow_html=True)  # Green theme
        
        # Show different pages based on user role
        if user_role == "admin":
            page = st.selectbox("Navigate to", ["Home", "Add Expense", "Search Expenses", "Modify Expense", "Download Reports", "Delete Expense"])
        else:
            page = st.selectbox("Navigate to", ["Home", "Add Expense", "Search Expenses", "Modify Expense", "Download Reports"])
        
        st.markdown("---")
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None

# Handle login
if page == "Login":
    st.header("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

    if login_button:
        role = authenticate_user(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            st.success(f"Logged in as {username} with {role} role")
        else:
            st.error("Invalid username or password")

# Handle user registration
elif page == "Register":
    st.header("Register New User")

    with st.form("register_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Employee", "Developer"])  # 'admin' role should be limited to admins only
        register_button = st.form_submit_button("Register")

    if register_button:
        # Check if username already exists
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username,))
        if cursor.fetchone()[0] > 0:
            st.error("Username already exists. Please choose a different username.")
        else:
            register_user(new_username, new_password, role)
            st.success("User registered successfully!")
        conn.close()

# Handle Home Page (only accessible after login)
elif page == "Home" and st.session_state.get("logged_in", False):
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
    expense_df = pd.DataFrame(expenses, columns=["ID", "Date", "Amount", "Purpose", "Description", "Bill Image", "Purchase Date", "Company Name", "Contact Details"])
    
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
    
    # Convert the 'Date' column back to the timestamp for plotting
    monthly_expenses["Date"] = monthly_expenses["Date"].dt.to_timestamp()

    fig2 = px.line(monthly_expenses, x="Date", y="Amount", title="Monthly Expense Trend",
                   labels={"Date": "Month", "Amount": "Total Amount (INR)"}, markers=True)
    st.plotly_chart(fig2)

    # Display recent expenses
    st.subheader("Recent Expenses")
    recent_expenses = get_recent_expenses()
    for expense in recent_expenses:
        with st.expander(f"Expense ID: {expense[0]}, Amount: ₹{expense[2]:.2f}"):
            st.write("### Expense Details")
            st.write(f"**Date:** {expense[1]}")
            st.write(f"**Amount:** ₹{expense[2]:.2f}")
            st.write(f"**Purpose:** {expense[3]}")
            st.write(f"**Description:** {expense[4]}")
            st.write(f"**Purchase Date:** {expense[6]}")
            st.write(f"**Company Name:** {expense[7]}")
            st.write(f"**Contact Details:** {expense[8]}")
            if expense[5]:
                st.image(BytesIO(expense[5]), caption="Bill Image")

# Handle Add Expense Page (only accessible after login)
elif page == "Add Expense" and st.session_state.get("logged_in", False):
    st.header("Add New Expense")
    
    with st.form("expense_form", clear_on_submit=True):
        amount = st.number_input("Expense Amount (INR)", min_value=0.01, step=0.01, format="%.2f")
        purpose = st.selectbox("Purpose of Purchase", ["Books", "Electronics", "Event", "Marketing", "Operations", "Travel", "Miscellaneous"])
        description = st.text_area("Description", max_chars=500)
        purchase_date = st.date_input("Date of Purchase")
        company_name = st.text_input("Company Name")
        contact_details = st.text_input("Contact Details")
        bill_image = st.file_uploader("Upload Bill Image (optional)", type=["jpg", "jpeg", "png", "pdf"])

        submitted = st.form_submit_button("Add Expense")

    if submitted:
        # Check if all required fields are filled
        if not amount or not purpose or not description or not purchase_date or not company_name or not contact_details:
            st.error("All fields are required!")
        elif bill_image is None:
            st.warning("Bill image is optional, but make sure other fields are filled out.")
        else:
            # Read the image file if uploaded
            bill_image_bytes = bill_image.read() if bill_image else None

            # Insert the expense into the database
            insert_expense(amount, purpose, description, purchase_date, bill_image_bytes, company_name, contact_details)
            st.success("Expense added successfully!")
# Handle Search Expenses Page (only accessible after login)
elif page == "Search Expenses" and st.session_state.get("logged_in", False):
    st.header("Search Expenses")

    with st.form("search_form"):
        purpose = st.selectbox("Purpose", ["All", "Books", "Electronics", "Event", "Marketing", "Operations", "Travel", "Miscellaneous"])
        start_date = st.date_input("Start Date", value=datetime(2020, 1, 1))
        end_date = st.date_input("End Date", value=datetime.now().date())
        search_button = st.form_submit_button("Search")

    if search_button:
        # Modify the function to handle purpose filtering
        if purpose == "All":
            expenses = get_expenses_by_date_range(start_date, end_date)
        else:
            expenses = get_expenses_by_purpose_and_date_range(purpose, start_date, end_date)
        
        if not expenses:
            st.warning("No expenses found for the given criteria.")
        else:
            st.success(f"Found {len(expenses)} expense(s)")

        for expense in expenses:
            with st.expander(f"Expense ID: {expense[0]}, Amount: ₹{expense[2]:.2f}"):
                st.write("### Expense Details")
                st.write(f"**Date:** {expense[1]}")
                st.write(f"**Amount:** ₹{expense[2]:.2f}")
                st.write(f"**Purpose:** {expense[3]}")
                st.write(f"**Description:** {expense[4]}")
                st.write(f"**Purchase Date:** {expense[6]}")
                st.write(f"**Company Name:** {expense[7]}")
                st.write(f"**Contact Details:** {expense[8]}")
                if expense[5]:
                    st.image(BytesIO(expense[5]), caption="Bill Image")
                    

elif page == "Delete Expense" and st.session_state.get("logged_in", False) and st.session_state.get("role") == "admin":
    st.header("Delete Expense")
    
    # Provide a text input to allow the admin to input the ID of the expense they want to delete
    expense_id = st.number_input("Enter the Expense ID to Delete", min_value=1, step=1)

    if st.button("Delete Expense"):
        if expense_id:
            # Confirm with the admin before deletion
            confirm = st.dialog(
                "Are you sure you want to delete this expense?"
            )
            if confirm:
                # Call delete_expense function to delete the record
                delete_expense(expense_id)
                st.success(f"Expense with ID {expense_id} deleted successfully!")
        else:
            st.error("Please enter a valid expense ID.")
                

# Modify Expense Page
elif page == "Modify Expense" and st.session_state.get("logged_in", False):
    st.header("Modify Expense")

    # Select an expense to modify
    expenses = get_expenses()
    expense_dict = {f"{exp[3]} - ₹{exp[2]:.2f} on {exp[6]}": exp[0] for exp in expenses}
    selected_expense_key = st.selectbox("Select an Expense to Modify", list(expense_dict.keys()))

    if selected_expense_key:
        selected_expense_id = expense_dict[selected_expense_key]
        selected_expense = next(exp for exp in expenses if exp[0] == selected_expense_id)

        with st.form("modify_form"):
            amount = st.number_input("Expense Amount (INR)", value=selected_expense[2], min_value=0.01, step=0.01, format="%.2f")
            purpose = st.selectbox("Purpose of Purchase", ["Books", "Electronics", "Event", "Marketing", "Operations", "Travel", "Miscellaneous"], index=["Books", "Electronics", "Event", "Marketing", "Operations", "Travel", "Miscellaneous"].index(selected_expense[3]))
            description = st.text_area("Description", value=selected_expense[4], max_chars=500)
            purchase_date = st.date_input("Date of Purchase", value=pd.to_datetime(selected_expense[6]).date())
            company_name = st.text_input("Company Name", value=selected_expense[7])
            contact_details = st.text_input("Contact Details", value=selected_expense[8])
            bill_image = st.file_uploader("Upload New Bill Image (optional)", type=["jpg", "jpeg", "png", "pdf"])

            update_button = st.form_submit_button("Update Expense")

            if update_button:
                bill_image_bytes = bill_image.read() if bill_image else selected_expense[5]
                update_expense(selected_expense_id, amount, purpose, description, purchase_date, bill_image_bytes, company_name, contact_details)
                st.success("Expense updated successfully!")

# Download Reports Page
elif page == "Download Reports" and st.session_state.get("logged_in", False):
    st.header("Download Expense Reports")

    with st.form("report_form"):
        start_date = st.date_input("Start Date", value=datetime(2020, 1, 1))
        end_date = st.date_input("End Date", value=datetime.now().date())
        download_button = st.form_submit_button("Generate Report")

    # Place the download button outside the form
    if download_button:
        expenses = get_expenses_by_date_range(start_date, end_date)
        excel_file = download_expense_report_as_excel(expenses)
        if excel_file:
            st.download_button(
                label="Download Expense Report as Excel",
                data=excel_file,
                file_name="expense_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No expenses found for the selected date range.")
    # Report generation logic here...

# Initialize tables
create_tables()


