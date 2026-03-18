import telebot
import pymongo
import os
import random

# Railway Variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URL')

# Aapki Personal Details
ADMIN_ID = 281457173
GROUP_ID = -1002657897913

# Multiple Adsterra Links (Randomly chalenge earning badhane ke liye)
AD_LINKS = [
    "https://www.effectivegatecpm.com/ieik85vff?key=d58462324f8afb5e36d3fade6811af49",
    "https://www.effectivegatecpm.com/pa3wchg46?key=3d881e1e67e1030ab609a17b17695d93",
    "https://www.effectivegatecpm.com/tiq1i1nwcs?key=9929dc9f815c415d0550bb3f64c1d854",
    "https://www.effectivegatecpm.com/kb96c0gieh?key=6b9065c47c1e21512fe3e8bced33144a"
]

bot = telebot.TeleBot(BOT_TOKEN)

# MongoDB Connection
client = pymongo.MongoClient(MONGO_URI)
db = client["TrackAndPlay_Bot_New"] # Naya DB taaki purana data safe rahe
users_col = db["users"]

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "points": 0})
    
    bot.send_message(message.chat.id, "🛰 **Welcome to TrackAndPlay AI!**\n\nCommands:\n/software - Latest Updates\n/wallet - Check Points\n/ad - Earn 10 Points")

@bot.message_handler(commands=['ad'])
def earn(message):
    selected_ad = random.choice(AD_LINKS) # Random ad select hogi
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("Claim Bonus Points 🎁", url=selected_ad)
    markup.add(btn)
    bot.send_message(message.chat.id, "Ad dekhne ke baad /claim likhein:", reply_markup=markup)

@bot.message_handler(commands=['claim'])
def claim(message):
    user_id = message.from_user.id
    users_col.update_one({"user_id": user_id}, {"$inc": {"points": 10}})
    bot.send_message(message.chat.id, "✅ 10 Points Added!")

@bot.message_handler(commands=['wallet'])
def wallet(message):
    user_data = users_col.find_one({"user_id": message.from_user.id})
    points = user_data['points'] if user_data else 0
    bot.reply_to(message, f"💰 Your Wallet: {points} Points")

# Special Admin Command (Sirf aapke liye)
@bot.message_handler(commands=['addpoints'])
def add_points_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            args = message.text.split()
            target_user = int(args[1])
            amount = int(args[2])
            users_col.update_one({"user_id": target_user}, {"$inc": {"points": amount}})
            bot.reply_to(message, f"✅ User {target_user} ko {amount} points mil gaye.")
        except:
            bot.reply_to(message, "Use: /addpoints [user_id] [amount]")

bot.polling()
