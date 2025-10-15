import requests

Info = {
    "Description": "Generate text using GPT API. Usage: /gpt <prompt>"
}

def execute(message, sender_id = None):
    try:
        r = requests.get(f"https://text.pollinations.ai/{message}", timeout=20)
        if r.status_code != 200:
            return [{"success": False, "type": "text", "data": f"❌ API error: {r.status_code}"}]
        return [{"success": True, "type": "text", "data": r.text.strip()}]
    except Exception as e:
        return [{"success": False, "type": "text", "data": f"🚨 Error: {str(e)}"}]
