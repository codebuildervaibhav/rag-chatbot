import sqlite3
import json

conn = sqlite3.connect('chat_history.db')
conn.row_factory = sqlite3.Row

print("--- conversations ---")
for r in conn.execute("SELECT * FROM conversations LIMIT 10"):
    print(dict(r))

print("--- messages ---")
for r in conn.execute("SELECT * FROM messages LIMIT 10"):
    print(dict(r))
