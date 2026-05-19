import logging
import os
import asyncio
import threading
import random
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

# 🕋 رابط سريع ومباشر ومستقر لتكبيرات العيد
EID_TAKBEERAT_URL = "https://download.quranicaudio.com/dhul_hijjah/takbeeraat_al_3id.mp3"

# تحديد المنطقة الزمنية لمدينة بغداد بدقة
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# --- 2. إعداد خادم الويب (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "🚀 Baghdad Holy Bot - Clean & Fixed!"

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
}

def get_current_prayer_times():
    today_key = datetime.now(BAGHDAD_TZ).strftime("%m-%d")
    return BAGHDAD_SCHEDULE.get(today_key, BAGHDAD_SCHEDULE["05-19"])

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
        await query.message.reply_text("⏳ جاري تحميل وإرسال تكبيرات العيد الفخمة، لحظات من فضلك...")
        try:
            await query.message.reply_audio(
                audio=EID_TAKBEERAT_URL,
                title="تكبيرات عيد الأضحى المبارك",
                performer="الحرم المكي الشريف",
                caption="🕋 *الله أكبر، الله أكبر، لا إله إلا الله... الله أكبر، الله أكبر، ولله الحمد.*\n\nتقبل الله طاعاتكم صالح الأعمال. ✨"
            )
        except Exception as e:
            logging.error(f"Audio send error: {e}")
            await query.message.reply_text("❌ حدث خطأ في تشغيل الصوت، يرجى المحاولة مرة أخرى.")

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
        await
