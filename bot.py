# bot.py - ربات netsit.ir
import telebot
import sqlite3
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# توکن خودت رو اینجا بذار
TOKEN = '8317450115:AAFNd21Z1Cy2vhO8txQA2iid8-Y6_VZyESI'  # عوضش کن!
bot = telebot.TeleBot(TOKEN)

# آیدی عددی @ihade3 (از @userinfobot بگیر)
ADMIN_ID = 5819488865  # عوضش کن!

# دیتابیس ساده
conn = sqlite3.connect('users.db')
conn.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    daily_mb INTEGER DEFAULT 0,
    last_day TEXT,
    is_premium INTEGER DEFAULT 0
)''')
conn.commit()
conn.close()

# چک کردن ۱ گیگ رایگان
def can_download(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT daily_mb, last_day, is_premium FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if not row:
        conn.execute("INSERT INTO users (user_id, daily_mb, last_day) VALUES (?, 0, ?)", (user_id, today))
        conn.commit()
        conn.close()
        return True
    
    mb, last_day, premium = row
    
    if last_day != today:
        conn.execute("UPDATE users SET daily_mb = 0, last_day = ? WHERE user_id = ?", (today, user_id))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    if premium == 1:
        return True
    return mb < 1024  # ۱ گیگ

# اضافه کردن حجم
def add_mb(user_id, size_mb):
    conn = sqlite3.connect('users.db')
    conn.execute("UPDATE users SET daily_mb = daily_mb + ? WHERE user_id = ?", (int(size_mb), user_id))
    conn.commit()
    conn.close()

# دستور استارت
@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("تماس با ادمین", url="https://t.me/ihade3"))
    
    bot.send_message(message.chat.id,
                     "خوش آمدید کانال ما @net_sit\n\n"
                     "فایل یا لینک اینستاگرام بفرستید!\n"
                     "رایگان تا ۱ گیگ در روز",
                     reply_markup=markup)

# فایل یا ویدیو
@bot.message_handler(content_types=['document', 'video'])
def handle_file(message):
    user_id = message.from_user.id
    
    if not can_download(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("خرید اشتراک", url="https://t.me/ihade3"))
        bot.reply_to(message, "حجم رایگان تموم شد!\nبرای خرید اشتراک به ادمین پیام بده:", reply_markup=markup)
        return
    
    file_info = bot.get_file(message.document.file_id if message.document else message.video.file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
    
    size_mb = (message.document.file_size if message.document else message.video.file_size) / (1024*1024)
    add_mb(user_id, size_mb)
    
    bot.reply_to(message, f"فایل آماده شد!\nحجم: {size_mb:.1f} مگ\nلینک دانلود:\n{file_url}")

# لینک اینستاگرام
@bot.message_handler(func=lambda m: 'instagram.com' in m.text)
def instagram(message):
    if not can_download(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("خرید اشتراک", url="https://t.me/ihade3"))
        bot.reply_to(message, "حجم رایگان تموم شد!\nبرای خرید به ادمین پیام بده:", reply_markup=markup)
        return
    
    bot.reply_to(message, "در حال دانلود از اینستاگرام... (فعلاً لینک می‌دم)\n" + message.text)

# دستورات ادمین
@bot.message_handler(commands=['add_week', 'add_month', 'add_year', 'remove'])
def admin_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        cmd = message.text.split()[0]
        username = message.text.split()[1].replace('@', '')
        
        conn = sqlite3.connect('users.db')
        if cmd in ['/add_week', '/add_month', '/add_year']:
            conn.execute("UPDATE users SET is_premium = 1 WHERE username = ?", (username,))
            bot.reply_to(message, f"اشتراک برای @{username} فعال شد!")
        elif cmd == '/remove':
            conn.execute("UPDATE users SET is_premium = 0 WHERE username = ?", (username,))
            bot.reply_to(message, f"اشتراک @{username} قطع شد!")
        conn.commit()
        conn.close()
    except:
        bot.reply_to(message, "خطا! مثلاً بنویس: /add_week @ali")

print("ربات روشن شد!")
bot.infinity_polling()
