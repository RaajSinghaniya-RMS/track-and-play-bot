import telebot
import pymongo
import os
import random
import datetime

# Railway Variables (Inhe Railway dashboard mein set karein)
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URL')

# Aapki Personal Details
ADMIN_ID = 281457173
GROUP_ID = -1002657897913

# Aapke Multiple Adsterra Links
AD_LINKS = [
    "https://www.effectivegatecpm.com/ieik85vff?key=d58462324f8afb5e36d3fade6811af49",
    "https://www.effectivegatecpm.com/pa3wchg46?key=3d881e1e67e1030ab609a17b17695d93",
    "https://www.effectivegatecpm.com/tiq1i1nwcs?key=9929dc9f815c415d0550bb3f64c1d854",
    "https://www.effectivegatecpm.com/kb96c0gieh?key=6b9065c47c1e21512fe3e8bced33144a"
]

bot = telebot.TeleBot(BOT_TOKEN)

# MongoDB Connection
client = pymongo.MongoClient(MONGO_URI)
db = client["TrackAndPlay_Bot_New"]
users_col = db["users"]

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "points": 0, "last_claim": ""})
    
    bot.send_message(message.chat.id, "🛰 **Welcome to TrackAndPlay AI Bot!**\n\nAb aap group mein active reh kar aur ads dekh kar Free Recharges jeet sakte hain!\n\n🔹 /daily - Get Daily 20 Points\n🔹 /ad - Earn 10 Points (Unlimited)\n🔹 /wallet - Check Your Points\n🔹 /leaderboard - See Top Players\n🔹 /software - Latest Receiver Updates")

@bot.message_handler(commands=['daily'])
def daily_bonus(message):
    user_id = message.from_user.id
    user_data = users_col.find_one({"user_id": user_id})
    
    today = str(datetime.date.today())
    last_claim = user_data.get("last_claim", "")

    if last_claim == today:
        bot.reply_to(message, "❌ Aapne aaj ka bonus pehle hi le liya hai. Kal wapis aana!")
    else:
        selected_ad = random.choice(AD_LINKS)
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton("Unlock Daily Bonus 🎁", url=selected_ad)
        markup.add(btn)
        bot.send_message(message.chat.id, "Daily 20 Points lene ke liye niche click karein aur fir /claim_daily likhein:", reply_markup=markup)

@bot.message_handler(commands=['claim_daily'])
def claim_daily(message):
    user_id = message.from_user.id
    user_data = users_col.find_one({"user_id": user_id})
    today = str(datetime.date.today())
    
    # Check again if already claimed to prevent cheating
    if user_data.get("last_claim") == today:
        bot.reply_to(message, "❌ Cheat attempts allowed nahi hain!")
        return

    users_col.update_one({"user_id": user_id}, {"$set": {"last_claim": today}, "$inc": {"points": 20}})
    bot.send_message(message.chat.id, "✅ Mubarak ho! 20 Bonus Points add ho gaye hain.")

@bot.message_handler(commands=['ad'])
def earn(message):
    selected_ad = random.choice(AD_LINKS)
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("Claim 10 Points 🎁", url=selected_ad)
    markup.add(btn)
    bot.send_message(message.chat.id, "Ad dekhne ke baad /claim likhein:", reply_markup=markup)

@bot.message_handler(commands=['claim'])
def claim(message):
    user_id = message.from_user.id
    users_col.update_one({"user_id": user_id}, {"$inc": {"points": 10}})
    bot.send_message(message.chat.id, "✅ 10 Points aapke wallet mein add ho gaye hain!")

@bot.message_handler(commands=['wallet'])
def wallet(message):
    user_data = users_col.find_one({"user_id": message.from_user.id})
    points = user_data['points'] if user_data else 0
    bot.reply_to(message, f"💰 Aapka Balance: **{points} Points**\n\nRank badhane ke liye /ad use karein.")

@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    top_users = users_col.find().sort("points", -1).limit(10)
    text = "🏆 **TrackAndPlay Top 10 Players** 🏆\n\n"
    for i, user in enumerate(top_users, 1):
        text += f"{i}. User: `{user['user_id']}` — {user['points']} Pts\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['software'])
def software_menu(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btn1 = telebot.types.InlineKeyboardButton("GX6605s Updates", url="https://trackandplay.com/category/gx6605s/")
    btn2 = telebot.types.InlineKeyboardButton("Sunplus Software", url="https://trackandplay.com/category/sunplus/")
    btn3 = telebot.types.InlineKeyboardButton("TP List", url="https://trackandplay.com/")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "🛰 **Apna Receiver Model Select Karein:**", reply_markup=markup)

# Admin command
@bot.message_handler(commands=['addpoints'])
def add_points_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            args = message.text.split()
            target_user = int(args[1])
            amount = int(args[2])
            users_col.update_one({"user_id": target_user}, {"$inc": {"points": amount}})
            bot.reply_to(message, f"✅ User {target_user} ko {amount} points diye gaye.")
        except:
            bot.reply_to(message, "Usage: /addpoints [user_id] [amount]")

bot.polling()
