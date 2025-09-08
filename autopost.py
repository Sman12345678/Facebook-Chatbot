import os
import time
import random
import requests
from report import report
from datetime import datetime
from messageHandler import handle_text_message, handle_attachment, handle_text_command
import sqlite3

# ENV config
PREFIX = os.getenv("PREFIX", "/")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")

# Fallback responses
FALLBACK_REPLIES = [
    "🔥 Cool one! But hey… DM me if you’re serious 😉",
    "😂 Haha that cracked me up. DM me if you want the real gist.",
    "😎 Smooth comment! Respect. DM me for more vibes 🚀",
    "👀 I see you… pull up in the DMs for the rest.",
    "🤣 You’re wild! Love it. Let’s chat more in DM.",
    "👌 Noted! Short and sweet—just like you. DM me if you’re down.",
    "🤖 That’s something even AI would blush at 😂. DM if you want more.",
    "🚀 Blast off! That comment deserves a salute. Catch me in DM!",
    "💡 Smart one, I like it. Wanna dive deeper? Hit my DM.",
    "🔥🔥🔥 Straight fire. Respect! DM and let’s keep it rolling."
]

DATABASE_NAME = 'replied_comments.db'

# -------------- SQLite Database Initialization --------------

def create_db():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS replied_comments (
        id TEXT PRIMARY KEY,
        timestamp INTEGER
    )
    ''')

    connection.commit()
    connection.close()

# Ensure the database is set up
create_db()

# -------------- Helpers for comment ID tracking --------------

def load_replied_comments():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM replied_comments")
    comments = cursor.fetchall()

    connection.close()
    return set(comment[0] for comment in comments)

def save_replied_comment(comment_id):
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Insert the comment ID and timestamp when it was replied to
    cursor.execute('''
    INSERT OR REPLACE INTO replied_comments (id, timestamp)
    VALUES (?, ?)
    ''', (comment_id, int(time.time())))

    connection.commit()
    connection.close()

# -------------- Facebook API posting/replying --------------

def post_text_to_page(message):
    url = "https://graph.facebook.com/v22.0/me/feed"
    payload = {
        "message": message,
        "access_token": PAGE_ACCESS_TOKEN
    }
    return requests.post(url, data=payload).json()

def reply_to_comment(comment_id, reply_message=None, image_url=None):
    url = f"https://graph.facebook.com/v22.0/{comment_id}/comments"
    payload = {"access_token": PAGE_ACCESS_TOKEN}

    if reply_message and not image_url:
        payload["message"] = reply_message
        return requests.post(url, data=payload).json()

    elif image_url and not reply_message:
        payload["attachment_url"] = image_url
        return requests.post(url, data=payload).json()

    elif reply_message and image_url:
        requests.post(url, data={"message": reply_message, "access_token": PAGE_ACCESS_TOKEN})
        requests.post(url, data={"attachment_url": image_url, "access_token": PAGE_ACCESS_TOKEN})
        return {"status": "✅ Sent in two steps"}

# -------------- Main comment processor --------------

def process_comments():
    url = f"https://graph.facebook.com/v22.0/{PAGE_ID}/feed"
    params = {
        "fields": "id,message,comments{id,from,message,attachment}",
        "access_token": PAGE_ACCESS_TOKEN
    }
    replied_comments = load_replied_comments()  # Now from SQLite database

    try:
        feed = requests.get(url, params=params).json()
        for post in feed.get("data", []):
            if "comments" in post:
                for comment in post["comments"]["data"]:
                    comment_id = comment["id"]

                    # Skip already replied comments
                    if comment_id in replied_comments:
                        continue

                    user_id = comment["from"]["id"]
                    username = comment["from"]["name"]

                    reply_text = None
                    reply_image = None

                    try:
                        if "message" in comment and comment["message"]:
                            text = comment["message"]

                            if text.startswith(PREFIX):
                                command_name = text[len(PREFIX):].split(" ")[0]
                                reply_text = handle_text_command(command_name, text, user_id)
                            else:
                                user_message = f"A user named {username} commented on your post with {text}, so provide a short and cool reply"
                                reply_text = handle_text_message(user_id, user_message)

                        elif "attachment" in comment:
                            attachment = comment["attachment"]
                            if attachment.get("type") == "photo":
                                image_url = attachment["media"]["image"]["src"]
                                reply_text = handle_attachment(user_id, image_url, "image")
                                reply_image = image_url

                    except Exception as e:
                        print(f"⚠️ Handler error: {e}")

                    # Use fallback if no handler reply
                    if not reply_text and not reply_image:
                        reply_text = random.choice(FALLBACK_REPLIES)

                    # Reply and mark as done
                    if reply_text or reply_image:
                        result = reply_to_comment(comment_id, reply_message=reply_text, image_url=reply_image)
                        print(f"✅ Replied to comment {comment_id}: {result}")
                        save_replied_comment(comment_id)  # Save the comment as replied in the DB

    except Exception as e:
        print(f"❌ Error processing comments: {e}")
        report(f"Comment processing error: {e}")

# -------------- Weekly content posting --------------

def get_content_pool():
    return [
        "🌍 Life is a journey, not a race. Take each step with intention and gratitude. #motivation #growth #koraai",
        "💡 Technology should empower us, not control us. #techtips #privacy #koraai",
        "🚀 Success is built one brick at a time. #success #grind #koraai",
        "🤖 AI is not here to replace humans; it’s here to amplify human potential. #AI #future #koraai",
        "🌱 Balance is power. Growth happens when effort meets patience. #mindset #balance #koraai",
        "🔥 Pressure makes diamonds... stay in the fight. #hustle #growth #koraai",
        "😂 I told my computer I needed a break… it froze. #techjokes #nerdlife #koraai",
        "🌌 You are literally made of stardust. #motivation #cosmos #koraai",
        "📚 Knowledge is free, but ignorance will charge you compound interest. #wisdom #growth #koraai",
        "🤣 My WiFi is like my motivation: blazing fast in the morning, buffering by midnight. #relatable #koraai",
        # Add more if needed
    ]

# -------------- Main loop --------------

def post():
    last_post_time = 0
    WEEK = 604800  # 1 week in seconds

    while True:
        now = time.time()

        if now - last_post_time >= WEEK:
            message = random.choice(get_content_pool())
            try:
                result = post_text_to_page(message)

                if result.get("error", {}).get("code") == 100:
                    report(f"Autopost OAuthException: {result['error']['message']}")

                print(f"[{datetime.now()}] ✅ Auto-posted: {message}")
                print(f"📡 Facebook Response: {result}")
                last_post_time = now

            except Exception as e:
                print(f"[{datetime.now()}] ❌ Auto-post failed: {e}")
                report(f"Autopost error: {e}")

        # Always check comments every 2 minutes
        process_comments()
        time.sleep(120)
