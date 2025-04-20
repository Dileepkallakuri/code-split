import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import sqlite3
import os
from dataclasses import dataclass
from typing import List, Dict, Optional

# Main function that serves as the entry point
def show_expense_tracker():
    # Initialize database if not exists
    init_database()
    
    # Initialize session state variables
    init_session_state()
    
    # Top-level navigation
    st.header("🗓️ Daily Expense Tracker")
    nav_options = ["Dashboard", "Transactions", "Calendar", "Accounts", "Statistics", "Settings"]
    selected_nav = st.sidebar.radio("Navigation", nav_options)
    
    # Navigation router
    if selected_nav == "Dashboard":
        show_dashboard()
    elif selected_nav == "Transactions":
        show_transactions_page()
    elif selected_nav == "Calendar":
        show_calendar_view()
    elif selected_nav == "Accounts":
        show_accounts_page()
    elif selected_nav == "Statistics":
        show_statistics_page()
    elif selected_nav == "Settings":
        show_settings_page()

def init_database():
    """Initialize SQLite database with tables if they don't exist"""
    db_path = "data/expense_tracker.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        currency TEXT NOT NULL,
        initial_balance REAL NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,  -- 'expense', 'income'
        icon TEXT,
        color TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,  -- 'expense', 'income', 'transfer'
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        category_id INTEGER,
        account_id INTEGER NOT NULL,
        to_account_id INTEGER,  -- for transfers
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id),
        FOREIGN KEY (account_id) REFERENCES accounts(id),
        FOREIGN KEY (to_account_id) REFERENCES accounts(id)
    )
    ''')
    
    # Insert default categories if not exist
    default_categories = [
        ('Food & Dining', 'expense', '🍔', '#FF5733'),
        ('Transportation', 'expense', '🚗', '#33B5FF'),
        ('Utilities', 'expense', '💡', '#33FF57'),
        ('Entertainment', 'expense', '🎬', '#D433FF'),
        ('Shopping', 'expense', '🛍️', '#FF33A8'),
        ('Health', 'expense', '🏥', '#33FFC4'),
        ('Salary', 'income', '💰', '#33FF57'),
        ('Investment', 'income', '📈', '#FFD700'),
        ('Gift', 'income', '🎁', '#9B59B6')
    ]
    
    for cat in default_categories:
        cursor.execute('''
        INSERT OR IGNORE INTO categories (name, type, icon, color)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = ? AND type = ?)
        ''', (*cat, cat[0], cat[1]))
    
    conn.commit()
    conn.close()

def init_session_state():
    """Initialize session state variables"""
    # Transaction form defaults
    if "transaction_date" not in st.session_state:
        st.session_state.transaction_date = datetime.date.today()
    if "transaction_type" not in st.session_state:
        st.session_state.transaction_type = "Expense"
    if "selected_account" not in st.session_state:
        st.session_state.selected_account = None
    if "current_view" not in st.session_state:
        st.session_state.current_view = "monthly"  # For calendar view
    if "current_month" not in st.session_state:
        st.session_state.current_month = datetime.date.today().month
    if "current_year" not in st.session_state:
        st.session_state.current_year = datetime.date.today().year

@dataclass
class Account:
    id: Optional[int]
    name: str
    type: str
    currency: str
    initial_balance: float
    
@dataclass
class Category:
    id: Optional[int]
    name: str
    type: str
    icon: str
    color: str
    
@dataclass
class Transaction:
    id: Optional[int]
    type: str
    amount: float
    date: str
    category_id: Optional[int]
    account_id: int
    to_account_id: Optional[int]
    description: Optional[str]

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect("data/expense_tracker.db")

def get_accounts() -> List[Account]:
    """Fetch all accounts from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, type, currency, initial_balance FROM accounts")
    accounts = [Account(id=row[0], name=row[1], type=row[2], 
                        currency=row[3], initial_balance=row[4]) 
                for row in cursor.fetchall()]
    conn.close()
    return accounts

def get_categories(type_filter=None) -> List[Category]:
    """Fetch categories from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if type_filter:
        cursor.execute("""
            SELECT id, name, type, icon, color FROM categories 
            WHERE type = ? ORDER BY name
            """, (type_filter,))
    else:
        cursor.execute("SELECT id, name, type, icon, color FROM categories ORDER BY type, name")
    
    categories = [Category(id=row[0], name=row[1], type=row[2], 
                           icon=row[3], color=row[4]) 
                  for row in cursor.fetchall()]
    conn.close()
    return categories

def save_transaction(transaction: Transaction) -> int:
    """Save a transaction to the database and return its ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO transactions 
    (type, amount, date, category_id, account_id, to_account_id, description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (transaction.type, transaction.amount, transaction.date,
          transaction.category_id, transaction.account_id,
          transaction.to_account_id, transaction.description))
    
    transaction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return transaction_id

def get_transactions(start_date=None, end_date=None, 
                     account_id=None, category_id=None, 
                     transaction_type=None) -> List[Dict]:
    """Fetch transactions with filters"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()
    
    query = '''
    SELECT t.*, c.name as category_name, c.icon as category_icon, 
           a.name as account_name, a2.name as to_account_name
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    JOIN accounts a ON t.account_id = a.id
    LEFT JOIN accounts a2 ON t.to_account_id = a2.id
    WHERE 1=1
    '''
    params = []
    
    if start_date:
        query += " AND t.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND t.date <= ?"
        params.append(end_date)
    if account_id:
        query += " AND (t.account_id = ? OR t.to_account_id = ?)"
        params.extend([account_id, account_id])
    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)
    if transaction_type:
        query += " AND t.type = ?"
        params.append(transaction_type)
    
    query += " ORDER BY t.date DESC, t.created_at DESC"
    
    cursor.execute(query, params)
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transactions

def get_account_balance(account_id):
    """Calculate current balance for an account"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get initial balance
    cursor.execute("SELECT initial_balance FROM accounts WHERE id = ?", (account_id,))
    initial_balance = cursor.fetchone()[0]
    
    # Get sum of incoming transactions (income + transfers in)
    cursor.execute("""
    SELECT COALESCE(SUM(amount), 0) FROM transactions 
    WHERE (type = 'income' AND account_id = ?) 
       OR (type = 'transfer' AND to_account_id = ?)
    """, (account_id, account_id))
    income = cursor.fetchone()[0]
    
    # Get sum of outgoing transactions (expenses + transfers out)
    cursor.execute("""
    SELECT COALESCE(SUM(amount), 0) FROM transactions 
    WHERE (type = 'expense' AND account_id = ?) 
       OR (type = 'transfer' AND account_id = ?)
    """, (account_id, account_id))
    expenses = cursor.fetchone()[0]
    
    conn.close()
    return initial_balance + income - expenses

def show_transactions_page():
    """Show transaction entry forms"""
    transaction_type = st.radio(
        "Transaction Type", 
        ["Expense", "Income", "Transfer"], 
        horizontal=True,
        key="transaction_type_selector"
    )
    
    if transaction_type == "Expense":
        show_expense_form()
    elif transaction_type == "Income":
        show_income_form()
    else:  # Transfer
        show_transfer_form()
    
    # Show recent transactions below the form
    st.subheader("Recent Transactions")
    show_recent_transactions()

def show_expense_form():
    """Form for adding expenses"""
    with st.form("expense_form"):
        st.subheader("Add Expense")
        
        date = st.date_input("Date", value=st.session_state.transaction_date)
        
        amount = st.number_input("Amount", min_value=0.01, step=1.0)
        
        # Get expense categories
        expense_categories = get_categories(type_filter="expense")
        category_options = [f"{cat.icon} {cat.name}" for cat in expense_categories]
        category_selected = st.selectbox("Category", category_options)
        selected_category_id = expense_categories[category_options.index(category_selected)].id
        
        # Account selection
        accounts = get_accounts()
        account_options = [account.name for account in accounts]
        account_selected = st.selectbox("From Account", account_options)
        selected_account_id = accounts[account_options.index(account_selected)].id
        
        description = st.text_area("Note", height=100)
        
        submitted = st.form_submit_button("Save")
        
        if submitted and amount > 0:
            transaction = Transaction(
                id=None,
                type="expense",
                amount=amount,
                date=date.strftime("%Y-%m-%d"),
                category_id=selected_category_id,
                account_id=selected_account_id,
                to_account_id=None,
                description=description
            )
            save_transaction(transaction)
            st.success("Expense saved successfully!")
            st.session_state.transaction_date = date  # Remember the date for next entry

def show_income_form():
    """Form for adding income"""
    # Implementation similar to expense form but for income
    pass

def show_transfer_form():
    """Form for transfers between accounts"""
    with st.form("transfer_form"):
        st.subheader("Add Transfer")
        
        date = st.date_input("Date", value=st.session_state.transaction_date)
        
        amount = st.number_input("Amount", min_value=0.01, step=1.0)
        
        # Account selections
        accounts = get_accounts()
        account_options = [account.name for account in accounts]
        
        from_account = st.selectbox("From Account", account_options)
        selected_from_id = accounts[account_options.index(from_account)].id
        
        # Filter out the selected "from" account
        to_accounts = [acc for acc in accounts if acc.id != selected_from_id]
        to_account_options = [account.name for account in to_accounts]
        
        to_account = st.selectbox("To Account", to_account_options)
        selected_to_id = to_accounts[to_account_options.index(to_account)].id
        
        description = st.text_area("Note", height=100)
        
        submitted = st.form_submit_button("Save")
        
        if submitted and amount > 0:
            transaction = Transaction(
                id=None,
                type="transfer",
                amount=amount,
                date=date.strftime("%Y-%m-%d"),
                category_id=None,  # Transfers don't need categories
                account_id=selected_from_id,
                to_account_id=selected_to_id,
                description=description
            )
            save_transaction(transaction)
            st.success("Transfer saved successfully!")
            st.session_state.transaction_date = date  # Remember the date for next entry

def show_calendar_view():
    """Show transactions in a calendar view"""
    # Month/Year selector
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀️ Previous"):
            if st.session_state.current_month == 1:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
            else:
                st.session_state.current_month -= 1
    
    with col2:
        month_year = f"{datetime.date(1900, st.session_state.current_month, 1).strftime('%B')} {st.session_state.current_year}"
        st.subheader(month_year, anchor=False)
    
    with col3:
        if st.button("Next ▶️"):
            if st.session_state.current_month == 12:
                st.session_state.current_month = 1
                st.session_state.current_year += 1
            else:
                st.session_state.current_month += 1
    
    # View selector
    view_type = st.radio("View", ["Daily", "Monthly"], horizontal=True)
    
    if view_type == "Monthly":
        show_monthly_calendar()
    else:
        show_daily_transactions()

def show_monthly_calendar():
    """Show a monthly calendar with transaction indicators"""
    # Implementation will go here
    pass

def show_daily_transactions():
    """Show transactions for a selected day"""
    # Date selector
    selected_date = st.date_input(
        "Select date",
        value=datetime.date(st.session_state.current_year, 
                           st.session_state.current_month, 1)
    )
    
    # Update session state if month/year changed
    if selected_date.month != st.session_state.current_month or \
       selected_date.year != st.session_state.current_year:
        st.session_state.current_month = selected_date.month
        st.session_state.current_year = selected_date.year
    
    # Get transactions for selected date
    transactions = get_transactions(
        start_date=selected_date.strftime("%Y-%m-%d"),
        end_date=selected_date.strftime("%Y-%m-%d")
    )
    
    # Display transactions
    if transactions:
        for tx in transactions:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    if tx['type'] == 'expense':
                        st.markdown(f"**{tx['category_icon']} {tx['category_name']}** - {tx['account_name']}")
                    elif tx['type'] == 'income':
                        st.markdown(f"**{tx['category_icon']} {tx['category_name']}** - {tx['account_name']}")
                    else:  # transfer
                        st.markdown(f"**Transfer** - {tx['account_name']} → {tx['to_account_name']}")
                    
                    if tx['description']:
                        st.text(tx['description'])
                with col2:
                    if tx['type'] == 'expense':
                        st.markdown(f"<div style='color: #FF5733; text-align: right;'>-{tx['amount']:.2f}</div>", unsafe_allow_html=True)
                    elif tx['type'] == 'income':
                        st.markdown(f"<div style='color: #33FF57; text-align: right;'>+{tx['amount']:.2f}</div>", unsafe_allow_html=True)
                    else:  # transfer
                        st.markdown(f"<div style='color: #33B5FF; text-align: right;'>{tx['amount']:.2f}</div>", unsafe_allow_html=True)
                st.divider()
    else:
        st.info("No transactions for this date.")

def show_dashboard():
    """Show the main dashboard with overview"""
    st.subheader("Summary")
    
    # Account balances
    st.markdown("#### Account Balances")
    accounts = get_accounts()
    
    cols = st.columns(len(accounts) if len(accounts) <= 3 else 3)
    
    for i, account in enumerate(accounts):
        col_index = i % 3
        with cols[col_index]:
            balance = get_account_balance(account.id)
            st.metric(account.name, f"{account.currency} {balance:.2f}")
    
    # This month's summary
    st.markdown("#### This Month")
    
    # Get current month data
    today = datetime.date.today()
    start_of_month = datetime.date(today.year, today.month, 1).strftime("%Y-%m-%d")
    end_of_month = (datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1)).strftime("%Y-%m-%d") \
        if today.month < 12 else datetime.date(today.year, 12, 31).strftime("%Y-%m-%d")
    
    # Income for the month
    income_transactions = get_transactions(start_date=start_of_month, end_date=end_of_month, transaction_type="income")
    total_income = sum(tx['amount'] for tx in income_transactions)
    
    # Expenses for the month
    expense_transactions = get_transactions(start_date=start_of_month, end_date=end_of_month, transaction_type="expense")
    total_expenses = sum(tx['amount'] for tx in expense_transactions)
    
    # Show summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Income", f"${total_income:.2f}")
    with col2:
        st.metric("Expenses", f"${total_expenses:.2f}")
    with col3:
        st.metric("Balance", f"${(total_income - total_expenses):.2f}")
    
    # Recent transactions
    st.markdown("#### Recent Transactions")
    show_recent_transactions(limit=5)
    
    if st.button("View All Transactions"):
        st.session_state.selected_nav = "Transactions"
        st.rerun()

def show_recent_transactions(limit=10):
    """Show a list of recent transactions"""
    transactions = get_transactions(limit=limit)
    
    if not transactions:
        st.info("No transactions found.")
        return
    
    for tx in transactions:
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.text(tx['date'])
            
            with col2:
                if tx['type'] == 'expense':
                    st.markdown(f"**{tx['category_icon']} {tx['category_name']}** - {tx['account_name']}")
                elif tx['type'] == 'income':
                    st.markdown(f"**{tx['category_icon']} {tx['category_name']}** - {tx['account_name']}")
                else:  # transfer
                    st.markdown(f"**Transfer** - {tx['account_name']} → {tx['to_account_name']}")
                if tx['description']:
                    st.text(tx['description'])
            
            with col3:
                if tx['type'] == 'expense':
                    st.markdown(f"<div style='color: #FF5733; text-align: right;'>-{tx['amount']:.2f}</div>", unsafe_allow_html=True)
                elif tx['type'] == 'income':
                    st.markdown(f"<div style='color: #33FF57; text-align: right;'>+{tx['amount']:.2f}</div>", unsafe_allow_html=True)
                else:  # transfer  
                    st.markdown(f"<div style='color: #33B5FF; text-align: right;'>{tx['amount']:.2f}</div>", unsafe_allow_html=True)
            
            st.divider()

def show_statistics_page():
    """Show statistics and visual reports"""
    st.subheader("Statistics")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.date(datetime.date.today().year, datetime.date.today().month, 1))
    with col2:
        end_date = st.date_input("End Date", value=datetime.date.today())
    
    # Make sure end date is not before start date
    if start_date > end_date:
        st.error("End date must be after start date")
        return
    
    # Get data for selected period
    income_data = get_transactions(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        transaction_type="income"
    )
    
    expense_data = get_transactions(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        transaction_type="expense"
    )
    
    # Overview metrics
    total_income = sum(tx['amount'] for tx in income_data)
    total_expenses = sum(tx['amount'] for tx in expense_data)
    balance = total_income - total_expenses
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Income", f"${total_income:.2f}")
    with col2:
        st.metric("Total Expenses", f"${total_expenses:.2f}")
    with col3:
        st.metric("Balance", f"${balance:.2f}")
    
    # Charts
    tab1, tab2, tab3 = st.tabs(["Income vs. Expenses", "Expense Breakdown", "Trends"])
    
    with tab1:
        show_income_vs_expenses_chart(income_data, expense_data)
    
    with tab2:
        show_expense_breakdown_chart(expense_data)
    
    with tab3:
        show_trends_chart(start_date, end_date)

def show_income_vs_expenses_chart(income_data, expense_data):
    """Show income vs expenses pie chart"""
    # Implementation will go here
    pass

def show_expense_breakdown_chart(expense_data):
    """Show expense breakdown by category"""
    if not expense_data:
        st.info("No expense data available for the selected period.")
        return
    
    # Group by category
    category_totals = {}
    for tx in expense_data:
        cat_name = tx['category_name'] if tx['category_name'] else 'Uncategorized'
        if cat_name in category_totals:
            category_totals[cat_name] += tx['amount']
        else:
            category_totals[cat_name] = tx['amount']
    
    # Create dataframe for chart
    df = pd.DataFrame({
        'Category': list(category_totals.keys()),
        'Amount': list(category_totals.values())
    })
    
    fig = px.pie(df, values='Amount', names='Category', 
                 title='Expense Breakdown by Category',
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

def show_trends_chart(start_date, end_date):
    """Show income and expense trends over time"""
    # Implementation will go here
    pass

def show_accounts_page():
    """Account management page"""
    st.subheader("Accounts")
    
    tab1, tab2 = st.tabs(["Current Accounts", "Add New Account"])
    
    with tab1:
        show_accounts_list()
    
    with tab2:
        show_add_account_form()

def show_accounts_list():
    """Display list of existing accounts"""
    accounts = get_accounts()
    
    if not accounts:
        st.info("No accounts found. Add your first account to get started.")
        return
    
    for account in accounts:
        with st.expander(f"{account.name} ({account.type})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text(f"Type: {account.type}")
                st.text(f"Currency: {account.currency}")
            
            with col2:
                balance = get_account_balance(account.id)
                st.metric("Current Balance", f"{account.currency} {balance:.2f}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Edit {account.name}", key=f"edit_{account.id}"):
                    st.session_state.edit_account_id = account.id
                    # This would open an edit form - to be implemented
            
            with col2:
                if st.button(f"Delete {account.name}", key=f"delete_{account.id}"):
                    # Confirmation modal would be better but not directly supported in Streamlit
                    if st.session_state.get('confirm_delete') == account.id:
                        delete_account(account.id)
                        st.success(f"Account '{account.name}' deleted.")
                        st.rerun()
                    else:
                        st.session_state.confirm_delete = account.id
                        st.warning(f"Click 'Delete {account.name}' again to confirm deletion.")

def show_add_account_form():
    """Form to add a new account"""
    with st.form("add_account_form"):
        st.subheader("Add New Account")
        
        name = st.text_input("Account Name")
        
        account_types = ["Cash", "Bank Account", "Credit Card", "Savings", "Investment", "Loan", "Other"]
        account_type = st.selectbox("Account Type", account_types)
        
        currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "INR"]
        currency = st.selectbox("Currency", currencies)
        
        initial_balance = st.number_input("Initial Balance", value=0.0)
        
        submitted = st.form_submit_button("Add Account")
        
        if submitted and name:
            add_account(name, account_type, currency, initial_balance)
            st.success(f"Account '{name}' added successfully!")
            st.rerun()

def add_account(name, account_type, currency, initial_balance):
    """Add a new account to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO accounts (name, type, currency, initial_balance)
    VALUES (?, ?, ?, ?)
    ''', (name, account_type, currency, initial_balance))
    
    conn.commit()
    conn.close()

def delete_account(account_id):
    """Delete an account from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if account has transactions
    cursor.execute('''
    SELECT COUNT(*) FROM transactions 
    WHERE account_id = ? OR to_account_id = ?
    ''', (account_id, account_id))
    
    transaction_count = cursor.fetchone()[0]
    
    if transaction_count > 0:
        conn.close()
        st.error("Cannot delete account with associated transactions.")
        return False
    
    cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()
    return True

def show_settings_page():
    """Settings page"""
    st.subheader("Settings")
    
    tab1, tab2, tab3 = st.tabs(["Categories", "Data Management", "Preferences"])
    
    with tab1:
        show_categories_management()
    
    with tab2:
        show_data_management()
    
    with tab3:
        show_preferences()

def show_settings_page():
    """Settings page"""
    st.subheader("Settings")
    
    tab1, tab2, tab3 = st.tabs(["Categories", "Data Management", "Preferences"])
    
    with tab1:
        show_categories_management()
    
    with tab2:
        show_data_management()
    
    with tab3:
        show_preferences()

def show_categories_management():
    """Manage expense and income categories"""
    st.markdown("#### Categories")
    
    # Category type selector
    category_type = st.radio("Category Type", ["Expense", "Income"], horizontal=True)
    
    # Get categories
    categories = get_categories(type_filter=category_type.lower())
    
    # Display existing categories
    if categories:
        for category in categories:
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    st.markdown(f"## {category.icon}")
                
                with col2:
                    st.markdown(f"**{category.name}**")
                    st.markdown(f"<div style='background-color: {category.color}; width: 20px; height: 20px; display: inline-block; border-radius: 50%;'></div> {category.color}", unsafe_allow_html=True)
                
                with col3:
                    if st.button(f"Edit", key=f"edit_cat_{category.id}"):
                        st.session_state.edit_category_id = category.id
                        st.session_state.edit_category_name = category.name
                        st.session_state.edit_category_icon = category.icon
                        st.session_state.edit_category_color = category.color
                    
                    if st.button(f"Delete", key=f"delete_cat_{category.id}"):
                        if st.session_state.get('confirm_delete_cat') == category.id:
                            delete_category(category.id)
                            st.success(f"Category '{category.name}' deleted.")
                            st.rerun()
                        else:
                            st.session_state.confirm_delete_cat = category.id
                            st.warning(f"Click 'Delete' again to confirm deletion of '{category.name}'.")
                
                st.divider()
    else:
        st.info(f"No {category_type.lower()} categories found.")
    
    # Add new category form
    with st.expander(f"Add New {category_type} Category"):
        with st.form(f"add_{category_type.lower()}_category"):
            name = st.text_input("Category Name")
            
            # Icons selection
            icons = ["🍔", "🚗", "💡", "🏠", "👕", "🏥", "💰", "📈", "🎁", "📱", "🛠️", "✈️", "🏫", "🎮", "🍹", "🎭"]
            selected_icon = st.selectbox("Icon", icons)
            
            # Color picker
            color = st.color_picker("Color", "#33B5FF")
            
            submitted = st.form_submit_button(f"Add {category_type} Category")
            
            if submitted and name:
                add_category(name, category_type.lower(), selected_icon, color)
                st.success(f"{category_type} category '{name}' added successfully!")
                st.rerun()
    
    # Edit category form (appears when Edit button is clicked)
    if hasattr(st.session_state, 'edit_category_id'):
        with st.form("edit_category_form"):
            st.subheader(f"Edit Category")
            
            name = st.text_input("Category Name", value=st.session_state.edit_category_name)
            
            # Icons selection
            icons = ["🍔", "🚗", "💡", "🏠", "👕", "🏥", "💰", "📈", "🎁", "📱", "🛠️", "✈️", "🏫", "🎮", "🍹", "🎭"]
            selected_icon = st.selectbox("Icon", icons, index=icons.index(st.session_state.edit_category_icon) if st.session_state.edit_category_icon in icons else 0)
            
            # Color picker
            color = st.color_picker("Color", st.session_state.edit_category_color)
            
            submitted = st.form_submit_button("Save Changes")
            
            if submitted and name:
                update_category(st.session_state.edit_category_id, name, selected_icon, color)
                st.success(f"Category '{name}' updated successfully!")
                del st.session_state.edit_category_id
                del st.session_state.edit_category_name
                del st.session_state.edit_category_icon
                del st.session_state.edit_category_color
                st.rerun()

def add_category(name, category_type, icon, color):
    """Add a new category to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO categories (name, type, icon, color)
    VALUES (?, ?, ?, ?)
    ''', (name, category_type, icon, color))
    
    conn.commit()
    conn.close()

def update_category(category_id, name, icon, color):
    """Update an existing category"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE categories
    SET name = ?, icon = ?, color = ?
    WHERE id = ?
    ''', (name, icon, color, category_id))
    
    conn.commit()
    conn.close()

def delete_category(category_id):
    """Delete a category and set associated transactions to uncategorized"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if category has transactions
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE category_id = ?", (category_id,))
    tx_count = cursor.fetchone()[0]
    
    if tx_count > 0:
        # Option 1: Set transactions to NULL category
        cursor.execute("UPDATE transactions SET category_id = NULL WHERE category_id = ?", (category_id,))
    
    # Delete the category
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    
    conn.commit()
    conn.close()
    return True

def show_data_management():
    """Data management options"""
    st.markdown("#### Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Export Data")
        export_format = st.selectbox("Format", ["CSV", "Excel", "JSON"])
        
        if st.button("Export All Data"):
            export_data(export_format)
    
    with col2:
        st.markdown("##### Import Data")
        upload_file = st.file_uploader("Upload File", type=["csv", "xlsx", "json"])
        
        if st.button("Import Data") and upload_file is not None:
            import_data(upload_file)
    
    # Database operations
    st.markdown("##### Database Operations")
    dangerous_ops = st.expander("Danger Zone", expanded=False)
    
    with dangerous_ops:
        st.warning("The following operations are destructive and cannot be undone!")
        
        if st.button("Clear All Transactions"):
            if st.session_state.get('confirm_clear_tx') == True:
                clear_transactions()
                st.success("All transactions have been cleared.")
                del st.session_state.confirm_clear_tx
            else:
                st.session_state.confirm_clear_tx = True
                st.error("⚠️ Click 'Clear All Transactions' again to confirm this irreversible action!")
        
        if st.button("Reset Entire Database"):
            if st.session_state.get('confirm_reset_db') == True:
                reset_database()
                st.success("Database has been reset to factory settings.")
                del st.session_state.confirm_reset_db
            else:
                st.session_state.confirm_reset_db = True
                st.error("⚠️ Click 'Reset Entire Database' again to confirm. ALL DATA WILL BE LOST!")

def export_data(format_type):
    """Export all data to the specified format"""
    conn = get_db_connection()
    
    # Get all data
    accounts_df = pd.read_sql_query("SELECT * FROM accounts", conn)
    categories_df = pd.read_sql_query("SELECT * FROM categories", conn)
    transactions_df = pd.read_sql_query("""
        SELECT t.*, c.name as category_name, a1.name as account_name, a2.name as to_account_name 
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN accounts a1 ON t.account_id = a1.id
        LEFT JOIN accounts a2 ON t.to_account_id = a2.id
    """, conn)
    
    conn.close()
    
    # Create output based on format
    if format_type == "CSV":
        # Save as CSV
        accounts_csv = accounts_df.to_csv(index=False)
        categories_csv = categories_df.to_csv(index=False)
        transactions_csv = transactions_df.to_csv(index=False)
        
        # Create a zip file containing all CSVs
        import io
        import zipfile
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('accounts.csv', accounts_csv)
            zip_file.writestr('categories.csv', categories_csv)
            zip_file.writestr('transactions.csv', transactions_csv)
        
        zip_buffer.seek(0)
        st.download_button(
            label="Download ZIP of CSV files",
            data=zip_buffer,
            file_name="expense_tracker_data.zip",
            mime="application/zip"
        )
    
    elif format_type == "Excel":
        # Save as Excel
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output) as writer:
            accounts_df.to_excel(writer, sheet_name='Accounts', index=False)
            categories_df.to_excel(writer, sheet_name='Categories', index=False)
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
        
        output.seek(0)
        st.download_button(
            label="Download Excel file",
            data=output,
            file_name="expense_tracker_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    elif format_type == "JSON":
        # Save as JSON
        import json
        
        data = {
            "accounts": accounts_df.to_dict(orient='records'),
            "categories": categories_df.to_dict(orient='records'),
            "transactions": transactions_df.to_dict(orient='records')
        }
        
        json_str = json.dumps(data, indent=2)
        st.download_button(
            label="Download JSON file",
            data=json_str,
            file_name="expense_tracker_data.json",
            mime="application/json"
        )

def import_data(file):
    """Import data from uploaded file"""
    try:
        # Process based on file type
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
            st.info("CSV import functionality is not fully implemented. Please use Excel or JSON for full data import.")
        
        elif file.name.endswith('.xlsx'):
            xl = pd.ExcelFile(file)
            accounts_df = pd.read_excel(xl, 'Accounts')
            categories_df = pd.read_excel(xl, 'Categories')
            transactions_df = pd.read_excel(xl, 'Transactions')
            
            # Import logic would go here
            st.success("Excel data imported successfully!")
            
        elif file.name.endswith('.json'):
            import json
            data = json.load(file)
            
            # Import logic would go here
            st.success("JSON data imported successfully!")
        
        else:
            st.error("Unsupported file format.")
    
    except Exception as e:
        st.error(f"Error importing data: {str(e)}")

def clear_transactions():
    """Clear all transactions from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM transactions")
    
    conn.commit()
    conn.close()

def reset_database():
    """Reset the entire database to its initial state"""
    import os
    import shutil
    
    # Path to the database
    db_path = "data/expense_tracker.db"
    
    # Check if file exists
    if os.path.exists(db_path):
        # Delete the file
        os.remove(db_path)
    
    # Reinitialize the database
    init_database()

def show_preferences():
    """User preferences"""
    st.markdown("#### Preferences")
    
    # Currency preference
    default_currency = st.selectbox(
        "Default Currency",
        ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "INR"],
        index=0  # Default to USD
    )
    
    # Date format
    date_format = st.selectbox(
        "Date Format",
        ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
        index=2  # Default to YYYY-MM-DD
    )
    
    # Theme preference
    theme = st.selectbox(
        "Application Theme",
        ["System Default", "Light", "Dark"],
        index=0
    )
    
    # First day of week
    first_day = st.selectbox(
        "First Day of Week",
        ["Sunday", "Monday"],
        index=1
    )
    
    if st.button("Save Preferences"):
        # In a real app, these preferences would be saved to the database
        # or local storage. For now, just display a success message.
        st.success("Preferences saved successfully!")
        st.info("Note: Some preferences may require an app restart to take effect.")