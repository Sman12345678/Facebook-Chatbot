
import random

Info = {
    "Description": "Get random programming jokes and tech humor to brighten your day"
}

def execute(message=None, sender_id=None):
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs! 🐛💡",
        
        "How many programmers does it take to change a light bulb? None, that's a hardware problem! 💡🔧",
        
        "Why do Java developers wear glasses? Because they can't C# 👓😄",
        
        "There are only 10 types of people in the world: those who understand binary and those who don't! 1️⃣0️⃣",
        
        "Why did the programmer quit his job? He didn't get arrays! 📊💸",
        
        "A SQL query goes into a bar, walks up to two tables and asks... 'Can I join you?' 🍺📋",
        
        "Why do programmers hate nature? It has too many bugs! 🌿🐛",
        
        "What's a programmer's favorite hangout place? Foo Bar! 🍻👨‍💻",
        
        "Why did the developer go broke? Because he used up all his cache! 💰💾",
        
        "How do you comfort a JavaScript bug? You console it! 🤗🐞",
        
        "Why don't programmers like to go outside? The sunlight causes too many reflections! ☀️💻",
        
        "What do you call a programmer from Finland? Nerdic! 🇫🇮🤓"
    ]
    
    selected_joke = random.choice(jokes)
    
    return f"""😂 **Programming Joke Time!**

{selected_joke}

🎭 *Hope that made you smile!*
🔄 Type `/joke` again for another one!

😎 *Powered by Kora AI's Humor Engine*"""
