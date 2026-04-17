import sqlite3

conn = sqlite3.connect('hireflow.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:", [t[0] for t in tables])

# Try to find candidate-related tables
for table in tables:
    table_name = table[0]
    if 'candidate' in table_name.lower() or 'user' in table_name.lower():
        print(f"\n--- Contents of {table_name} ---")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
        rows = cursor.fetchall()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columns: {columns}")
        for row in rows:
            print(row)

conn.close()
