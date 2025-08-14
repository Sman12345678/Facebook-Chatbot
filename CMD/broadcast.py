
import os
import app
import sqlite3

Info = {
    "Description": "Admin-only: Broadcast message to all recent users"
}

def execute(message, sender_id):
    ADMIN_ID = os.getenv("ADMIN_ID")
    if str(sender_id) != str(ADMIN_ID):
        return "🚫 This command is restricted to admin only."
    
    if not message or not message.strip():
        return """📢 **Broadcast Command**

🔧 **Usage:** `/broadcast Your message here`

📝 **Example:** 
`/broadcast 🎉 New feature added! Check out the /imagine command for AI image generation!`

⚠️ **Warning:** This sends the message to all users who interacted in the last 7 days."""
    
    try:
        c = app.conn.cursor()
        # Get users who interacted in the last 7 days
        c.execute("SELECT DISTINCT user_id FROM conversations WHERE timestamp >= datetime('now', '-7 days') AND user_id != ?", (sender_id,))
        users = c.fetchall()
        
        if not users:
            return "📭 No active users found to broadcast to."
        
        broadcast_msg = f"📢 **Broadcast Message:**\n\n{message.strip()}\n\n---\n💡 This is a message from the bot admin."
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            user_id = user[0]
            try:
                success = app.send_message(user_id, broadcast_msg)
                if success:
                    app.store_message(user_id, f"📢 Broadcast: {message.strip()}", "bot", "broadcast")
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                app.logger.error(f"Failed to send broadcast to {user_id}: {str(e)}")
                failed_count += 1
        
        return f"📊 **Broadcast Results:**\n\n✅ Successfully sent: {sent_count}\n❌ Failed: {failed_count}\n📈 Total attempted: {len(users)}"
        
    except Exception as e:
        return f"❌ Error during broadcast: {str(e)}"
