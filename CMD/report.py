import app as Suleiman
import os
import time
user_id = os.getenv("ADMIN_ID")

def execute(message,sender_id):
    if not message:
        return "🧘 Please provide a message to be sent to Admin"

    # Send to admin
    admin_message = f"""📝 **New Feedback Report**

👤 **From User:** {sender_id}
📅 **Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}

💬 **Message:**
{message}

---
# Placeholder for user stats, as they are not available in this context.
# If user_stats were available, they would be formatted here.
# Example:
# 📊 **User Stats:**
# • Total messages: {user_stats['total_messages']}
# • First interaction: {user_stats['first_interaction']}
# • Last seen: {user_stats['last_interaction']}

🤖 *Powered by Kora AI*"""

    # Prepare the message data with quick replies for the admin
    admin_message_data = {
        "text": admin_message,
        "quick_replies": [
            {
                "content_type": "text",
                "title": "✉️ Reply to User",
                "payload": f"REPLY_TO_{sender_id}"
            },
            {
                "content_type": "text",
                "title": "📊 User History",
                "payload": f"USER_HISTORY_{sender_id}"
            },
            {
                "content_type": "text",
                "title": "🚫 Block User",
                "payload": f"BLOCK_USER_{sender_id}"
            }
        ]
    }

    # Send the report to admin with quick reply buttons
    success = Suleiman.send_quick_reply(user_id, admin_message_data)

    if success:
        return "✅ Your message has been sent to the admin successfully!"
    else:
        return "⚠️ Failed to send your message to the admin. Please try again later."