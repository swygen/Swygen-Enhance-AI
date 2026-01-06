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
BOT_TOKEN = '8030029502:AAG0NhCvXN38yJ_BvWP2T7j0meh6P23sXXw'
ADMIN_ID = 6243881362
CHANNEL_ID = -1002879589597
CHANNEL_LINK = "https://t.me/RedX_Developer"

# JSONBIN DATABASE CONFIG
JSONBIN_API_KEY = '$2a$10$CWZ5aFPmaczB/T4.PumaJO3H3lYV7PoqIwcTKpn6oBp0TX.hQFIEu'
BIN_ID = '695d56af43b1c97be91da474'
BASE_URL = f'https://api.jsonbin.io/v3/b/{BIN_ID}'

# 🔥 NEW AI MODEL (CodeFormer - More Stable & Better Detail)
AI_MODEL = "sczhou/CodeFormer"

# PAYMENT INFO
NAGAD_NUMBER = "01812774257"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')
user_photos = {}

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🧠 DATABASE ENGINE
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
                print("✅ Database Connected!")
            else:
                print("⚠️ Database Error - Using Local Memory")
        except: pass

    def save(self):
        def _sync():
            with self.lock:
                headers = {'Content-Type': 'application/json', 'X-Master-Key': JSONBIN_API_KEY}
                try: requests.put(BASE_URL, json=self.local_data, headers=headers)
                except: pass
        threading.Thread(target=_sync).start()

    def get_user(self, uid):
        return self.local_data['users'].get(str(uid))

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
        user = self.local_data['users'].get(uid)
        if not user: return False
        
        today = datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%Y-%m-%d")
        if user.get("last_date") != today:
            user["last_date"] = today
            user["used"] = 0
            if user["plan"] == "Free": user["limit"] = 5
            self.save()
        return user["used"] < user["limit"]

    def increment_usage(self, uid):
        self.local_data['users'][str(uid)]["used"] += 1
        self.save()

    def upgrade_user(self, uid, plan, limit, duration):
        uid = str(uid)
        if uid in self.local_data['users']:
            self.local_data['users'][uid]["plan"] = plan
            self.local_data['users'][uid]["limit"] = limit
            self.local_data['users'][uid]["expiry"] = f"{duration} Days"
            self.save()

db = Database()

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🎨 UI FUNCTIONS
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # বাটনগুলোর নাম হুবহু হ্যান্ডেলারের সাথে মিলতে হবে
    markup.add("👤 Profile", "📸 Photo Enhance")
    markup.add("💎 Upgrade", "📜 Terms Policy")
    markup.add("👨‍💻 Developer Info") 
    return markup

def check_sub(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['creator', 'administrator', 'member']
    except: return False # চ্যানেল আইডি ভুল থাকলে ফলস আসবে

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🤖 BOT HANDLERS
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

@bot.message_handler(commands=['start'])
def start(m):
    user_id = m.chat.id
    name = m.from_user.first_name
    db.register_user(user_id, name)
    
    msg = (
        f"👋 **স্বাগতম {name}!**\n\n"
        f"📸 **Swygen Ultra Enhancer** এ আপনাকে স্বাগতম।\n"
        f"আমি আপনার নরমাল ছবিকে **4K Quality** তে কনভার্ট করতে পারি।\n\n"
        f"👇 কাজ শুরু করতে জয়েন করুন:"
    )
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    mk.add(InlineKeyboardButton("✅ Check Joined", callback_data="check_join"))
    bot.send_message(user_id, msg, reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def join_verify(call):
    uid = call.message.chat.id
    if check_sub(uid):
        bot.delete_message(uid, call.message.message_id)
        bot.send_message(uid, "🎉 **ভেরিফিকেশন সফল!**\nএখন নিচের মেনু ব্যবহার করুন।", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনও চ্যানেলে জয়েন করেননি!", show_alert=True)

# --- 📸 ENHANCE LOGIC (UPDATED FOR STABILITY) ---
@bot.message_handler(func=lambda m: "Photo Enhance" in m.text)
def enhance_req(m):
    if not db.check_limit(m.chat.id):
        return bot.send_message(m.chat.id, "🚫 **আজকের লিমিট শেষ!**\nআপগ্রেড করতে '💎 Upgrade' চাপুন।")
    bot.send_message(m.chat.id, "🖼️ **আপনার ছবিটি পাঠান:**\n(আমি সেটিকে High Quality তে কনভার্ট করে দেব)")

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    uid = m.chat.id
    user_photos[uid] = m.photo[-1].file_id
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("✨ Start Enhancing (4K)", callback_data="do_enhance"))
    bot.reply_to(m, "📸 **ছবি রিসিভ করেছি!**\nHigh Quality করতে নিচের বাটনে চাপুন।", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "do_enhance")
def process_enhance(call):
    uid = call.message.chat.id
    
    if not db.check_limit(uid):
        return bot.answer_callback_query(call.id, "❌ লিমিট শেষ!", show_alert=True)

    prog_msg = bot.send_message(uid, "⏳ **সার্ভারে কানেক্ট করা হচ্ছে...**")
    
    try:
        # Download
        file_info = bot.get_file(user_photos[uid])
        downloaded_file = bot.download_file(file_info.file_path)
        input_path = f"input_{uid}.jpg"
        with open(input_path, 'wb') as f: f.write(downloaded_file)
        
        bot.edit_message_text("⚡ **AI প্রসেসিং চলছে (CodeFormer)...**\n_ফেস ডিটেইলস ঠিক করা হচ্ছে..._", uid, prog_msg.message_id)
        
        # 🔥 UPDATED AI CLIENT (CodeFormer)
        # এটি GFPGAN এর চেয়ে বেশি স্টেবল
        client = Client(AI_MODEL)
        
        # CodeFormer Parameters:
        # 1. Background Enhance: True
        # 2. Face Upsample: True
        # 3. Upscale: 2 (High Quality but safe from timeout)
        # 4. Fidelity: 0.7 (Balance between reality and enhancement)
        result = client.predict(
            input_path, 
            True,       
            True,       
            2,          
            0.7,        
            fn_index=0  
        )
        
        # Result handling
        output_image = result[0] if isinstance(result, (list, tuple)) else result
        
        with open(output_image, 'rb') as ph:
            cap = f"✨ **Enhanced by Swygen AI**\n💎 Quality: Premium HD"
            bot.send_photo(uid, ph, caption=cap)
            
        db.increment_usage(uid)
        bot.delete_message(uid, prog_msg.message_id)
        os.remove(input_path)
        
    except Exception as e:
        # ERROR HANDLING
        print(f"❌ ERROR: {e}") 
        bot.edit_message_text(f"⚠️ **সার্ভার একটু ব্যস্ত!**\nদয়া করে ১০ সেকেন্ড পর আবার চেষ্টা করুন।\n(ফ্রি সার্ভারে মাঝে মাঝে চাপ থাকে)", uid, prog_msg.message_id)
        try: os.remove(input_path)
        except: pass

# --- 👤 PROFILE ---
@bot.message_handler(func=lambda m: "Profile" in m.text)
def profile(m):
    user = db.get_user(m.chat.id)
    if not user: return
    msg = (
        f"👤 **{user['name']} এর প্রোফাইল**\n\n"
        f"📦 প্ল্যান: **{user['plan']}**\n"
        f"🔄 আজকের বাকি: **{user['limit'] - user['used']}** টি\n"
        f"📅 জয়েনিং: {user['join_date']}"
    )
    bot.send_message(m.chat.id, msg)

# --- 👨‍💻 DEVELOPER INFO (FIXED) ---
# "in" অপারেটর ব্যবহার করায় বাটন এখন কাজ করবে ১০০%
@bot.message_handler(func=lambda m: "Developer Info" in m.text)
def dev_info(m):
    msg = (
        f"👨‍💻 **DEVELOPER INFO**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** Ayman Hasan Shaan\n"
        f"🚀 **Brand:** Swygen IT\n"
        f"🌐 **Web:** [swygen.xyz](https://swygen.xyz)\n"
        f"✈️ **Telegram:** @Swygen_bd\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Made with ❤️ by Swygen IT"
    )
    bot.send_message(m.chat.id, msg, disable_web_page_preview=True)

# --- 💎 UPGRADE & TERMS ---
@bot.message_handler(func=lambda m: "Upgrade" in m.text)
def upgrade_menu(m):
    msg = (
        f"💎 **PREMIUM PACKAGES**\n\n"
        f"1️⃣ **Starter:** 400tk (20 Pics/Day)\n"
        f"2️⃣ **Pro:** 900tk (40 Pics/Day)\n"
        f"3️⃣ **Business:** 1800tk (60 Pics/Day)"
    )
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("Buy Starter", callback_data="buy_Starter"))
    mk.add(InlineKeyboardButton("Buy Pro", callback_data="buy_Pro"))
    mk.add(InlineKeyboardButton("Buy Business", callback_data="buy_Business"))
    bot.send_message(m.chat.id, msg, reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def payment(call):
    plan = call.data.split("_")[1]
    msg = bot.send_message(call.message.chat.id, f"💳 **{plan} Plan** এর জন্য পেমেন্ট করুন:\n\n📱 **Nagad:** `{NAGAD_NUMBER}`\n\nটাকা পাঠিয়ে TrxID দিন:")
    bot.register_next_step_handler(msg, verify_trx, plan)

def verify_trx(m, plan):
    bot.send_message(m.chat.id, "✅ রিকোয়েস্ট এডমিনের কাছে পাঠানো হয়েছে।")
    adm_mk = InlineKeyboardMarkup()
    adm_mk.add(InlineKeyboardButton("Approve", callback_data=f"app_{m.chat.id}_{plan}"), InlineKeyboardButton("Reject", callback_data=f"rej_{m.chat.id}"))
    bot.send_message(ADMIN_ID, f"🔔 **New Order:** {plan}\nUser: {m.chat.id}\nTrx: `{m.text}`", reply_markup=adm_mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("app_", "rej_")))
def admin_action(call):
    if call.from_user.id != ADMIN_ID: return
    action, uid = call.data.split("_")[:2]
    if action == "app":
        plan = call.data.split("_")[2]
        limit = 20 if plan == "Starter" else 40 if plan == "Pro" else 60
        db.upgrade_user(uid, plan, limit, 7)
        bot.send_message(uid, f"🎉 **{plan} Plan Activated!**")
        bot.edit_message_text("✅ Approved", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(uid, "❌ Payment Rejected.")
        bot.edit_message_text("❌ Rejected", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: "Terms Policy" in m.text)
def terms(m):
    bot.send_message(m.chat.id, "📜 **Terms:**\n1. No refund.\n2. Do not spam.\n© Swygen IT")

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🔥 RUN SERVER
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
if __name__ == "__main__":
    print("🤖 Swygen Bot Online...")
    keep_alive()
    bot.infinity_polling(skip_pending=True)
