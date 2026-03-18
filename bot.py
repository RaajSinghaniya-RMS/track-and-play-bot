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

# Website Direct Mapping (Isme keywords aur unke links hain)
SITE_MAP = {
    "independent tv": "https://trackandplay.com/category/independent-tv/",
    "gx6605s": "https://trackandplay.com/category/gx6605s/",
    "sunplus": "https://trackandplay.com/category/sunplus/",
    "montage": "https://trackandplay.com/category/montage/",
    "solid": "https://trackandplay.com/category/solid/",
    "tp list": "https://trackandplay.com/category/tp-list/",
    "software": "https://trackandplay.com/category/software-updates/",
    "strong tp": "https://trackandplay.com/category/tp-list/"
}

bot = telebot.TeleBot(BOT_TOKEN)
client = pymongo.MongoClient(MONGO_URI)
db = client["TrackAndPlay_Bot_New"]
users_col = db["users"]
meta_col = db["metadata"]

# --- 1. AI EXPERT (Technical & Human-like) ---
def get_ai_response(user_query, user_name):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        
        # System Instruction: AI ko "Insan" banana
        system_instruction = f"""
        Aapka naam TrackAndPlay AI hai. Aap ek Senior Satellite Tracking Expert hain.
        User ka naam {user_name} hai.
        
        IMPORTANT RULES:
        1. Agar user 'Strong TP' ya 'Signal' mange: Pehle puchiye ki wo kaunsi satellite (e.g. 95e, NSS6, Paksat) align karna chahte hain. 
        2. Bina satellite ka naam jaane generic reply mat dein. User se dish size aur LNB type bhi puchiye.
        3. Agar user kisi chipset (GX, Sunplus) ya Box (Solid, Independent TV) ki baat kare, toh hamesha kahein ki 'Iska latest software trackandplay.com par mil jayega'.
        4. Baat karne ka style friendly aur supportive hona chahiye, bilkul ek expert ki tarah.
        5. Har reply ke end mein 'Visit: trackandplay.com' likhein.
        """
        
        payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Query: {user_query}"}]}]}
        response = requests.post(url, json=payload).json()
        return response['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"Hey {user_name}, technical issue ki wajah se reply nahi de pa raha. Aap trackandplay.com par check karein."

# --- 2. AUTO COMMANDS (Har 2 Ghante mein) ---
def post_commands():
    while True:
        time.sleep(7200)
        txt = "🤖 **TrackAndPlay Bot Commands:**\n\n🔹 /daily_gift - Get 25 Pts\n🔹 /ad - Get 10 Pts\n🔹 /wallet - Check Pts\n\n💡 **Tip:** Box ka naam likhein (e.g. GX6605s) aur direct link payein!"
        try: bot.send_message(GROUP_ID, txt, parse_mode="Markdown")
        except: pass

threading.Thread(target=post_commands, daemon=True).start()

# --- 3. MAIN MESSAGE HANDLER ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_text = message.text.lower()
    user_name = message.from_user.first_name
    
    # Check for Direct Mapping (Keywords like Solid, GX6605s)
    for key, link in SITE_MAP.items():
        if key in user_text:
            bot.reply_to(message, f"Hey {user_name}, aapne **{key.upper()}** ke bare mein pucha. Iska direct link ye raha:\n\n🔗 [Yahan se Download Karein]({link})", parse_mode="Markdown")
            return

    # Technical Keywords Check (TP, Signal, Problem)
    tech_keys = ['tp', 'signal', 'frequency', 'issue', 'problem', 'dish', 'not working', 'biss']
    if any(word in user_text for word in tech_keys):
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_ai_response(message.text, user_name)
        bot.reply_to(message, response)
        return

    # Private chat fallback
    if message.chat.type == 'private':
        bot.reply_to(message, f"Hey {user_name}, aapke sawal ka jawab hamari website trackandplay.com par hai. Search: '{message.text}'")

bot.polling()
