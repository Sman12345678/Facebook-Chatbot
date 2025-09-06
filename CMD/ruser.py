import os
from config import ADMINS
import sqlite3

def execute(query=None, sender_id=None):
    # ADMIN_ID = os.getenv("ADMIN_ID")
    if str(sender_id) not in [str(a) for a in ADMINS]:
        return "⛔ Unauthorized: This command is for admin only."
    try:
        conn = sqlite3.connect('bot_memory.db')
        c = conn.cursor()
        c.execute("SELECT user_id, last_interaction FROM user_context ORDER BY last_interaction DESC LIMIT 20")
        users = c.fetchall()
        conn.close()
        if not users:
            return "🤔 No recent users found."
        user_list = "\n".join([f"• 🧑 `{uid}`   🕒 {ts}" for uid, ts in users])
        header = "👥 **Recent Users**\n\n"
        return f"{header}{user_list}"
    except Exception as e:
        return f"⚠️ Error fetching users: {str(e)}"
