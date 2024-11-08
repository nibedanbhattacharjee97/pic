import streamlit as st
import pandas as pd
import sqlite3

# Initialize the SQLite database
conn = sqlite3.connect("pc.db")
c = conn.cursor()

# Create person and transactions tables if they don't already exist
c.execute('''CREATE TABLE IF NOT EXISTS person (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                phone TEXT UNIQUE
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_id INTEGER,
                amount_paid INTEGER DEFAULT 0,
                amount_due INTEGER DEFAULT 700,
                FOREIGN KEY (guest_id) REFERENCES person(id)
            )''')
conn.commit()

# Function to add a new person
def add_person(name, phone):
    try:
        c.execute("INSERT INTO person (name, phone) VALUES (?, ?)", (name, phone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Function to record a payment
def update_payment_status(name, amount):
    c.execute("SELECT id FROM person WHERE name = ?", (name,))
    guest = c.fetchone()
    
    if guest:
        guest_id = guest[0]
        c.execute("SELECT * FROM transactions WHERE guest_id = ?", (guest_id,))
        record = c.fetchone()
        
        if record:
            # Update existing transaction
            new_amount_paid = record[2] + amount
            new_amount_due = max(700 - new_amount_paid, 0)
            c.execute("UPDATE transactions SET amount_paid = ?, amount_due = ? WHERE guest_id = ?",
                      (new_amount_paid, new_amount_due, guest_id))
        else:
            # New transaction
            amount_due = 700 - amount
            c.execute("INSERT INTO transactions (guest_id, amount_paid, amount_due) VALUES (?, ?, ?)",
                      (guest_id, amount, amount_due))
        conn.commit()
        return True
    else:
        return False

# Main app
st.title("Picnic Guest Payment Tracker")

# Add a new person
st.header("Add a New Person")
new_name = st.text_input("Person's Name")
new_phone = st.text_input("Phone Number")
if st.button("Add Person"):
    if add_person(new_name, new_phone):
        st.success(f"Person '{new_name}' added successfully.")
    else:
        st.error("This person already exists or phone number is in use.")

# Record a payment
st.header("Record a Payment")
guest_names = [row[0] for row in c.execute("SELECT name FROM person").fetchall()]
selected_name = st.selectbox("Select Person", guest_names)
payment_amount = st.number_input("Enter amount paid", min_value=0, max_value=700, step=100)

if st.button("Submit Payment"):
    if update_payment_status(selected_name, payment_amount):
        st.success("Payment recorded successfully.")
    else:
        st.error("Error recording payment.")

# Transaction Summary
st.header("Transaction Summary")
query = '''
    SELECT p.name, p.phone, COALESCE(t.amount_paid, 0) as amount_paid, COALESCE(t.amount_due, 700) as amount_due
    FROM person p
    LEFT JOIN transactions t ON p.id = t.guest_id
'''
transaction_data = pd.read_sql(query, conn)
st.write(transaction_data)

# Pending Payments
st.header("Pending Payments")
pending_data = transaction_data[transaction_data["amount_due"] > 0]
st.write(pending_data)
