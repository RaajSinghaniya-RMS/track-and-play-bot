import telebot
import pymongo
import os

# Railway se variables uthana
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URL')
AD_LINK = os.getenv('AD_LINK')

bot = telebot.TeleBot(BOT_TOKEN)

# MongoDB Connection (Existing Cluster, New Database)
client = pymongo.MongoClient(MONGO_URI)
db = client["TrackAndPlay_Bot"] # <--- Ye naya folder banayega, purana data safe rahega
users_col = db["users"]

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "points": 0})
    
    bot.send_message(message.chat.id, "🛰 **Welcome to TrackAndPlay AI!**\n\nCommands:\n/software - Latest Updates\n/wallet - Check Points\n/ad - Earn 10 Points")

@bot.message_handler(commands=['software'])
def software_menu(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    # Aapki website ke categories
    btn1 = telebot.types.InlineKeyboardButton("GX6605s", url="https://trackandplay.com/category/gx6605s/")
    btn2 = telebot.types.InlineKeyboardButton("Sunplus", url="https://trackandplay.com/category/sunplus/")
    btn3 = telebot.types.InlineKeyboardButton("TP List", url="https://trackandplay.com/")
    
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "🛰 **Select Category:**", reply_markup=markup)

@bot.message_handler(commands=['ad'])
def earn(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("Claim Bonus Points", url=AD_LINK)
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
    bot.reply_to(message, f"💰 Your Wallet: {user_data['points']} Points")

bot.polling()
