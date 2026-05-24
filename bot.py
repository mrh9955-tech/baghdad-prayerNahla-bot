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

# الرقم التعريفي الجديد لحسابك الشخصي (المسؤول) لتفعيل ميزة الإحصائيات السريعة لك وحده
ADMIN_ID = 5656787  

SUBSCRIBERS_FILE = "subscribers.txt"

# --- دالة حفظ وجلب المشتركين من ملف دائم ---
def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(int(line.strip()) for line in f if line.strip().isdigit())
    return set()

def save_subscriber(user_id):
    subs = load_subscribers()
    if user_id not in subs:
        with open(SUBSCRIBERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

# شحن المشتركين بالذاكرة عند التشغيل لضمان استقرار الإشعارات
subscribed_users = load_subscribers()

# --- النصوص والواجهات الثابتة ---
TXT_WELCOME = "🕌 *بوت العبادات لمدينة بغداد وضواحيها*\nصدقة جارية بنية شفاء الوالدة. اختر قسماً من القائمة:"

TXT_AZKAR_SABAH = (
    "☀️ *أذكار الصباح كاملة (تذكير يومي):*\n\n"
    "1. *آية الكرسي:* {اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...}\n\n"
    "2. *المعوذات (3 مرات):* الإخلاص، الفلق، الناس.\n\n"
    "3. أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير.\n\n"
    "4. ربي أسألك خير ما في هذا اليوم وخير ما بعده، وأعوذ بك من شر ما في هذا اليوم وشر ما بعده.\n\n"
    "5. اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك النشور.\n\n"
    "6. *سيد الإستغفار:* اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت، أعوذ بك من شر ما صنعت، أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت."
)

TXT_AZKAR_MASSA = (
    "🌙 *أذكار المساء كاملة (تذكير قبل المغرب):*\n\n"
    "1. *آية الكرسي:* {اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّوم...}\n\n"
    "2. *المعوذات (3 مرات):* الإخلاص، الفلق، الناس.\n\n"
    "3. أمسينا وأمسي الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير.\n\n"
    "4. ربي أسألك خير ما في هذه الليلة وخير ما بعدها، وأعوذ بك من شر ما في هذه الليلة وشر ما بعدها.\n\n"
    "5. اللهم بك أمسينا، وبك أصبحنا، وبك نحيا، وبك نموت، وإليك المصير.\n\n"
    "6. *سيد الإستغفار:* اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت..."
)

TXT_DUAS_PAGE = "🤲 *أدعية الشفاء وتفريج الهم*\n\n١. اللهم رب الناس أذهب البأس، اشفِ أنت الشافي، لا شفاء إلا شفاؤك، شفاءً لا يغادر سقماً.\n٢. لا إله إلا أنت سبحانك إني كنت من الظالمين.\n٣. اللهم فرج همنا واكشف غمنا واشِف مرضانا."

TXT_QIBLA = (
    "🕋 *اتجاه القِبلة لمدينة بغداد وضواحيها:*\n\n"
    "• اتجاه القبلة في مدينة بغداد هو نحو **الجنوب الغربي** تقريباً.\n"
    "• الزاوية الجغرافية الدقيقة (الإنحراف): **204° درجة** من اتجاه الشمال باتجاه حركة عقارب الساعة.\n\n"
    "💡 *نصيحة لتحديد دقيق:* يمكنك استخدام تطبيق البوصلة في هاتفك وتوجيهه نحو الدرجة 204 لتحديد مكان القبلة الصحيح تماماً في منزلك."
)

DUA_LIST = [
    "🤲 *دعاء الساعة:* اللهم اشفِ والدتي وعافها وألبسها ثوب الصحة والعافية يا رب العالمين.",
    "🤲 *دعاء الساعة:* اللهم فرج همومنا، واقضِ ديوننا، واجعل التوفيق حليفنا في كل خطوة.",
    "🤲 *دعاء الساعة:* اللهم صلِّ وسلم وبارك على نبينا محمد وعلى آله وصحبه أجمعين.",
    "🤲 *دعاء الساعة:* يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين."
]

# جدول مواقيت صلاة بغداد لشهر ذو الحجة
PRAYER_DATABASE = {
    "2026-05-17": {"hijri": "1 ذو الحجة", "الفجر": "03:25", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:00", "العشاء": "20:27"},
    "2026-05-18": {"hijri": "2 ذو الحجة", "الفجر": "03:24", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:01", "العشاء": "20:29"},
    "2026-05-19": {"hijri": "3 ذو الحجة", "الفجر": "03:23", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:01", "العشاء": "20:29"},
    "2026-05-20": {"hijri": "4 ذو الحجة", "الفجر": "03:22", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:02", "العشاء": "20:30"},
    "2026-05-21": {"hijri": "5 ذو الحجة", "الفجر": "03:21", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:31"},
    "2026-05-22": {"hijri": "6 ذو الحجة", "الفجر": "03:20", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:32"},
    "2026-05-23": {"hijri": "7 ذو الحجة", "الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:04", "العشاء": "20:33"},
    "2026-05-24": {"hijri": "8 ذو الحجة", "الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:05", "العشاء": "20:34"},
    "2026-05-25": {"hijri": "9 ذو الحجة", "الفجر": "03:18", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:35"},  # عرفة
    "2026-05-26": {"hijri": "10 ذو الحجة", "الفجر": "03:17", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:36"}, # العيد
    "2026-05-27": {"hijri": "11 ذو الحجة", "الفجر": "03:16", "الظهر": "12:05", "العصر": "15:46", "المغرب": "19:07", "العشاء": "20:37"},
    "2026-05-28": {"hijri": "12 ذو الحجة", "الفجر": "03:16", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:07", "العشاء": "20:38"},
    "2026-05-29": {"hijri": "13 ذو الحجة", "الفجر": "03:15", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:08", "العشاء": "20:39"},
    "2026-05-30": {"hijri": "14 ذو الحجة", "الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"},
    "2026-05-31": {"hijri": "15 ذو الحجة", "الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"},
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
    "2026-06-12": {"hijri": "27 ذو الحجة", "الفجر": "03:10", "الظهر": "12:07", "Cyber": "15:49", "المغرب": "19:15", "العشاء": "20:48"},
    "2026-06-13": {"hijri": "28 ذو الحجة", "الفجر": "03:10", "الظهر": "12:08", "العصر": "15:49", "المغرب": "19:16", "العشاء": "20:49"},
    "2026-06-14": {"hijri": "29 ذو الحجة", "الفجر": "03:10", "الظهر": "12:08", "العصر": "15:50", "المغرب": "19:16", "العشاء": "20:49"},
    "2026-06-15": {"hijri": "30 ذو الحجة", "الفجر": "03:10", "الظهر": "12:08", "العصر": "15:50", "المغرب": "19:17", "العشاء": "20:50"}
}

def get_prayer_text():
    now_time = datetime.now(BAGHDAD_TZ)
    date_key = now_time.strftime("%Y-%m-%d")
    m_date = now_time.strftime("%d/%m/%Y")
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

# --- محرك التنبيهات والأذكار المجدولة بالثانية ---
async def prayer_alert_engine(application: Application):
    notified_before = {}
    notified_azan = {}
    last_dua_key = ""
    last_sabah_date = ""
    last_massa_date = ""
    arafah_alert_sent = False

    while True:
        try:
            now = datetime.now(BAGHDAD_TZ)
            date_key = now.strftime("%Y-%m-%d")
            now_str = now.strftime("%H:%M")

            current_subs = load_subscribers()

            # 1. إرسال أذكار الصباح كاملة تلقائياً الساعة 7:00 صباحاً
            if now_str == "07:00" and last_sabah_date != date_key:
                for uid in list(current_subs):
                    try: await application.bot.send_message(uid, TXT_AZKAR_SABAH, parse_mode="Markdown")
                    except: pass
                last_sabah_date = date_key

            if date_key in PRAYER_DATABASE:
                day_data = PRAYER_DATABASE[date_key]
                
                # 2. إرسال أذكار المساء كاملة قبل أذان المغرب بـ 20 دقيقة
                maghrib_time_obj = datetime.strptime(day_data["المغرب"], "%H:%M")
                massa_time_obj = datetime.combine(datetime.today(), maghrib_time_obj.time()) - timedelta(minutes=20)
                massa_time_str = massa_time_obj.strftime("%H:%M")
                
                if now_str == massa_time_str and last_massa_date != date_key:
                    for uid in list(current_subs):
                        try: await application.bot.send_message(uid, TXT_AZKAR_MASSA, parse_mode="Markdown")
                        except: pass
                    last_massa_date = date_key

                # تنبيهات ذو الحجة وعرفة وعيد الأضحى المبارك
                if day_data['hijri'] == "8 ذو الحجة" and now_str == "20:00" and not arafah_alert_sent:
                    for uid in list(current_subs):
                        try: await application.bot.send_message(uid, "🌙 *تذكير عظيم:* غداً هو يوم عرفة، صيام هذا اليوم يكفر السنة الماضية والباقية.", parse_mode="Markdown")
                        except: pass
                    arafah_alert_sent = True
                    
                if day_data['hijri'] == "9 ذو الحجة" and now_str == "05:00":
                    for uid in list(current_subs):
                        try: await application.bot.send_message(uid, "🕋 *أقبل يوم عرفة:* خير الدعاء دعاء يوم عرفة، أكثروا من ذكره والدعاء لشفاء المرضى.", parse_mode="Markdown")
                        except: pass

                # تنبيهات الصلوات الرسمية (قبل بـ 10 دقائق ووقت الأذان)
                for name in ["الفجر", "الظهر", "العصر", "المغرب", "العشاء"]:
                    p_time = day_data[name]
                    p_time_obj = datetime.strptime(p_time, "%H:%M")
                    alert_time_obj = datetime.combine(datetime.today(), p_time_obj.time()) - timedelta(minutes=10)
                    alert_str = alert_time_obj.strftime("%H:%M")

                    if now_str == alert_str and notified_before.get(name) != date_key:
                        for uid in list(current_subs):
                            try: await application.bot.send_message(uid, f"⏳ بقي 10 دقائق على أذان *{name}* في بغداد. تهيأ للصلاة واذكر الله.", parse_mode="Markdown")
                            except: pass
                        notified_before[name] = date_key

                    if now_str == p_time and notified_azan.get(name) != date_key:
                        for uid in list(current_subs):
                            try: await application.bot.send_message(uid, f"🕌 *الله أكبر الله أكبر..*\nحان الآن وقت أذان *{name}* في بغداد وجوارها.", parse_mode="Markdown")
                            except: pass
                        notified_azan[name] = date_key

            # 3. إرسال الأدعية المجدولة في أوقاتك الدقيقة الستة
            target_dua_times = ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
            current_dua_key = f"{date_key}-{now_str}"
            
            if now_str in target_dua_times and last_dua_key != current_dua_key:
                last_dua_key = current_dua_key
                dua_index = target_dua_times.index(now_str) % len(DUA_LIST)
                for uid in list(current_subs):
                    try: await application.bot.send_message(uid, DUA_LIST[dua_index], parse_mode="Markdown")
                    except: pass

        except Exception as e:
            logging.error(f"خطأ في محرك التنبيهات: {e}")

        await asyncio.sleep(10)

# --- الواجهة الرئيسية بالأزرار المحدثة والصافية ---
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱️ المواقيت الدقيقة للجدول", callback_data='prayer')],
        [InlineKeyboardButton("☀️ أذكار الصباح والمساء", callback_data='azkar')],
        [InlineKeyboardButton("🤲 أدعية الشفاء والهم", callback_data='duas')],
        [InlineKeyboardButton("🕋 اتجاه القِبلة في بغداد", callback_data='qibla')] # زر القبلة الجديد
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_subscriber(user_id) 
    await update.message.reply_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=get_main_keyboard())

# --- الأمر السري المخصص لآيدي حسابك الجديد للإحصائيات ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        current_subs = load_subscribers()
        total = len(current_subs)
        await update.message.reply_text(f"📊 *إحصائيات البوت الدائمة:*\n\nعدد المشتركين الإجمالي والمسجلين في النظام هو: `{total}` مستخدم.", parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    back_kb = [[InlineKeyboardButton("🔙 عودة للقائمة", callback_data='main')]]
    
    if query.data == 'prayer':
        await query.edit_message_text(get_prayer_text(), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'azkar':
        # تجميع الأذكار في عرض سريع للمستخدم عند الضغط من القائمة
        txt_combined = f"{TXT_AZKAR_SABAH}\n\n-----------\n\n{TXT_AZKAR_MASSA}"
        await query.edit_message_text(txt_combined, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'duas':
        await query.edit_message_text(TXT_DUAS_PAGE, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'qibla':
        await query.edit_message_text(TXT_QIBLA, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'main':
        await query.edit_message_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=get_main_keyboard())

def run_flask():
    app = Flask(__name__)
    @app.route('/')
    def home(): return "Prayer Bot Permanent Subs Active"
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats)) 
    application.add_handler(CallbackQueryHandler(button_click))
    
    loop = asyncio.new_event_loop()
    threading.Thread(target=lambda: loop.run_until_complete(prayer_alert_engine(application)), daemon=True).start()
    
    application.run_polling()
