
import sqlite3
import os

db_path = r"C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\agent\memory\autonomous_memory.sqlite3"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT kind, key, content FROM memory_records WHERE kind = 'conversation' ORDER BY created_at DESC LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    print(f"Kind: {r['kind']}, Key: {r['key']}")
    print(f"Content: {r['content']}")
    print("-" * 20)
conn.close()
