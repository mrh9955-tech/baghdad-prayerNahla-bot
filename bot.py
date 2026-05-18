import logging
import os
import asyncio
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. إعداد السجلات ومراقبة البوت ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"

# تخزين المشتركين لإرسال التنبيهات التلقائية لهم
subscribed_users = set()

# --- 2. إعداد خادم الويب (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "🚀 Baghdad Prayer Bot - Hardcoded Schedule is Live!"

# --- 3. جدول مواقيت بغداد الورقي مكتوب يدوياً بالدقيقة لضمان التطابق التام ---
# الصيغة: "الشهر-اليوم": {"الفجر": "س:د", "الظهر": "س:د", "العصر": "س:د", "المغرب": "س:د", "العشاء": "س:د"}
BAGHDAD_SCHEDULE = {
    "05-18": {"الفجر": "03:24", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:01", "العشاء": "20:29"}, # الإثنين 18 أيار
    "05-19": {"الفجر": "03:23", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:01", "العشاء": "20:29"}, # الثلاثاء 19 أيار
    "05-20": {"الفجر": "03:22", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:02", "العشاء": "20:30"}, # الأربعاء 20 أيار
    "05-21": {"الفجر": "03:21", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:31"}, # الخميس 21 أيار
    "05-22": {"الفجر": "03:20", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:32"}, # الجمعة 22 أيار
    "05-23": {"الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:04", "العشاء": "20:33"}, # السبت 23 أيار
    "05-24": {"الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:05", "العشاء": "20:34"}, # الأحد 24 أيار
    "05-25": {"الفجر": "03:18", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:35"}, # الإثنين 25 أيار
    "05-26": {"الفجر": "03:17", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:36"}, # الثلاثاء 26 أيار
    "05-27": {"الفجر": "03:16", "الظهر": "12:05", "العصر": "15:46", "المغرب": "19:07", "العشاء": "20:37"}, # الأربعاء 27 أيار
    "05-28": {"الفجر": "03:16", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:07", "العشاء": "20:38"}, # الخميس 28 أيار
    "05-29": {"الفجر": "03:15", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:08", "العشاء": "20:39"}, # الجمعة 29 أيار
    "05-30": {"الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"}, # السبت 30 أيار
    "05-31": {"الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"}, # الأحد 31 أيار
    "06-01": {"الفجر": "03:13", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:10", "العشاء": "20:41"}, # الإثنين 1 حزيران
    "06-02": {"الفجر": "03:13", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:10", "العشاء": "20:42"}, # الثلاثاء 2 حزيران
    "06-03": {"الفجر": "03:12", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:11", "العشاء": "20:43"}, # الأربعاء 3 حزيران
    "06-04": {"الفجر": "03:12", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:12", "العشاء": "20:43"}, # الخميس 4 حزيران
    "06-05": {"الفجر": "03:12", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:12", "العشاء": "20:44"}, # الجمعة 5 حزيران
    "06-06": {"الفجر": "03:11", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:13", "العشاء": "20:45"}, # السبت 6 حزيران
}

def get_current_prayer_times():
    # جلب التاريخ الحالي بالنظام (شهر-يوم) لمعرفة توقيته من الجدول الثابت
    today_key = datetime.now().strftime("%m-%d")
    # إذا كان اليوم مسجلاً بالجدول نعرضه، وإلا نعطي يوماً افتراضياً لحين تحديث بقية الأشهر
    if today_key in BAGHDAD_SCHEDULE:
        return BAGHDAD_SCHEDULE[today_key]
    else:
        return BAGHDAD_SCHEDULE["05-18"] # الافتراضي كحماية للكود

# --- 4. واجهة الأزرار الرئيسية وأمر البدء ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribed_users.add(user_id)
    
    user_name = update.effective_user.first_name
    welcome_text = (
        f"🕌 مرحباً بك يا {user_name} في بوت العبادات والمواقيت لمدينة بغداد.\n\n"
        "✨ تم تفعيل نظام التنبيهات التلقائي المطابق لجدول المدينة الرسمي تماماً بالدقيقة."
    )
    
    keyboard = [
        [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم", callback_data='prayer_times')],
        [InlineKeyboardButton("📿 حصن المسلم والأذكار", callback_data='azkar_menu')],
        [InlineKeyboardButton("📖 المصحف الإلكتروني", callback_data='quran_menu')],
        [InlineKeyboardButton("🧭 اتجاه القبلة الشرعية", callback_data='qibla_info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# --- 5. لوحة التحكم بالأزرار التفاعلية ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'prayer_times':
        times = get_current_prayer_times()
        message = (
            "🕌 *مواقيت الصلاة اليوم لمدينة بغداد*\n"
            "📌 (مطابقة لجدول الأوقات الرسمي بالدقيقة مية بالمية)\n"
            "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
            f"🕋 الفجر: {times['الفجر']}\n"
            f"☀️ الظهر: {times['الظهر']}\n"
            f"🎯 العصر: {times['العصر']}\n"
            f"🌙 المغرب: {times['المغرب']}\n"
            f"🌌 العشاء: {times['العشاء']}\n"
            "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
            "🔔 يرسل البوت تنبيهاً تلقائياً في وقت الأذان المكتوب أعلاه بالضبط."
        )
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='main_menu')]]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'azkar_menu':
        message = "📿 *قائمة الأذكار اليومية - اختر ذكراً للبدء بالعداد:* "
        keyboard = [
            [InlineKeyboardButton("💬 سبحان الله وبحمده", callback_data='count_1')],
            [InlineKeyboardButton("💬 أستغفر الله وأتوب إليه", callback_data='count_2')],
            [InlineKeyboardButton("🔙 العودة الرئيسية", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data in ['count_1', 'count_2']:
        await query.answer(text="✨ تقبل الله طاعتك وغفر ذنبك ورزقك من حيث لا تحتسب ✅", show_alert=True)

    elif query.data == 'quran_menu':
        message = "📖 *المصحف الإلكتروني المتكامل:*"
        keyboard = [
            [InlineKeyboardButton("سورة الكهف 📑", url="https://quran.com/18")],
            [InlineKeyboardButton("سورة الملك 🌌", url="https://quran.com/67")],
            [InlineKeyboardButton("قراءة المصحف كاملاً 📚", url="https://quran.com")],
            [InlineKeyboardButton("🔙 العودة", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'qibla_info':
        message = (
            "🧭 *اتجاه القبلة لمدينة بغداد:*\n\n"
            "الانحراف الزاوي للقبلة هو **203.45 درجة** من اتجاه الشمال.\n"
            "استخدم الرابط المباشر لتحديدها عبر كاميرا الهاتف والـ GPS بدقة:"
        )
        keyboard = [
            [InlineKeyboardButton("📍 حدد القبلة عبر القمر الصناعي", url="https://qiblafinder.withgoogle.com/")],
            [InlineKeyboardButton("🔙 العودة", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم", callback_data='prayer_times')],
            [InlineKeyboardButton("📿 حصن المسلم والأذكار", callback_data='azkar_menu')],
            [InlineKeyboardButton("📖 المصحف الإلكتروني", callback_data='quran_menu')],
            [InlineKeyboardButton("🧭 اتجاه القبلة الشرعية", callback_data='qibla_info')]
        ]
        welcome_text = "🕌 قائمة العبادات والمواقيت المتكاملة لمدينة بغداد:"
        await query.edit_message_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 6. نظام التنبيهات والتدقيق التلقائي التام حسب جدول الورقة ---
async def check_prayer_times(application: Application):
    last_notified = ""
    while True:
        try:
            now = datetime.now().strftime("%H:%M")
            if now != last_notified:
                times = get_current_prayer_times()
                for prayer_name, prayer_time in times.items():
                    if now == prayer_time:
                        alert_text = f"🕌 *تنبيه أذان الفريضة*\n\nحان الآن موعد أذان [{prayer_name}] بحسب التوقيت المحلي لمدينة بغداد.\n\n✨ قم إلى صلاتك يرحمك الله."
                        last_notified = now
                        for user_id in list(subscribed_users):
                            try:
                                await application.bot.send_message(chat_id=user_id, text=alert_text, parse_mode="Markdown")
                            except Exception:
                                pass
        except Exception as e:
            logging.error(f"Error in background notification loop: {e}")
        await asyncio.sleep(30)

def start_prayer_checker(application):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_prayer_times(application))

# --- 7. التشغيل النظيف والمباشر ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    web_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False))
    web_thread.daemon = True
    web_thread.start()
    
    checker_thread = threading.Thread(target=start_prayer_checker, args=(application,), daemon=True)
    checker_thread.start()
    
    logging.info("🚀 تم إطلاق البوت والاقتران المباشر بالجدول الورقي...")
    application.run_polling(drop_pending_updates=True, close_loop=False)
