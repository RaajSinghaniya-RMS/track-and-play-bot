import telebot
import pymongo
import os
import random
import datetime
import requests
import feedparser
import time
import threading

# --- SETTINGS & CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URL')
# Aapne jo key di hai wahi yahan add ki hai
GEMINI_KEY = "AIzaSyAj7-o0Go-Xar2fwKYks83E_ihpsBKAtTQ"
ADMIN_ID = 281457173
GROUP_ID = -1002657897913 
RSS_URL = "https://trackandplay.com/feed/"

# Aapke 4 Adsterra Links
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

# --- 1. AI EXPERT (Human-like Technical Support) ---
def get_ai_response(user_query, user_name):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        
        system_instruction = f"""
        Aapka naam TrackAndPlay AI Assistant hai. Aap ek Senior Satellite & DTH Engineer hain.
        User ka naam {user_name} hai. 
        
        Rules:
        1. Friendly aur expert ki tarah baat karein.
        2. Agar user GX6605s, Sunplus, Montage, ya chipset ki baat kare, toh kahein: 'Iska best modified software trackandplay.com par available hai'.
        3. Agar TP/Signal pucha jaye, toh user se uski Dish size aur Region (Shehar) puchein.
        4. Technical keywords par hamesha trackandplay.com ka reference dein.
        5. Short aur helpful answers dein.
        """
        
        payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Query: {user_query}"}]}]}
        response = requests.post(url, json=payload).json()
        return response['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"Hey {user_name}, thoda technical issue hai. Aap tab tak trackandplay.com par latest TPs aur Softwares check kar sakte hain!"

# --- 2. RSS AUTO-POST (Website Sync) ---
def check_rss_feed():
    while True:
        try:
            feed = feedparser.parse(RSS_URL)
            if feed.entries:
                latest_post = feed.entries[0]
                post_id = latest_post.id
                last_sent = meta_col.find_one({"type": "last_rss_id"})
                if not last_sent or last_sent["id"] != post_id:
                    msg = f"🆕 **New Software Update!**\n\n🔥 {latest_post.title}\n\n🔗 [Download Now]({latest_post.link})"
                    bot.send_message(GROUP_ID, msg, parse_mode="Markdown")
                    meta_col.update_one({"type": "last_rss_id"}, {"$set": {"id": post_id}}, upsert=True)
        except: pass
        time.sleep(600)

threading.Thread(target=check_rss_feed, daemon=True).start()

# --- 3. COMMAND HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "points": 0, "last_claim": ""})
    bot.send_message(message.chat.id, "🛰 **TrackAndPlay AI Assistant Live!**\n\nMain ek technical expert hoon. Aap mujhse koi bhi Satellite sawal puch sakte hain.\n\nCommands:\n/daily_gift - 25 Pts\n/ad - 10 Pts\n/wallet - Balance\n/leaderboard - Top Players")

@bot.message_handler(commands=['daily_gift'])
def daily_gift(message):
    user_id = message.from_user.id
    today = str(datetime.date.today())
    u = users_col.find_one({"user_id": user_id})
    if u.get("last_claim") == today:
        bot.reply_to(message, "❌ Aaj ka gift mil chuka hai!")
    else:
        ad = random.choice(AD_LINKS)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Unlock 25 Points 🎁", url=ad))
        bot.send_message(message.chat.id, "Ad dekh kar /claim_gift likhein:", reply_markup=markup)

@bot.message_handler(commands=['claim_gift'])
def claim_gift(message):
    users_col.update_one({"user_id": message.from_user.id}, {"$set": {"last_claim": str(datetime.date.today())}, "$inc": {"points": 25}})
    bot.reply_to(message, "✅ 25 Points Added!")

@bot.message_handler(commands=['ad'])
def ad_command(message):
    ad = random.choice(AD_LINKS)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Get 10 Points 🎁", url=ad))
    bot.send_message(message.chat.id, "Ad open karein fir /claim likhein:", reply_markup=markup)

@bot.message_handler(commands=['claim'])
def claim_pts(message):
    users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"points": 10}})
    bot.send_message(message.chat.id, "✅ 10 Points Added!")

@bot.message_handler(commands=['wallet'])
def wallet(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    bot.reply_to(message, f"💰 Balance: {u['points'] if u else 0} Points")

# --- 4. HUMAN-LIKE CHAT HANDLER ---
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    # Technical Keywords Check
    keywords = ['signal', 'tp', 'software', 'gx6605s', 'sunplus', 'montage', 'dish', 'frequency', 'biss']
    
    if any(word in message.text.lower() for word in keywords):
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_ai_response(message.text, message.from_user.first_name)
        bot.reply_to(message, response)

bot.polling()
