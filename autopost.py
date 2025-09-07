import os
import time
import random
import requests
from datetime import datetime
import app
from messageHandler import handle_text_message, handle_attachment, handle_text_command
from app import PREFIX  # for command detection

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")  # set your Page ID in .env

FALLBACK_REPLIES = [
    "🔥 Cool one! But hey… DM me if you’re serious 😉",
    "😂 Haha that cracked me up. DM me if you want the real gist.",
    "😎 Smooth comment! Respect. DM for more vibes 🚀",
    "👀 I see you… pull up in the DMs for the rest.",
    "🤣 You’re wild! Love it. Let’s chat more in DM.",
    "👌 Noted! Short and sweet—just like you. DM me if you’re down.",
    "🤖 That’s something even AI would blush at 😂. DM if you want more.",
    "🚀 Blast off! That comment deserves a salute. Catch me in DM!",
    "💡 Smart one, I like it. Wanna dive deeper? Hit my DM.",
    "🔥🔥🔥 Straight fire. Respect! DM and let’s keep it rolling."
]

def post_text_to_page(message):
    url = "https://graph.facebook.com/v22.0/me/feed"
    payload = {
        "message": message,
        "access_token": PAGE_ACCESS_TOKEN
    }
    return requests.post(url, data=payload).json()

def reply_to_comment(comment_id, reply_message=None, image_url=None):
    url = f"https://graph.facebook.com/v22.0/{comment_id}/comments"
    payload = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    if reply_message:
        payload["message"] = reply_message
    if image_url:
        payload["attachment_url"] = image_url
    return requests.post(url, data=payload).json()

def process_comments():
    url = f"https://graph.facebook.com/v22.0/{PAGE_ID}/feed"
    params = {
        "fields": "id,message,comments{id,from,message,attachment}",
        "access_token": PAGE_ACCESS_TOKEN
    }
    try:
        feed = requests.get(url, params=params).json()
        for post in feed.get("data", []):
            if "comments" in post:
                for comment in post["comments"]["data"]:
                    comment_id = comment["id"]
                    user_id = comment["from"]["id"]
                    username = comment["from"]["name"]

                    reply_text = None
                    reply_image = None

                    try:
                        # Text comment
                        if "message" in comment and comment["message"]:
                            text = comment["message"]

                            if text.startswith(PREFIX):
                                command_name = text[len(PREFIX):].split(" ")[0]
                                reply_text = handle_text_command(command_name, text, user_id)
                            else:
                                user_message = f"A user named {username} commented on your post with {text}, so provide a short and cool reply"
                                reply_text = handle_text_message(user_id, user_message)

                        # Image comment
                        elif "attachment" in comment:
                            attachment = comment["attachment"]
                            if attachment.get("type") == "photo":
                                image_url = attachment["media"]["image"]["src"]
                                reply_text = handle_attachment(user_id, image_url, "image")
                                reply_image = image_url
                    except Exception as e:
                        print(f"⚠️ Handler error: {e}")

                    # Fallback if handler failed or returned nothing
                    if not reply_text and not reply_image:
                        reply_text = random.choice(FALLBACK_REPLIES)

                    # Post reply
                    if reply_text or reply_image:
                        result = reply_to_comment(comment_id, reply_message=reply_text, image_url=reply_image)
                        print(f"✅ Replied to comment {comment_id}: {result}")

    except Exception as e:
        print(f"❌ Error processing comments: {e}")
        app.report(f"Comment processing error: {e}")

def get_content_pool():
    return [
        "🌍 Life is a journey, not a race. Take each step with intention and gratitude. "
        "The small choices you make daily shape your future. Stay consistent, stay humble, and stay focused. #motivation #growth #koraai",

        "💡 Technology should empower us, not control us. Learn to use tools that save time, "
        "protect your privacy, and expand your creativity. Master the machine before it masters you. #techtips #privacy #koraai",

        "🚀 Success is built one brick at a time. Don’t chase shortcuts; embrace the process. "
        "Every setback is a setup for a stronger comeback. #success #grind #koraai",

        "🤖 AI is not here to replace humans; it’s here to amplify human potential. "
        "Those who learn to work alongside it will lead the future. #AI #future #koraai",

        "🌱 Balance is power. Work hard, rest well, and invest in your mind. "
        "Growth happens when effort meets patience. #mindset #balance #koraai",
    ]

def post():
    last_post_time = 0
    WEEK = 604800  # seconds in a week

    while True:
        now = time.time()

        # Post once a week
        if now - last_post_time >= WEEK:
            message = random.choice(get_content_pool())
            try:
                result = post_text_to_page(message)

                if result.get("error", {}).get("code") == 100:
                    app.report(f"Autopost OAuthException, need app-scoped ID: {result['error']['message']}")

                print(f"[{datetime.now()}] ✅ Auto-posted: {message}")
                print(f"📡 Facebook Response: {result}")
                last_post_time = now

            except Exception as e:
                print(f"[{datetime.now()}] ❌ Auto-post failed: {e}")
                app.report(f"Autopost error: {e}")

        # Always check comments every 2 minutes
        process_comments()
        time.sleep(120)
