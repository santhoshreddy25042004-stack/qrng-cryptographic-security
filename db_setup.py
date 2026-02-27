import sqlite3

# Create database file
conn = sqlite3.connect("results.db")
cursor = conn.cursor()

# Table 1: Randomness Testing Results
cursor.execute("""
CREATE TABLE IF NOT EXISTS testing_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rng_type TEXT,
    entropy REAL,
    zeros INTEGER,
    ones INTEGER,
    frequency_p REAL,
    runs_p REAL
)
""")

# Table 2: Cryptography Results
cursor.execute("""
CREATE TABLE IF NOT EXISTS crypto_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rng_type TEXT,
    key_entropy REAL,
    ciphertext_hash TEXT
)
""")

conn.commit()
conn.close()

print("✅ Database created successfully: results.db")
print("✅ Tables created: testing_results, crypto_results")
