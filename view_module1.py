import sqlite3
import pandas as pd

DB_FILE = "results.db"
TABLE = "module1_graph_results"

conn = sqlite3.connect(DB_FILE)

# Show latest 20 rows
df = pd.read_sql_query(
    f"SELECT * FROM {TABLE} ORDER BY id DESC LIMIT 20",
    conn
)

conn.close()

print("\n==============================")
print("📊 MODULE-1 GRAPH RESULTS (Latest 20)")
print("==============================\n")

if df.empty:
    print("❌ No Module-1 graph data found.")
    print("✅ Run: python -m qrng  -> choose option 5 (run multiple times)")
else:
    print(df.to_string(index=False))
