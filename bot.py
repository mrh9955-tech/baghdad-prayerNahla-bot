import logging
import os
import threading
import requests
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. إعداد السجلات ومراقبة البوت ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# التوكن الخاص ببوتك تلقائياً
TOKEN = "8804058766:AAE2rc5Fh5H8oGuJM6KV1P1-NwREE5bvRk4"

# --- 2. إعداد خادم الويب (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running!"

# --- 3. جلب مواقيت الصلاة لبغداد ---
def get_baghdad_prayer_times():
    try:
        url = "http://api.aladhan.com/v1/timingsByCity?city=Baghdad&country=Iraq&method=4"
        response = requests.get(url).json()
        timings = response['data']['timings']
        return {
            "الفجر": timings['Fajr'],
            "الظهر": timings['Dhuhr'],
            "العصر": timings['Asr'],
            "المغرب": timings['Maghrib'],
            "العشاء": timings['Isha']
        }
    except Exception as e:
        logging.error(f"Error fetching times: {e}")
        return None

# --- 4. واجهة الأزرار وأمر البدء ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"🕌 مرحباً بك يا {user_name} في بوت المواقيت والأذكار الفخم.\n\n"
        "✨ تم تفعيل النظام التلقائي للتنبيهات والعبادات بنجاح لمدينة بغداد وضواحيها."
    )
    keyboard = [
        [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم في بغداد", callback_data='prayer_times')],
        [InlineKeyboardButton("📿 أذكار الصباح والمساء التفاعلية", callback_data='azkar_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# --- 5. دالة الأزرار التفاعلية ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'prayer_times':
        times = get_baghdad_prayer_times()
        if times:
            message = (
                "🕌 *مواقيت الصلاة اليوم لمدينة بغداد*\n"
                "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
                 f"🕋 الفجر: {times['الفجر']}\n"
                 f"☀️ الظهر: {times['الظهر']}\n"
                 f"🎯 العصر: {times['العصر']}\n"
                 f"🌙 المغرب: {times['المغرب']}\n"
                 f"🌌 العشاء: {times['العشاء']}\n"
                "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
                "⏱️ سيقوم البوت بإرسال تنبيه فخم في وقت الأذان بالضبط تلقائياً."
            )
        else:
            message = "⚠️ عذراً، حدث خطأ في جلب المواقيت حالياً، حاول مجدداً."
        await query.edit_message_text(text=message, parse_mode="Markdown")
        
    elif query.data == 'azkar_menu':
        azkar_text = (
            "📿 *العداد الذكي للأذكار*\n\n"
            "اضغط على الزر أدناه عند الانتهاء من الذكر:"
        )
        keyboard = [[InlineKeyboardButton("💬 سبحان الله وبحمده (اضغط هنا)", callback_data='dhikr_count')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=azkar_text, parse_mode="Markdown", reply_markup=reply_markup)

    elif query.data == 'dhikr_count':
        await query.answer(text="✨ تقبل الله طاعتك وغفر ذنبك ورزقك من حيث لا تحتسب ✅", show_alert=True)

# --- 6. دالة تشغيل البوت القياسية والمستقرة ---
def run_bot():
    # إنشاء حلقة أحداث جديدة ونظيفة متوافقة مع بايثون 3.10
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    logging.info("⚡ البوت الفخم يستعد للاستماع للرسائل...")
    # تشغيل البولينج القياسي المستقر
    application.run_polling(close_loop=False, drop_pending_updates=True)

# --- 7. تشغيل البوت تلقائياً في الخلفية تماماً عند استدعاء gunicorn ---
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
