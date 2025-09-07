import os
import time
import random
import requests
from report import report 
from datetime import datetime
from messageHandler import handle_text_message, handle_attachment, handle_text_command

PREFIX = os.getenv("PREFIX","/")

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
        report(f"Comment processing error: {e}")

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

        "🔥 Pressure makes diamonds, but only if you don’t crack under the weight. "
        "Your challenges are shaping you into something rare and unbreakable—stay in the fight. #hustle #growth #koraai",

        "😂 I told my computer I needed a break… it froze. But honestly, maybe it was just trying to chill with me. "
        "Sometimes even machines know when to slow down. #techjokes #nerdlife #koraai",

        "🌌 You are literally made of stardust. Every atom in your body was born in the core of a star. "
        "Don’t walk through life doubting yourself—you’re cosmic royalty. #motivation #cosmos #koraai",

        "📚 Knowledge is free, but ignorance will charge you compound interest. "
        "The more you avoid learning today, the more expensive tomorrow becomes. #wisdom #growth #koraai",

        "🤣 My WiFi is like my motivation: blazing fast in the morning, buffering by midnight. "
        "Maybe the trick is to refresh both regularly. #funny #relatable #koraai",

        "⚡ Every pro was once a beginner who refused to quit. "
        "Consistency beats raw talent when talent gets lazy. Keep showing up. #success #inspiration #koraai",

        "🧠 Thinking outside the box is powerful, but first—know what’s inside the box. "
        "Master the basics, then flip the script. #creativity #growth #koraai",

        "🤣 Why don’t programmers like nature? Too many bugs. "
        "Still, the irony is that the world’s best code—DNA—is written by nature itself. #techjokes #programming #koraai",

        "💪 Discipline eats motivation for breakfast. "
        "Motivation fades when it rains, when you’re tired, or when no one is cheering. Discipline doesn’t care—it gets the job done. #mindset #focus #koraai",

        "🌍 Be the type of energy that no WiFi password can lock out. "
        "Good vibes, genuine kindness, and real passion spread further than any signal. #positivity #vibes #koraai",

        "🤣 I asked my phone for space… now it’s on airplane mode. "
        "Guess even devices need boundaries sometimes. #funny #techlife #koraai",

        "🎯 Dreams don’t work unless you do. Wishing builds nothing, but effort builds everything. "
        "Pick up the hammer and start laying bricks on your dream today. #success #drive #koraai",

        "😂 The cloud isn’t in the sky—it’s just someone else’s computer. "
        "Remember, convenience is never free; you’re paying with data, even if not with cash. #techhumor #AI #koraai",

        "🌱 Growth feels uncomfortable because it’s change in motion. "
        "Like shoes that suddenly don’t fit, life forces you to evolve into bigger versions of yourself. #life #growth #koraai",

        "🚀 Don’t just chase trends. Build something so authentic that others chase you. "
        "Leaders innovate, followers imitate. Decide which side you’re on. #innovation #future #koraai",

        # --- New 10 longer ones ---
        "🌟 Confidence isn’t walking into a room thinking you’re better than everyone—it’s walking in without the need to compare at all. "
        "Your light doesn’t dim when others shine; it just adds more brightness to the room. #confidence #growth #koraai",

        "😂 People say money doesn’t buy happiness, but have you ever seen someone frown on a jet ski? "
        "Still, true joy isn’t in things—it’s in freedom, purpose, and laughter. #funny #life #koraai",

        "🌍 The problem isn’t time—it’s focus. You get the same 24 hours as legends, dreamers, and billionaires. "
        "The question is, where are you spending your attention? #focus #discipline #koraai",

        "🤣 My password is my dog’s name… plus the year he bit me. Hackers don’t stand a chance. "
        "Sometimes humor is the only firewall you need. #funny #tech #koraai",

        "🧘 Mental health isn’t a luxury, it’s a foundation. "
        "You charge your phone daily, but when was the last time you recharged your mind? "
        "Log out, breathe, and remember—you’re human, not hardware. #mindset #balance #koraai",

        "💡 Ideas are cheap, execution is priceless. "
        "Anyone can dream of flying cars; it takes discipline to build an engine. #innovation #success #koraai",

        "😂 If procrastination was a sport, I’d probably sign up tomorrow. "
        "But hey—done is better than perfect, and starting beats waiting. #funny #productivity #koraai",

        "🌌 Look up at the stars. Every galaxy is proof that expansion is the natural state of the universe. "
        "So why keep shrinking yourself to fit small expectations? Expand. #cosmos #motivation #koraai",

        "🎵 Music heals in ways medicine can’t. One song can carry memories, mend hearts, and inspire revolutions. "
        "So never underestimate the soundtrack of your life. #music #life #koraai",

        "🚀 The future belongs to the curious—the ones who ask questions, break patterns, and try again when they fail. "
        "Curiosity is the fuel, persistence is the rocket, and vision is the destination. #future #growth #koraai",
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
                    report(f"Autopost OAuthException, need app-scoped ID: {result['error']['message']}")

                print(f"[{datetime.now()}] ✅ Auto-posted: {message}")
                print(f"📡 Facebook Response: {result}")
                last_post_time = now

            except Exception as e:
                print(f"[{datetime.now()}] ❌ Auto-post failed: {e}")
                report(f"Autopost error: {e}")

        # Always check comments every 2 minutes
        process_comments()
        time.sleep(120)
