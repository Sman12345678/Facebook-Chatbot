import logging
from datetime import datetime
from config import ADMINS
# from app import send_message

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
        send_message(ADMIN_ID, formatted_message)
        logger.info("Error successfully sent to the bot admin.")
    except Exception as e:
        logger.error(f"Failed to notify admin about the error: {e}")
