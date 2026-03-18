import telebot
import pymongo
import os
import random
import datetime
import requests
import feedparser
import time
import threading

# --- CONFIGURATION (Sari Details Verified) ---
BOT_TOKEN = "8738534218:AAGhnt3qo_zFhinx_sfUMR-9eJUerrlRL8o"
MONGO_URI = "mongodb+srv://rms:Agrms224166@rmsbot.fipfmok.mongodb.net/?retryWrites=true&w=majority&appName=RMSBOT"
GEMINI_KEY = "AIzaSyAj7-o0Go-Xar2fwKYks83E_ihpsBKAtTQ"
ADMIN_ID = 281457173
GROUP_ID = -1002657897913 

# Direct Mapping for Website Categories
SITE_MAP = {
    "independent tv": "https://trackandplay.com/category/independent-tv/",
    "gx6605s": "https://trackandplay.com/category/gx6605s/",
    "sunplus": "https://trackandplay.com/category/sunplus/",
    "montage": "https://trackandplay.com/category/montage/",
    "solid": "https://trackandplay.com/category/solid/",
    "tp list": "https://trackandplay.com/category/tp-list/",
    "strong tp": "https://trackandplay.com/category/tp-list/"
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

# --- 1. AI EXPERT LOGIC (Fixed for Human-like Chat) ---
def get_ai_response(user_query, user_name):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        system_instruction = f"""
        Aapka naam TrackAndPlay AI Assistant hai. Aap Senior Satellite Engineer hain.
        User: {user_name}.
        Rules: 
        1. Friendly expert ki tarah baat karein. 
        2. Strong TP mange toh puchiye kaunsi satellite? 
        3. Software mange toh trackandplay.com ka link dein.
        4. User se details puchiye (e.g. Dish size, Region).
        """
        payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Query: {user_query}"}]}]}
        response = requests.post(url, json=payload).json()
        return response['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"Hey {user_name}, technical help ke liye trackandplay.com visit karein."

# --- 2. RSS FEED (Auto-Post Website Updates) ---
def check_rss_feed():
    while True:
        try:
            feed = feedparser.parse("https://trackandplay.com/feed/")
            if feed.entries:
                latest = feed.entries[0]
                last_sent = meta_col.find_one({"type": "last_rss_id"})
                if not last_sent or last_sent["id"] != latest.id:
                    msg = f"🆕 **New Update on TrackAndPlay!**\n\n🔥 {latest.title}\n\n🔗 [Download Now]({latest.link})"
                    bot.send_message(GROUP_ID, msg, parse_mode="Markdown")
                    meta_col.update_one({"type": "last_rss_id"}, {"$set": {"id": latest.id}}, upsert=True)
        except: pass
        time.sleep(600)

threading.Thread(target=check_rss_feed, daemon=True).start()

# --- 3. AUTO-COMMANDS POSTER (Every 2 Hours) ---
def post_commands():
    while True:
        time.sleep(7200)
        txt = "🤖 **Quick Help:** Bot ki sari commands dekhne ke liye `/help` likhein!"
        try: bot.send_message(GROUP_ID, txt, parse_mode="Markdown")
        except: pass

threading.Thread(target=post_commands, daemon=True).start()

# --- 4. COMMAND HANDLERS ---

@bot.message_handler(commands=['help', 'start'])
def send_help(message):
    user_name = message.from_user.first_name
    # Database initialization on start
    if not users_col.find_one({"user_id": message.from_user.id}):
        users_col.insert_one({"user_id": message.from_user.id, "points": 0, "last_claim": ""})
        
    help_text = (
        f"👋 **Hello {user_name}! TrackAndPlay AI Bot Ready.**\n\n"
        "🔹 `/daily_gift` - Rozana 25 Bonus Points lein.\n"
        "🔹 `/ad` - Ek ad dekh kar 10 points kamayein.\n"
        "🔹 `/wallet` - Apna total balance check karein.\n"
        "🔹 `/leaderboard` - Group ke top earners dekhein.\n\n"
        "🛰 **Help:** Kuch bhi technical puchiye ya chipset ka naam likhein!"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['daily_gift'])
def daily_gift(message):
    ad = random.choice(AD_LINKS)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Unlock 25 Points 🎁", url=ad))
    bot.send_message(message.chat.id, "Gift ke liye ad link open karein aur phir `/claim_gift` likhein:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['claim_gift'])
def claim_gift(message):
    user_id = message.from_user.id
    today = str(datetime.date.today())
    user_data = users_col.find_one({"user_id": user_id})
    
    if user_data and user_data.get("last_claim") == today:
        bot.reply_to(message, "❌ Aaj ka gift mil chuka hai! Kal wapis aana.")
    else:
        users_col.update_one({"user_id": user_id}, {"$set": {"last_claim": today}, "$inc": {"points": 25}}, upsert=True)
        bot.reply_to(message, "✅ 25 Points added successfully!")

@bot.message_handler(commands=['ad'])
def earn_ad(message):
    ad = random.choice(AD_LINKS)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Get 10 Points 🎁", url=ad))
    bot.send_message(message.chat.id, "Ad dekhne ke baad `/claim` likhein:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['claim'])
def claim_ad_points(message):
    users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"points": 10}}, upsert=True)
    bot.send_message(message.chat.id, "✅ 10 Points added to your wallet!")

@bot.message_handler(commands=['wallet'])
def check_wallet(message):
    user_data = users_col.find_one({"user_id": message.from_user.id})
    pts = user_data['points'] if user_data else 0
    bot.reply_to(message, f"💰 **Aapka Balance:** {pts} Points")

@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    top_users = users_col.find().sort("points", -1).limit(10)
    txt = "🏆 **TrackAndPlay Top 10 Earners** 🏆\n\n"
    for i, user in enumerate(top_users, 1):
        txt += f"{i}. User ID: `{user['user_id']}` — {user['points']} Pts\n"
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")

# --- 5. SMART MESSAGE HANDLER (Keywords & AI) ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text == "/":
        send_help(message)
        return

    user_text = message.text.lower()
    user_name = message.from_user.first_name

    # Keyword Mapping Check
    for key, link in SITE_MAP.items():
        if key in user_text:
            bot.reply_to(message, f"✅ {user_name}, **{key.upper()}** ka direct link:\n🔗 [Download Karein]({link})", parse_mode="Markdown")
            return

    # AI Expert Trigger
    tech_keys = ['tp', 'signal', 'frequency', 'dish', 'issue', 'problem', 'not working', 'biss', 'software']
    if any(word in user_text for word in tech_keys):
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_ai_response(message.text, user_name)
        bot.reply_to(message, response)
        return

    if message.chat.type == 'private':
        bot.reply_to(message, "Mujhe samajh nahi aaya. Commands dekhne ke liye `/help` likhein.")

bot.polling(none_stop=True)
