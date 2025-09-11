
import requests

memory_db = {}

def execute(message, sender_id):
    if not message:
        return "Please provide a message. /ai hello"
    if sender_id not in memory_db:
        memory_db[sender_id] = []
    memory_db[sender_id].append(message)

    # Keep only last 5 messages
    if len(memory_db[sender_id]) > 5:
        memory_db[sender_id] = memory_db[sender_id][-5:]

    url = f"https://text.pollinations.ai/{message}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code}"
