import requests
import sqlite3

# Initialize or connect to SQLite database
conn = sqlite3.connect('messages.db')
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,
    message TEXT NOT NULL
)
''')
conn.commit()

def execute(message, sender_id):
    # Store message and sender_id in database
    cursor.execute('INSERT INTO messages (sender_id, message) VALUES (?, ?)', (sender_id, message))
    conn.commit()

    # Prepare URL
    url = f"https://text.pollinations.ai/{message}"

    # Send GET request
    response = requests.get(url)

    # Return response text or status code if error
    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code}"

