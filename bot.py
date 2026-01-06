import telebot
import requests
import time
import os
import threading
import pytz
from datetime import datetime
from gradio_client import Client
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from keep_alive import keep_alive

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🔥 SWYGEN PREMIUM CONFIG
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
BOT_TOKEN = '8030029502:AAG0NhCvXN38yJ_BvWP2T7j0meh6P23sXXw' # আপনার বটের টোকেন
ADMIN_ID = 6243881362             # আপনার টেলিগ্রাম আইডি (এডমিন)
CHANNEL_ID = -1002879589597       # আপনার চ্যানেলের আইডি
CHANNEL_LINK = "https://t.me/RedX_Developer" # চ্যানেলের লিংক

# 🔑 HUGGINGFACE VIP TOKEN (High Speed & No Queue)
HF_TOKEN = "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"

# JSONBIN DATABASE (ডাটা সেভ রাখার জন্য)
JSONBIN_API_KEY = '$2a$10$CWZ5aFPmaczB/T4.PumaJO3H3lYV7PoqIwcTKpn6oBp0TX.hQFIEu' #
BIN_ID = '695d56af43b1c97be91da474'
BASE_URL = f'https://api.jsonbin.io/v3/b/{BIN_ID}'

# AI MODEL (CodeFormer - Best for Details & Clarity)
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
    markup.add("👤 Profile", "📸 Photo Enhance")
    markup.add("💎 Upgrade", "📜 Terms Policy")
    markup.add("👨‍💻 Developer Info") 
    return markup

def check_sub(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['creator', 'administrator', 'member']
    except: return False # চ্যানেল আইডি ভুল হলে false রিটার্ন করবে

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🤖 BOT HANDLERS
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

@bot.message_handler(commands=['start'])
def start(m):
    user_id = m.chat.id
    name = m.from_user.first_name
    db.register_user(user_id, name)
    
    msg = (
        f"👋 **আসসালামু আলাইকুম, {name}!**\n\n"
        f"📸 **Swygen Ultra Enhancer** এ আপনাকে স্বাগতম।\n"
        f"আমি আপনার নরমাল ছবিকে **4K HD Quality** তে কনভার্ট করতে পারি, যা ছবির ডিটেইলস ঠিক রেখে হাই কোয়ালিটি করে।\n\n"
        f"⚠️ **বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন:**"
    )
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    mk.add(InlineKeyboardButton("✅ Joined", callback_data="check_join"))
    bot.send_message(user_id, msg, reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def join_verify(call):
    uid = call.message.chat.id
    name = call.from_user.first_name
    
    if check_sub(uid):
        bot.delete_message(uid, call.message.message_id)
        welcome_msg = (
            f"🎉 **স্বাগতম {name}!**\n"
            f"ধন্যবাদ আমাদের সাথে যুক্ত হওয়ার জন্য।\n\n"
            f"এখন আপনি নিচের মেনু থেকে **Photo Enhance** সিলেক্ট করে আপনার ছবি হাই কোয়ালিটি করতে পারবেন।"
        )
        bot.send_message(uid, welcome_msg, reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনও চ্যানেলে জয়েন করেননি!", show_alert=True)

# --- 📸 ENHANCE LOGIC ---
@bot.message_handler(func=lambda m: "Photo Enhance" in m.text)
def enhance_req(m):
    user = db.get_user(m.chat.id)
    if not db.check_limit(m.chat.id):
        return bot.send_message(m.chat.id, "🚫 **আজকের লিমিট শেষ!**\nআরও ছবি এডিট করতে **Upgrade** বাটনে ক্লিক করে প্যাকেজ কিনুন।")
    
    msg = (
        f"📸 **প্রিয় {user['name']},**\n\n"
        f"যে ছবিটি আপনি **Enhance & High Quality** করতে চান, সেটি এখন পাঠান।\n"
        f"⚠️ _নোট: আমি ছবির ডিটেইলস নষ্ট না করে সুন্দরভাবে ক্লিয়ার করে দিব।_"
    )
    bot.send_message(m.chat.id, msg)

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    uid = m.chat.id
    user_photos[uid] = m.photo[-1].file_id
    
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("✨ Enhance High Quality", callback_data="do_enhance"))
    
    bot.reply_to(m, "🖼️ **ছবি আপলোড সম্পন্ন!**\nHigh Quality করতে নিচের বাটনে ক্লিক করুন।", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "do_enhance")
def process_enhance(call):
    uid = call.message.chat.id
    
    if not db.check_limit(uid):
        return bot.answer_callback_query(call.id, "❌ আপনার লিমিট শেষ। আপগ্রেড করুন।", show_alert=True)

    # 1. Fake Live Progress Animation
    prog_msg = bot.send_message(uid, "⏳ **Connecting to Server...**")
    steps = [
        "🔄 **Processing... 10%**\n_Analyzing Image details..._",
        "🔄 **Processing... 40%**\n_Enhancing Face & Skin texture..._",
        "🔄 **Processing... 70%**\n_Applying 4K HD Filters..._",
        "🔄 **Processing... 90%**\n_Finalizing Quality..._",
        "✅ **Processing... 100%**\n_Uploading Result..._"
    ]
    
    try:
        # Download Image
        file_info = bot.get_file(user_photos[uid])
        downloaded_file = bot.download_file(file_info.file_path)
        input_path = f"input_{uid}.jpg"
        with open(input_path, 'wb') as f: f.write(downloaded_file)
        
        # Start Animation in separate thread to not block
        def animate():
            for step in steps:
                try:
                    bot.edit_message_text(step, uid, prog_msg.message_id)
                    time.sleep(1.5)
                except: pass
        threading.Thread(target=animate).start()
        
        # 🔥 AI ENHANCE with VIP TOKEN
        # hf_token ব্যবহার করায় এটি কিউ ব্রেক করে কাজ করবে
        client = Client(AI_MODEL, hf_token=HF_TOKEN)
        
        # CodeFormer Settings for Best Detail Retention:
        # Background Enhance = True
        # Face Upsample = True
        # Upscale = 2 (Best balance for HD without timeout)
        # Fidelity = 0.7 (ডিটেইলস ধরে রাখার জন্য বেস্ট ভ্যালু)
        result = client.predict(input_path, True, True, 2, 0.7, fn_index=0)
        
        output_image = result[0] if isinstance(result, (list, tuple)) else result
        
        with open(output_image, 'rb') as ph:
            cap = (
                f"✨ **Enhanced Successfully!**\n\n"
                f"🤖 **Bot:** Swygen Ultra Enhancer\n"
                f"👨‍💻 **Dev:** Ayman Hasan Shaan\n"
                f"💬 **Feedback:** [Swygen IT](https://swygen.xyz)"
            )
            bot.send_photo(uid, ph, caption=cap, parse_mode='Markdown')
            
        db.increment_usage(uid)
        bot.delete_message(uid, prog_msg.message_id)
        os.remove(input_path)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(f"❌ টেকনিক্যাল এরর। দয়া করে আবার চেষ্টা করুন।", uid, prog_msg.message_id)
        try: os.remove(input_path)
        except: pass

# --- 👤 PROFILE ---
@bot.message_handler(func=lambda m: "Profile" in m.text)
def profile(m):
    user = db.get_user(m.chat.id)
    if not user: return
    rem = user['limit'] - user['used']
    msg = (
        f"👤 **USER PROFILE**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📛 নাম: **{user['name']}**\n"
        f"🆔 আইডি: `{user['id']}`\n"
        f"📅 জয়েন তারিখ: {user['join_date']}\n\n"
        f"📦 প্যাকেজ: **{user['plan']}**\n"
        f"🔄 ব্যবহার করেছেন: **{user['used']}** টি\n"
        f"⏳ বাকি আছে: **{rem}** টি\n"
        f"━━━━━━━━━━━━━━━"
    )
    bot.send_message(m.chat.id, msg)

# --- 👨‍💻 DEVELOPER INFO ---
@bot.message_handler(func=lambda m: "Developer Info" in m.text)
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
    bot.send_message(m.chat.id, msg, disable_web_page_preview=True)

# --- 💎 UPGRADE SYSTEM ---
@bot.message_handler(func=lambda m: "Upgrade" in m.text)
def upgrade_menu(m):
    user = db.get_user(m.chat.id)
    msg = (
        f"💎 **PREMIUM PACKAGES**\n"
        f"প্রিয় **{user['name']}**, আপনার লিমিট বাড়াতে প্যাকেজ সিলেক্ট করুন:\n\n"
        f"1️⃣ **Starter Plan**\n"
        f"💰 400 BDT | 📸 20 Images/Day | ⏳ 7 Days\n\n"
        f"2️⃣ **Pro Plan**\n"
        f"💰 900 BDT | 📸 40 Images/Day | ⏳ 7 Days\n\n"
        f"3️⃣ **Business Plan**\n"
        f"💰 1800 BDT | 📸 60 Images/Day | ⏳ 7 Days"
    )
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("🔹 Buy Starter (400tk)", callback_data="buy_Starter"))
    mk.add(InlineKeyboardButton("🔶 Buy Pro (900tk)", callback_data="buy_Pro"))
    mk.add(InlineKeyboardButton("💠 Buy Business (1800tk)", callback_data="buy_Business"))
    
    bot.send_message(m.chat.id, msg, reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def payment(call):
    plan = call.data.split("_")[1]
    amount = "400" if plan == "Starter" else "900" if plan == "Pro" else "1800"
    
    msg = bot.send_message(call.message.chat.id, 
        f"💳 **পেমেন্ট ইনস্ট্রাকশন ({plan} Plan)**\n\n"
        f"অনুগ্রহ করে **{amount} টাকা** নিচের নম্বরে সেন্ড মানি করুন।\n"
        f"📱 **Nagad:** `{NAGAD_NUMBER}`\n\n"
        f"📝 টাকা পাঠানোর পর আপনার **Transaction ID (TrxID)** টি এখানে লিখে পাঠান।"
    )
    bot.register_next_step_handler(msg, verify_trx, plan, amount)

def verify_trx(m, plan, amount):
    trx = m.text
    uid = m.chat.id
    user = db.get_user(uid)
    
    bot.send_message(uid, "✅ **পেমেন্ট রিকোয়েস্ট জমা হয়েছে!**\nএডমিন অ্যাপ্রুভ করলে আপনার প্যাকেজ চালু হয়ে যাবে।")
    
    # Admin Notification
    adm_mk = InlineKeyboardMarkup()
    adm_mk.add(
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
    bot.send_message(ADMIN_ID, adm_msg, reply_markup=adm_mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("app_", "rej_")))
def admin_action(call):
    if call.from_user.id != ADMIN_ID: return
    action, uid = call.data.split("_")[:2]
    
    if action == "app":
        plan = call.data.split("_")[2]
        # Setting limits based on package
        limit = 20 if plan == "Starter" else 40 if plan == "Pro" else 60
        
        db.upgrade_user(uid, plan, limit, 7)
        bot.send_message(uid, f"🎉 **অভিনন্দন!**\nআপনার **{plan} Package** চালু হয়েছে।\nএখন আপনি দৈনিক {limit} টি ছবি এডিট করতে পারবেন।")
        bot.edit_message_text(f"✅ Approved {plan} for {uid}", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(uid, "❌ আপনার পেমেন্ট রিজেক্ট করা হয়েছে।\nকারণ: ভুল ট্রানজ্যাকশন আইডি।")
        bot.edit_message_text("❌ Request Rejected", call.message.chat.id, call.message.message_id)

# --- 📜 TERMS POLICY ---
@bot.message_handler(func=lambda m: "Terms Policy" in m.text)
def terms(m):
    msg = (
        "📜 **TERMS & POLICY**\n\n"
        "1. **Usage Policy:** By using this bot, you agree not to process any illegal, explicit, or harmful content.\n"
        "2. **Data Privacy:** We value your privacy. Your photos are processed securely and deleted immediately from our servers after enhancement.\n"
        "3. **Refund Policy:** Digital subscriptions and packages are non-refundable once activated.\n"
        "4. **Fair Use:** Do not attempt to spam or abuse the bot's service. Abuse may result in a permanent ban.\n\n"
        "© Swygen IT 2026"
    )
    bot.send_message(m.chat.id, msg)

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🔥 RUN SERVER
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
if __name__ == "__main__":
    print("🤖 Swygen Bot Online with VIP Access...")
    keep_alive()
    bot.infinity_polling(skip_pending=True)
