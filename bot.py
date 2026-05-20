import logging
import os
import threading
import asyncio
from datetime import datetime, timedelta
import pytz
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات الأساسية ---
logging.basicConfig(level=logging.INFO)
TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# حفظ المشتركين لضمان وصول التنبيهات
subscribed_users = set()

# --- النصوص والواجهات ---
TXT_WELCOME = "Core 🕌 *بوت العبادات لمدينة بغداد وضواحيها*\nصدقة جارية بنية شفاء الوالدة. اختر قسماً من القائمة:"
TXT_AZKAR = "☀️ *أذكار الصباح والمساء*\n\n*أذكار الصباح:* أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير.\n\n*أذكار المساء:* أمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير."
TXT_DUAS_PAGE = "🤲 *أدعية الشفاء وتفريج الهم*\n\n١. اللهم رب الناس أذهب البأس، اشفِ أنت الشافي، لا شفاء إلا شفاؤك، شفاءً لا يغادر سقماً.\n٢. لا إله إلا أنت سبحانك إني كنت من الظالمين.\n٣. اللهم فرج همنا واكشف غمنا واشِف مرضانا."

DUA_LIST = [
    "🤲 *دعاء الساعة:* اللهم اشفِ والدتي وعافها وألبسها ثوب الصحة والعافية يا رب العالمين.",
    "🤲 *دعاء الساعة:* اللهم فرج همومنا، واقضِ ديوننا، واجعل التوفيق حليفنا في كل خطوة.",
    "🤲 *دعاء الساعة:* اللهم صلِّ وسلم وبارك على نبينا محمد وعلى آله وصحبه أجمعين.",
    "🤲 *دعاء الساعة:* يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين."
]

# --- تفريغ الجدول الرسمي (ذو الحجة 1447 / أيار - حزيران 2026) ---
# المفتاح هو رقم اليوم في شهر مايو (أيار) أو يونيو (حزيران)
PRAYER_DATABASE = {
    # شهر أيار (May)
    "2026-05-17": {"hijri": "1 ذو الحجة", "الفجر": "03:25", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:00", "العشاء": "20:27"},
    "2026-05-18": {"hijri": "2 ذو الحجة", "الفجر": "03:24", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:01", "العشاء": "20:29"},
    "2026-05-19": {"hijri": "3 ذو الحجة", "الفجر": "03:23", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:01", "العشاء": "20:29"},
    "2026-05-20": {"hijri": "4 ذو الحجة", "الفجر": "03:22", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:02", "العشاء": "20:30"},
    "2026-05-21": {"hijri": "5 ذو الحجة", "الفجر": "03:21", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:31"},
    "2026-05-22": {"hijri": "6 ذو الحجة", "الفجر": "03:20", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:32"},
    "2026-05-23": {"hijri": "7 ذو الحجة", "الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:04", "العشاء": "20:33"},
    "2026-05-24": {"hijri": "8 ذو الحجة", "الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:05", "العشاء": "20:34"},
    "2026-05-25": {"hijri": "9 ذو الحجة", "الفجر": "03:18", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:35"}, # يوم عرفة
    "2026-05-26": {"hijri": "10 ذو الحجة", "الفجر": "03:17", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:36"}, # العيد
    "2026-05-27": {"hijri": "11 ذو الحجة", "الفجر": "03:16", "الظهر": "12:05", "العصر": "15:46", "المغرب": "19:07", "العشاء": "20:37"},
    "2026-05-28": {"hijri": "12 ذو الحجة", "الفجر": "03:16", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:07", "العشاء": "20:38"},
    "2026-05-29": {"hijri": "13 ذو الحجة", "الفجر": "03:15", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:08", "العشاء": "20:39"},
    "2026-05-30": {"hijri": "14 ذو الحجة", "الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"},
    "2026-05-31": {"hijri": "15 ذو الحجة", "الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"},
    # شهر حزيران (June)
    "2026-06-01": {"hijri": "16 ذو الحجة", "الفجر": "03:13", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:10", "العشاء": "20:41"},
    "2026-06-02": {"hijri": "17 ذو الحجة", "الفجر": "03:13", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:10", "العشاء": "20:42"},
    "2026-06-03": {"hijri": "18 ذو الحجة", "الفجر": "03:12", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:11", "العشاء": "20:43"},
    "2026-06-04": {"hijri": "19 ذو الحجة", "الفجر": "03:12", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:12", "العشاء": "20:43"},
    "2026-06-05": {"hijri": "20 ذو الحجة", "الفجر": "03:12", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:12", "العشاء": "20:44"},
    "2026-06-06": {"hijri": "21 ذو الحجة", "الفجر": "03:11", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:13", "العشاء": "20:45"},
    "2026-06-07": {"hijri": "22 ذو الحجة", "الفجر": "03:11", "الظهر": "12:06", "العصر": "15:48", "المغرب": "19:13", "العشاء": "20:46"},
    "2026-06-08": {"hijri": "23 ذو الحجة", "الفجر": "03:11", "الظهر": "12:07", "العصر": "15:48", "المغرب": "19:14", "العشاء": "20:46"},
    "2026-06-09": {"hijri": "24 ذو الحجة", "الفجر": "03:10", "الظهر": "12:07", "العصر": "15:49", "المغرب": "19:14", "العشاء": "20:47"},
    "2026-06-10": {"hijri": "25 ذو الحجة", "الفجر": "03:10", "الظهر": "12:07", "العصر": "15:49", "المغرب": "19:15", "العشاء": "20:47"},
    "2026-06-11": {"hijri": "26 ذو الحجة", "الفجر": "03:10", "الظهر": "12:07", "العصر": "15:49", "المغرب": "19:15", "العشاء": "20:48"},
    "2026-06-12": {"hijri": "27 ذو الحجة", "الفجر": "03:10", "الظهر": "12:07", "العصر": "15:49", "المغرب": "19:15", "العشاء": "20:48"},
    "2026-06-13": {"hijri": "28 ذو الحجة", "الفجر": "03:10", "الظهر": "12:08", "العصر": "15:49", "المغرب": "19:16", "العشاء": "20:49"},
    "2026-06-14": {"hijri": "29 ذو الحجة", "الفجر": "03:10", "الظهر": "12:08", "العصر": "15:50", "المغرب": "19:16", "العشاء": "20:49"},
    "2026-06-15": {"hijri": "30 ذو الحجة", "الفجر": "03:10", "الظهر": "12:08", "العصر": "15:50", "المغرب": "19:17", "العشاء": "20:50"}
}

def get_prayer_text():
    now_time = datetime.now(BAGHDAD_TZ)
    date_key = now_time.strftime("%Y-%m-%d")
    m_date = now_time.strftime("%d/%m/%Y")
    
    # جلب اليوم من قاعدة البيانات أو وضع قيم افتراضية إذا خرج عن الشهر
    day_data = PRAYER_DATABASE.get(date_key, {"hijri": "---", "الفجر": "03:22", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:01", "العشاء": "20:29"})
    
    return (
        f"🕌 *مواقيت الصلاة لمدينة بغداد وضواحيها*\n"
        f"📅 التاريخ: {m_date} م | {day_data['hijri']}\n\n"
        f"🕋 الفجر: {day_data['الفجر']}\n"
        f"☀️ الظهر: {day_data['الظهر']}\n"
        f"🎯 العصر: {day_data['العصر']}\n"
        f"🌙 المغرب: {day_data['المغرب']}\n"
        f"🌌 العشاء: {day_data['العشاء']}\n\n"
        f"⚠️ تنبيهات الأذان وقبل الأذان بـ 10 دقائق تصلك تلقائياً."
    )

# --- محرك التنبيهات عالي الدقة ---
async def prayer_alert_engine(application: Application):
    notified_before = {}
    notified_azan = {}
    last_dua_hour = -1
    arafah_alert_sent = False

    while True:
        try:
            now = datetime.now(BAGHDAD_TZ)
            date_key = now.strftime("%Y-%m-%d")
            now_str = now.strftime("%H:%M")

            # التأكد من وجود اليوم الحالي في جدولنا
            if date_key in PRAYER_DATABASE:
                day_data = PRAYER_DATABASE[date_key]
                
                # 1. التذكير بيوم عرفة (قبل يوم وفي نفس اليوم)
                if day_data['hijri'] == "8 ذو الحجة" and now_str == "20:00" and not arafah_alert_sent:
                    for uid in list(subscribed_users):
                        try: await application.bot.send_message(uid, "🌙 *تذكير عظيم:* غداً هو يوم عرفة (٩ ذو الحجة)، صيام هذا اليوم يكفر السنة الماضية والباقية. لا تنسوا نية الصيام وعقد العزم!", parse_mode="Markdown")
                        except: pass
                    arafah_alert_sent = True
                    
                if day_data['hijri'] == "9 ذو الحجة" and now_str == "05:00":
                    for uid in list(subscribed_users):
                        try: await application.bot.send_message(uid, "🕋 *أقبل يوم عرفة:* خير الدعاء دعاء يوم عرفة، أكثروا من: (لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير) والدعاء لشفاء المرضى وتفريج الهموم.", parse_mode="Markdown")
                        except: pass

                # 2. فحص مواقيت الصلاة (التنبيه والأذان) للقسم الحالي
                for name in ["الفجر", "الظهر", "العصر", "المغرب", "العشاء"]:
                    p_time = day_data[name]
                    p_time_obj = datetime.strptime(p_time, "%H:%M")
                    alert_time_obj = datetime.combine(datetime.today(), p_time_obj.time()) - timedelta(minutes=10)
                    alert_str = alert_time_obj.strftime("%H:%M")

                    # إشعار قبل الأذان بـ 10 دقائق
                    if now_str == alert_str and notified_before.get(name) != date_key:
                        for uid in list(subscribed_users):
                            try: await application.bot.send_message(uid, f"⏳ بقي 10 دقائق على أذان *{name}* في بغداد. تهيأ للصلاة واذكر الله.", parse_mode="Markdown")
                            except: pass
                        notified_before[name] = date_key

                    # إشعار وقت الأذان بالضبط
                    if now_str == p_time and notified_azan.get(name) != date_key:
                        for uid in list(subscribed_users):
                            try: await application.bot.send_message(uid, f"اضغط 🕌 *الله أكبر الله أكبر..*\nحان الآن وقت أذان *{name}* في بغداد وجوارها.", parse_mode="Markdown")
                            except: pass
                        notified_azan[name] = date_key

            # 3. إرسال أدعية متغيرة كل 3 ساعات تلقائياً
            if now.hour % 3 == 0 and now.hour != last_dua_hour:
                last_dua_hour = now.hour
                dua_index = (now.hour // 3) % len(DUA_LIST)
                for uid in list(subscribed_users):
                    try: await application.bot.send_message(uid, DUA_LIST[dua_index], parse_mode="Markdown")
                    except: pass

        except Exception as e:
            logging.error(f"خطأ في محرك التنبيهات: {e}")

        await asyncio.sleep(10) # الفحص الدوري كل 10 ثوانٍ لضمان اللحظية

# --- دوال واجهة البوت والأزرار ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribed_users.add(update.effective_user.id) # تسجيل المشترك تلقائياً فوراً
    kb = [
        [InlineKeyboardButton("⏱️ المواقيت الدقيقة للجدول", callback_data='prayer')],
        [InlineKeyboardButton("☀️ أذكار الصباح والمساء", callback_data='azkar')],
        [InlineKeyboardButton("🤲 أدعية الشفاء والهم", callback_data='duas')]
    ]
    await update.message.reply_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    back_kb = [[InlineKeyboardButton("🔙 عودة للقائمة", callback_data='main')]]
    
    if query.data == 'prayer':
        await query.edit_message_text(get_prayer_text(), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'azkar':
        await query.edit_message_text(TXT_AZKAR, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'duas':
        await query.edit_message_text(TXT_DUAS_PAGE, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'main':
        kb = [
            [InlineKeyboardButton("⏱️ المواقيت الدقيقة للجدول", callback_data='prayer')],
            [InlineKeyboardButton("☀️ أذكار الصباح والمساء", callback_data='azkar')],
            [InlineKeyboardButton("🤲 أدعية الشفاء والهم", callback_data='duas')]
        ]
        await query.edit_message_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

def run_flask():
    app = Flask(__name__)
    @app.route('/')
    def home(): return "Baghdad Prayer Table Online"
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    # تشغيل محرك الأوقات الجديد المأخوذ من ورقة الجدول بدقة 10 ثوانٍ
    loop = asyncio.new_event_loop()
    threading.Thread(target=lambda: loop.run_until_complete(prayer_alert_engine(application)), daemon=True).start()
    
    application.run_polling()
