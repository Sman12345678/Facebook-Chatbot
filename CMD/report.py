import app as Suleiman
from config import ADMINS
import time

def execute(message, sender_id):
    if not message:
        return "🧘 Please provide a message to be sent to Admin"

    admin_message = f"""📝 *New Feedback Report*

👤 **From User:** {sender_id}
📅 **Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}

💬 **Message:**
{message}\n
🤖 *Powered by Kora AI*"""

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

    # Only send to valid PSIDs (digits only)
    valid_admins = [str(a) for a in ADMINS if str(a).isdigit() and len(str(a)) > 4]
    print("Valid admins to send quick reply:", valid_admins)

    try:
        success = Suleiman.send_quick_reply(valid_admins, admin_message_data)
    except Exception as e:
        print("Error sending quick reply:", e)
        return f"⚠️ Failed to send your message to the admin. Error: {str(e)}"

    if success:
        return "✅ Your message has been sent to the admin successfully!"
    else:
        return "⚠️ Failed to send your message to the admin. Please try again later."
