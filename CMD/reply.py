from config import ADMINS
import os
import app

Info = {
    "Description": "Admin-only: Reply to user feedback messages"
}

def execute(message, sender_id):
    # ADMIN_ID = os.getenv("ADMIN_ID")
    if str(sender_id) not in [str(a) for a in ADMINS]:
        return "🚫 This command is restricted to admin only."
    
    if not message or not message.strip():
        return """📬 **Reply to User Feedback**

🔧 **Usage:** `/reply USER_ID|Your message`

📝 **Example:** 
`/reply 1234567890|Thank you for your feedback! We've noted your suggestion.`

💡 **Tip:** You can get user IDs from feedback messages or recent messages view."""
    
    try:
        if "|" not in message:
            return "⚠️ Invalid format. Use: `/reply USER_ID|Your message`"
        
        user_id, reply_message = message.split("|", 1)
        user_id = user_id.strip()
        reply_message = reply_message.strip()
        
        if not user_id or not reply_message:
            return "⚠️ Both user ID and message are required."
        
        # Send reply to user
        success = app.send_message(user_id, f"📩 **Reply from Admin:**\n\n{reply_message}")
        
        if success:
            # Store the admin reply in conversation
            app.store_message(user_id, f"📩 Reply from Admin: {reply_message}", "bot", "admin_reply")
            return f"✅ Reply sent successfully to user {user_id}!"
        else:
            return f"❌ Failed to send reply to user {user_id}. Please check the user ID."
            
    except Exception as e:
        return f"❌ Error processing reply: {str(e)}"
