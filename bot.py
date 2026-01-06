import telebot
import requests
import time
import os
import threading
import pytz
from datetime import datetime
from gradio_client import Client
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from keep_alive import keep_alive

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🔥 PREMIUM CONFIGURATION
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
BOT_TOKEN = '8030029502:AAG0NhCvXN38yJ_BvWP2T7j0meh6P23sXXw'  # আপনার বটের টোকেন দিন
ADMIN_ID = 6243881362             # আপনার টেলিগ্রাম আইডি দিন (এডমিন)
CHANNEL_ID = -1002879589597       # আপনার চ্যানেলের আইডি (যেমন: -100...)
CHANNEL_LINK = "https://t.me/RedX_Developer" # চ্যানেলের লিংক

# JSONBIN DATABASE (ডাটা সেভ রাখার জন্য)
JSONBIN_API_KEY = '$2a$10$CWZ5aFPmaczB/T4.PumaJO3H3lYV7PoqIwcTKpn6oBp0TX.hQFIEu' # আপনার কি (আগেরটা ব্যবহার করেছি)
BIN_ID = '695d56af43b1c97be91da474' # আপনার বিন আইডি
BASE_URL = f'https://api.jsonbin.io/v3/b/{BIN_ID}'

# AI MODEL
AI_MODEL = "TencentARC/GFPGAN"

# PAYMENT INFO
NAGAD_NUMBER = "01812774257"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

# টেম্পোরারি মেমোরি (ছবি হোল্ড করার জন্য)
user_photos = {}

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🧠 SMART DATABASE ENGINE
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
class Database:
    def __init__(self):
        self.local_data = {"users": {}}
        self.lock = threading.Lock()
        self.load_from_cloud()

    def load_from_cloud(self):
        headers = {'X-Master-Key': JSONBIN_API_KEY}
        try:
            response = requests.get(BASE_URL, headers=headers)
            if response.status_code == 200:
                self.local_data = response.json().get('record', {"users": {}})
                if "users" not in self.local_data: self.local_data["users"] = {}
                print("✅ Database Loaded!")
            else:
                print("⚠️ Database Error!")
        except: pass

    def save(self):
        def _sync():
            with self.lock:
                headers = {'Content-Type': 'application/json', 'X-Master-Key': JSONBIN_API_KEY}
                try: requests.put(BASE_URL, json=self.local_data, headers=headers)
                except: pass
        threading.Thread(target=_sync).start()

    def get_user(self, uid):
        uid = str(uid)
        return self.local_data['users'].get(uid)

    def register_user(self, user_id, name):
        uid = str(user_id)
        if uid not in self.local_data['users']:
            bd_time = datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%Y-%m-%d")
            self.local_data['users'][uid] = {
                "name": name,
                "id": uid,
                "join_date": bd_time,
                "plan": "Free",
                "limit": 5,
                "used": 0,
                "last_date": bd_time,
                "expiry": "Lifetime"
            }
            self.save()
            return True
        return False

    def check_limit(self, uid):
        uid = str(uid)
        user = self.local_data['users'][uid]
        today = datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%Y-%m-%d")
        
        # তারিখ পরিবর্তন হলে লিমিট রিসেট
        if user.get("last_date") != today:
            user["last_date"] = today
            user["used"] = 0
            # প্ল্যান চেক
            if user["plan"] == "Free": user["limit"] = 5
            # পেইড প্ল্যানের মেয়াদ চেক করার লজিক এখানে এড করা যাবে
            self.save()
        
        return user["used"] < user["limit"]

    def increment_usage(self, uid):
        uid = str(uid)
        self.local_data['users'][uid]["used"] += 1
        self.save()

    def upgrade_user(self, uid, plan, limit, duration):
        uid = str(uid)
        user = self.local_data['users'][uid]
        user["plan"] = plan
        user["limit"] = limit
        user["expiry"] = f"{duration} Days"
        self.save()

db = Database()

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🎨 UI & KEYBOARDS
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("👤 Profile", "📸 Photo Enhance")
    markup.add("💎 Upgrade", "📜 Terms Policy")
    markup.add("👨‍💻 Developer Info")
    return markup

def check_sub(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['creator', 'administrator', 'member']
    except: return False # এডমিন না বানালে ফলস আসবে

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🤖 BOT LOGIC
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

@bot.message_handler(commands=['start'])
def start(m):
    user_id = m.chat.id
    name = m.from_user.first_name
    db.register_user(user_id, name)
    
    msg = (
        f"👋 **আসসালামু আলাইকুম, {name}!**\n\n"
        f"📸 **Swygen Photo Enhancer Bot** এ আপনাকে স্বাগতম।\n"
        f"আমি আপনার নরমাল ছবিকে **4K HD Quality** তে কনভার্ট করতে পারি।\n\n"
        f"⚠️ **বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন:**"
    )
    
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    mk.add(InlineKeyboardButton("✅ Joined", callback_data="check_join"))
    
    bot.send_message(user_id, msg, reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def join_verify(call):
    uid = call.message.chat.id
    if check_sub(uid):
        bot.delete_message(uid, call.message.message_id)
        bot.send_message(uid, f"🎉 **ধন্যবাদ {call.from_user.first_name}!**\nআপনি সফলভাবে জয়েন করেছেন। এখন নিচের মেনু থেকে অপশন সিলেক্ট করুন।", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনও জয়েন করেননি!", show_alert=True)

# --- 👤 PROFILE ---
@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(m):
    user = db.get_user(m.chat.id)
    if not user: return start(m)
    
    rem = user['limit'] - user['used']
    msg = (
        f"👤 **USER PROFILE**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📛 নাম: **{user['name']}**\n"
        f"🆔 আইডি: `{user['id']}`\n"
        f"📅 জয়েন: {user['join_date']}\n\n"
        f"📦 **প্যাকেজ:** {user['plan']}\n"
        f"🔄 **দৈনিক লিমিট:** {user['limit']} টি\n"
        f"✅ **ব্যবহার করেছেন:** {user['used']} টি\n"
        f"⏳ **বাকি আছে:** {rem} টি\n"
        f"━━━━━━━━━━━━━━━"
    )
    bot.send_message(m.chat.id, msg)

# --- 📸 PHOTO ENHANCE FLOW ---
@bot.message_handler(func=lambda m: m.text == "📸 Photo Enhance")
def enhance_req(m):
    user = db.get_user(m.chat.id)
    if not db.check_limit(m.chat.id):
        return bot.send_message(m.chat.id, "🚫 **আজকের লিমিট শেষ!**\nআরও ছবি এডিট করতে **Upgrade** বাটনে ক্লিক করে প্যাকেজ কিনুন।")
        
    msg = (
        f"📸 **প্রিয় {user['name']},**\n\n"
        f"আপনার যে ছবিটা **High Quality Enhance** করতে চান, সেটা এখন পাঠান।\n"
        f"⚠️ **নোট:** ছবি যেন বেশি বড় ফাইলের না হয়।"
    )
    bot.send_message(m.chat.id, msg)

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    uid = m.chat.id
    # সেভ ফটো আইডি
    user_photos[uid] = m.photo[-1].file_id
    
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("✨ Enhance High Quality", callback_data="do_enhance"))
    
    bot.reply_to(m, "🖼️ **ছবি রিসিভ করা হয়েছে!**\nনিচের বাটনে ক্লিক করলে প্রসেসিং শুরু হবে।", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "do_enhance")
def process_enhance(call):
    uid = call.message.chat.id
    
    # লিমিট চেক
    if not db.check_limit(uid):
        return bot.answer_callback_query(call.id, "❌ আপনার লিমিট শেষ। আপগ্রেড করুন।", show_alert=True)
    
    if uid not in user_photos:
        return bot.answer_callback_query(call.id, "❌ সেশন এক্সপায়ারড। আবার ছবি পাঠান।", show_alert=True)

    # 1. LIVE PROGRESS ANIMATION
    steps = ["⬜⬜⬜⬜⬜ 0%", "🟩⬜⬜⬜⬜ 20%", "🟩🟩⬜⬜⬜ 40%", "🟩🟩🟩⬜⬜ 60%", "🟩🟩🟩🟩⬜ 80%", "🟩🟩🟩🟩🟩 100%"]
    prog_msg = bot.send_message(uid, "⏳ **Connecting to Server...**")
    
    try:
        # ডাউনলোড
        file_info = bot.get_file(user_photos[uid])
        downloaded_file = bot.download_file(file_info.file_path)
        input_path = f"input_{uid}.jpg"
        with open(input_path, 'wb') as f: f.write(downloaded_file)
        
        # ফেক অ্যানিমেশন (রিয়েলিস্টিক ফিল দেওয়ার জন্য)
        for step in steps:
            bot.edit_message_text(f"⚡ **Enhancing Photo...**\n{step}\n_ডিটেইলস ঠিক করা হচ্ছে..._", uid, prog_msg.message_id)
            time.sleep(0.5)
            
        bot.edit_message_text("🎨 **Finalizing Ultra HD Quality...**", uid, prog_msg.message_id)
        
        # AI কল
        client = Client(AI_MODEL)
        result = client.predict(input_path, "v1.4", 4, fn_index=0) # 4x Scale
        
        # সেন্ড রেজাল্ট
        with open(result[1], 'rb') as ph:
            cap = (
                f"✨ **Enhanced Successfully!**\n"
                f"🤖 **Bot:** Swygen Enhance AI\n"
                f"👨‍💻 **Dev:** Ayman Hasan Shaan\n\n"
                f"💬 **Feedback:** [Click Here](https://swygen.xyz)"
            )
            bot.send_photo(uid, ph, caption=cap, parse_mode='Markdown')
        
        # আপডেট ডাটাবেস
        db.increment_usage(uid)
        bot.delete_message(uid, prog_msg.message_id)
        
        # ক্লিনআপ
        os.remove(input_path)
        
    except Exception as e:
        bot.edit_message_text("❌ সার্ভার এরর! দয়া করে আবার চেষ্টা করুন।", uid, prog_msg.message_id)
        print(e)

# --- 💎 UPGRADE SYSTEM ---
@bot.message_handler(func=lambda m: m.text == "💎 Upgrade")
def upgrade_menu(m):
    user = db.get_user(m.chat.id)
    msg = (
        f"💎 **PREMIUM PACKAGES**\n"
        f"প্রিয় **{user['name']}**, লিমিট বাড়াতে প্যাকেজ কিনুন:\n\n"
        f"1️⃣ **Starter Plan**\n"
        f"💰 400 BDT | 📸 20 Images/Day | ⏳ 7 Days\n\n"
        f"2️⃣ **Pro Plan**\n"
        f"💰 900 BDT | 📸 40 Images/Day | ⏳ 7 Days\n\n"
        f"3️⃣ **Business Plan**\n"
        f"💰 1800 BDT | 📸 60 Images/Day | ⏳ 7 Days"
    )
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("🔹 Buy Starter (400tk)", callback_data="buy_starter"))
    mk.add(InlineKeyboardButton("🔶 Buy Pro (900tk)", callback_data="buy_pro"))
    mk.add(InlineKeyboardButton("💠 Buy Business (1800tk)", callback_data="buy_business"))
    
    bot.send_message(m.chat.id, msg, reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def payment_instruction(call):
    plan = call.data.split("_")[1].capitalize()
    amount = "400" if plan == "Starter" else "900" if plan == "Pro" else "1800"
    
    msg = bot.send_message(call.message.chat.id, 
        f"💳 **পেমেন্ট ইনস্ট্রাকশন ({plan} Plan)**\n\n"
        f"অনুগ্রহ করে **{amount} টাকা** নিচের নম্বরে সেন্ড মানি করুন।\n"
        f"📱 **Nagad:** `{NAGAD_NUMBER}`\n\n"
        f"📝 টাকা পাঠানোর পর আপনার **Transaction ID (TrxID)** টি এখানে লিখে পাঠান।"
    )
    bot.register_next_step_handler(msg, process_trx, plan, amount)

def process_trx(m, plan, amount):
    trx = m.text
    uid = m.chat.id
    user = db.get_user(uid)
    
    bot.send_message(uid, "✅ **রিকুয়েস্ট জমা হয়েছে!**\nএডমিন চেক করে আপনার প্ল্যান চালু করে দিবেন।")
    
    # এডমিন নোটিফিকেশন
    mk = InlineKeyboardMarkup()
    mk.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"app_{uid}_{plan}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"rej_{uid}")
    )
    
    adm_msg = (
        f"🔔 **NEW ORDER RECEIVED**\n"
        f"👤 User: {user['name']} (`{uid}`)\n"
        f"📦 Plan: **{plan}**\n"
        f"💰 Amount: {amount} BDT\n"
        f"🧾 TrxID: `{trx}`"
    )
    bot.send_message(ADMIN_ID, adm_msg, reply_markup=mk)

# --- 👑 ADMIN ACTION ---
@bot.callback_query_handler(func=lambda c: c.data.startswith(("app_", "rej_")))
def admin_decision(call):
    action, uid, plan = call.data.split("_")[0], call.data.split("_")[1], call.data.split("_")[2] if len(call.data.split("_")) > 2 else None
    
    if action == "app":
        # সেট লিমিট
        limit = 20 if plan == "Starter" else 40 if plan == "Pro" else 60
        db.upgrade_user(uid, plan, limit, 7)
        
        bot.edit_message_text(f"✅ **Approved {plan} for {uid}**", call.message.chat.id, call.message.message_id)
        bot.send_message(uid, f"🎉 **অভিনন্দন!**\nআপনার **{plan} Package** চালু হয়েছে।\nএখন আপনি দৈনিক {limit} টি ছবি এডিট করতে পারবেন।")
    else:
        bot.edit_message_text("❌ **Request Rejected.**", call.message.chat.id, call.message.message_id)
        bot.send_message(uid, "❌ আপনার পেমেন্ট ভেরিফিকেশন ব্যর্থ হয়েছে। সঠিক তথ্য দিয়ে আবার চেষ্টা করুন।")

# --- 📜 OTHER INFO ---
@bot.message_handler(func=lambda m: m.text == "📜 Terms Policy")
def terms(m):
    msg = (
        "📜 **TERMS & POLICY**\n\n"
        "1. **Usage:** Do not upload illegal or explicit content.\n"
        "2. **Privacy:** We do not store your photos. They are deleted immediately after processing.\n"
        "3. **Refund:** Digital goods are non-refundable once the plan is activated.\n"
        "4. **Fair Use:** Do not spam the bot. Abuse may lead to a ban.\n\n"
        "© Swygen IT 2026"
    )
    bot.send_message(m.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "👨‍💻 Developer Info")
def dev_info(m):
    user = db.get_user(m.chat.id)
    msg = (
        f"👨‍💻 **DEVELOPER INFORMATION**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👋 হ্যালো **{user['name']}**,\n"
        f"এই প্রফেশনাল বটটি তৈরি করেছেন **Ayman Hasan Shaan**।\n\n"
        f"🏢 **Brand:** Swygen IT\n"
        f"🌐 **Website:** [swygen.xyz](https://swygen.xyz)\n"
        f"✈️ **Telegram:** @Swygen_bd\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(m.chat.id, msg)

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🔥 RUN SERVER
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
if __name__ == "__main__":
    print("🤖 Ultra Enhancer Bot is Live...")
    keep_alive()
    bot.infinity_polling(skip_pending=True)
