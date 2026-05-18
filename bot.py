import logging
import os
import asyncio
import threading
from datetime import datetime, timedelta
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
    return "🚀 Baghdad Prayer Bot - Advanced Notifications with 10-Min Reminder is Live!"

# --- 3. تفريغ جدول مواقيت بغداد الورقي كاملاً (30 يوماً دقيقة بدقيقة) ---
BAGHDAD_SCHEDULE = {
    # --- شهر أيار (مايس) ---
    "05-17": {"الفجر": "03:25", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:00", "العشاء": "20:27"}, 
    "05-18": {"الفجر": "03:24", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:01", "العشاء": "20:29"}, 
    "05-19": {"الفجر": "03:23", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:01", "العشاء": "20:29"}, 
    "05-20": {"الفجر": "03:22", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:02", "العشاء": "20:30"}, 
    "05-21": {"الفجر": "03:21", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:31"}, 
    "05-22": {"الفجر": "03:20", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:32"}, 
    "05-23": {"الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:04", "العشاء": "20:33"}, 
    "05-24": {"الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:05", "العشاء": "20:34"}, 
    "05-25": {"الفجر": "03:18", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:35"}, 
    "05-26": {"الفجر": "03:17", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:36"}, 
    "05-27": {"الفجر": "03:16", "الظهر": "12:05", "العصر": "15:46", "المغرب": "19:07", "العشاء": "20:37"}, 
    "05-28": {"الفجر": "03:16", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:07", "العشاء": "20:38"}, 
    "05-29": {"الفجر": "03:15", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:08", "العشاء": "20:39"}, 
    "05-30": {"الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"}, 
    "05-31": {"الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"}, 
    
    # --- شهر حزيران (يونيو) ---
    "06-01": {"الفجر": "03:13", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:10", "العشاء": "20:41"}, 
    "06-02": {"الفجر": "03:13", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:10", "العشاء": "20:42"}, 
    "06-03": {"الفجر": "03:12", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:11", "العشاء": "20:43"}, 
    "06-04": {"الفجر": "03:12", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:12", "العشاء": "20:43"}, 
    "06-05": {"الفجر": "03:12", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:12", "العشاء": "20:44"}, 
    "06-06": {"الفجر": "03:11", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:13", "العشاء": "20:45"}, 
    "06-07": {"الفجر": "03:11", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:13", "العشاء": "20:46"}, 
    "06-08": {"الفجر": "03:11", "الظهر": "12:07", "العصر": "15:48", "المغرب": "19:14", "العشاء": "20:46"}, 
    "06-09": {"الفجر": "03:10", "الظهر": "12:07", "العصر": "15:49", "المغرب": "19:14", "العشاء": "20:47"}, 
    "06-10": {"الفجر": "03:10", "الظهر": "12:07", "العصر": "15:49", "المغرب": "19:15", "العشاء": "20:47"}, 
    "06-11": {"الفجر": "03:10", "الظهر": "12:07", "العصر": "15:49", "المغرب": "19:15", "العشاء": "20:48"}, 
    "06-12": {"الفجر": "03:10", "助手": "12:07", "العصر": "15:49", "المغرب": "19:15", "العشاء": "20:48"}, 
    "06-13": {"الفجر": "03:10", "الظهر": "12:08", "العصر": "15:49", "المغرب": "19:16", "العشاء": "20:49"}, 
    "06-14": {"الفجر": "03:10", "الظهر": "12:08", "العصر": "15:50", "المغرب": "19:16", "العشاء": "20:49"}, 
    "06-15": {"الفجر": "03:10", "الظهر": "12:08", "العصر": "15:50", "المغرب": "19:16", "العشاء": "20:50"}, 
}

def get_current_prayer_times():
    today_key = datetime.now().strftime("%m-%d")
    if today_key in BAGHDAD_SCHEDULE:
        return BAGHDAD_SCHEDULE[today_key]
    else:
        return BAGHDAD_SCHEDULE["06-15"]

# --- 4. واجهة الأزرار الرئيسية وأمر البدء ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribed_users.add(user_id)
    
    user_name = update.effective_user.first_name
    welcome_text = (
        f"🕌 مرحباً بك يا {user_name} في بوت العبادات والمواقيت لمدينة بغداد.\n\n"
        "✨ تم تفعيل نظام التنبيهات المزدوج (تذكير قبل الأذان بـ 10 دقائق + تنبيه وقت الأذان بالضبط)."
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
            "📌 (مطابقة لجدول الأوقات الورقي بالكامل 100%)\n"
            "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
            f"🕋 الفجر: {times['الفجر']}\n"
            f"☀️ الظهر: {times['الظهر']}\n"
            f"🎯 العصر: {times['العصر']}\n"
            f"🌙 المغرب: {times['المغرب']}\n"
            f"🌌 العشاء: {times['العشاء']}\n"
            "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
            "🔔 يرسل البوت تذكيراً قبل الأذان بـ 10 دقائق، وتنبيهاً عند دخول الوقت."
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

# --- 6. نظام التنبيهات المزدوج التلقائي (وقت الأذان + قبل الوقت بـ 10 دقائق) ---
async def check_prayer_times(application: Application):
    last_notified_exact = ""
    last_notified_pre = ""
    
    while True:
        try:
            now_dt = datetime.now()
            now_str = now_dt.strftime("%H:%M")
            
            # حساب الوقت بعد 10 دقائق لمعرفة التنبيه المسبق
            pre_time_str = (now_dt + timedelta(minutes=10)).strftime("%H:%M")
            
            times = get_current_prayer_times()
            if times:
                for prayer_name, prayer_time in times.items():
                    # 1. التدقيق للتنبيه المسبق (قبل 10 دقائق)
                    if pre_time_str == prayer_time and pre_time_str != last_notified_pre:
                        pre_alert_text = f"🚨 *تذكير مسبق بفريضة {prayer_name}*\n\nمتبقي **10 دقائق** فقط على رفع أذان [{prayer_name}] بتوقيت بغداد.\n\n🍃 تهيأ للوضوء والاستعداد للصلاة يرحمك الله."
                        last_notified_pre = pre_time_str
                        for user_id in list(subscribed_users):
                            try:
                                await application.bot.send_message(chat_id=user_id, text=pre_alert_text, parse_mode="Markdown")
                            except Exception:
                                pass
                                
                    # 2. التدقيق لوقت الأذان بالضبط
                    if now_str == prayer_time and now_str != last_notified_exact:
                        exact_alert_text = f"🕌 *تنبيه أذان الفريضة*\n\nحان الآن موعد أذان [{prayer_name}] بحسب التوقيت المحلي لمدينة بغداد.\n\n✨ قم إلى صلاتك يرحمك الله، وعجّل بالخير."
                        last_notified_exact = now_str
                        for user_id in list(subscribed_users):
                            try:
                                await application.bot.send_message(chat_id=user_id, text=exact_alert_text, parse_mode="Markdown")
                            except Exception:
                                pass
                                
        except Exception as e:
            logging.error(f"Error in advanced notification loop: {e}")
        await asyncio.sleep(25)

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
    
    logging.info("🚀 تم إطلاق البوت بنظام التنبيه المزدوج المطور...")
    application.run_polling(drop_pending_updates=True, close_loop=False)
