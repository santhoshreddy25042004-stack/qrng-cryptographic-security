import sqlite3

def delete_crypto_results():
    conn = sqlite3.connect("results.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM crypto_results
    """)

    conn.commit()
    conn.close()

    print("✅ All crypto results (Module-3) deleted successfully")

if __name__ == "__main__":
    delete_crypto_results()
