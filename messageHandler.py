import os
import google.generativeai as genai
import importlib
from dotenv import load_dotenv
import logging
import requests
from io import BytesIO
import urllib3
import time
import json
import app

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

time_now = time.asctime(time.localtime(time.time()))
system_instruction = f"""
You are KORA AI, an intelligent assistant for Facebook Messenger own and created by Suleiman 

Core Guidelines:
• Be helpful, informative, and use emojis to make conversations engaging with soft badass style
• When users ask about commands, guide them to use the proper command syntax
• For comprehensive topics, provide advantages, disadvantages, and key information
• If you lack information, suggest reliable online sources

Available Commands:
• /help - View all commands
• /imagine - Generate images  
• /lyrics - Get song lyrics
• /image - Search for images
• /bbc - Latest news headlines
• /report - Send feedback to owner

Image Generation: When users request image creation, guide them to use the /imagine command.

Current date: {time_now}
"""

IMAGE_ANALYSIS_PROMPT = """Analyize the image keenly and explain it's content,if it's a text translate it and identify the Language. If it Contain a Question Solve it perfectly"""

# Store model instances for each user to maintain conversation context
user_models = {}

def initialize_text_model(user_id, history=None):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 30,
            "max_output_tokens": 8192,
        }
    )
    gemini_history = []
    if history:
        for message in history:
            content = message["content"]
            # Optionally keep type in context for richer prompting
            if message.get("type") == "analysis":
                content = f"[Image Analysis Result]\n{content}"
            elif message.get("type") == "error":
                content = f"[Error]\n{content}"
            gemini_history.append({
                "role": message["role"],
                "parts": [content]
            })
    chat = model.start_chat(history=gemini_history)
    user_models[user_id] = chat
    return chat

def get_or_create_chat(user_id, history=None):
    """Get existing chat or create a new one with latest persistent history"""
    if user_id in user_models:
        return user_models[user_id]
    else:
        return initialize_text_model(user_id, history)

def handle_text_message(user_id, user_message, history=None):
    try:
        logger.info("Processing text message from %s: %s", user_id, user_message)
        chat = get_or_create_chat(user_id, history)
       
        response = chat.send_message(f"{system_instruction}\n\nHuman: {user_message}")
        return response.text
    except Exception as e:
        logger.error("Error processing text message: %s", str(e))
        app.report(str(e))
        if user_id in user_models:
            del user_models[user_id]
        return "😔 Sorry, I encountered an error processing your message."

def handle_text_command(command_name, message, sender_id):
    command_name=command_name.lower()
    try:
        cmd_module = importlib.import_module(f"CMD.{command_name}")
        return cmd_module.execute(message, sender_id)
    except ImportError:
        logger.warning("Command %s not found.", command_name)
        return "🚫 The Command you are using does not exist, Type /help to view Available Command"

def handle_attachment(user_id, attachment_data, attachment_type="image", history=None):
    if attachment_type != "image":
        return "🚫 Unsupported attachment type. Please send an image."
    logger.info("Processing image attachment from %s", user_id)
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content([
            IMAGE_ANALYSIS_PROMPT,
            {'mime_type': 'image/jpeg', 'data': attachment_data.getvalue() if isinstance(attachment_data, BytesIO) else attachment_data}
        ])
        analysis_result = f"🖼️ Image Analysis:\n{response.text}\n______\nPowered By Kora AI\n______"

        # Always use latest persistent history
        chat = get_or_create_chat(user_id, history=history)
        chat.send_message(analysis_result)

        return analysis_result
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}")
        app.report(str(e))
        return "🚨 Error analyzing the image. Please try again later."
        
