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
RSS_URL = "https://trackandplay.com/feed/"

# Professional Category Mapping
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

# --- 1. ADVANCED AI LOGIC (English & Website Context) ---
def get_ai_response(user_query, user_name):
    # Fetching latest website content before replying
    try:
        feed = feedparser.parse(RSS_URL)
        latest_info = "\n".join([f"- {e.title}: {e.link}" for e in feed.entries[:8]])
    except:
        latest_info = "Check trackandplay.com for latest updates."

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        
        system_instruction = f"""
        You are the 'TrackAndPlay AI Assistant', a Senior Satellite & DTH Expert.
        User Name: {user_name}.
        Language: Strictly English (Global Users).
        
        Context from trackandplay.com:
        {latest_info}

        Rules:
        1. Be professional, helpful, and human-like.
        2. If a user asks for software (GX6605s, Independent TV, etc.), check the list above. If found, provide the direct link.
        3. For TP/Signal queries, ask for their Satellite name, Dish size, and Region first.
        4. Never say 'search on website'. Instead, provide a solution or a specific category link.
        5. Use bold text and bullet points for better UI.
        """
        
        payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Query: {user_query}"}]}]}
        response = requests.post(url, json=payload).json()
        return response['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"Hello {user_name}, I'm currently processing multiple requests. Please visit **trackandplay.com** for instant technical guides."

# --- 2. RSS AUTO-POSTER ---
def check_rss_feed():
    while True:
        try:
            feed = feedparser.parse(RSS_URL)
            if feed.entries:
                latest = feed.entries[0]
                last_sent = meta_col.find_one({"type": "last_rss_id"})
                if not last_sent or last_sent["id"] != latest.id:
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(telebot.types.InlineKeyboardButton("📥 Download Software", url=latest.link))
                    msg = f"🛰 **NEW UPDATE DETECTED**\n\n📝 **Title:** {latest.title}\n\nCheck the latest software update below:"
                    bot.send_message(GROUP_ID, msg, reply_markup=markup, parse_mode="Markdown")
                    meta_col.update_one({"type": "last_rss_id"}, {"$set": {"id": latest.id}}, upsert=True)
        except: pass
        time.sleep(600)

threading.Thread(target=check_rss_feed, daemon=True).start()

# --- 3. AUTO-COMMANDS (Every 2 Hours) ---
def post_commands():
    while True:
        time.sleep(7200)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Explore Website", url="https://trackandplay.com"))
        txt = "🤖 **HOW TO USE TRACKANDPLAY BOT?**\n\n💰 `/daily_gift` - Claim 25 Pts\n💎 `/ad` - Earn 10 Pts\n💳 `/wallet` - Check Balance\n🏆 `/leaderboard` - Top Users\n\n💡 **Tip:** Just type your box name (e.g., Solid) to get direct links!"
        try: bot.send_message(GROUP_ID, txt, reply_markup=markup, parse_mode="Markdown")
        except: pass

threading.Thread(target=post_commands, daemon=True).start()

# --- 4. MESSAGE HANDLERS ---

@bot.message_handler(commands=['help', 'start'])
def send_help(message):
    user_name = message.from_user.first_name
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🎁 Daily Gift", callback_data="gift"),
        telebot.types.InlineKeyboardButton("💳 Wallet", callback_data="wallet"),
        telebot.types.InlineKeyboardButton("🛰 TP List", url="https://trackandplay.com/category/tp-list/"),
        telebot.types.InlineKeyboardButton("🌐 Website", url="https://trackandplay.com")
    )
    
    welcome_text = (
        f"🛰 **WELCOME TO TRACKANDPLAY AI**\n\n"
        f"Hello **{user_name}**! I am your global Satellite Assistant.\n\n"
        "**Available Services:**\n"
        "• Earn points via ads and daily gifts.\n"
        "• Get latest software for GX6605s, Sunplus, etc.\n"
        "• Real-time AI Technical Support.\n\n"
        "Click the buttons below or type your query!"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text == "/":
        send_help(message)
        return

    user_text = message.text.lower()
    user_name = message.from_user.first_name

    # Check Direct Mapping
    for key, link in SITE_MAP.items():
        if key in user_text:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🔗 Open Download Page", url=link))
            bot.reply_to(message, f"✅ **{user_name}**, here is the direct link for **{key.upper()}**:", reply_markup=markup, parse_mode="Markdown")
            return

    # Technical AI Expert (Global English)
    tech_keys = ['tp', 'signal', 'frequency', 'dish', 'issue', 'problem', 'not working', 'biss', 'software']
    if any(word in user_text for word in tech_keys):
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_ai_response(message.text, user_name)
        bot.reply_to(message, response, parse_mode="Markdown")
        return

    if message.chat.type == 'private':
        bot.reply_to(message, "I didn't quite get that. Type `/help` to see all commands!")

# --- 5. REWARD SYSTEM ---
@bot.message_handler(commands=['daily_gift'])
def daily_gift(message):
    ad = random.choice(AD_LINKS)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔓 Unlock 25 Points", url=ad))
    bot.send_message(message.chat.id, "Click below to open the ad, then type `/claim_gift` to receive points:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['claim_gift'])
def claim_gift(message):
    today = str(datetime.date.today())
    users_col.update_one({"user_id": message.from_user.id}, {"$set": {"last_claim": today}, "$inc": {"points": 25}}, upsert=True)
    bot.reply_to(message, "🎉 **Success!** 25 Points have been added to your wallet.")

bot.polling(none_stop=True)
