import telebot
import pymongo
import os
import random
import datetime
import requests
import feedparser
import time
import threading

# --- CONFIGURATION ---
BOT_TOKEN = "8738534218:AAGhnt3qo_zFhinx_sfUMR-9eJUerrlRL8o"
MONGO_URI = "mongodb+srv://rms:Agrms224166@rmsbot.fipfmok.mongodb.net/?retryWrites=true&w=majority&appName=RMSBOT"
GEMINI_KEY = "AIzaSyAj7-o0Go-Xar2fwKYks83E_ihpsBKAtTQ"
ADMIN_ID = 281457173
GROUP_ID = -1002657897913 

# Website Mapping (Direct Category Links)
SITE_MAP = {
    "independent tv": "https://trackandplay.com/category/independent-tv/",
    "gx6605s": "https://trackandplay.com/category/gx6605s/",
    "sunplus": "https://trackandplay.com/category/sunplus/",
    "montage": "https://trackandplay.com/category/montage/",
    "solid": "https://trackandplay.com/category/solid/",
    "tp list": "https://trackandplay.com/category/tp-list/",
    "software": "https://trackandplay.com/category/software-updates/"
}

AD_LINKS = [
    "https://www.effectivegatecpm.com/ieik85vff?key=d58462324f8afb5e36d3fade6811af49",
    "https://www.effectivegatecpm.com/pa3wchg46?key=3d881e1e67e1030ab609a17b17695d93",
    "https://www.effectivegatecpm.com/tiq1i1nwcs?key=9929dc9f815c415d0550bb3f64c1d854",
    "https://www.effectivegatecpm.com/kb96c0gieh?key=6b9065c47c1e21512fe3e8bced33144a"
]

bot = telebot.TeleBot(BOT_TOKEN)
client = pymongo.MongoClient(MONGO_URI)
db = client["TrackAndPlay_Bot_New"]
users_col = db["users"]
meta_col = db["metadata"]

# --- 1. AI EXPERT (Technical Support & Troubleshooting) ---
def get_ai_response(user_query, user_name):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        
        system_instruction = f"""
        Aapka naam TrackAndPlay AI Assistant hai. Aap ek expert Satellite Engineer hain.
        User: {user_name}.
        
        Rules:
        1. Agar user Strong TP mange: Pehle puchiye ki wo kaunsi satellite (e.g. 95e, 108e) align karna chahte hain aur unka Dish size kya hai.
        2. Technical Issue (e.g. Signal problem): User ko step-by-step guide karein (LNB check, Wire check, F-connector check).
        3. Human-like: Bilkul insano ki tarah baat karein, hamesha helpful rahein.
        4. Links: Har reply ke end mein 'More info: trackandplay.com' likhein.
        """
        
        payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Query: {user_query}"}]}]}
        response = requests.post(url, json=payload).json()
        return response['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"Hey {user_name}, aapke technical sawal ka jawab hamari website trackandplay.com par detailed article mein hai. Kripya wahan search karein."

# --- 2. SMART KEYWORD HANDLER (Direct Links) ---
def get_direct_link(text):
    text = text.lower()
    for key, link in SITE_MAP.items():
        if key in text:
            return link
    return None

# --- 3. AUTO COMMANDS & RSS (Same as before) ---
def post_commands():
    while True:
        time.sleep(7200) # 2 Hours
        txt = "🤖 **TrackAndPlay Bot Commands:**\n\n🔹 /daily_gift - 25 Pts\n🔹 /ad - 10 Pts\n🔹 /wallet - Balance\n\n💡 **Tip:** Box ka naam likhein (e.g. GX6605s) aur direct link payein!"
        try: bot.send_message(GROUP_ID, txt, parse_mode="Markdown")
        except: pass

threading.Thread(target=post_commands, daemon=True).start()

# --- 4. MAIN MESSAGE HANDLER ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_text = message.text.lower()
    user_name = message.from_user.first_name
    
    # Check for Direct Mapping first (Independent TV, GX6605s etc.)
    link = get_direct_link(user_text)
    if link:
        bot.reply_to(message, f"Hey {user_name}, aapne **{user_text}** ke bare mein pucha. Iska latest software/category link niche hai:\n\n🔗 [Click Here to Download]({link})", parse_mode="Markdown")
        return

    # If technical keywords found, use AI Expert
    tech_keywords = ['signal', 'tp', 'frequency', 'dish', 'issue', 'problem', 'not working', 'biss', 'key']
    if any(word in user_text for word in tech_keywords):
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_ai_response(message.text, user_name)
        bot.reply_to(message, response)
        return

    # Fallback (If nothing found)
    if message.chat.type == 'private':
        bot.reply_to(message, f"Hey @{message.from_user.username}, aapke sawal ka jawab hamari website trackandplay.com par maujood hai. Search bar mein '{message.text}' likhein.")

bot.polling()
