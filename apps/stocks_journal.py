import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import io

def show_stocks_journal():
    st.header("📊 Stocks Journal")
    
    # Initialize DB connection
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
    
    # Create tabs for different sections
    tabs = st.tabs(["Add Transaction", "Stock Average Calculator", "Transaction History", "Portfolio Analysis"])
    
    # Add Transaction Tab
    with tabs[0]:
        st.subheader("Add Transaction")
        
        with st.form(key="add_transaction_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                ticker = st.text_input("Ticker Symbol", placeholder="e.g., AAPL")
                transaction_type = st.selectbox("Transaction Type", ["BUY", "SELL"])
                price = st.number_input("Price per Share", min_value=0.0, format="%.2f")
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, format="%.2f")
                fees = st.number_input("Fees", min_value=0.0, format="%.2f", value=0.0)
            with col3:
                transaction_date = st.date_input("Transaction Date", value=datetime.today())
                notes = st.text_input("Notes (Optional)", placeholder="e.g., Dividend stock")
            
            submit_button = st.form_submit_button(label="💾 Add Transaction")
            
            if submit_button:
                if not ticker:
                    st.error("❌ Ticker symbol is required.")
                else:
                    total_value = price * quantity
                    c.execute('''INSERT INTO stock_transactions (ticker, transaction_type, price, quantity, 
                            total_value, fees, transaction_date, notes) 
                            VALUES (?,?,?,?,?,?,?,?)''',
                            (ticker.upper(), transaction_type, price, quantity, total_value, fees, 
                            transaction_date.isoformat(), notes))
                    conn.commit()
                    st.success("✅ Transaction added successfully!")
                    st.rerun()
    
    # Stock Average Calculator Tab
    with tabs[1]:
        st.subheader("Stock Average Calculator")
        
        df = pd.read_sql_query("SELECT * FROM stock_transactions", conn)
        
        if df.empty:
            st.info("No stock transactions recorded yet. Add transactions in the 'Add Transaction' tab.")
        else:
            ticker_list = df['ticker'].unique().tolist()
            if ticker_list:
                selected_ticker = st.selectbox("Select Ticker", ticker_list, key="avg_ticker")
                
                # Calculate average price for selected ticker
                ticker_df = df[df['ticker'] == selected_ticker]
                
                # Buy transactions
                buy_df = ticker_df[ticker_df['transaction_type'] == 'BUY']
                total_buy_shares = buy_df['quantity'].sum()
                total_buy_value = (buy_df['price'] * buy_df['quantity']).sum()
                
                # Sell transactions
                sell_df = ticker_df[ticker_df['transaction_type'] == 'SELL']
                total_sell_shares = sell_df['quantity'].sum()
                
                # Current holdings
                current_shares = total_buy_shares - total_sell_shares
                
                # Stock summary
                st.markdown("##### Current Holdings")
                col1, col2, col3 = st.columns(3)
                
                if current_shares > 0:
                    avg_price = total_buy_value / total_buy_shares
                    col1.metric("Average Price", f"{avg_price:.2f}")
                    col2.metric("Shares Owned", f"{current_shares:.2f}")
                    col3.metric("Total Value", f"{current_shares * avg_price:.2f}")
                    
                    # What-If Calculator
                    st.markdown("#### What-If Calculator")
                    st.write("See how buying more shares would affect your average cost basis")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        new_shares = st.number_input("New Shares to Buy", min_value=0.0, step=1.0, value=0.0)
                    with col2:
                        new_price = st.number_input("Price per Share", min_value=0.0, step=0.1, value=0.0)
                        
                    if new_shares > 0 and new_price > 0:
                        new_total_value = total_buy_value + (new_shares * new_price)
                        new_total_shares = total_buy_shares + new_shares
                        new_avg = new_total_value / new_total_shares
                        
                        st.markdown("##### New Average After Purchase")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Current Avg", f"{avg_price:.2f}")
                        col2.metric("New Avg", f"{new_avg:.2f}", f"{(new_avg - avg_price):.2f}")
                        col3.metric("Total Shares", f"{new_total_shares:.2f}")
                        
                    # Visualize purchase history
                    st.markdown("#### Purchase History")
                    if not buy_df.empty:
                        # Convert transaction_date to datetime for sorting
                        buy_df['transaction_date'] = pd.to_datetime(buy_df['transaction_date'])
                        buy_df = buy_df.sort_values('transaction_date')
                        
                        # Create a simple matplotlib figure
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(buy_df['transaction_date'], buy_df['price'], marker='o', linestyle='-', label='Purchase Price')
                        ax.axhline(y=avg_price, color='green', linestyle='-', label='Average Price')
                        
                        for i, row in buy_df.iterrows():
                            ax.annotate(f"{row['quantity']:.0f} shares", 
                                    (row['transaction_date'], row['price']), 
                                    textcoords="offset points",
                                    xytext=(0,10), 
                                    ha='center')
                        
                        ax.set_title(f'{selected_ticker} Purchase History vs Average')
                        ax.set_xlabel('Date')
                        ax.set_ylabel('Price')
                        ax.legend()
                        ax.grid(True)
                        
                        # Convert plot to a PNG image
                        buf = io.BytesIO()
                        fig.savefig(buf, format='png')
                        buf.seek(0)
                        
                        # Display the image
                        st.image(buf, use_container_width=True)
                else:
                    st.info(f"You don't currently own any shares of {selected_ticker}.")
    
    # Transaction History Tab
    with tabs[2]:
        st.subheader("Transaction History")
        
        df = pd.read_sql_query("SELECT * FROM stock_transactions ORDER BY transaction_date DESC", conn)
        
        if df.empty:
            st.info("No transactions recorded yet. Add transactions in the 'Add Transaction' tab.")
        else:
            st.dataframe(df)
            
            # Edit/Delete functionality
            selected_id = st.selectbox("Select Transaction ID to Edit/Delete", df['id'], key="edit_transaction_id")
            row = df[df['id'] == selected_id].iloc[0]
            
            with st.expander(f"✏️ Edit/Delete Transaction ID {selected_id}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_ticker = st.text_input("Ticker Symbol", value=row['ticker'], key=f"ticker_{selected_id}")
                    new_transaction_type = st.selectbox("Transaction Type", ["BUY", "SELL"], 
                                                        index=["BUY", "SELL"].index(row['transaction_type']), 
                                                        key=f"type_{selected_id}")
                    new_price = st.number_input("Price per Share", min_value=0.0, value=float(row['price']), 
                                                format="%.2f", key=f"price_{selected_id}")
                with col2:
                    new_quantity = st.number_input("Quantity", min_value=0.0, value=float(row['quantity']), 
                                                format="%.2f", key=f"quantity_{selected_id}")
                    new_fees = st.number_input("Fees", min_value=0.0, value=float(row['fees']), 
                                            format="%.2f", key=f"fees_{selected_id}")
                with col3:
                    new_date = st.date_input("Transaction Date", value=pd.to_datetime(row['transaction_date']).date(), 
                                            key=f"date_{selected_id}")
                    new_notes = st.text_input("Notes", value=row['notes'], key=f"notes_{selected_id}")
                
                new_total_value = new_price * new_quantity
                
                col4, col5 = st.columns(2)
                with col4:
                    if st.button("✅ Update", key=f"update_transaction_{selected_id}"):
                        c.execute('''UPDATE stock_transactions SET ticker=?, transaction_type=?, price=?, quantity=?, 
                                total_value=?, fees=?, transaction_date=?, notes=? WHERE id=?''',
                                (new_ticker.upper(), new_transaction_type, new_price, new_quantity, 
                                new_total_value, new_fees, new_date.isoformat(), new_notes, selected_id))
                        conn.commit()
                        st.success("✅ Transaction updated!")
                        st.rerun()
                with col5:
                    if st.button("🗑️ Delete", key=f"delete_transaction_{selected_id}"):
                        c.execute("DELETE FROM stock_transactions WHERE id=?", (selected_id,))
                        conn.commit()
                        st.success("🗑️ Transaction deleted!")
                        st.rerun()
    
    # Portfolio Analysis Tab
    with tabs[3]:
        st.subheader("Portfolio Analysis")
        
        df = pd.read_sql_query("SELECT * FROM stock_transactions", conn)
        
        if df.empty:
            st.info("No stock transactions recorded yet. Add transactions in the 'Add Transaction' tab.")
        else:
            # Add transaction date as datetime
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            
            # Basic statistics
            total_invested = df[df['transaction_type'] == 'BUY']['total_value'].sum()
            total_sold = df[df['transaction_type'] == 'SELL']['total_value'].sum()
            total_fees = df['fees'].sum()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Invested", f"{total_invested:.2f}")
            col2.metric("Total Sold", f"{total_sold:.2f}")
            col3.metric("Total Fees", f"{total_fees:.2f}")
            
            # Transaction Count by Ticker
            st.markdown("### Transaction Count by Ticker")
            ticker_counts = df['ticker'].value_counts().reset_index()
            ticker_counts.columns = ['Ticker', 'Transaction Count']
            
            # Create simple bar chart with matplotlib instead of plotly
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(ticker_counts['Ticker'], ticker_counts['Transaction Count'])
            ax.set_ylabel('Transaction Count')
            ax.set_title('Transaction Count by Ticker')
            
            # Convert plot to a PNG image
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            
            # Display the image
            st.image(buf, use_container_width=True)
            
            # Monthly Investment
            st.markdown("### Monthly Investment")
            df['month'] = df['transaction_date'].dt.strftime('%Y-%m')
            monthly_investment = df[df['transaction_type'] == 'BUY'].groupby('month')['total_value'].sum().reset_index()
            
            # Create simple line chart with matplotlib instead of plotly
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(monthly_investment['month'], monthly_investment['total_value'], marker='o')
            ax.set_ylabel('Total Value')
            ax.set_title('Monthly Investment')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convert plot to a PNG image
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            
            # Display the image
            st.image(buf, use_container_width=True)