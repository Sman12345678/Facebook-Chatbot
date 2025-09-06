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
{message}

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

    # Only send to valid PSIDs (digits only, min length 5)
    valid_admins = [str(a) for a in ADMINS if str(a).isdigit() and len(str(a)) > 4]
    print("Valid admins to send quick reply:", valid_admins)

    if not valid_admins:
        return "⚠️ No valid admin IDs found."

    results = []
    for admin_id in valid_admins:
        try:
            success = Suleiman.send_quick_reply(admin_id, admin_message_data)
            if success:
                results.append(f"✅ Sent to {admin_id}")
            else:
                results.append(f"⚠️ Failed for {admin_id}")
        except Exception as e:
            print(f"Error sending quick reply to {admin_id}: {e}")
            results.append(f"❌ Error for {admin_id}: {str(e)}")

    return "\n".join(results)
