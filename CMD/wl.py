from config import OWNER_ID, ADMINS

def execute(message, sender_id):
    # Only the owner can manage admins
    if str(sender_id) != str(OWNER_ID):
        return "Only the owner can use this command."

    parts = message.strip().split()
    if len(parts) < 2 or parts[0].lower() != "/wl":
        return "Usage: /wl add <id>, /wl del <id>, or /wl list"

    action = parts[1].lower()

    if action == "add":
        if len(parts) < 3:
            return "Usage: /wl add <id>"
        admin_id = str(parts[2])
        if admin_id not in [str(a) for a in ADMINS]:
            ADMINS.append(admin_id)
            return f"Admin {admin_id} added."
        else:
            return f"Admin {admin_id} already exists."

    elif action == "del":
        if len(parts) < 3:
            return "Usage: /wl del <id>"
        admin_id = str(parts[2])
        if admin_id == str(OWNER_ID):
            return "Cannot remove owner."
        if admin_id in [str(a) for a in ADMINS]:
            ADMINS.remove(admin_id)
            return f"Admin {admin_id} removed."
        else:
            return f"Admin {admin_id} not found."

    elif action == "list":
        if ADMINS:
            return "Admins: " + ", ".join(str(a) for a in ADMINS)
        else:
            return "No admins yet."

    else:
        return "Unknown action. Use add, del, or list."
