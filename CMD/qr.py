
import requests
from io import BytesIO

Info = {
    "Description": "Generate QR codes for text, URLs, or any data you want to encode"
}

def execute(message=None, sender_id=None):
    if not message or not message.strip():
        return """📱 **QR Code Generator**

🔧 **How to use:**
Type: `/qr [text or URL]`

📝 **Examples:**
• `/qr https://google.com`
• `/qr Hello World!`
• `/qr My contact info`

✨ Generate QR codes instantly for any text or URL!"""

    text_to_encode = message.strip()
    
    try:
        # Using QR Server API (free service)
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={requests.utils.quote(text_to_encode)}"
        
        response = requests.get(qr_url, timeout=10)
        
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            
            return {
                "success": True,
                "type": "image",
                "data": image_data,
                "caption": f"📱 QR Code for: {text_to_encode[:50]}{'...' if len(text_to_encode) > 50 else ''}"
            }
        else:
            return "❌ Failed to generate QR code. Please try again."
            
    except Exception as e:
        return f"❌ Error generating QR code: {str(e)}"
