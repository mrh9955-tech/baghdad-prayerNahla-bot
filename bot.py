import logging
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# إعداد خفيف
logging.basicConfig(level=logging.INFO)
TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"

# خادم Flask بسيط جداً (فقط ليبقي السيرفر مفتوحاً)
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Active"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("⏱️ المواقيت", callback_data='prayer_times'), InlineKeyboardButton("🧭 القبلة", callback_data='qibla')],
        [InlineKeyboardButton("📖 المصحف", callback_data='quran_menu'), InlineKeyboardButton("🤲 الأدعية", callback_data='duas_menu')]
    ]
    await update.message.reply_text("🕌 أهلاً بك. البوت يعمل بنية شفاء الوالدة.", reply_markup=InlineKeyboardMarkup(kb))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # تحسين السرعة: استخدام إجابة مباشرة لكل زر
    if query.data == 'prayer_times':
        await query.edit_message_text("🕋 الفجر: 03:23\n☀️ الظهر: 12:04\n🎯 العصر: 15:46\n🌙 المغرب: 19:01\n🌌 العشاء: 20:29", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='main_menu')]]))
    elif query.data == 'qibla':
        await query.edit_message_text("🧭 رابط القبلة:\nhttps://qiblafinder.withgoogle.com", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='main_menu')]]))
    elif query.data == 'quran_menu':
        await query.edit_message_text("📖 اختر السورة:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 آية الكرسي", callback_data='q_kursi')], [InlineKeyboardButton("🔙 عودة", callback_data='main_menu')]]))
    elif query.data == 'duas_menu':
        await query.edit_message_text("🤲 اختر الدعاء:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🩺 الشفاء", callback_data='v_shifa')], [InlineKeyboardButton("🔙 عودة", callback_data='main_menu')]]))
    elif query.data == 'main_menu':
        await start(update, context)

if __name__ == '__main__':
    # تشغيل Flask في الخلفية (Thread)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()
    
    # تشغيل البوت الأساسي
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    application.run_polling()
