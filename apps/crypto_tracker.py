import streamlit as st
import pandas as pd
from datetime import datetime
from utils.db import init_crypto_db

def main():
    st.header("📈 Crypto Trade Tracker")
    conn, c = init_crypto_db()

    with st.expander("➕ Add New Trade"):
        col1, col2, col3 = st.columns(3)
        with col1:
            pair = st.selectbox("Pair", ["BTC/USDT", "ETH/USDT", "ADA/USDT", "XRP/USDT", "SOL/USDT"])
            position = st.selectbox("Position", ["LONG", "SHORT"])
            trade_type = st.selectbox("Action", ["BUY", "SELL"])
        with col2:
            entry_price = st.number_input("Entry Price", min_value=0.0, format="%.4f")
            exit_price = st.number_input("Exit Price (0 if open)", min_value=0.0, format="%.4f")
            qty = st.number_input("Quantity", min_value=0.0, format="%.4f")
        with col3:
            fee_pct = st.slider("Fee %", 0.0, 1.0, 0.1)
            # Updated: Trade automatically set to OPEN unless exit price is provided
            status = "OPEN" if exit_price == 0 else "CLOSED"
            st.info(f"Status: {status}")
            target_pct = st.slider("Target %", 0.0, 100.0, 5.0)
            
            # Add P/L option for manual entry
            manual_pnl = st.checkbox("Set P/L manually")
            if manual_pnl:
                pnl_value = st.number_input("P/L Value", format="%.2f")

        if st.button("💾 Save Trade"):
            total = entry_price * qty
            fee = total * (fee_pct / 100)
            cashflow = -total - fee if trade_type == "BUY" else total - fee
            breakeven = entry_price * (1 + fee_pct / 100) if position == "LONG" else entry_price * (1 - fee_pct / 100)
            target = entry_price * (1 + target_pct / 100) if position == "LONG" else entry_price * (1 - target_pct / 100)
            
            # Calculate P/L if the trade is closed and exit price is set
            pnl = 0.0
            if status == "CLOSED" and exit_price > 0:
                if position == "LONG":
                    # Long: Profit when exit price is higher than entry
                    pnl = ((exit_price - entry_price) * qty) - (2 * fee)  # account for fees on both entry and exit
                else:
                    # Short: Profit when exit price is lower than entry
                    pnl = ((entry_price - exit_price) * qty) - (2 * fee)
            
            # Use manual P/L if specified
            if manual_pnl:
                pnl = pnl_value

            # Fixed INSERT statement to match the table columns
            c.execute('''INSERT INTO trades (pair, trade_type, position, entry_price, exit_price, quantity, 
                       total, fee, net_cashflow, breakeven_price, target_price, status, profit_loss, timestamp) 
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                      (pair, trade_type, position, entry_price, exit_price, qty, total, fee, cashflow,
                       breakeven, target, status, pnl, datetime.now().isoformat()))
            conn.commit()
            st.success("✅ Trade saved.")
            st.rerun()

    # Load & show trades
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC", conn)
    if not df.empty:
        # Fix column names in case DB schema was updated
        if 'price' in df.columns and 'entry_price' not in df.columns:
            df = df.rename(columns={'price': 'entry_price'})
        if 'exit_price' not in df.columns:
            df['exit_price'] = 0.0
            
        st.subheader("📊 Trade History")
        
        # Calculate P/L for display and update status based on exit price
        for i, row in df.iterrows():
            # Update status based on exit price
            if row['exit_price'] <= 0:
                df.at[i, 'status'] = 'OPEN'
            else:
                df.at[i, 'status'] = 'CLOSED'
                
            # Calculate P/L for closed trades
            if df.at[i, 'status'] == 'CLOSED':
                if row['position'] == 'LONG':
                    df.at[i, 'calculated_pnl'] = ((row['exit_price'] - row['entry_price']) * row['quantity']) - (2 * row['fee'])
                else:
                    df.at[i, 'calculated_pnl'] = ((row['entry_price'] - row['exit_price']) * row['quantity']) - (2 * row['fee'])
            else:
                # For open trades, use the stored P/L value
                df.at[i, 'calculated_pnl'] = row['profit_loss']
                
        st.dataframe(df)

        selected_id = st.selectbox("Select Trade ID", df['id'], key="select_id")
        row = df[df['id'] == selected_id].iloc[0]

        with st.expander(f"✏️ Edit/Delete Trade ID {selected_id}"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_exit_price = st.number_input("Exit Price", 
                    value=float(row['exit_price']) if 'exit_price' in row else 0.0,
                    format="%.4f", key=f"exit_{selected_id}")
                    
                # Status automatically determined by exit price
                new_status = "CLOSED" if new_exit_price > 0 else "OPEN"
                st.info(f"Status: {new_status}")
                
            with col2:
                # Calculate P/L based on exit price
                if new_status == "CLOSED" and new_exit_price > 0:
                    if row['position'] == 'LONG':
                        calc_pnl = ((new_exit_price - row['entry_price']) * row['quantity']) - (2 * row['fee'])
                    else:
                        calc_pnl = ((row['entry_price'] - new_exit_price) * row['quantity']) - (2 * row['fee'])
                    st.metric("Calculated P/L", f"{calc_pnl:.2f}")
                    
                    # Option to override the calculated P/L
                    override_pnl = st.checkbox("Override P/L", key=f"override_{selected_id}")
                    if override_pnl:
                        new_pnl = st.number_input("P/L Value", value=calc_pnl, format="%.2f", key=f"pnl_{selected_id}")
                    else:
                        new_pnl = calc_pnl
                else:
                    new_pnl = st.number_input("P/L", value=float(row['profit_loss']), format="%.2f", key=f"pnl_{selected_id}")

            with col3:
                if st.button("✅ Update", key=f"update_{selected_id}"):
                    c.execute("UPDATE trades SET status=?, exit_price=?, profit_loss=? WHERE id=?",
                            (new_status, new_exit_price, new_pnl, selected_id))
                    conn.commit()
                    st.success("✅ Updated.")
                    st.rerun()

                if st.button("🗑️ Delete Trade", key=f"delete_{selected_id}"):
                    c.execute("DELETE FROM trades WHERE id=?", (selected_id,))
                    conn.commit()
                    st.success("🗑️ Deleted.")
                    st.rerun()

if __name__ == "__main__":
    main()