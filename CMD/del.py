from config import ADMINS
import os
import logging
import re

Info = {
    "Description": "Admin-only: Delete a CMD file. Usage: /del filename.py"
}

def execute(message, sender_id):
   # ADMIN_ID = os.getenv("ADMIN_ID")

    # ✅ Admin check
    if str(sender_id) not in [str(a) for a in ADMINS]:
        return {"success": False, "type": "text", "data": "🚫 Only the admin can use this command."}
    
    try:
        if not message or ".py" not in message:
            return {"success": False, "type": "text", "data": "❌ Invalid format. Usage: /del filename.py"}
        
        # ✅ Extract filename (first .py word)
        match = re.search(r"([^\s]+\.py)", message)
        if not match:
            return {"success": False, "type": "text", "data": "❌ Could not find a valid .py filename."}
        
        filename = match.group(1).strip()

        # ✅ Sanitize filename
        if any(x in filename for x in ["/", "\\", ".."]) or not filename.endswith(".py"):
            return {"success": False, "type": "text", "data": "❌ Invalid filename."}
        
        file_path = os.path.join("CMD", filename)

        # ✅ Delete if exists
        if not os.path.exists(file_path):
            return {"success": False, "type": "text", "data": f"⚠️ CMD/{filename} does not exist."}
        
        os.remove(file_path)
        return {"success": True, "type": "text", "data": f"🗑️ CMD/{filename} deleted successfully."}

    except Exception as e:
        logging.error(f"Delete error by sender {sender_id}, message={message}, error={e}")
        return {"success": False, "type": "text", "data": f"🚨 Error deleting file: {e}"}
