import logging
import os
import asyncio
import threading
import random
import pytz
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- 1. إعداد السجلات ومراقبة البوت ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"

# 👑 معرف حسابك الخاص كأدمن
ADMIN_ID = 1007425134

# تخزين المشتركين لإرسال التنبيهات التلقائية لهم
subscribed_users = set()

# تحديد المنطقة الزمنية لمدينة بغداد بدقة
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# --- 2. إعداد خادم الويب (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "🚀 Baghdad Holy Bot - Dynamic Wisdom System Active!"

# --- 3. قاعدة البيانات النصية الكاملة للمصحف والأذكار والأدعية ---

TXT_KURSI = (
    "👑 *آية الكرسي كاملة بالتشكيل:*\n\n"
    "《اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ "
    "لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ "
    "يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ "
    "وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ》\n\n"
    "✨ *فضلها:* من قرأها دبر كل صلاة مكتوبة لم يمنعه من دخول الجنة إلا أن يموت."
)

TXT_MULK = (
    "🌌 *سورة الملك كاملة بالتشكيل:*\n\n"
    "بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ\n"
    "تَبَارَكَ الَّذِي بِيَدِهِ الْمُلْكُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ (1) الَّذِي خَلَقَ الْمَوْتَ وَالْحَيَاةَ لِيَبْلُوَكُمْ أَيُّكُمْ أَحْسَنُ عَمَلًا وَهُوَ الْعَزِيزُ الْغَفُورُ (2) "
    "الَّذِي خَلَقَ سَبْعَ سَمَاوَاتٍ طِبَاقًا مَّا تَرَى فِي خَلْقِ الرَّحْمَـٰنِ مِن تَفَاوُتٍ فَارْجِعِ الْبَصَرَ هَلْ تَرَى مِن فُطُورٍ (3) ثُمَّ ارْجِعِ الْبَصَرَ كَرَّتَيْنِ يَنقَلِبْ إِلَيْكَ الْبَصَرُ خَاسِئًا وَهُوَ حَسِيرٌ (4) "
    "وَلَقَدْ زَيَّنَّا السَّمَاءَ الدُّنْيَا بِمَصَابِيحَ وَجَعَلْنَاهَا رُجُومًا لِّلشَّيَاطِينِ وَأَعْتَدْنَا لَهُمْ عَذَابَ السَّعِيرِ (5) وَلِلَّذِينَ كَفَرُوا بِرَبِّهِمْ عَذَابُ جَهَنَّمَ وَبِئْسَ الْمَصِيرُ (6) "
    "إِذَا أُلْقُوا فِيهَا سَمِعُوا لَهَا شَهِيقًا وَهِيَ تَفُورُ (7) تَكَادُ تَمَيَّزُ مِنَ الْغَيْظِ كُلَّمَا أُلْقِيَ فِيهَا فَوْجٌ سَأَلَهُمْ خَزَنَتُهَا أَلَمْ يَأْتِكُمْ نَذِيرٌ (8) قَالُوا بَلَى قَدْ جَاءَنَا نَذِيرٌ فَكَذَّبْنَا وَقُلْنَا مَا نَزَّلَ اللَّهُ مِن شَيْءٍ إِنْ أَنتُمْ إِلَّا فِي ضَلَالٍ كَبِيرٍ (9) "
    "وَقَالُوا لَوْ كُنَّا نَسْمَعُ أَوْ نَعْقِلُ مَا كُنَّا فِي أَصْحَابِ السَّعِيرِ (10) فَاعْتَرَفُوا بِذَنبِهِمْ فَسُحْقًا لِّأَصْحَابِ السَّعِيرِ (11) إِنَّ الَّذِينَ يَخْشَوْنَ رَبَّهُم بِالْغَيْبِ لَهُم مَّغْفِرَةٌ وَأَجْرٌ كَبِيرٌ (12) "
    "وَأَسِرُّوا قَوْلَكُمْ أَوِ اجْهَرُوا بِهِ إِنَّهُ عَلِيمٌ بِذَاتِ الصُّدُورِ (13) أَلَا يَعْلَمُ مَنْ خَلَقَ وَهُوَ اللَّطِيفُ الْخَبِيرُ (14) هُوَ الَّذِي جَعَلَ لَكُمُ الْأَرْضَ ذَلُولًا فَامْشُوا فِي مَنَاكِبِهَا وَكُلُوا مِن رِّزْقِهِ وَإِلَيْهِ النُّشُورُ (15) "
    "أَأَمِنتُم مَّن فِي السَّمَاءِ أَن يَخْسِفَ بِكُمُ الْأَرْضَ فَإِذَا هِيَ تَمُورُ (16) أَمْ أَمِنتُم مَّن فِي السَّمَاءِ أَن يُرْسِلَ عَلَيْكُمْ حَاصِبًا فَسَتَعْلَمُونَ كَيْفَ نَذِيرٍ (17) وَلَقَدْ كَذَّبَ الَّذِينَ مِن قَبْلِهِمْ فَكَيْفَ كَانَ نَكِيرٍ (18) "
    "أَوَلَمْ يَرَوْا إِلَى الطَّيْرِ فَوْقَهُمْ صَافَّاتٍ وَيَقْبِضْنَ مَا يُمْسِكُهُنَّ إِلَّا الرَّحْمَـٰنُ إِنَّهُ بِكُلِّ شَيْءٍ بَصِيرٌ (19) أَمَّنْ هَـٰذَا الَّذِي هُوَ جُندٌ لَّكُمْ يَنصُرُكُم مِّن دُونِ الرَّحْمَـٰنِ إِنِ الْكَافِرُونَ إِلَّا فِي غُرُورٍ (20) "
    "أَمَّنْ هَـٰذَا الَّذِي يَرْزُقُكُمْ إِنْ أَمْسَكَ رِزْقَهُ بَلْ لَّجُّوا فِي عُتُوٍّ وَنُفُورٍ (21) أَفَمَن يَمْشِي مُكِبًّا عَلَىٰ وَجْهِهِ أَهْدَىٰ أَمَّن يَمْشِي سَوِيًّا عَلَىٰ صِرَاطٍ مُّسْتَقِيمٍ (22) "
    "قُل *هُوَ الَّذِي أَنشَأَكُمْ وَجَعَلَ لَكُمُ السَّمْعَ وَالْأَبْصَارَ وَالْأَفْئِدَةَ قَلِيلًا مَّا تَشْكُرُونَ (23) قُلْ هُوَ الَّذِي ذَرَأَكُمْ فِي الْأَرْضِ وَإِلَيْهِ تُحْشَرُونَ (24) وَيَقُولُونَ مَتَىٰ هَـٰذَا الْوَعْدُ إِن كُنتُمْ صَادِقِينَ (25) قُلْ إِنَّمَا الْعِلْمُ عِندَ اللَّهِ وَإِنَّمَا أَنَا نَذِيرٌ مُّبِينٌ (26) فَلَمَّا رَأَوْهُ زُلْفَةً سِيئَتْ وُجُوهُ الَّذِينَ كَفَرُوا وَقِيلَ هَـٰذَا الَّذِي كُنتُم بِهِ تَدَّعُونَ (27) قُلْ أَرَأَيْتُمْ إِنْ أَهْلَكَنِيَ اللَّهُ وَمَن مَّعِيَ أَوْ رَحِمَنَا فَمَن يُجِيرُ الْكَافِرِينَ مِنْ عَذَابٍ أَلِيمٍ (28) قُل_ هُوَ الرَّحْمَـٰنُ آمَنَّا بِهِ وَعَلَيْهِ تَوَكَّلْنَا فَسَتَعْلَمُونَ مَنْ هُوَ فِي ضَلَالٍ مُّبِينٍ (29) قُلْ أَرَأَيْتُمْ إِنْ أَصْبَحَ مَاؤُكُمْ غَوْرًا فَمَن يَأْتِيكُم بِمَاءٍ مَّعِينٍ (30)*"
)

TXT_QISAR = (
    "📖 *قصار السور كاملة بالتشكيل:*\n\n"
    "🥇 *سورة الإخلاص:*\n"
    "بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ\n"
    "قُلْ هُوَ اللَّهُ أَحَدٌ (1) اللَّهُ الصَّمَدُ (2) لَمْ يَلِدْ وَلَمْ يُولَدْ (3) وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ (4)\n\n"
    "🥈 *سورة الفلق:*\n"
    "بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ\n"
    "قُل *أَعُوذُ بِرَبِّ الْفَلَقِ (1) مِن شَرِّ مَا خَلَقَ (2) وَمِن شَرِّ غَاسِقٍ إِذَا وَقَب (3) وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ (4) وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ (5)*\n\n"
    "🥉 *سورة الناس:*\n"
    "بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ\n"
    "قُل *أَعُوذُ بِرَبِّ النَّاسِ (1) مَلِكِ النَّاسِ (2) إِلَـٰهِ النَّاسِ (3) مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ (4) الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ (5) مِنَ الْجِنَّةِ وَالنَّاسِ (6)*\n\n"
    "🏅 *سورة الكوثر:*\n"
    "بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ\n"
    "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ (1) فَصَلِّ لِرَبِّكَ وَانْحَرْ (2) إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ (3)"
)

TXT_MORNING = (
    "☀️ *أذكار الصباح المباركة كاملة:*\n\n"
    "🔹 *أصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ* وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ.\n\n"
    "🔹 *اللَّهُمَّ بِكَ أَصْبَحْنَا*، وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ النُّشُورُ.\n\n"
    "🔹 *اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ*، خَلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت.\n\n"
    "🔹 *بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ* فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ. (3 مرات)"
)

TXT_EVENING = (
    "🌙 *أذكار المساء المباركة كاملة:*\n\n"
    "🔹 *أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ* وَالْحَمْدُ لِلَّهِ.\n\n"
    "🔹 *اللَّهُمَّ بِكَ أَمْسَيْنَا*، وَبِكَ أَصْبَحْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ الْمَصِيرُ.\n\n"
    "🔹 *حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ* عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ. (7 مرات)\n\n"
    "🔹 *أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ* مِنْ شَرِّ مَا خَلَقَ. (3 مرات)"
)

TXT_HAMM = (
    "🤲 *أذكار وأدعية الهم والفرج وتفريج الكرب:*\n\n"
    "🔹 *دعاء الكرب:* لَا إِلَهَ إِلَّا اللَّهُ الْعَظِيمُ الْحَلِيمُ، لَا إِلَهَ إِلَّا اللَّهُ رَبُّ الْعَرْشِ الْعَظِيمِ.\n\n"
    "🔹 *دعاء ذي النون:* لَّا إِلَـٰهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ.\n\n"
    "🔹 *اللَّهُمَّ رَحْمَتَكَ أَرْجُو* فَلَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ، وَأَصْلِحْ لِي شَأْنِي كُلَّهُ.\n\n"
    "🔹 *اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ*، وَالْعَجْزِ وَالْكَسَلِ، وَضَلَعِ الدَّيْنِ وَغَلَبَةِ الرِّجَالِ."
)

TXT_SHIFA = (
    "🩺 *أذكار وأدعية الشفاء من المرض (الرقية الشرعية):*\n\n"
    "🔹 *دعاء النبي ﷺ للمريض:* أَذْهِبِ الْبَاسَ رَبَّ النَّاسِ، وَاشْفِ أَنْتَ الشَّافِي، لَا شِفَاءَ إِلَّا شِفَاؤُكَ.\n\n"
    "🔹 *بِسْمِ اللَّهِ (3 مرات)*، ثم تقول: أَعُوذُ بِعِزَّةِ اللَّهِ وَقُدْرَتِهِ مِنْ شَرِّ مَا أَجِدُ وَأُحَاذِرُ. (7 مرات)\n\n"
    "🔹 *أَسْأَلُ اللَّهَ الْعَظِيمَ* رَبَّ الْعَرْشِ الْعَظِيمِ أَنْ يَشْفِيَكَ. (7 مرات)"
)

# 📚 قاعدة بيانات الـحِـكَـم المتغيرة ذاتياً حسب أيام الشهر وضمان التنوع اليومي
DAILY_WISDOMS = [
    "✨ *حكمة اليوم:* \"إن الله يعطي الدنيا لمن يحب ومن لا يحب، ولا يعطي الدين إلا لمن أحب.\"",
    "✨ *حكمة اليوم:* \"إن الله لا ينظر إلى صوركم وأموالكم، ولكن ينظر إلى قلوبكم وأعمالكم.\"",
    "✨ *حكمة اليوم:* \"من أصلح مابينه وبين الله، أصلح الله مابينه وبين الناس.\"",
    "✨ *حكمة اليوم:* \"عجباً لأمر المؤمن إن أمره كله خير، إن أصابته سراء شكر فكان خيراً له، وإن أصابته ضراء صبر فكان خيراً له.\"",
    "✨ *حكمة اليوم:* \"وعزتي وجلالي لأستجيبن لك ولو بعد حين.. ثق بالفرج وعليك بالدعاء.\"",
    "✨ *حكمة اليوم:* \"لو علمتم كيف يدبر الله الأمور لعلت قلوبكم من محبته.\"",
    "✨ *حكمة اليوم:* \"ما رُفع كف إلى الله بالدعاء إلا ورجع ممتلئاً خيراً ويقيناً.\""
]

def get_dynamic_wisdom():
    # اختيار الحكمة بالاعتماد على رقم اليوم الحالي للحصول على حكمة متجددة يومياً
    day_num = datetime.now(BAGHDAD_TZ).day
    index = day_num % len(DAILY_WISDOMS)
    return DAILY_WISDOMS[index]

# --- 4. جدول مواقيت بغداد الورقي الشرعي ---
BAGHDAD_SCHEDULE = {
    "05-19": {"الفجر": "03:23", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:01", "العشاء": "20:29"}, 
    "05-20": {"الفجر": "03:22", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:02", "العشاء": "20:30"}, 
    "05-21": {"الفجر": "03:21", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:31"}, 
}

def get_current_prayer_times():
    today_key = datetime.now(BAGHDAD_TZ).strftime("%m-%d")
    return BAGHDAD_SCHEDULE.get(today_key, BAGHDAD_SCHEDULE["05-19"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribed_users.add(user_id)
    welcome_text = f"🕌 مرحباً بك يا {update.effective_user.first_name} في بوت العبادات والأذكار المتكامل لمدينة بغداد."
    
    keyboard = [
        [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم", callback_data='prayer_times')],
        [InlineKeyboardButton("📖 المصحف الإلكتروني", callback_data='quran_menu')],
        [InlineKeyboardButton("📿 حصن المسلم والأذكار", callback_data='azkar_menu')],
        [InlineKeyboardButton("🤲 أدعية الهم والفرج والشفاء", callback_data='duas_menu')],
        [InlineKeyboardButton("✨ حكمة اليوم المتجددة", callback_data='wisdom_day')]
    ]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return

    status_msg = await update.message.reply_text("⏳ جاري نشر وتوزيع رسالتك المباركة...")
    count = 0
    if update.message.text:
        for sub_id in list(subscribed_users):
            if sub_id != ADMIN_ID:
                try:
                    await context.bot.send_message(chat_id=sub_id, text=update.message.text)
                    count += 1
                except Exception: pass
    await status_msg.edit_text(f"✅ تم النشر لـ ({count}) مشترك نشط!")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'prayer_times':
        times = get_current_prayer_times()
        message = f"🕌 *مواقيت الصلاة لبغداد:*\n\n🕋 الفجر: {times['الفجر']} | ☀️ الظهر: {times['الظهر']}\n🎯 العصر: {times['العصر']} | 🌙 المغرب: {times['المغرب']}\n🌌 العشاء: {times['العشاء']}"
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data='main_menu')]]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'quran_menu':
        message = "📖 *المصحف الإلكتروني - السور كاملة بالتشكيل داخل التطبيق:* "
        keyboard = [
            [InlineKeyboardButton("👑 آية الكرسي كاملة", callback_data='q_kursi')],
            [InlineKeyboardButton("🌌 سورة الملك كاملة", callback_data='q_mulk')],
            [InlineKeyboardButton("📑 قصار السور كاملة", callback_data='q_qisar')],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'q_kursi':
        keyboard = [[InlineKeyboardButton("🔙 عودة للمصحف", callback_data='quran_menu')]]
        await query.edit_message_text(text=TXT_KURSI, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'q_mulk':
        keyboard = [[InlineKeyboardButton("🔙 عودة للمصحف", callback_data='quran_menu')]]
        await query.edit_message_text(text=TXT_MULK, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'q_qisar':
        keyboard = [[InlineKeyboardButton("🔙 عودة للمصحف", callback_data='quran_menu')]]
        await query.edit_message_text(text=TXT_QISAR, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'azkar_menu':
        message = "📿 *قسم الأذكار اليومية المكتوبة كاملة:* "
        keyboard = [
            [InlineKeyboardButton("☀️ أذكار الصباح كاملة", callback_data='view_morning')],
            [InlineKeyboardButton("🌙 أذكار المساء كاملة", callback_data='view_evening')],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'view_morning':
        keyboard = [[InlineKeyboardButton("🔙 عودة للأذكار", callback_data='azkar_menu')]]
        await query.edit_message_text(text=TXT_MORNING, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'view_evening':
        keyboard = [[InlineKeyboardButton("🔙 عودة للأذكار", callback_data='azkar_menu')]]
        await query.edit_message_text(text=TXT_EVENING, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'duas_menu':
        message = "🤲 *بوابة الأدعية المستجابة والرقية الشرعية:* "
        keyboard = [
            [InlineKeyboardButton("🔹 أدعية الهم والفرج وتيسير الكرب", callback_data='view_hamm')],
            [InlineKeyboardButton("🩺 أدعية الشفاء من المرض والرقية", callback_data='view_shifa')],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='main_menu')]
        ]
        await query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'view_hamm':
        keyboard = [[InlineKeyboardButton("🔙 عودة للأدعية", callback_data='duas_menu')]]
        await query.edit_message_text(text=TXT_HAMM, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'view_shifa':
        keyboard = [[InlineKeyboardButton("🔙 عودة للأدعية", callback_data='duas_menu')]]
        await query.edit_message_text(text=TXT_SHIFA, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'wisdom_day':
        # استدعاء الحكمة اليومية المتغيرة تلقائياً
        wisdom_text = get_dynamic_wisdom()
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='main_menu')]]
        await query.edit_message_text(text=wisdom_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("⏱️ مواقيت الصلاة اليوم", callback_data='prayer_times')],
            [InlineKeyboardButton("📖 المصحف الإلكتروني", callback_data='quran_menu')],
            [InlineKeyboardButton("📿 حصن المسلم والأذكار", callback_data='azkar_menu')],
            [InlineKeyboardButton("🤲 أدعية الهم والفرج والشفاء", callback_data='duas_menu')],
            [InlineKeyboardButton("✨ حكمة اليوم المتجددة", callback_data='wisdom_day')]
        ]
        await query.edit_message_text(text="🕌 قائمة العبادات والمواقيت المتكاملة لمدينة بغداد:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 5. نظام الأتمتة الدوري للتنبيهات ---
async def check_prayer_times(application: Application):
    last_exact = ""
    while True:
        try:
            now_str = datetime.now(BAGHDAD_TZ).strftime("%H:%M")
            times = get_current_prayer_times()
            if times:
                for name, p_time in times.items():
                    if now_str == p_time and now_str != last_exact:
                        last_exact = now_str
                        for uid in list(subscribed_users):
                            try: await application.bot.send_message(chat_id=uid, text=f"🕌 حان الآن موعد أذان [{name}] في بغداد.")
                            except Exception: pass
        except Exception: pass
        await asyncio.sleep(20)

# --- 6. التشغيل والربط ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast))
    
    web_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True)
    web_thread.start()
    
    checker_thread = threading.Thread(target=lambda: asyncio.run(check_prayer_times(application)), daemon=True)
    checker_thread.start()
    
    logging.info("🚀 تم تحديث نظام الحكم وإلغاء التكبيرات بنجاح...")
    application.run_polling(drop_pending_updates=True)
