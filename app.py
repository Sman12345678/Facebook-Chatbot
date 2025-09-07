import os
import logging
import sqlite3
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from flask_cors import CORS
import requests
import messageHandler
import time
from io import BytesIO
import json
import traceback
from datetime import datetime, timezone
from autopost import post
import threading
import psutil
from report import report 
# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('app_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()
ADMIN_ID = os.getenv("ADMIN_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PREFIX = os.getenv("PREFIX", "/")
API_VERSION = "v22.0"
INITIALIZED = False
start_time = time.time()

class FacebookAPIError(Exception):
    pass

def get_current_time():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def split_long_message(message, max_length=2000):
    if len(message) <= max_length:
        return [message]
    chunks = []
    while message:
        if len(message) <= max_length:
            chunks.append(message)
            break
        split_point = message.rfind(' ', 0, max_length)
        if split_point == -1:
            split_point = max_length
        chunks.append(message[:split_point])
        message = message[split_point:].strip()
    return chunks
def validate_environment():
    global INITIALIZED
    if not PAGE_ACCESS_TOKEN or PAGE_ACCESS_TOKEN == "your_facebook_page_access_token":
        logger.warning("PAGE_ACCESS_TOKEN not configured - running in limited mode")
        INITIALIZED = False
        return False
    if not VERIFY_TOKEN or VERIFY_TOKEN == "your_verify_token":
        logger.warning("VERIFY_TOKEN not configured - webhook verification will fail")
        INITIALIZED = False
        return False
    try:
        verify_url = f"https://graph.facebook.com/{API_VERSION}/me"
        response = requests.get(verify_url, params={"access_token": PAGE_ACCESS_TOKEN})
        if response.status_code != 200:
            logger.error(f"Invalid PAGE_ACCESS_TOKEN: {response.text}")
            INITIALIZED = False
            return False
        logger.info("Facebook API token validated successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to validate Facebook API token: {str(e)}")
        INITIALIZED = False
        return False

def init_db():
    try:
        conn = sqlite3.connect('bot_memory.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            message TEXT NOT NULL,
            sender TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            metadata TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_context (
            user_id TEXT PRIMARY KEY,
            last_interaction DATETIME,
            conversation_state TEXT,
            user_preferences TEXT,
            conversation_history TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS message_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sender_id TEXT,
            message_type TEXT,
            status TEXT,
            error_message TEXT,
            metadata TEXT
        )''')
        conn.commit()
        logger.info("Database initialized successfully")
        return conn
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

def store_message(user_id, message, sender, message_type="text", metadata=None):
    """
    Store message in database and update conversation history, including all message types.
    Each history item includes 'role', 'content', and 'type'.
    """
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO conversations
                    (user_id, message, sender, message_type, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (user_id, message, sender, message_type,
                  json.dumps(metadata) if metadata else None, get_current_time()))
        # Update user context with conversation history
        c.execute('''SELECT conversation_history FROM user_context WHERE user_id = ?''', (user_id,))
        result = c.fetchone()
        if result:
            history = json.loads(result[0]) if result[0] else []
        else:
            history = []
        # Standardize role for chat models
        role = "user" if sender == "user" else "assistant"
        history.append({
            "role": role,
            "content": message,
            "type": message_type
        })
        # Limit history to last 50 messages
        if len(history) > 50:
            history = history[-50:]
        c.execute('''INSERT OR REPLACE INTO user_context
                    (user_id, last_interaction, conversation_history)
                    VALUES (?, ?, ?)''',
                 (user_id, get_current_time(), json.dumps(history)))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to store message: {str(e)}")

def get_conversation_history(user_id):
    """
    Get full conversation history for a user, including all message types.
    """
    try:
        c = conn.cursor()
        c.execute('''SELECT conversation_history FROM user_context WHERE user_id = ?''', (user_id,))
        result = c.fetchone()
        if result and result[0]:
            return json.loads(result[0])
        return []
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        return []

def log_message_status(sender_id, message_type, status, error_message=None, metadata=None):
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO message_logs
                    (sender_id, message_type, status, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?)''',
                 (sender_id, message_type, status, error_message,
                  json.dumps(metadata) if metadata else None))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to log message status: {str(e)}")

def send_quick_reply(recipient_id, quick_reply_data):
    """Send quick reply buttons to user"""
    api_url = f"https://graph.facebook.com/{API_VERSION}/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}

    data = {
        "recipient": {"id": recipient_id},
        "message": quick_reply_data
    }

    try:
        response = requests.post(api_url, params=params, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"Quick reply sent successfully to {recipient_id}")
            return True
        else:
            logger.error(f"Failed to send quick reply: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending quick reply: {str(e)}")
        return False

def send_message(recipient_id, message):
    """
    Send message to Facebook Messenger. Supports both text and image messages.
    """
    api_url = f"https://graph.facebook.com/{API_VERSION}/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    logger.debug(f"=== START SEND MESSAGE ===")
    logger.debug(f"Recipient ID: {recipient_id}")
    logger.debug(f"Message type: {type(message)}")
    logger.debug(f"Message content: {message}")
    try:
        if isinstance(message, dict):
            if message.get("type") == "image":
                data = {
                    "recipient": {"id": recipient_id},
                    "message": {
                        "attachment": {
                            "type": "image",
                            "payload": {
                                "attachment_id": message["content"]
                            }
                        }
                    }
                }
                message_type = "image"
                message_content = f"[IMAGE: {message['content']}]"
                logger.debug(f"Prepared image message with attachment_id: {message['content']}")
                response = requests.post(api_url, params=params, headers=headers, json=data)
                response_json = response.json() if response.text else {}
                if response.status_code == 200:
                    log_message_status(recipient_id, message_type, "success", metadata=response_json)
                    logger.info(f"Successfully sent {message_type} message to {recipient_id}")
                    return True
                else:
                    error_msg = response_json.get("error", {}).get("message", "Unknown error")
                    log_message_status(recipient_id, message_type, "failed", error_msg, response_json)
                    logger.error(f"Failed to send message: {error_msg}")
                    return False
            else:
                logger.error(f"Unsupported message type: {message.get('type')}")
                return False
        else:
            if not isinstance(message, str):
                message = str(message)
            messages = split_long_message(message)
            success = True
            for msg_part in messages:
                data = {
                    "recipient": {"id": recipient_id},
                    "message": {"text": msg_part}
                }
                message_type = "text"
                message_content = msg_part
                logger.debug("Prepared text message")
                logger.debug(f"Sending request to Facebook API: {json.dumps(data, indent=2)}")
                response = requests.post(api_url, params=params, headers=headers, json=data)
                response_json = response.json() if response.text else {}
                logger.debug(f"Facebook API Response Status: {response.status_code}")
                logger.debug(f"Facebook API Response: {json.dumps(response_json, indent=2)}")
                if response.status_code == 200:
                    log_message_status(recipient_id, message_type, "success", metadata=response_json)
                else:
                    error_msg = response_json.get("error", {}).get("message", "Unknown error")
                    log_message_status(recipient_id, message_type, "failed", error_msg, response_json)
                    logger.error(f"Failed to send message: {error_msg}")
                    success = False
                    break
            return success
    except Exception as e:
        error_msg = str(e)
        log_message_status(recipient_id, "error", error_msg)
        logger.error(f"Error in send_message: {error_msg}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    finally:
        logger.debug("=== END SEND MESSAGE ===")

def upload_image_to_graph(image_data):
    url = f"https://graph.facebook.com/{API_VERSION}/me/message_attachments"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    logger.debug("=== START IMAGE UPLOAD ===")
    try:
        if not isinstance(image_data, BytesIO):
            logger.error(f"Invalid image_data type: {type(image_data)}")
            return {"success": False, "error": "Invalid image data type"}
        image_data.seek(0)
        files = {"filedata": ("image.jpg", image_data, "image/jpeg")}
        data = {"message": '{"attachment":{"type":"image", "payload":{}}}'}
        logger.debug("Sending image upload request to Facebook")
        response = requests.post(url, params=params, files=files, data=data)
        response_json = response.json()
        logger.debug(f"Upload response status: {response.status_code}")
        logger.debug(f"Upload response content: {json.dumps(response_json, indent=2)}")
        if response.status_code == 200 and "attachment_id" in response_json:
            logger.info(f"Image upload successful. Attachment ID: {response_json['attachment_id']}")
            return {"success": True, "attachment_id": response_json["attachment_id"]}
        else:
            logger.error(f"Image upload failed. Response: {response.text}")
            return {"success": False, "error": response_json.get("error", {}).get("message", "Unknown error")}
    except Exception as e:
        logger.error(f"Error in upload_image_to_graph: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}
    finally:
        logger.debug("=== END IMAGE UPLOAD ===")

def process_command_response(sender_id, response):
    logger.debug(f"=== START PROCESS COMMAND RESPONSE ===")
    logger.debug(f"Sender ID: {sender_id}")
    logger.debug(f"Response type: {type(response)}")
    logger.debug(f"Response content: {response}")
    try:
        if isinstance(response, dict):
            if response.get("success"):
                if response.get("type") == "image" and isinstance(response.get("data"), BytesIO):
                    logger.debug("Processing image response")
                    upload_response = upload_image_to_graph(response["data"])
                    logger.debug(f"Upload response: {upload_response}")
                    if upload_response.get("success"):
                        message_data = {
                            "type": "image",
                            "content": upload_response["attachment_id"]
                        }
                        # Store generated image message
                        store_message(sender_id, f"[Generated image: {upload_response['attachment_id']}]", "bot", "image")
                        logger.debug(f"Sending image message with data: {message_data}")
                        if send_message(sender_id, message_data):
                            logger.info(f"Successfully sent image message to {sender_id}")
                        else:
                            logger.error(f"Failed to send image message to {sender_id}")
                            error_msg = "Failed to send image"
                            store_message(sender_id, error_msg, "bot", "error")
                            send_message(sender_id, error_msg)
                    else:
                        error_msg = f"Failed to upload image: {upload_response.get('error')}"
                        logger.error(error_msg)
                        store_message(sender_id, error_msg, "bot", "error")
                        send_message(sender_id, error_msg)
                else:
                    store_message(sender_id, response.get("data", "No data provided"), "bot", response.get("type", "text"))
                    send_message(sender_id, response.get("data", "No data provided"))
            else:
                error_msg = response.get("data", "Command failed")
                store_message(sender_id, error_msg, "bot", "error")
                send_message(sender_id, error_msg)
        else:
            store_message(sender_id, str(response), "bot", "text")
            send_message(sender_id, str(response))
    except Exception as e:
        logger.error(f"Error processing command response: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_msg = "Error processing command response"
        store_message(sender_id, error_msg, "bot", "error")
        send_message(sender_id, error_msg)
    finally:
        logger.debug("=== END PROCESS COMMAND RESPONSE ===")

def handle_command_message(sender_id, message_text):
    command_parts = message_text[len(PREFIX):].split(maxsplit=1)
    command_name = command_parts[0]
    command_args = command_parts[1] if len(command_parts) > 1 else ""
    logger.debug(f"Processing command: {command_name} with args: {command_args}")
    try:
        response = messageHandler.handle_text_command(command_name, command_args,sender_id)
        if isinstance(response, list):
            for item in response:
                process_command_response(sender_id, item)
        else:
            process_command_response(sender_id, response)
    except Exception as e:
        logger.error(f"Error handling command: {str(e)}")
        error_msg = f"Error processing command: {str(e)}"
        store_message(sender_id, error_msg, "bot", "error")
        send_message(sender_id, error_msg)

@app.route('/webhook', methods=['GET'])
def verify():
    token_sent = request.args.get("hub.verify_token")
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge", "")
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Check if bot is properly initialized
        if not INITIALIZED:
            logger.warning("Webhook received but bot not properly initialized - check Facebook tokens")
            return "Bot not initialized", 503

        data = request.get_json()
        logger.debug(f"Received webhook data: {json.dumps(data, indent=2)}")

        if data.get("object") != "page":
            logger.warning("Received non-page object in webhook")
            return "Not a page object", 404

        def handle_payload(sender_id, payload):
            # Only handle payload if it's get_started_button
            if payload == "get_started_button":
                greeting = """👋 Welcome! I'm Kora AI, your intelligent assistant!

🤖 **What I can do:**
• 📝 Answer questions and provide information
• 🖼️ Analyze images you send me
• 🎨 Generate images with /imagine command
• 📰 Get latest news with /bbc
• 🎵 Find lyrics with /lyrics
• ✉️ Send emails with /mail
• ⏰ Check time with /time

Type **/help** to see all available commands!

How can I assist you today? 😊"""
                store_message(sender_id, "[Get Started - New User]", "user", "postback")
                store_message(sender_id, greeting, "bot", "text")
                send_message(sender_id, greeting)
                # Send quick reply buttons for popular commands
                quick_replies = {
                    "text": "Choose a quick action:",
                    "quick_replies": [
                        {
                            "content_type": "text",
                            "title": "📰 Latest News",
                            "payload": "QUICK_NEWS"
                        },
                        {
                            "content_type": "text",
                            "title": "🎨 Generate Image",
                            "payload": "QUICK_IMAGE"
                        },
                        {
                            "content_type": "text",
                            "title": "📜 Help Menu",
                            "payload": "QUICK_HELP"
                        },
                        {
                            "content_type": "text",
                            "title": "📊 Bot Stats",
                            "payload": "QUICK_STATS"
                        }
                    ]
                }
                send_quick_reply(sender_id, quick_replies)
                return True
            return False

        for entry in data["entry"]:
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]

                # Handle postback payloads (button clicks)
                if "postback" in event:
                    payload = event["postback"].get("payload", "")
                    if handle_payload(sender_id, payload):
                        continue  # Only handle get_started_button as payload

                # Handle message events (normal text, quick reply payloads, attachments)
                if "message" in event:
                    message = event["message"]
                    # Handle quick reply payloads as normal message text
                    if "quick_reply" in message:
                        payload = message["quick_reply"].get("payload", "")
                        message_text = payload  # Treat quick reply payload as normal message text
                    else:
                        message_text = message.get("text", "")

                    attachments = message.get("attachments", [])
                    logger.debug(f"Processing message from {sender_id}: {message_text}")

                    try:
                        # Always store user messages
                        if message_text:
                            store_message(sender_id, message_text, "user", "text")
                        # Handle quick actions and bot commands
                        if message_text == "QUICK_NEWS":
                            handle_command_message(sender_id, "/bbc")
                            continue
                        elif message_text == "QUICK_IMAGE":
                            response = "🎨 To generate an image, just describe what you want to see! Example: 'Create a beautiful sunset over mountains'"
                            store_message(sender_id, response, "bot", "text")
                            send_message(sender_id, response)
                            continue
                        elif message_text == "QUICK_HELP":
                            handle_command_message(sender_id, "/help")
                            continue
                        elif message_text == "QUICK_STATS":
                            handle_command_message(sender_id, "/stats")
                            continue
                        elif message_text == "ADMIN_STATS":
                            handle_command_message(sender_id, "/stats")
                            continue
                        elif message_text == "ADMIN_LOGS":
                            if str(sender_id) == str(ADMIN_ID):
                                try:
                                    with open('app_debug.log', 'r') as f:
                                        logs = f.read()[-2000:]  # Last 2000 characters
                                    response = f"📋 **Recent Logs:**\n```\n{logs}\n```"
                                    store_message(sender_id, response, "bot", "text")
                                    send_message(sender_id, response)
                                except Exception as e:
                                    error_msg = f"❌ Error reading logs: {str(e)}"
                                    store_message(sender_id, error_msg, "bot", "error")
                                    send_message(sender_id, error_msg)
                            else:
                                response = "🚫 Admin access required"
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            continue
                        elif message_text == "ADMIN_MESSAGES":
                            if str(sender_id) == str(ADMIN_ID):
                                try:
                                    c = conn.cursor()
                                    c.execute("""
                                        SELECT user_id, message, sender, timestamp 
                                        FROM conversations 
                                        ORDER BY timestamp DESC 
                                        LIMIT 10
                                    """)
                                    recent = c.fetchall()
                                    response = "📬 **Recent Messages:**\n\n"
                                    for msg in recent:
                                        response += f"👤 User: {msg[0][:8]}...\n💬 {msg[1][:50]}...\n📅 {msg[3]}\n---\n"
                                    store_message(sender_id, response, "bot", "text")
                                    send_message(sender_id, response)
                                except Exception as e:
                                    error_msg = f"❌ Error fetching messages: {str(e)}"
                                    store_message(sender_id, error_msg, "bot", "error")
                                    send_message(sender_id, error_msg)
                            else:
                                response = "🚫 Admin access required"
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            continue
                        elif message_text == "ADMIN_USERS":
                            if str(sender_id) == str(ADMIN_ID):
                                try:
                                    c = conn.cursor()
                                    c.execute("""
                                        SELECT user_id, COUNT(*) as msg_count, MAX(timestamp) as last_seen
                                        FROM conversations 
                                        GROUP BY user_id 
                                        ORDER BY last_seen DESC 
                                        LIMIT 10
                                    """)
                                    users = c.fetchall()
                                    response = "👥 **Active Users:**\n\n"
                                    for user in users:
                                        response += f"👤 ID: {user[0][:8]}...\n💬 Messages: {user[1]}\n📅 Last seen: {user[2]}\n---\n"
                                    store_message(sender_id, response, "bot", "text")
                                    send_message(sender_id, response)
                                except Exception as e:
                                    error_msg = f"❌ Error fetching users: {str(e)}"
                                    store_message(sender_id, error_msg, "bot", "error")
                                    send_message(sender_id, error_msg)
                            else:
                                response = "🚫 Admin access required"
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            continue
                        elif message_text == "ADMIN_SYSTEM":
                            if str(sender_id) == str(ADMIN_ID):
                                import psutil
                                try:
                                    uptime = get_bot_uptime()
                                    hours, remainder = divmod(uptime, 3600)
                                    minutes, seconds = divmod(remainder, 60)
                                    
                                    cpu_percent = psutil.cpu_percent()
                                    memory = psutil.virtual_memory()
                                    
                                    response = f"""🔧 **System Information:**

⏱️ **Uptime:** {int(hours)}h {int(minutes)}m {int(seconds)}s
💾 **Memory:** {memory.percent}% used
🖥️ **CPU:** {cpu_percent}% used
📊 **Status:** {'✅ Initialized' if INITIALIZED else '❌ Limited Mode'}
🌐 **Facebook API:** {'✅ Connected' if INITIALIZED else '❌ Disconnected'}

💡 **Bot Version:** Kora AI v2.0"""
                                    store_message(sender_id, response, "bot", "text")
                                    send_message(sender_id, response)
                                except Exception as e:
                                    error_msg = f"❌ Error getting system info: {str(e)}"
                                    store_message(sender_id, error_msg, "bot", "error")
                                    send_message(sender_id, error_msg)
                            else:
                                response = "🚫 Admin access required"
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            continue
                        elif message_text == "ADMIN_BROADCAST":
                            if str(sender_id) == str(ADMIN_ID):
                                response = """📢 **Broadcast Mode**

To broadcast a message to all users, use:
`/broadcast [your message]`

Example:
`/broadcast 🎉 Bot updated with new features!`

This will send your message to all users who have interacted with the bot."""
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            else:
                                response = "🚫 Admin access required"
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            continue
                        elif message_text.startswith("REPLY_TO_"):
                            if str(sender_id) == str(ADMIN_ID):
                                target_user_id = message_text.replace("REPLY_TO_", "")
                                response = f"""✉️ **Reply Mode Activated**

You are now replying to user: {target_user_id[:8]}...

To send a reply, use:
`/reply {target_user_id} [your message]`

Example:
`/reply {target_user_id} Thank you for your feedback!`"""
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            else:
                                response = "🚫 Admin access required"
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            continue
                        elif message_text.startswith("USER_HISTORY_"):
                            if str(sender_id) == str(ADMIN_ID):
                                target_user_id = message_text.replace("USER_HISTORY_", "")
                                try:
                                    history = get_conversation_history(target_user_id)
                                    response = f"📜 **Conversation History for {target_user_id[:8]}...**\n\n"
                                    recent_messages = history[-10:] if len(history) > 10 else history
                                    for msg in recent_messages:
                                        role_emoji = "👤" if msg["role"] == "user" else "🤖"
                                        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                                        response += f"{role_emoji} {content}\n---\n"
                                    if len(history) > 10:
                                        response += f"\n📈 Showing last 10 of {len(history)} total messages"
                                    store_message(sender_id, response, "bot", "text")
                                    send_message(sender_id, response)
                                except Exception as e:
                                    error_msg = f"❌ Error fetching user history: {str(e)}"
                                    store_message(sender_id, error_msg, "bot", "error")
                                    send_message(sender_id, error_msg)
                            else:
                                response = "🚫 Admin access required"
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            continue
                        elif message_text.startswith("BLOCK_USER_"):
                            if str(sender_id) == str(ADMIN_ID):
                                target_user_id = message_text.replace("BLOCK_USER_", "")
                                # For now, just show a confirmation message
                                # You can implement actual blocking logic later
                                response = f"🚫 **Block User Confirmation**\n\nUser {target_user_id[:8]}... would be blocked.\n\n⚠️ This feature is not yet implemented in the current version."
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            else:
                                response = "🚫 Admin access required"
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            continue

                        # Handle commands (e.g., /imagine ...)
                        if message_text.startswith(PREFIX):
                            handle_command_message(sender_id, message_text)
                        # Handle image attachments from user
                        elif attachments:
                            for attachment in attachments:
                                if attachment["type"] == "image":
                                    image_url = attachment["payload"]["url"]
                                    try:
                                        response = requests.get(image_url)
                                        image_data = BytesIO(response.content)
                                        # Store user image message
                                        store_message(sender_id, f"[Image Url: {image_url}]", "user", "image")
                                        # Always pass latest persistent history
                                        history = get_conversation_history(sender_id)
                                        # Process the image and get analysis
                                        result = messageHandler.handle_attachment(sender_id, image_data, "image", history)
                                        # Store bot's analysis result
                                        store_message(sender_id, f"Image Analysis:{result}", "bot", "analysis")
                                        send_message(sender_id, result)
                                    except Exception as e:
                                        logger.error(f"Error processing image: {str(e)}")
                                        error_msg = "Error processing image"
                                        store_message(sender_id, error_msg, "bot", "error")
                                        send_message(sender_id, error_msg)
                                        report(str(e))

                        # Handle plain text messages (non-command, non-image)
                        elif message_text:
                            try:
                                # Check if message contains URLs (don't treat as image)
                                url_patterns = ['http://', 'https://', 'www.', '.com', '.org', '.net', '.py','.js','.html']
                                contains_url = any(pattern in message_text.lower() for pattern in url_patterns)

                                if contains_url:
                                    logger.debug(f"Message contains URL, processing as text: {message_text}")

                                history = get_conversation_history(sender_id)
                                response = messageHandler.handle_text_message(sender_id, message_text, history)
                                # Normal text response
                                store_message(sender_id, response, "bot", "text")
                                send_message(sender_id, response)
                            except Exception as e:
                                logger.error(f"Error processing message: {str(e)}")
                                error_msg = "Sorry, I encountered an error processing your message."
                                store_message(sender_id, error_msg, "bot", "error")
                                send_message(sender_id, error_msg)
                                report(str(e))
                    except Exception as e:
                        logger.error(f"Error processing attachment: {str(e)}")
                        error_msg = "Error processing attachment"
                        store_message(sender_id, error_msg, "bot", "error")
                        send_message(sender_id, error_msg)
                        report(str(e))

        return "EVENT_RECEIVED", 200
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        report(f"ERROR IN WEBHOOK: {str(e)}")
        return "Internal error", 500
                                                                               
@app.route('/api/stats', methods=['GET'])
def api_stats():
    """
    Provide comprehensive bot statistics for monitoring dashboard
    """
    try:
        c = conn.cursor()

        # Total messages
        c.execute("SELECT COUNT(*) FROM conversations")
        total_messages = c.fetchone()[0]

        # Today's messages
        c.execute("SELECT COUNT(*) FROM conversations WHERE DATE(timestamp) = DATE('now')")
        today_messages = c.fetchone()[0]

        # Active users (users who sent messages in last 24 hours)
        c.execute("SELECT COUNT(DISTINCT user_id) FROM conversations WHERE timestamp >= datetime('now', '-1 day')")
        active_users = c.fetchone()[0]

        # Error rate (percentage of failed messages in last 24 hours)
        c.execute("SELECT COUNT(*) FROM message_logs WHERE timestamp >= datetime('now', '-1 day')")
        total_recent = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM message_logs WHERE status = 'failed' AND timestamp >= datetime('now', '-1 day')")
        failed_recent = c.fetchone()[0]

        error_rate = round((failed_recent / total_recent * 100) if total_recent > 0 else 0, 2)

        # Most popular commands
        c.execute("""
            SELECT message, COUNT(*) as count
            FROM conversations
            WHERE message LIKE '/%' AND timestamp >= datetime('now', '-7 days')
            GROUP BY message
            ORDER BY count DESC
            LIMIT 5
        """)
        popular_commands = c.fetchall()

        # Message types distribution
        c.execute("""
            SELECT message_type, COUNT(*) as count
            FROM conversations
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY message_type
        """)
        message_types = dict(c.fetchall())

        return jsonify({
            "total_messages": total_messages,
            "today_messages": today_messages,
            "active_users": active_users,
            "error_rate": error_rate,
            "popular_commands": [{"command": cmd[0], "count": cmd[1]} for cmd in popular_commands],
            "message_types": message_types,
            "facebook_integration": INITIALIZED
        })

    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api', methods=['GET'])
def api():
    query = request.args.get('query')
    uid = request.args.get('uid')
    if not query:
        return jsonify({"error": "No query provided"}), 400
    try:
        user_id = uid if uid else f"api_user_{str(int(time.time()))}"
        store_message(user_id, query, "user", "text")
        history = get_conversation_history(user_id)
        response = messageHandler.handle_text_message(user_id, query, history)
        store_message(user_id, response, "bot", "text")
        return jsonify({"response":response})
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    uptime = get_bot_uptime()
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    return jsonify({
        "status": "online",
        "uptime": f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
        "initialized": INITIALIZED,
        "timestamp": get_current_time()
    })

@app.route('/history', methods=['GET'])
def user_history():
    logger.info("GET /history called.")
    user_id = request.args.get("id")
    admin_code = request.args.get("admin")
    if not user_id:
        logger.warning("No user id provided to /history endpoint.")
        return jsonify({"error": "No user id provided"}), 400
    if admin_code != os.getenv("ADMIN_CODE", "ICU14CU"):
        logger.warning("Invalid admin code provided to /history endpoint.")
        return jsonify({"error": "Invalid admin code"}), 403
    try:
        history = get_conversation_history(user_id)
        logger.info(f"User history fetched for user_id={user_id}")
        return jsonify({"user_id": user_id, "conversation_history": history})
    except Exception as e:
        logger.error(f"Error fetching conversation history: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def error(e):
    return render_template('error.html')

def autouptime():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        logger.info("No RENDER_EXTERNAL_URL found, auto uptimer is disabled.")
        return
    logger.info(f"Auto uptimer started for {url}")
    while True:
        try:
            time.sleep(20)
            resp = requests.get(url)
            logger.debug(f"Uptimer ping sent to {url}, status: {resp.status_code}")
        except Exception as e:
            logger.error(f"Error in auto uptimer: {str(e)}")


def get_bot_uptime():
    return time.time() - start_time

try:
    fb_valid = validate_environment()
    conn = init_db()
    if fb_valid:
        INITIALIZED = True
        logger.info("🎉Application initialized successfully with Facebook integration")
    else:
        INITIALIZED = False
        logger.warning("⚠️ Application running in limited mode - Facebook integration disabled")
        logger.info("💡 Set valid PAGE_ACCESS_TOKEN and VERIFY_TOKEN to enable full functionality")
except Exception as e:
    logger.critical(f"Failed to initialize application: {str(e)}")
    INITIALIZED = False
    logger.info("🔧 Application running with minimal functionality")

if __name__ == '__main__':
    logger.info("""==================
    APP STARTED SUCCESSFULLY......
    ===================
    CREATED BY SULEIMAN
    ==================""")
    threading.Thread(target=post, daemon=True).start()
    threading.Thread(target=autouptime,daemon=True).start()
    app.run(debug=True, host='0.0.0.0',port=3000)
