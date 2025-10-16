import os
import importlib
import logging

# Configure logging
logger = logging.getLogger()

def execute(message=None, sender_id=None):
    EXCLUDED_COMMANDS = {"__init__.py", "post.py", "pic.py", "help.py", "imagine.py", "file.py", "install.py"}

    response = (
        "╭──⦿【 ♕ KORA AI COMMANDS 】\n"
        "│ 🌈 Available Modules:\n"
        "╰────────────⦿\n\n"
    )

    for filename in os.listdir("CMD"):
        if filename.endswith(".py") and filename not in EXCLUDED_COMMANDS:
            command_name = filename[:-3]
            try:
                cmd_module = importlib.import_module(f"CMD.{command_name}")
                description = getattr(cmd_module, "Info", {}).get("Description", "No description available.")
                response += (
                    f"╭──⦿【 ⚙️ /{command_name} 】\n"
                    f"│ 📝 Description: {description}\n"
                    f"╰────────────⦿\n\n"
                )
            except Exception as e:
                logger.warning(f"Failed to load command {command_name}: {e}")
                response += (
                    f"╭──⦿【 ⚙️ /{command_name} 】\n"
                    f"│ ⚠️ Description: Unable to load description.\n"
                    f"╰────────────⦿\n\n"
                )

    response += (
        "╭──⦿【 💬 USAGE 】\n"
        "│ Type: /command_name\n"
        "│ Example: /up\n"
        "╰────────────⦿\n\n"
        "╭────────────⦿\n"
        "│ 🛡️ KORA AI by Kolawole Suleiman\n"
        "╰────────────⦿"
    )

    return response
