def report(error_message):
    """
    Send an error message to the bot admin.
    """
    try:
        formatted_message = f"""🚨Error Alert🚨

🔴 Timestamp (UTC): {get_current_time()}

🛠️ **Error Message:**
{error_message}

📂 |= End of Report =|"""
        send_message(ADMIN_ID, formatted_message)
        logger.info("Error successfully sent to the bot admin.")
    except Exception as e:
        logger.error(f"Failed to notify admin about the error: {e}")
