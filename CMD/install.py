import os
import logging
import re

Info = {
    "Description": "Admin-only: Install (create/update) a CMD file. Usage: /install filename.py <code>"
}

def execute(message, sender_id):
    ADMIN_ID = os.getenv("ADMIN_ID")

    # ✅ Admin check
    if str(sender_id) != str(ADMIN_ID):
        return {"success": False, "type": "text", "data": "🚫 Only the admin can use this command."}
    
    try:
        if not message or ".py" not in message:
            return {"success": False, "type": "text", "data": "❌ Invalid format. Usage: /install filename.py <code>"}
        
        # ✅ Extract filename (first word ending with .py)
        match = re.search(r"([^\s]+\.py)", message)
        if not match:
            return {"success": False, "type": "text", "data": "❌ Could not find a valid .py filename."}
        
        filename = match.group(1).strip()

        # ✅ Everything after filename = code
        start_index = message.find(filename) + len(filename)
        code = message[start_index:].lstrip()

        # ✅ Secure filename (block traversal tricks)
        if any(x in filename for x in ["/", "\\", ".."]) or not filename.endswith(".py"):
            return {"success": False, "type": "text", "data": "❌ Invalid filename."}

        os.makedirs("CMD", exist_ok=True)
        file_path = os.path.join("CMD", filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        return {"success": True, "type": "text", "data": f"✅ CMD/{filename} installed successfully."}

    except Exception as e:
        logging.error(f"Install error by sender {sender_id}, message={message}, error={e}")
        return {"success": False, "type": "text", "data": f"🚨 Error installing file: {e}"}
