import logging
import os
import asyncio
import threading
import pytz
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات ---
TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')
subscribed_users = set()

# --- إعداد السيرفر لـ Render ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

# --- النصوص الكاملة ---
TXT_KURSI = "👑 *آية الكرسي:*\nاللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ."
TXT_MORNING = "☀️ *أذكار الصباح:*\nأصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير."
TXT_EVENING = "🌙 *أذكار المساء:*\nأمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير."
TXT_SHIFA = "🤲 *أدعية الشفاء:*\nاللهم رب الناس أذهب البأس، اشفِ أنت الشافي، لا شفاء إلا شفاؤك، شفاءً لا يغادر سقماً."

# --- دوال العمل ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribed_users.add(update.effective_user.id)
    kb = [
        [InlineKeyboardButton("⏱️ المواقيت", callback_data='prayer_times'), InlineKeyboardButton("🧭 القبلة", callback_data='qibla')],
        [InlineKeyboardButton("📖 المصحف", callback_data='quran_menu'), InlineKeyboardButton("🤲 الأدعية", callback_data='duas_menu')]
    ]
    await update.message.reply_text("🕌 أهلاً بك. البوت يعمل بنية شفاء الوالدة. نسألكم الدعاء.", reply_markup=InlineKeyboardMarkup(kb))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'qibla':
        await query.edit_message_text("🧭 رابط القبلة:\nhttps://qiblafinder.withgoogle.com", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='main_menu')]]))
    elif query.data == 'quran_menu':
        await query.edit_message_text("📖 اختر:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 آية الكرسي", callback_data='q_kursi')], [InlineKeyboardButton("🔙 عودة", callback_data='main_menu')]]))
    elif query.data == 'q_kursi':
        await query.edit_message_text(TXT_KURSI, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='quran_menu')]]))
    elif query.data == 'duas_menu':
        await query.edit_message_text("🤲 اختر:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🩺 الشفاء", callback_data='v_shifa')], [InlineKeyboardButton("🔙 عودة", callback_data='main_menu')]]))
    elif query.data == 'v_shifa':
        await query.edit_message_text(TXT_SHIFA, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='duas_menu')]]))
    elif query.data == 'main_menu':
        await start(update, context)

# --- نظام المهام الدورية (الخلفية) ---
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == '__main__':
    # تشغيل السيرفر في خيط منفصل (Thread)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # تشغيل البوت
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    print("البوت يعمل الآن...")
    application.run_polling()
