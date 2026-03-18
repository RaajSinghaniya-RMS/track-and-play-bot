import telebot
import pymongo
import os
import random
import datetime
import requests
import feedparser
import time
import threading

# --- CONFIGURATION (Sari Details Added) ---
BOT_TOKEN = "8738534218:AAGhnt3qo_zFhinx_sfUMR-9eJUerrlRL8o"
MONGO_URI = "mongodb+srv://rms:Agrms224166@rmsbot.fipfmok.mongodb.net/?retryWrites=true&w=majority&appName=RMSBOT"
GEMINI_KEY = "AIzaSyAj7-o0Go-Xar2fwKYks83E_ihpsBKAtTQ"
ADMIN_ID = 281457173
GROUP_ID = -1002657897913 
RSS_URL = "https://trackandplay.com/feed/"

# Direct Mapping
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

# --- 1. LIVE RSS CONTENT FETCH (Reply se pehle read karne ke liye) ---
def get_latest_website_content():
    try:
        feed = feedparser.parse(RSS_URL)
        content_summary = ""
        for entry in feed.entries[:5]: # Latest 5 posts scan karega
            content_summary += f"- Title: {entry.title}, Link: {entry.link}\n"
        return content_summary
    except:
        return "Website details currently unavailable."

# --- 2. AI EXPERT LOGIC (Updated for Smart Reply) ---
def get_ai_response(user_query, user_name):
    live_content = get_latest_website_content() # Har reply se pehle read karega
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        
        system_instruction = f"""
        Aapka naam TrackAndPlay AI Assistant hai. Aap Senior Satellite Engineer hain.
        User: {user_name}. 
        Aapki website 'trackandplay.com' par ye latest posts hain:
        {live_content}

        Rules:
        1. Friendly expert ki tarah baat karein.
        2. Agar user kuch mange jo upar di gayi 'Latest Posts' list mein hai, toh turant uska link dein.
        3. Agar user Strong TP mange, toh usse Satellite ka naam puchein.
        4. Kabhi ye mat kahein ke 'website par jaakar search karo', balki user ko solution dein ya upar di gayi list se link dein.
        5. Baat karne ka tarika bilkul human jaisa (bilkul Raaj Singhaniya jaisa friendly) hona chahiye.
        """
        
        payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Query: {user_query}"}]}]}
        response = requests.post(url, json=payload).json()
        return response['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"AI Error: {e}")
        return f"Hey {user_name}, mujhe lagta hai aapko trackandplay.com par iska solution mil jayega. Ek baar check karein!"

# --- 3. AUTO RSS POSTER (Har 10 Minute mein Group mein Update) ---
def check_rss_feed_loop():
    while True:
        try:
            feed = feedparser.parse(RSS_URL)
            if feed.entries:
                latest = feed.entries[0]
                last_sent = meta_col.find_one({"type": "last_rss_id"})
                if not last_sent or last_sent["id"] != latest.id:
                    msg = f"🆕 **New Software Update!**\n\n🔥 {latest.title}\n\n🔗 [Download Now]({latest.link})"
                    bot.send_message(GROUP_ID, msg, parse_mode="Markdown")
                    meta_col.update_one({"type": "last_rss_id"}, {"$set": {"id": latest.id}}, upsert=True)
        except: pass
        time.sleep(600)

threading.Thread(target=check_rss_feed_loop, daemon=True).start()

# --- 4. AUTO-COMMANDS (Har 2 Ghante) ---
def post_commands():
    while True:
        time.sleep(7200)
        txt = "🤖 **Quick Help:** Bot ki sari commands dekhne ke liye `/help` likhein ya chipset ka naam likhein!"
        try: bot.send_message(GROUP_ID, txt, parse_mode="Markdown")
        except: pass

threading.Thread(target=post_commands, daemon=True).start()

# --- 5. MESSAGE HANDLERS ---

@bot.message_handler(commands=['help', 'start'])
def send_help(message):
    user_name = message.from_user.first_name
    help_text = (
        f"👋 **Hello {user_name}! TrackAndPlay Bot Ready.**\n\n"
        "🔹 `/daily_gift` - 25 Bonus Points\n"
        "🔹 `/ad` - 10 Bonus Points\n"
        "🔹 `/wallet` - Balance check karein\n"
        "🔹 `/leaderboard` - Top earners\n\n"
        "🛰 **Technical Help:** Kuch bhi chipset (Solid, GX6605s) ya TP ke bare mein puchiye!"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text == "/":
        send_help(message)
        return

    user_text = message.text.lower()
    user_name = message.from_user.first_name

    # Check Direct Mapping First
    for key, link in SITE_MAP.items():
        if key in user_text:
            bot.reply_to(message, f"✅ {user_name}, **{key.upper()}** ka direct link:\n🔗 [Download Karein]({link})", parse_mode="Markdown")
            return

    # Technical AI Expert
    tech_keys = ['tp', 'signal', 'frequency', 'dish', 'issue', 'problem', 'not working', 'biss', 'software', 'software update']
    if any(word in user_text for word in tech_keys):
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_ai_response(message.text, user_name)
        bot.reply_to(message, response)
        return

    if message.chat.type == 'private':
        bot.reply_to(message, "Mujhe samajh nahi aaya. Commands ke liye /help likhein.")

# Reward Handlers
@bot.message_handler(commands=['daily_gift'])
def daily_gift(message):
    ad = random.choice(AD_LINKS)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Unlock Points 🎁", url=ad))
    bot.send_message(message.chat.id, "Gift ke liye ad link open karein aur phir `/claim_gift` likhein:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['claim_gift'])
def claim_gift(message):
    today = str(datetime.date.today())
    users_col.update_one({"user_id": message.from_user.id}, {"$set": {"last_claim": today}, "$inc": {"points": 25}}, upsert=True)
    bot.reply_to(message, "✅ 25 Points added!")

bot.polling(none_stop=True)
