import app  

# Command Info
Info = {
    "Description": "KORA AI Bot Status",
    "bot_name": "KORA AI",
    "owner": "Kolawole Suleiman",
    "version": "v2.0",
    "purpose": "Provides intelligent assistance, information, and dynamic interaction.",
    "last_update": "October 16, 2025"
}

def format_duration(seconds):
    """
    Convert seconds into days, hours, minutes, seconds.
    """
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

def execute(message=None, sender_id=None):
    """
    Generate and return the bot's formatted status display.
    """
    uptime_seconds = app.get_bot_uptime()
    uptime_str = format_duration(uptime_seconds)

    response = (
        "╭──⦿【 🤖 KORA AI STATUS 】\n"
        f"│ 🧠 Bot Name: {Info['bot_name']}\n"
        f"│ 👤 Owner: {Info['owner']}\n"
        f"│ 🧩 Version: {Info['version']}\n"
        f"│ 🎯 Purpose: {Info['purpose']}\n"
        f"│ 📅 Last Update: {Info['last_update']}\n"
        "╰──────────⦿\n\n"
        "╭──⦿【 ⏳ UPTIME 】\n"
        f"│ 🕒 {uptime_str}\n"
        "╰──────────⦿\n\n"
        "╭──────────⦿\n"
        "│ 🙏 Thank you for using KORA AI\n"
        "│ 🛡️ Developed by Kolawole Suleiman\n"
        "╰──────────⦿"
    )

    return response
