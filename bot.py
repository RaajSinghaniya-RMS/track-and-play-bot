import telebot
import pymongo
import os
import random
import datetime
import requests
import feedparser
import time
import threading

# --- SETTINGS & VARIABLES ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URL')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
ADMIN_ID = 281457173
GROUP_ID = -1002657897913 # Aapka Group ID
RSS_URL = "https://trackandplay.com/feed/"

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
meta_col = db["metadata"] # Last post track karne ke liye

# --- 1. RSS AUTO-POST LOGIC (Background Task) ---
def check_rss_feed():
    while True:
        try:
            feed = feedparser.parse(RSS_URL)
            if feed.entries:
                latest_post = feed.entries[0]
                post_id = latest_post.id
                
                # Check if this post is already sent
                last_sent = meta_col.find_one({"type": "last_rss_id"})
                if not last_sent or last_sent["id"] != post_id:
                    # Naya post mila! Group mein bhejo
                    msg = f"🆕 **New Update on TrackAndPlay!**\n\n🔥 {latest_post.title}\n\n🔗 [Yahan se Download Karein]({latest_post.link})"
                    bot.send_message(GROUP_ID, msg, parse_mode="Markdown")
                    
                    # Database update karo
                    meta_col.update_one({"type": "last_rss_id"}, {"$set": {"id": post_id}}, upsert=True)
        except Exception as e:
            print(f"RSS Error: {e}")
        
        time.sleep(600) # Har 10 minute mein check karega

# RSS thread start karein
threading.Thread(target=check_rss_feed, daemon=True).start()

# --- 2. AI EXPERT (Gemini) ---
@bot.message_handler(commands=['ask_ai'])
def ask_ai(message):
    query = message.text.replace('/ask_ai', '').strip()
    if not query:
        bot.reply_to(message, "Sawal likhein. Example: /ask_ai 95e strong TP?")
        return
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": f"You are a Satellite and Receiver expert for trackandplay.com. User asks: {query}"}]}]}
        res = requests.post(url, json=payload).json()
        ans = res['candidates'][0]['content']['parts'][0]['text']
        bot.reply_to(message, f"🤖 **AI Assistant:**\n\n{ans}")
    except:
        bot.reply_to(message, "AI abhi busy hai, trackandplay.com check karein.")

# --- 3. REWARDS & ADS ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "points": 0, "last_claim": ""})
    bot.send_message(message.chat.id, "🛰 **TrackAndPlay Pro Bot**\n\n/daily_gift - Get 25 Pts\n/ad - Earn 10 Pts\n/ask_ai - Ask Expert\n/wallet - Balance")

@bot.message_handler(commands=['daily_gift'])
def daily_gift(message):
    user_id = message.from_user.id
    today = str(datetime.date.today())
    user_data = users_col.find_one({"user_id": user_id})

    if user_data.get("last_claim") == today:
        bot.reply_to(message, "❌ Aaj ka gift mil chuka hai!")
    else:
        ad = random.choice(AD_LINKS)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Unlock Points 🎁", url=ad))
        bot.send_message(message.chat.id, "Ad dekh kar /claim_gift likhein:", reply_markup=markup)

@bot.message_handler(commands=['claim_gift'])
def claim_gift(message):
    user_id = message.from_user.id
    users_col.update_one({"user_id": user_id}, {"$set": {"last_claim": str(datetime.date.today())}, "$inc": {"points": 25}})
    bot.reply_to(message, "✅ 25 Points Added!")

@bot.message_handler(commands=['ad'])
def earn_points(message):
    ad = random.choice(AD_LINKS)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Get 10 Points 🎁", url=ad))
    bot.send_message(message.chat.id, "Link open karein fir /claim likhein:", reply_markup=markup)

@bot.message_handler(commands=['claim'])
def claim_pts(message):
    users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"points": 10}})
    bot.send_message(message.chat.id, "✅ 10 Points Added!")

@bot.message_handler(commands=['wallet'])
def wallet(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    bot.reply_to(message, f"💰 Wallet: {u['points'] if u else 0} Points")

bot.polling()
