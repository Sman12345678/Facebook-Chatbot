from config import OWNER_ID, ADMINS

def execute(message, sender_id):
    parts = message.strip().split()
    if sender_id != OWNER_ID:
        return "Only the owner can use this command."
    if len(parts) != 3 or parts[0] != "/wl":
        return "Invalid command format. Use /wl -a <id> or /wl -r <id>."
    action, admin_id = parts[1], parts[2]
    if action == "-a":
        if admin_id not in ADMINS:
            ADMINS.append(admin_id)
            return f"Admin {admin_id} added."
        else:
            return f"Admin {admin_id} is already an admin."
    elif action == "-r":
        if admin_id == OWNER_ID:
            return "Cannot remove owner."
        if admin_id in ADMINS:
            ADMINS.remove(admin_id)
            return f"Admin {admin_id} removed."
        else:
            return f"Admin {admin_id} is not an admin."
    else:
        return "Unknown action. Use -a to add or -r to remove."
