import os
import app

Info = {
    "Description": "Admin-only: The command is restricted to admin usage with comprehensive postback buttons"
}

def execute(message, sender_id):
    ADMIN_ID = os.getenv("ADMIN_ID")
    if str(sender_id) != str(ADMIN_ID):
        return {
            "success": False,
            "type": "text",
            "data": "🚫 This room is for the Bot owner only."
        }
    
    # Send admin panel with postback buttons
    admin_panel = {
        "text": "👑 Welcome to Admin Control Panel!\n\nChoose an action:",
        "quick_replies": [
            {
                "content_type": "text",
                "title": "📊 Bot Stats",
                "payload": "ADMIN_STATS"
            },
            {
                "content_type": "text", 
                "title": "📝 View Logs",
                "payload": "ADMIN_LOGS"
            },
            {
                "content_type": "text",
                "title": "💬 Recent Messages", 
                "payload": "ADMIN_MESSAGES"
            },
            {
                "content_type": "text",
                "title": "👥 Active Users",
                "payload": "ADMIN_USERS"
            },
            {
                "content_type": "text",
                "title": "🔧 System Info",
                "payload": "ADMIN_SYSTEM"
            },
            {
                "content_type": "text",
                "title": "📢 Broadcast",
                "payload": "ADMIN_BROADCAST"
            }
        ]
    }
    
    # Send the quick reply buttons
    app.send_quick_reply(sender_id, admin_panel)
    
    return {
        "success": True,
        "type": "text", 
        "data": "Admin panel loaded with action buttons above ⬆️"
    }
