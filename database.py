
import sqlite3
import pandas as pd

DB_NAME = "finance.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                description TEXT
            )
        """)


def add_transaction(date, category, transaction_type, amount, description):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO transactions
            (date, category, type, amount, description)
            VALUES (?, ?, ?, ?, ?)
        """, (date, category, transaction_type, amount, description))


def get_transactions():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM transactions ORDER BY date DESC, id DESC",
            conn
        )


def delete_transaction(transaction_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
        )


def update_transaction(
    transaction_id, date, category, transaction_type, amount, description
):
    with get_connection() as conn:
        conn.execute("""
            UPDATE transactions
            SET date = ?, category = ?, type = ?,
                amount = ?, description = ?
            WHERE id = ?
        """, (
            date, category, transaction_type,
            amount, description, transaction_id
        ))
