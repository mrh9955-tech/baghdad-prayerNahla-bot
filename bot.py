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
    return "🚀 Baghdad Holy Bot - Advanced Notifications & Eid Schedule is Live!"

# --- 3. جدول مواقيت بغداد الورقي كاملاً ---
BAGHDAD_SCHEDULE = {
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
    "06-12": {"الفجر": "03:10", "الظهر": "12:07", "العصر": "15:49", "المغرب": "19:15", "العشاء": "20:48"}, 
    "06-13": {"الفجر": "03:10", "الظهر": "12:08", "العصر": "15:49", "المغرب": "19:16", "العشاء": "20:49"}, 
    "06-14": {"الفجر": "03:10", "الظهر": "12:08", "العصر": "15:50", "المغرب": "19:16", "العشاء": "20:49"}, 
    "06-15": {"الفجر": "03:10", "الظهر": "12:08", "العصر": "15:50", "المغرب": "19:16", "العشاء": "20:50"}, 
}

def get_current_prayer_times():
    today_key = datetime.now().strftime("%m-%d")
    return BAGHDAD_SCHEDULE.get(today_key, BAGHDAD_SCHEDULE["05-18"])

# --- 4. نصوص الأذكار والسور المقروءة داخلياً ---
TXT_MORNING = "☀️ *أذكار الصباح المباركة:*\n\n🔹 أصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ.\n🔹 رَبِّ أَسْأَلُكَ خَيْرَ مَا فِي هَذَا الْيَوْمِ وَخَيْرَ مَا بَعْدَهُ.\n🔹 اللَّهُمَّ بِكَ أَصْبَحْنَا، وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ النُّشُورُ.\n\nآية الكرسي: {اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...}"
TXT_EVENING = "🌙 *أذكار المساء المباركة (وقت الاستجابة):*\n\n🔹 أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ.\n🔹 اللَّهُمَّ مَا أَصْبَحَ أو أَمْسَى بِي مِنْ نِعْمَةٍ أَوْ بِأَحَدٍ مِنْ خَلْقِكَ فَمِنْكَ وَحْدَهُ لَا شَرِيكَ لَكَ.\n🔹 حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ (7 مرات)."

DEE_TEN_DAYS = "📿 *من أدعية العشر الأواخر من ذي الحجة:*\n\n\"اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنِّي، اللَّهُمَّ اجْعَلْنَا فِي هَذِهِ الأَيَّامِ الْمُبَارَكَةِ مِمَّنْ قَبِلْتَ صِيَامَهُمْ وَقِيَامَهُمْ وَغَفَرْتَ ذُنُوبَهُمْ\"."

# --- 5. واجهة الأزرار الرئيسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribed_users.add(user_id)
    
    welcome_text = (
        f"🕌 مرحباً بك يا {update.effective_user.first_name} في بوت العبادات المتكامل لبغداد.\n\n"
        "✨ نظام التنبيه التلقائي المطور يعمل بالخلفية لخدمتك (تنبيهات أذان مسبقة + أذكار مؤتمتة + تهاني العيد السعيد)."
    )
    
    keyboard = [
        [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم", callback_data='prayer_times')],
        [InlineKeyboardButton("📖 المصحف الإلكتروني (داخل التطبيق)", callback_data='quran_menu')],
        [InlineKeyboardButton("📿 حصن المسلم والأذكار", callback_data='azkar_menu')],
        [InlineKeyboardButton("✨ حكمة اليوم الإيمانية", callback_data='wisdom_day')]
    ]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 6. لوحة التحكم والتحويل الداخلي ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'prayer_times':
        times = get_current_prayer_times()
        message = (
            "🕌 *مواقيت الصلاة اليوم لمدينة بغداد*\n"
            "📌 (مطابقة لجدول الأوقات الورقي بالكامل 100%)\n"
            "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
            f"🕋 الفجر: {times['الفجر']} | ☀️ الظهر: {times['الظهر']}\n"
            f"🎯 العصر: {times['العصر']} | 🌙 المغرب: {times['المغرب']}\n"
            f"🌌 العشاء: {times['العشاء']}\n"
            "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
            "🔔 يرسل البوت التنبيهات التلقائية والأذكار بوقتها الشرعي مباركاً."
        )
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='main_menu')]]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'quran_menu':
        message = "📖 *المصحف الإلكتروني المتكامل داخل التليكرام:*\n(سهل جداً ومناسب لكبار السن دون روابط خارجية)"
        keyboard = [
            [InlineKeyboardButton("👑 آية الكرسي", callback_data='q_kursi')],
            [InlineKeyboardButton("📑 سورة الكهف كاملة", callback_data='q_kahf')],
            [InlineKeyboardButton("🌌 سورة الملك كاملة", callback_data='q_mulk')],
            [InlineKeyboardButton("🔙 العودة", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'q_kursi':
        text = "📖 *آية الكرسي - قراءة مباركة:*\n\n【اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۚ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ】"
        keyboard = [[InlineKeyboardButton("🔙 عودة للمصحف", callback_data='quran_menu')]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'q_mulk':
        text = "📖 *سورة الملك (مكتوبة داخل التطبيق):*\n\n【تَبَارَكَ الَّذِي بِيَدِهِ الْمُلْكُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ ۝ الَّذِي خَلَقَ الْمَوْتَ وَالْحَيَاةَ لِيَبْلُوَكُمْ أَيُّكُمْ أَحْسَنُ عَمَلًا وَهُوَ الْعَزِيزُ الْغَفُورُ ۝ الَّذِي خَلَقَ سَبْعَ سَمَاوَاتٍ طِبَاقًا مَّا تَرَى فِي خَلْقِ الرَّحْمَنِ مِن تَفَاوُتٍ فَارْجِعِ الْبَصَرَ هَلْ تَرَى مِن فُطُورٍ...】"
        keyboard = [[InlineKeyboardButton("🔙 عودة للمصحف", callback_data='quran_menu')]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'q_kahf':
        text = "📖 *سورة الكهف (نص مريح لكبار السن):*\n\n【الْحَمْدُ لِلَّهِ الَّذِي أَنزَلَ عَلَى عَبْدِهِ الْكِتَابَ وَلَمْ يَجْعَل لَّهُ عِوجًا ۜ ۝ قَيِّمًا لِّيُنذِرَ بَأْسًا شَدِيدًا مِّن لَّدُنْهُ وَيُبَشِّرَ الْمُؤْمِنِينَ الَّذِينَ يَعْمَلُونَ الصَّالِحَاتِ أَنَّ لَهُمْ أَجْرًا حَسَنًا ۝ مَّاكِثِينَ فِيهِ أَبَدًا...】"
        keyboard = [[InlineKeyboardButton("🔙 عودة للمصحف", callback_data='quran_menu')]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'azkar_menu':
        message = "📿 *حصن المسلم والأذكار اليومية المكتوبة:* "
        keyboard = [
            [InlineKeyboardButton("☀️ أذكار الصباح", callback_data='view_morning')],
            [InlineKeyboardButton("🌙 أذكار المساء", callback_data='view_evening')],
            [InlineKeyboardButton("🔙 العودة", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'view_morning':
        keyboard = [[InlineKeyboardButton("🔙 عودة للأذكار", callback_data='azkar_menu')]]
        await query.edit_message_text(text=TXT_MORNING, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'view_evening':
        keyboard = [[InlineKeyboardButton("🔙 عودة للأذكار", callback_data='azkar_menu')]]
        await query.edit_message_text(text=TXT_EVENING, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'wisdom_day':
        text = "✨ *حكمة اليوم الإيمانية:*\n\n\"إن الله يعطي الدنيا لمن يحب ومن لا يحب، ولا يعطي الدين إلا لمن أحب، فمن أعطاه الدين فقد أحبه. جعلنا الله وإياكم من أحبابه.\""
        keyboard = [[InlineKeyboardButton("🔙 العودة الرئيسية", callback_data='main_menu')]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم", callback_data='prayer_times')],
            [InlineKeyboardButton("📖 المصحف الإلكتروني (داخل التطبيق)", callback_data='quran_menu')],
            [InlineKeyboardButton("📿 حصن المسلم والأذكار", callback_data='azkar_menu')],
            [InlineKeyboardButton("✨ حكمة اليوم الإيمانية", callback_data='wisdom_day')]
        ]
        await query.edit_message_text(text="¼️ قائمة العبادات والمواقيت المتكاملة لمدينة بغداد:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 7. نظام الأتمتة المطور ومعايدات العيد المجدولة ---
async def check_prayer_times(application: Application):
    last_exact = ""
    last_pre = ""
    last_morning_azkar = ""
    last_evening_azkar = ""
    last_dua_day = ""
    last_pre_eid = ""
    last_eid_day = ""

    while True:
        try:
            now_dt = datetime.now()
            now_str = now_dt.strftime("%H:%M")
            date_str = now_dt.strftime("%m-%d")
            
            pre_time_str = (now_dt + timedelta(minutes=10)).strftime("%H:%M")
            times = get_current_prayer_times()
            
            if times:
                # أ. إرسال أذكار الصباح التلقائية الساعة 07:00 صباحاً
                if now_str == "07:00" and date_str != last_morning_azkar:
                    last_morning_azkar = date_str
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=TXT_MORNING, parse_mode="Markdown")
                        except Exception: pass

                # ب. إرسال أدعية العشر الأواخر من ذي الحجة (من 5 حزيران إلى 15 حزيران) الساعة 02:00 ظهراً
                if "06-05" <= date_str <= "06-15":
                    if now_str == "14:00" and date_str != last_dua_day:
                        last_dua_day = date_str
                        for user_id in list(subscribed_users):
                            try: await application.bot.send_message(chat_id=user_id, text=DEE_TEN_DAYS, parse_mode="Markdown")
                            except Exception: pass

                # ج. أذكار المساء تلقائياً قبل أذان المغرب بـ 30 دقيقة
                maghrib_time = datetime.strptime(times['المغرب'], "%H:%M")
                evening_azkar_time = (maghrib_time - timedelta(minutes=30)).strftime("%H:%M")
                if now_str == evening_azkar_time and date_str != last_evening_azkar:
                    last_evening_azkar = date_str
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=TXT_EVENING, parse_mode="Markdown")
                        except Exception: pass

                # د. تهنئة وقفة العيد (يوم عرفة - 26 حزيران) الساعة 04:00 عصراً
                if date_str == "06-26" and now_str == "16:00" and date_str != last_pre_eid:
                    last_pre_eid = date_str
                    pre_eid_text = "🕋 *يا لبيك اللهم لبيك، لبيك لا شريك لك لبيك...*\n\n✨ يسر البوت أن يهنئكم بيوم عرفة المبارك، سائلين الله سبحانه أن يتقبل دعاءكم وصالح أعمالكم، وكل عام وأنتم بخير وصحة بمناسبة قرب حلول عيد الأضحى المبارك! 🌿"
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=pre_eid_text, parse_mode="Markdown")
                        except Exception: pass

                # هـ. تهنئة يوم عيد الأضحى (يوم العيد - 27 حزيران) الساعة 06:30 صباحاً (بعد صلاة العيد)
                if date_str == "06-27" and now_str == "06:30" and date_str != last_eid_day:
                    last_eid_day = date_str
                    eid_text = "🎉 *الله أكبر، الله أكبر، لا إله إلا الله، الله أكبر، الله أكبر، ولله الحمد...*\n\n🎈 تقبل الله صلاتكم وطاعتكم بعد خروجكم من صلاة العيد! أضحى مبارك وكل عام وأنتم وأهلكم بألف خير وعافية وسعادة ونعمة من الله. عساكم من عواده دائمًا. ✨"
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=eid_text, parse_mode="Markdown")
                        except Exception: pass

                # و. التدقيق السريع للتنبيه المسبق وللأذان بالضبط
                for prayer_name, prayer_time in times.items():
                    if pre_time_str == prayer_time and pre_time_str != last_pre:
                        last_pre = pre_time_str
                        pre_msg = f"🚨 *تذكير مسبق*\n\nمتبقي **10 دقائق** على رفع أذان [{prayer_name}] بتوقيت بغداد.\n\n🍃 تهيأ للوضوء والاستعداد للصلاة يرحمك الله."
                        for user_id in list(subscribed_users):
                            try: await application.bot.send_message(chat_id=user_id, text=pre_msg, parse_mode="Markdown")
                            except Exception: pass

                    if now_str == prayer_time and now_str != last_exact:
                        last_exact = now_str
                        exact_msg = f"🕌 *تنبيه أذان الفريضة*\n\nحان الآن موعد أذان [{prayer_name}] بحسب التوقيت المحلي لمدينة بغداد.\n\n✨ قم إلى صلاتك يرحمك الله."
                        for user_id in list(subscribed_users):
                            try: await application.bot.send_message(chat_id=user_id, text=exact_msg, parse_mode="Markdown")
                            except Exception: pass

        except Exception as e:
            logging.error(f"Error in automated loop: {e}")
        await asyncio.sleep(20)

def start_prayer_checker(application):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_prayer_times(application))

# --- 8. التشغيل والربط ---
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
    
    logging.info("🚀 البوت الفخم يعمل الآن بحسابات الأعياد والمعايدات الجديدة...")
    application.run_polling(drop_pending_updates=True, close_loop=False)
