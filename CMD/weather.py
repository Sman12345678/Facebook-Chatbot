
import requests
import os

Info = {
    "Description": "Get current weather information for any city worldwide"
}

def execute(message=None, sender_id=None):
    if not message or not message.strip():
        return """🌤️ **Weather Command Usage:**

📍 **How to use:**
Type: `/weather [city name]`

📝 **Examples:**
• `/weather London`
• `/weather New York`
• `/weather Lagos`

🌍 Get real-time weather updates for any city worldwide!"""

    city = message.strip()
    
    try:
        # Using OpenWeatherMap free tier (no API key needed for basic info)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=demo&units=metric"
        
        # Fallback to a free weather service
        fallback_url = f"http://wttr.in/{city}?format=j1"
        
        try:
            response = requests.get(fallback_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                current = data.get('current_condition', [{}])[0]
                
                temp = current.get('temp_C', 'N/A')
                desc = current.get('weatherDesc', [{}])[0].get('value', 'N/A')
                humidity = current.get('humidity', 'N/A')
                wind = current.get('windspeedKmph', 'N/A')
                
                return f"""🌤️ **Weather in {city.title()}**

🌡️ **Temperature:** {temp}°C
☁️ **Condition:** {desc}
💧 **Humidity:** {humidity}%
💨 **Wind Speed:** {wind} km/h

📍 **Location:** {city.title()}
⏰ **Updated:** Just now

🔮 *Weather data provided by wttr.in*"""
            else:
                raise Exception("Weather service unavailable")
                
        except:
            return f"""🌤️ **Weather Service**

📍 **City:** {city.title()}

⚠️ Sorry, weather data is temporarily unavailable. Please try again later.

💡 **Tip:** Make sure you've entered a valid city name.

🌍 *Powered by Kora AI*"""
            
    except Exception as e:
        return f"❌ Error getting weather data: Please check the city name and try again."
