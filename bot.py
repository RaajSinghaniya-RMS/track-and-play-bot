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

# --- 1. AI EXPERT (Website Search Integration) ---
def get_ai_response(user_query, user_name):
    try:
        # AI ko instruct karna ki wo search kare aur links de
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        
        system_instruction = f"""
        Aapka naam TrackAndPlay AI Assistant hai. Aap ek Senior Satellite Engineer hain.
        User: {user_name}.
        
        IMPORTANT: Agar user kisi Set Top Box (Independent TV, GX6605s, Sunplus, Solid) ka software mange, toh aapko seedha answer nahi dena, balki kehna hai: 'Ji zaroor, iska software hamari website trackandplay.com par available hai. Aap category section mein jaakar latest post download kar sakte hain.'
        
        Aapko 'Technical Issue' wala message KABHI nahi dena hai. Agar aapko exact link nahi pata, toh user ko search karne ka tarika batayein (e.g. Visit trackandplay.com and use search bar for "{user_query}").
        Baat karne ka tarika human jaisa rakhein.
        """
        
        payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Query: {user_query}"}]}]}
        response = requests.post(url, json=payload).json()
        return response['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"Hey {user_name}, aapke sawal ka jawab hamari website trackandplay.com par details ke sath maujood hai. Search bar mein '{user_query}' likhein."

# --- 2. AUTO-COMMANDS POSTER (Every 2 Hours) ---
def post_commands_every_2h():
    while True:
        time.sleep(7200) # 2 ghante
        command_text = (
            "🤖 **TrackAndPlay Bot Kaise Use Karein?**\n\n"
            "🔹 /daily_gift - Rozana 25 points lein\n"
            "🔹 /ad - Ads dekh kar 10 points kamayein\n"
            "🔹 /wallet - Apna balance check karein\n"
            "🔹 /leaderboard - Top users dekhein\n\n"
            "💡 **Help:** Kuch bhi likhein (e.g. Independent TV Software) aur AI aapko guide karega!"
        )
        try:
            bot.send_message(GROUP_ID, command_text, parse_mode="Markdown")
        except: pass

threading.Thread(target=post_commands_every_2h, daemon=True).start()

# --- 3. RSS AUTO-POST ---
def check_rss_feed():
    while True:
        try:
            feed = feedparser.parse("https://trackandplay.com/feed/")
            if feed.entries:
                latest = feed.entries[0]
                last_sent = meta_col.find_one({"type": "last_rss_id"})
                if not last_sent or last_sent["id"] != latest.id:
                    msg = f"🆕 **New Post!**\n\n🔥 {latest.title}\n\n🔗 [Open in App]({latest.link})"
                    bot.send_message(GROUP_ID, msg, parse_mode="Markdown")
                    meta_col.update_one({"type": "last_rss_id"}, {"$set": {"id": latest.id}}, upsert=True)
        except: pass
        time.sleep(600)

threading.Thread(target=check_rss_feed, daemon=True).start()

# --- 4. CORE HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "points": 0, "last_claim": ""})
    bot.send_message(message.chat.id, "🛰 **TrackAndPlay Pro AI Bot Ready!**", parse_mode="Markdown")

@bot.message_handler(commands=['ad', 'daily_gift'])
def ads_handler(message):
    ad = random.choice(AD_LINKS)
    markup = telebot.types.InlineKeyboardMarkup()
    # Native browser support ke liye web_app ya simple url buttons use hote hain
    markup.add(telebot.types.InlineKeyboardButton("Claim Points 🎁", url=ad))
    bot.send_message(message.chat.id, "Ad link open karein aur points claim karein:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    if message.chat.type != 'private' and not any(word in message.text.lower() for word in ['software', 'signal', 'tp', 'box', 'tv', 'dish']):
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    response = get_ai_response(message.text, message.from_user.first_name)
    bot.reply_to(message, response)

bot.polling()
