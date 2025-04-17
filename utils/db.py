import sqlite3
import pandas as pd

def init_crypto_db():
    """Initialize crypto database connection"""
    conn = sqlite3.connect('crypto_trades.db')
    c = conn.cursor()
    # Create table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS trades
    (id INTEGER PRIMARY KEY,
     pair TEXT,
     trade_type TEXT,
     position TEXT,
     entry_price REAL,
     exit_price REAL,
     quantity REAL,
     total REAL,
     fee REAL,
     net_cashflow REAL,
     breakeven_price REAL,
     target_price REAL,
     status TEXT,
     profit_loss REAL,
     timestamp TEXT)
    ''')
    conn.commit()
    return conn, c

def init_stocks_db():
    """Initialize stocks database connection"""
    conn = sqlite3.connect('stocks_journal.db')
    c = conn.cursor()
    # Create table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS stock_transactions
    (id INTEGER PRIMARY KEY,
     ticker TEXT,
     transaction_type TEXT,
     price REAL,
     quantity REAL,
     total_value REAL,
     fees REAL,
     transaction_date TEXT,
     notes TEXT)
    ''')
    conn.commit()
    return conn, c

def fetch_all_data(conn, table_name, order_by=None):
    """Fetch all data from a table"""
    query = f"SELECT * FROM {table_name}"
    if order_by:
        query += f" ORDER BY {order_by}"
    return pd.read_sql_query(query, conn)

def execute_query(conn, query, params=None):
    """Execute a SQL query"""
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    conn.commit()
    return cursor