import telebot
import pymongo
import os
import random
import datetime
import requests
import feedparser # Isse website ke naye posts fetch honge

# --- INITIALIZATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URL')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
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

# --- 1. AI EXPERT (Gemini Integration) ---
def get_ai_response(user_query):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": f"You are a Satellite expert for trackandplay.com. Answer this query concisely: {user_query}"}]}]}
        response = requests.post(url, json=payload)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "Sorry, AI abhi offline hai. Aap website check karein: trackandplay.com"

@bot.message_handler(commands=['ask_ai'])
def ai_handler(message):
    query = message.text.replace('/ask_ai', '')
    if not query:
        bot.reply_to(message, "Apna sawal likhein. Example: /ask_ai No signal on 95e")
        return
    bot.send_chat_action(message.chat.id, 'typing')
    answer = get_ai_response(query)
    bot.reply_to(message, f"🤖 **AI Expert:**\n\n{answer}")

# --- 2. SMART NOTIFICATIONS (Website Sync) ---
@bot.message_handler(commands=['check_updates'])
def sync_website(message):
    feed = feedparser.parse("https://trackandplay.com/feed/")
    latest_post = feed.entries[0]
    title = latest_post.title
    link = latest_post.link
    bot.send_message(message.chat.id, f"🆕 **Latest on TrackAndPlay:**\n\n{title}\n\n🔗 [Download/Read More]({link})", parse_mode="Markdown")

# --- 3. GROUP GROWTH (Add Members Logic) ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_and_track(message):
    for member in message.new_chat_members:
        bot.send_message(GROUP_ID, f"Welcome {member.first_name}! 🛰\nUnlock Premium TPs by adding 5 friends or watching ads (/ad).")

# --- 4. CORE REWARDS (Daily & Adsterra) ---
@bot.message_handler(commands=['daily_gift']) # Replaced /daily with /daily_gift as requested
def daily_gift(message):
    user_id = message.from_user.id
    user_data = users_col.find_one({"user_id": user_id})
    today = str(datetime.date.today())
    
    if user_data.get("last_claim") == today:
        bot.reply_to(message, "❌ Kal wapis aana!")
    else:
        ad = random.choice(AD_LINKS)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Unlock Gift 🎁", url=ad))
        bot.send_message(message.chat.id, "Gift ke liye ad dekhein fir /claim_gift likhein:", reply_markup=markup)

@bot.message_handler(commands=['claim_gift'])
def claim_gift(message):
    user_id = message.from_user.id
    users_col.update_one({"user_id": user_id}, {"$set": {"last_claim": str(datetime.date.today())}, "$inc": {"points": 25}})
    bot.send_message(message.chat.id, "✅ 25 Bonus Points added!")

# --- EXISTING COMMANDS (Wallet, Software, Leaderboard) ---
@bot.message_handler(commands=['wallet'])
def wallet(message):
    user_data = users_col.find_one({"user_id": message.from_user.id})
    bot.reply_to(message, f"💰 Wallet: {user_data['points'] if user_data else 0} Points")

bot.polling()
