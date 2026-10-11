
import sqlite3

transaction_id = 1  # Replace with the incorrect transaction's ID

conn = sqlite3.connect("finance.db")
conn.execute(
    "DELETE FROM transactions WHERE id = ?",
    (transaction_id,)
)
conn.commit()
conn.close()

print("Incorrect transaction deleted.")
