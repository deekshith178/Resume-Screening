import sqlite3

conn = sqlite3.connect('guidance_demo.db')
cursor = conn.cursor()

# Delete test jobs
cursor.execute("DELETE FROM jobs WHERE id LIKE 'test-%'")

# Show remaining jobs
cursor.execute("SELECT id, title FROM jobs")
rows = cursor.fetchall()

conn.commit()
conn.close()

print('Remaining jobs:', rows if rows else 'None')
