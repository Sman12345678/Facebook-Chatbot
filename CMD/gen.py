import requests
from io import BytesIO
import logging

logging.basicConfig(filename="image_generator.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

Info = {"Description": "Generate an image based on the given prompt using the custom API."}

def execute(message, sender_id):
    if not message:
        return {"success": False, "type": "text", "data": "❌ Please provide a prompt for image generation"}
    try:
        logging.info(f"Attempting to generate image with prompt: {message}")
        api_url = f"https://theone-fast-image-gen.vercel.app/?prompt={message}"
        initial_response = {"success": True, "type": "text", "data": "🎨 Generating your image..."}
        download_url = requests.get(api_url).json().get("download_url")
        img_response = requests.get(download_url)
        image_data = BytesIO(img_response.content)
        image_data.seek(0)
        logging.info("Image generated successfully")
        return [initial_response, {"success": True, "type": "image", "data": image_data}]
    except Exception as e:
        logging.error(f"Error generating image: {str(e)}")
        return {"success": False, "type": "text", "data": f"🚨 An error occurred: {str(e)}"}
