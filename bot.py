import logging, os, threading
from flask import Flask
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات ---
TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# --- النصوص ---
TXT_WELCOME = "🕌 *مرحباً بك في بوت العبادات*\nهذا البوت صدقة جارية بنية شفاء الوالدة. اختر من القائمة:"
TXT_PRAYER = "🕌 *مواقيت الصلاة في بغداد*\n📅 19/05/2026 م | 2 ذو الحجة 1447 هـ\n\n🕋 الفجر: 03:23\n☀️ الظهر: 12:04\n🎯 العصر: 15:46\n🌙 المغرب: 19:01\n🌌 العشاء: 20:29"

# --- دوال البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("⏱️ المواقيت", callback_data='prayer')],
        [InlineKeyboardButton("🧭 اتجاه القبلة", callback_data='qibla')],
        [InlineKeyboardButton("☀️ الأذكار", callback_data='azkar')],
        [InlineKeyboardButton("🤲 الأدعية", callback_data='duas')]
    ]
    await update.message.reply_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'prayer':
        await query.edit_message_text(TXT_PRAYER, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='start_menu')]]))
    elif query.data == 'qibla':
        await query.edit_message_text("🧭 *اتجاه القبلة:*\nhttps://qiblafinder.withgoogle.com", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='start_menu')]]))
    elif query.data == 'start_menu':
        kb = [
            [InlineKeyboardButton("⏱️ المواقيت", callback_data='prayer')],
            [InlineKeyboardButton("🧭 اتجاه القبلة", callback_data='qibla')],
            [InlineKeyboardButton("☀️ الأذكار", callback_data='azkar')],
            [InlineKeyboardButton("🤲 الأدعية", callback_data='duas')]
        ]
        await query.edit_message_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# --- تشغيل السيرفر ---
def run_flask():
    app = Flask(__name__)
    @app.route('/')
    def home(): return "Bot is Active"
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == '__main__':
    # تشغيل السيرفر في خلفية
    threading.Thread(target=run_flask, daemon=True).start()
    
    # تشغيل البوت
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    print("البوت يعمل الآن...")
    application.run_polling()
