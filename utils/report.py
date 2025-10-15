import logging
from datetime import datetime
from config import ADMINS

logger = logging.getLogger(__name__)

def get_current_time():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def report(error_message):
    from app import send_message
    try:
        formatted_message = f"""🚨Error Alert🚨

🔴 Timestamp (UTC): {get_current_time()}

🛠️ Error Message:
{error_message}

📂 |= End of Report =|"""
        for admin_id in ADMINS:
            send_message(str(admin_id), formatted_message)
        logger.info("Error successfully sent to the bot admin(s).")
    except (ImportError, TypeError, ValueError) as e:
        logger.error(f"Failed to notify admin about the error: {e}")
