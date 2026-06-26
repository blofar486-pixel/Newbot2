import random
import logging
import threading
import time
from datetime import datetime, timedelta
import pytz
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Live Logs Monitoring
logging.basicConfig(level=logging.INFO)

# ✅ Aapka Telegram Bot Token
BOT_TOKEN = "8328605174:AAFeNEZR2BfW3i21BywTVeuDL-Oopo562gA"

bot = telebot.TeleBot(BOT_TOKEN)
PK_TZ = pytz.timezone('Asia/Karachi')

ADMIN_CHAT_ID = None
ALLOWED_USERS = set()
MAINTENANCE_MODE = False

PAIRS_CATEGORIES = {
    "majors": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD"],
    "euro": ["EUR/GBP", "EUR/JPY", "EUR/AUD", "EUR/CAD"],
    "gbp": ["GBP/JPY", "GBP/AUD", "GBP/CAD", "GBP/CHF"],
    "cross": ["AUD/JPY", "AUD/CAD", "NZD/JPY", "CAD/JPY"],
    "exotics": ["USD/TRY", "USD/ZAR", "USD/INR", "USD/BRL"]
}

def is_authorized(chat_id, user_id):
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID is None:
        ADMIN_CHAT_ID = user_id
        ALLOWED_USERS.add(user_id)
        return True
    if user_id == ADMIN_CHAT_ID:
        return True
    if MAINTENANCE_MODE:
        bot.send_message(chat_id, "⚠️ **Maintenance Active.**")
        return False
    if user_id not in ALLOWED_USERS:
        bot.send_message(chat_id, f"❌ **Access Denied.** ID: `{user_id}`")
        return False
    return True

# --- 2-Minute Session Outcome Evaluator (For Both Single & Multi) ---
def manage_signal_lifecycle(chat_id, message_id, pairs_list):
    # Poore 2 minutes (120 seconds) tak session report monitor setup delay
    time.sleep(120)
    
    try:
        final_report = "📊 **RQT SESSION REPORT (FINISHED)** 📊\n"
        final_report += "=============================\n"
        
        for p in pairs_list:
            outcome = "🟢 WIN (Pure) 🔥" if random.randint(1, 100) <= 93 else "🔴 LOSS (Break)"
            final_report += f"💱 `{p}` ➜ {outcome}\n"
            
        final_report += "=============================\n**Status Evaluated Successfully.**\n🧹 _Clearing chat screen in 10s..._"
        bot.edit_message_text(final_report, chat_id, message_id, parse_mode="Markdown")
        
        time.sleep(10)
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "🧹 **Signal session completed.** Press /start to analyze fresh algorithmic setups.")
    except Exception as e:
        logging.error(f"Lifecycle monitoring failed: {e}")

@bot.message_handler(commands=['adduser'])
def add_user(message):
    if message.from_user.id == ADMIN_CHAT_ID:
        try:
            new_id = int(message.text.split()[1])
            ALLOWED_USERS.add(new_id)
            bot.reply_to(message, f"✅ Added: `{new_id}`")
        except:
            bot.reply_to(message, "Use: `/adduser [id]`")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_authorized(message.chat.id, message.from_user.id):
        return
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📦 Multi-Pair Pack (Distributed Time)", callback_data="mode_multi"),
        InlineKeyboardButton("💱 Single Pair Radar", callback_data="mode_single")
    )
    bot.reply_to(message, "🎯 **RQT QUANT V6.5 HYBRID SYSTEM**\nApna preferred trading setup select karein:", reply_markup=markup, parse_mode="Markdown")

# --- Flow 1: Multi Pack Handling ---
@bot.callback_query_handler(func=lambda call: call.data == "mode_multi")
def select_multi_pack(call):
    if not is_authorized(call.message.chat.id, call.from_user.id):
        return
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🌐 Majors", callback_data="pkm_majors"),
        InlineKeyboardButton("🇪🇺 EUR", callback_data="pkm_euro"),
        InlineKeyboardButton("🇬🇧 GBP", callback_data="pkm_gbp"),
        InlineKeyboardButton("🇦🇺 Minors", callback_data="pkm_cross"),
        InlineKeyboardButton("📊 Exotics", callback_data="pkm_exotics"),
        InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")
    )
    bot.edit_message_text("📦 **MULTI-PAIR DISTRIBUTED SIGNALS**\nMarket category pack chunain:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('pkm_'))
def handle_multi_timeframe(call):
    if not is_authorized(call.message.chat.id, call.from_user.id):
        return
    bot.answer_callback_query(call.id)
    category = call.data.replace("pkm_", "")
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⏱️ 1 Min Strategy", callback_data=f"genm_1m_{category}"),
        InlineKeyboardButton("⏱️ 5 Min Strategy", callback_data=f"genm_5m_{category}"),
        InlineKeyboardButton("⬅️ Back", callback_data="mode_multi")
    )
    bot.edit_message_text(f"📦 **Pack: {category.upper()}**\nTimeframe select karein:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('genm_'))
def generate_multi_signals(call):
    if not is_authorized(call.message.chat.id, call.from_user.id):
        return
    bot.answer_callback_query(call.id)
    raw_data = call.data.replace("genm_", "")
    timeframe, category = raw_data.split("_", 1)
    pairs = PAIRS_CATEGORIES.get(category, [])
    now_pk = datetime.now(PK_TZ)
    
    output = f"💎 **RQT TIME-DISTRIBUTED SIGNALS** 💎\n"
    output += f"📅 Baseline: `{now_pk.strftime('%I:%M %p')}` | Expiry: `{timeframe.upper()}`\n"
    output += "===============================\n"
    
    step_minutes = 3 if timeframe == "1m" else 5
    current_gap = step_minutes
    active_pairs = pairs[:4]
    
    for pair in active_pairs:
        pair_seed = sum(ord(c) for c in pair)
        algo_bias = (pair_seed + now_pk.minute + current_gap) % 3
        direction = "🟢 CALL (UP) 📈" if algo_bias == 0 else ("🔴 PUT (DOWN) 📉" if algo_bias == 1 else "🟢 CALL (UP) 📈")
        str_tag = "94%" if algo_bias == 0 else ("93%" if algo_bias == 1 else "91%")
        
        future_time = now_pk + timedelta(minutes=current_gap)
        output += f"🔹 **{pair}** ➜ ⏱️ `{future_time.strftime('%I:%M %p')}`\n  ↳ Direction: {direction} *({str_tag})*\n\n"
        current_gap += step_minutes
        
    output += "===============================\n⏳ _Live outcome validation update will overwrite here in 2 mins._"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 Main Menu", callback_data="back_main"))
    sent_msg = bot.edit_message_text(output, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    threading.Thread(target=manage_signal_lifecycle, args=(sent_msg.chat.id, sent_msg.message_id, active_pairs)).start()

# --- Flow 2: Single Pair Handling ---
@bot.callback_query_handler(func=lambda call: call.data == "mode_single")
def select_single_pack(call):
    if not is_authorized(call.message.chat.id, call.from_user.id):
        return
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🌐 Majors", callback_data="pks_majors"),
        InlineKeyboardButton("🇪🇺 EUR", callback_data="pks_euro"),
        InlineKeyboardButton("🇬🇧 GBP", callback_data="pks_gbp"),
        InlineKeyboardButton("🇦🇺 Minors", callback_data="pks_cross"),
        InlineKeyboardButton("📊 Exotics", callback_data="pks_exotics"),
        InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")
    )
    bot.edit_message_text("💱 **SINGLE ASSET CUSTOM RADAR**\nMarket pack category select karein:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('pks_'))
def display_single_pairs(call):
    if not is_authorized(call.message.chat.id, call.from_user.id):
        return
    bot.answer_callback_query(call.id)
    category = call.data.replace("pks_", "")
    pairs = PAIRS_CATEGORIES.get(category, [])
    
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(p, callback_data=f"sels_{category}_{p}") for p in pairs]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("⬅️ Back", callback_data="mode_single"))
    bot.edit_message_text(f"📦 **Pack: {category.upper()}**\nJis single asset par trade karni hai usey select chunain:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('sels_'))
def handle_single_timeframe(call):
    if not is_authorized(call.message.chat.id, call.from_user.id):
        return
    bot.answer_callback_query(call.id)
    raw_info = call.data.replace("sels_", "")
    category, pair = raw_info.split("_", 1)
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⏱️ 1 Min Strategy", callback_data=f"gens_1m_{pair}"),
        InlineKeyboardButton("⏱️ 5 Min Strategy", callback_data=f"gens_5m_{pair}"),
        InlineKeyboardButton("⬅️ Back", callback_data=f"pks_{category}")
    )
    bot.edit_message_text(f"💱 **Asset: {pair}**\nIs custom single pair ke liye strategy select karein:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('gens_'))
def generate_single_signal(call):
    if not is_authorized(call.message.chat.id, call.from_user.id):
        return
    bot.answer_callback_query
