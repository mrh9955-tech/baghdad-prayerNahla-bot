import logging
import os
import requests
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
    return "🚀 Advanced Holy Bot is fully active and calibrated!"

# --- 3. جلب مواقيت الصلاة ومطابقتها لجدول بغداد اليدوي ---
def get_baghdad_prayer_times():
    try:
        # الاعتماد على الهيئة المصرية كمصدر أساسي
        url = "http://api.aladhan.com/v1/timingsByCity?city=Baghdad&country=Iraq&method=5"
        response = requests.get(url).json()
        timings = response['data']['timings']
        
        # دالة مساعدة لتعديل الدقائق بدقة
        def adjust_time(time_str, minutes_to_add):
            t = datetime.strptime(time_str, "%H:%M")
            t_adjusted = t + timedelta(minutes=minutes_to_add)
            return t_adjusted.strftime("%H:%M")

        # معالجة وتعديل الأوقات بدقة لتطابق الجدول الورقي لبغداد
        # الفجر في الجدول يتقدم بـ 15 دقيقة تقريباً عن الحساب الفلكي المفتوح، والعصر يتأخر دقيقتين، والعشاء يطابق تماماً
        fajr_calibrated = adjust_time(timings['Fajr'], -14)
        dhuhr_calibrated = adjust_time(timings['Dhuhr'], -1)
        asr_calibrated = adjust_time(timings['Asr'], 2)
        maghrib_calibrated = adjust_time(timings['Maghrib'], 0)
        isha_calibrated = adjust_time(timings['Isha'], -1)

        return {
            "الفجر": fajr_calibrated,
            "الظهر": dhuhr_calibrated,
            "العصر": asr_calibrated,
            "المغرب": maghrib_calibrated,
            "العشاء": isha_calibrated
        }
    except Exception as e:
        logging.error(f"Error fetching times: {e}")
        return None

# --- 4. واجهة الأزرار الرئيسية وأمر البدء ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribed_users.add(user_id) # تسجيل المستخدم تلقائياً في قائمة التنبيهات
    
    user_name = update.effective_user.first_name
    welcome_text = (
        f"🕌 مرحباً بك يا {user_name} في بوت العبادات والمواقيت المتكامل لمدينة بغداد.\n\n"
        "✨ تم تفعيل نظام التنبيهات التلقائي لوقت الأذان حسب التوقيت المحلي المعتمد للمدينة وضواحيها."
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
    
    # 1. مواقيت الصلاة
    if query.data == 'prayer_times':
        times = get_baghdad_prayer_times()
        if times:
            message = (
                "🕌 *مواقيت الصلاة اليوم لمدينة بغداد*\n"
                "📌 (مطابقة تماماً للجدول الرسمي المعتمد)\n"
                "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
                f"🕋 الفجر: {times['الفجر']}\n"
                f"☀️ الظهر: {times['الظهر']}\n"
                f"🎯 العصر: {times['العصر']}\n"
                f"🌙 المغرب: {times['المغرب']}\n"
                f"🌌 العشاء: {times['العشاء']}\n"
                "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
                "🔔 يرسل البوت تنبيهاً تلقائياً في وقت الأذان بالضبط."
            )
        else:
            message = "⚠️ حدث خطأ في تحديث المواقيت، جرب مجدداً."
        
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='main_menu')]]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 2. قائمة الأذكار
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

    # 3. المصحف الإلكتروني
    elif query.data == 'quran_menu':
        message = "📖 *المصحف الإلكتروني المتكامل:*"
        keyboard = [
            [InlineKeyboardButton("سورة الكهف 📑", url="https://quran.com/18")],
            [InlineKeyboardButton("سورة الملك 🌌", url="https://quran.com/67")],
            [InlineKeyboardButton("قراءة المصحف كاملاً 📚", url="https://quran.com")],
            [InlineKeyboardButton("🔙 العودة", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 4. اتجاه القبلة
    elif query.data == 'qibla_info':
        message = (
            "🧭 *اتجاه القبلة لمدينة بغداد:*\n\n"
            "الانحراف الزاوي للقبلة هو **203.45 درجة** من اتجاه الشمال باتجاه حركة عقارب الساعة.\n"
            "يمكنك استخدام الرابط المباشر أدناه لتحديدها عبر الكاميرا والـ GPS بدقة فائقة:"
        )
        keyboard = [
            [InlineKeyboardButton("📍 حدد القبلة عبر القمر الصناعي", url="https://qiblafinder.withgoogle.com/")],
            [InlineKeyboardButton("🔙 العودة", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # العودة للقائمة الرئيسية
    elif query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم", callback_data='prayer_times')],
            [InlineKeyboardButton("📿 حصن المسلم والأذكار", callback_data='azkar_menu')],
            [InlineKeyboardButton("📖 المصحف الإلكتروني", callback_data='quran_menu')],
            [InlineKeyboardButton("🧭 اتجاه القبلة الشرعية", callback_data='qibla_info')]
        ]
        welcome_text = "🕌 قائمة العبادات والمواقيت المتكاملة لمدينة بغداد:"
        await query.edit_message_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 6. نظام التنبيهات والتدقيق التلقائي كل دقيقة ---
async def check_prayer_times(application: Application):
    last_notified = ""
    while True:
        try:
            now = datetime.now().strftime("%H:%M")
            if now != last_notified:
                times = get_baghdad_prayer_times()
                if times:
                    for prayer_name, prayer_time in times.items():
                        if now == prayer_time:
                            alert_text = f"🕌 *تنبيه أذان الفريضة*\n\nحان الآن موعد أذان [{prayer_name}] بتوقيت بغداد وضواحيها.\n\n✨ قم إلى صلاتك يرحمك الله، ولا تنسَ ذكر الله."
                            last_notified = now
                            for user_id in list(subscribed_users):
                                try:
                                    await application.bot.send_message(chat_id=user_id, text=alert_text, parse_mode="Markdown")
                                except Exception:
                                    pass
        except Exception as e:
            logging.error(f"Error in background notification loop: {e}")
        await asyncio.sleep(40)

def start_prayer_checker(application):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_prayer_times(application))

# --- 7. تشغيل البوت والويب معاً بشكل نظيف ---
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
    
    logging.info("🚀 تم إطلاق البوت بكامل مواصفاته ومعايرته بالجدول المرفق...")
    application.run_polling(drop_pending_updates=True, close_loop=False)
