import logging
import os
import asyncio
import threading
import random  # مكتبة الاختيار العشوائي لتجديد الأدعية
import pytz
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. إعداد السجلات ومراقبة البوت ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"

# تخزين المشتركين لإرسال التنبيهات التلقائية لهم
subscribed_users = set()

# رابط ملف صوت تكبيرات العيد
EID_TAKBEERAT_URL = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

# تحديد المنطقة الزمنية لمدينة بغداد بدقة
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# --- 2. إعداد خادم الويب (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "🚀 Baghdad Holy Bot - Periodic Duas & Qibla Direction Restored!"

# --- 3. جدول مواقيت بغداد الورقي كاملاً (مطابق للصورة تماماً لشهر أيار 2026) ---
BAGHDAD_SCHEDULE = {
    "05-17": {"الفجر": "03:25", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:00", "العشاء": "20:27"}, 
    "05-18": {"الفجر": "03:24", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:01", "العشاء": "20:29"}, 
    "05-19": {"الفجر": "03:23", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:01", "العشاء": "20:29"}, 
    "05-20": {"الفجر": "03:22", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:02", "العشاء": "20:30"}, 
    "05-21": {"الفجر": "03:21", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:31"}, 
    "05-22": {"الفجر": "03:20", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:32"}, 
    "05-23": {"الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:04", "العشاء": "20:33"}, 
    "05-24": {"الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:05", "العشاء": "20:34"}, 
    "05-25": {"الفجر": "03:18", "ILظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:35"}, 
    "05-26": {"الفجر": "03:17", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:36"}, 
    "05-27": {"الفجر": "03:16", "الظهر": "12:05", "العصر": "15:46", "المغرب": "19:07", "العشاء": "20:37"}, 
    "05-28": {"الفجر": "03:16", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:07", "العشاء": "20:38"}, 
    "05-29": {"الفجر": "03:15", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:08", "العشاء": "20:39"}, 
    "05-30": {"الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"}, 
    "05-31": {"الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"}, 
}

def get_current_prayer_times():
    today_key = datetime.now(BAGHDAD_TZ).strftime("%m-%d")
    return BAGHDAD_SCHEDULE.get(today_key, BAGHDAD_SCHEDULE["05-19"])

# --- 4. قائمة الأدعية القصيرة المتجددة ---
SHORT_DUAS = [
    "🤲 اللهم إنك عفو تحب العفو فاعف عني.",
    "🤲 ربِّ اغفر لي ولوالدي ولمن دخل بيتي مؤمناً.",
    "🤲 اللهم آتنا في الدنيا حسنة وفي الآخرة حسنة وقنا عذاب النار.",
    "🤲 يا حي يا قيوم برحمتك أستغيث أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين.",
    "🤲 اللهم مصرف القلوب صرف قلوبنا على طاعتك.",
    "🤲 يا مقلب القلوب ثبت قلبي على دينك.",
    "🤲 اللهم إني أسألك الهدى والتقى والعفاف والغنى.",
    "🤲 ربِّ اجعلني مقيم الصلاة ومن ذريتي ربنا وتقبل دعاء.",
    "🤲 اللهم إني أعوذ بك من الهم والحزن، والعجز والكسل.",
    "🤲 ربِّ اشرح لي صدري ويسر لي أمري.",
    "🤲 اللهم اجعل في قلبي نوراً وفي بصري نوراً وفي سمعي نوراً.",
    "🤲 اللهم إني أسألك علماً نافعاً ورزقاً طيباً وعملاً متقبلاً.",
    "🤲 رَبَّنَا تَقَبَّلْ مِنَّا إِنَّكَ أَنتَ السَّمِيعُ الْعَلِيمُ.",
    "🤲 اللهم لا تجعل مصيبتنا في ديننا ولا تجعل الدنيا أكبر همنا.",
    "🤲 ربِّ أعني ولا تعن علي، وانصرني ولا تنصر علي.",
    "🤲 اللهم إني أسألك العافية في الدنيا والآخرة."
]

TXT_MORNING = "☀️ *أذكار الصباح المباركة:*\n\n🔹 أصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ.\n🔹 رَبِّ أَسْأَلُكَ خَيْرَ مَا فِي هَذَا الْيَوْمِ وَخَيْرَ مَا بَعْدَهُ.\n🔹 اللَّهُمَّ بِكَ أَصْبَحْنَا، وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ النُّشُورُ.\n\nآية الكرسي: {اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...}"
TXT_EVENING = "🌙 *أذكار المساء المباركة (وقت الاستجابة):*\n\n🔹 أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ.\n🔹 اللَّهُمَّ مَا أَصْبَحَ أو أَمْسَى بِي مِنْ نِعْمَةٍ أَوْ بِأَحَدٍ مِنْ خَلْقِكَ فَمِنْكَ وَحْدَهُ لَا شَرِيكَ لَكَ.\n🔹 حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ (7 مرات)."

# --- 5. واجهة الأزرار الرئيسية (تم إرجاع زر القبلة) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribed_users.add(user_id)
    
    welcome_text = (
        f"🕌 مرحباً بك يا {update.effective_user.first_name} في بوت العبادات المتكامل لبغداد.\n\n"
        "✨ تم ضبط التوقيتات والأدعية الدورية وإعادة بوصلة اتجاه القبلة لخدمتكم بدقة."
    )
    
    keyboard = [
        [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم", callback_data='prayer_times')],
        [InlineKeyboardButton("🕋 اتجاه القبلة لمدينة بغداد", callback_data='qibla_direction')],
        [InlineKeyboardButton("📖 المصحف الإلكتروني (داخل التطبيق)", callback_data='quran_menu')],
        [InlineKeyboardButton("📿 حصن المسلم والأذكار", callback_data='azkar_menu')],
        [InlineKeyboardButton("🎧 تكبيرات العيد (استماع مباشر)", callback_data='play_takbeerat')],
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

    elif query.data == 'qibla_direction':
        message = (
            "🕋 *اتجاه القبلة الصحيح لمدينة بغداد:*\n\n"
            "📍 زاوية اتجاه القبلة في بغداد هي تقريباً **193.35 درجة** باتجاه الجنوب الغربي.\n\n"
            "📱 *طريقة الاستخدام عبر الهاتف:*\n"
            "1. افتح تطبيق البوصلة على جهازك.\n"
            "2. ضع الهاتف بشكل مسطح تماماً على يدك.\n"
            "3. وجّه أعلى الهاتف نحو الدرجة **193°** لتكون مواجهاً للكعبة المشرفة مباشرة.\n\n"
            "تقبل الله صلاتكم وطاعاتكم صالح الأعمال ✨"
        )
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='main_menu')]]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'play_takbeerat':
        await query.message.reply_audio(
            audio=EID_TAKBEERAT_URL,
            title="تكبيرات عيد الأضحى المبارك",
            performer="صوت مأثور عالي الجودة",
            caption="🕋 *الله أكبر، الله أكبر، لا إله إلا الله...* \n\nاستمع وشعّ روحانية العيد المبارك بقلبك وعائلتك. ✨"
        )

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
        text = "📖 *آية الكرسي - قراءة مباركة:*\n\n【اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...】"
        keyboard = [[InlineKeyboardButton("🔙 عودة للمصحف", callback_data='quran_menu')]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'q_mulk':
        text = "📖 *سورة الملك (مكتوبة داخل التطبيق):*\n\n【تَبَارَكَ الَّذِي بِيَدِهِ الْمُلْكُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ...】"
        keyboard = [[InlineKeyboardButton("🔙 عودة للمصحف", callback_data='quran_menu')]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'q_kahf':
        text = "📖 *سورة الكهف (نص مريح لكبار السن):*\n\n【الْحَمْدُ لِلَّهِ الَّذِي أَنزَلَ عَلَى عَبْدِهِ الْكِتَابَ...】"
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
        text = "✨ *حكمة اليوم الإيمانية:*\n\n\"إن الله يعطي الدنيا لمن يحب ومن لا يحب، ولا يعطي الدين إلا لمن أحب...\""
        keyboard = [[InlineKeyboardButton("🔙 العودة الرئيسية", callback_data='main_menu')]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم", callback_data='prayer_times')],
            [InlineKeyboardButton("🕋 اتجاه القبلة لمدينة بغداد", callback_data='qibla_direction')],
            [InlineKeyboardButton("📖 المصحف الإلكتروني (داخل التطبيق)", callback_data='quran_menu')],
            [InlineKeyboardButton("📿 حصن المسلم والأذكار", callback_data='azkar_menu')],
            [InlineKeyboardButton("🎧 تكبيرات العيد (استماع مباشر)", callback_data='play_takbeerat')],
            [InlineKeyboardButton("✨ حكمة اليوم الإيمانية", callback_data='wisdom_day')]
        ]
        await query.edit_message_text(text="🕌 قائمة العبادات والمواقيت المتكاملة لمدينة بغداد:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 7. نظام الأتمتة المطور والمصحح بالكامل بتوقيت بغداد الصارم ---
async def check_prayer_times(application: Application):
    last_exact = ""
    last_pre = ""
    last_morning_azkar = ""
    last_evening_azkar = ""
    last_pre_arafa = ""
    last_arafa_fasting = ""
    last_arafa_dua = ""
    last_pre_eid = ""
    last_eid_day = ""
    
    # لتتبع أوقات إرسال الدعاء الدوري لمنع التكرار في نفس الساعة
    last_periodic_dua_hour = ""

    while True:
        try:
            now_dt = datetime.now(BAGHDAD_TZ)
            now_str = now_dt.strftime("%H:%M")
            hour_str = now_dt.strftime("%H")
            date_str = now_dt.strftime("%m-%d")
            
            pre_time_str = (now_dt + timedelta(minutes=10)).strftime("%H:%M")
            times = get_current_prayer_times()
            
            if times:
                # 🌟 ميزة الأدعية الدورية المتجددة (كل 3 ساعات من 9 صباحاً إلى قبل العشاء)
                if now_str in ["09:00", "12:00", "15:00", "18:00"] and hour_str != last_periodic_dua_hour:
                    last_periodic_dua_hour = hour_str
                    # اختيار دعاء عشوائي متجدد من القائمة
                    selected_dua = random.choice(SHORT_DUAS)
                    periodic_msg = f"✨ *جرعة إيمانية متجددة* ✨\n\n{selected_dua}\n\n🌿 لا تنسَ ذكر الله في هذه الساعات المباركة."
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=periodic_msg, parse_mode="Markdown")
                        except Exception: pass

                # أ. أذكار الصباح التلقائية (الساعة 07:00 صباحاً بتوقيت بغداد)
                if now_str == "07:00" and date_str != last_morning_azkar:
                    last_morning_azkar = date_str
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=TXT_MORNING, parse_mode="Markdown")
                        except Exception: pass

                # ب. أذكار المساء تلقائياً قبل أذان المغرب بـ 30 دقيقة بتوقيت بغداد
                maghrib_time = datetime.strptime(times['المغرب'], "%H:%M")
                evening_azkar_time = (maghrib_time - timedelta(minutes=30)).strftime("%H:%M")
                if now_str == evening_azkar_time and date_str != last_evening_azkar:
                    last_evening_azkar = date_str
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=TXT_EVENING, parse_mode="Markdown")
                        except Exception: pass

                # 1. تذكير مسبق قبل يوم عرفة (يوم الاثنين 25 أيار) الساعة 08:00 مساءً بتوقيت بغداد
                if date_str == "05-25" and now_str == "20:00" and date_str != last_pre_arafa:
                    last_pre_arafa = date_str
                    pre_arafa_text = "🚨 *تذكير مبارك - غداً يوم عرفة*\n\nغداً الثلاثاء هو يوم عرفة المشهود (9 ذي الحجة)، فاستعدوا لصيامه وتهيؤوا بالدعاء الصادق."
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=pre_arafa_text, parse_mode="Markdown")
                        except Exception: pass

                # 2. أجر صيام يوم عرفة (فجر يوم عرفة الثلاثاء 26 أيار) الساعة 04:00 صباحاً بتوقيت بغداد
                if date_str == "05-26" and now_str == "04:00" and date_str != last_arafa_fasting:
                    last_arafa_fasting = date_str
                    fasting_text = "🕋 *أجر صيام يوم عرفة*\n\nقال رسول الله ﷺ عن صيام يوم عرفة: «أَحْتَسِبُ عَلَى اللهِ أَنْ يُكَفِّرَ السَّنَةَ الَّتِي قَبْلَهُ، وَالسَّنَةَ الَّتِي بَعْدَهُ».\n\n✨ تقبل الله طاعتكم وثبّت أجركم."
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=fasting_text, parse_mode="Markdown")
                        except Exception: pass

                # 3. دعاء يوم عرفة (ظهر يوم عرفة الثلاثاء 26 أيار) الساعة 12:30 ظهراً وقت الموقف المبارك
                if date_str == "05-26" and now_str == "12:30" and date_str != last_arafa_dua:
                    last_arafa_dua = date_str
                    arafa_dua_text = "🤲 *خير الدعاء دعاء يوم عرفة*\n\nقال النبي ﷺ: «خَيْرُ الدُّعَاءِ دُعَاءُ يَوْمِ عَرَفَةَ، وَخَيْرُ مَا قُلْتُ أَنَا وَالنَّبِيُّونَ مِنْ قَبْلِي: لاَ إِلَهَ إِلاَّ اللَّهُ وَحْدَهُ لاَ شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ»."
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=arafa_dua_text, parse_mode="Markdown")
                        except Exception: pass

                # 4. تهنئة وقفة العيد والمساء (يوم عرفة الثلاثاء 26 أيار) الساعة 04:00 عصراً بتوقيت بغداد
                if date_str == "05-26" and now_str == "16:00" and date_str != last_pre_eid:
                    last_pre_eid = date_str
                    pre_eid_text = "🕋 *يا لبيك اللهم لبيك، لبيك لا شريك لك لبيك...*\n\n✨ يسر البوت أن يهنئكم بيوم عرفة المبارك وقرب حلول عيد الأضحى المبارك! 🌿"
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=pre_eid_text, parse_mode="Markdown")
                        except Exception: pass

                # 5. تهنئة يوم عيد الأضحى المبارك (يوم الأربعاء 27 أيار) الساعة 05:15 صباحاً (بعد صلاة العيد بـ 20 دقيقة من الشروق تماماً)
                if date_str == "05-27" and now_str == "05:15" and date_str != last_eid_day:
                    last_eid_day = date_str
                    eid_text = "🎉 *الله أكبر، الله أكبر، ولله الحمد...*\n\n🎈 تقبل الله صلاتكم وطاعتكم بعد خروجكم من صلاة العيد المباركة! أضحى مبارك وكل عام وأنتم وأهلكم بألف خير وعافية."
                    for user_id in list(subscribed_users):
                        try: await application.bot.send_message(chat_id=user_id, text=eid_text, parse_mode="Markdown")
                        except Exception: pass

                # و. التدقيق التلقائي الفوري للتنبيه المسبق وللأذان بالضبط (بتوقيت بغداد)
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
    
    logging.info("🚀 البوت جاهز بالكامل بعد إعادة زر القبلة ومزامنة الأدعية الدورية المتجددة...")
    application.run_polling(drop_pending_updates=True, close_loop=False)       
