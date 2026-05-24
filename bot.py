import logging
import os
from datetime import datetime, timedelta
import pytz
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات الأساسية ---
logging.basicConfig(level=logging.INFO)
TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# الرقم التعريفي لحسابك المسؤول
ADMIN_ID = 5656787  
SUBSCRIBERS_FILE = "subscribers.txt"

def load_subscribers():
    subs = {5656787} 
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            for line in f:
                if line.strip().isdigit():
                    subs.add(int(line.strip()))
    return subs

def save_subscriber(user_id):
    subs = load_subscribers()
    if user_id not in subs:
        with open(SUBSCRIBERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

# --- النصوص والواجهات الثابتة ---
TXT_WELCOME = "🕌 *بوت العبادات لمدينة بغداد وضواحيها*\nصدقة جارية بنية شفاء الوالدة. اختر قسماً من القائمة:"

TXT_AZKAR_SABAH = (
    "☀️ *أذكار الصباح كاملة (تذكير يومي):*\n\n"
    "1. *آية الكرسي:* {اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...}\n\n"
    "2. *المعوذات (3 مرات):* الإخلاص، الفلق، الناس.\n\n"
    "3. أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير.\n\n"
    "4. ربي أسألك خير ما في هذا اليوم وخير ما بعده، وأعوذ بك من شر ما في هذا اليوم وشر ما بعده.\n\n"
    "5. اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك النشور.\n\n"
    "6. *سيد الإستغفار:* اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت..."
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

PRAYER_DATABASE = {
    "2026-05-17": {"hijri": "1 ذو الحجة", "الفجر": "03:25", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:00", "العشاء": "20:27"},
    "2026-05-18": {"hijri": "2 ذو الحجة", "الفجر": "03:24", "الظهر": "12:04", "العصر": "15:45", "المغرب": "19:01", "العشاء": "20:29"},
    "2026-05-19": {"hijri": "3 ذو الحجة", "الفجر": "03:23", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:01", "العشاء": "20:29"},
    "2026-05-20": {"hijri": "4 ذو الحجة", "الفجر": "03:22", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:02", "العشاء": "20:30"},
    "2026-05-21": {"hijri": "5 ذو الحجة", "الفجر": "03:21", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:31"},
    "2026-05-22": {"hijri": "6 ذو الحجة", "الفجر": "03:20", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:03", "العشاء": "20:32"},
    "2026-05-23": {"hijri": "7 ذو الحجة", "الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:04", "العشاء": "20:33"},
    "2026-05-24": {"hijri": "8 ذو الحجة", "الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:05", "العشاء": "20:34"},
    "2026-05-25": {"hijri": "9 ذو الحجة", "الفجر": "03:18", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:35"},  
    "2026-05-26": {"hijri": "10 ذو الحجة", "الفجر": "03:17", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:36"}, 
    "2026-05-27": {"hijri": "11 ذو الحجة", "الفجر": "03:16", "الظهر": "12:05", "العصر": "15:46", "المغرب": "19:07", "العشاء": "20:37"},
    "2026-05-28": {"hijri": "12 ذو الحجة", "الفجر": "03:16", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:07", "العشاء": "20:38"},
    "2026-05-29": {"hijri": "13 ذو الحجة", "الفجر": "03:15", "الظهر": "12:05", "Alloc": "15:47", "المغرب": "19:08", "العشاء": "20:39"},
    "2026-05-30": {"hijri": "14 ذو الحجة", "الفجر": "03:14", "الظهر": "12:05", "Alloc": "15:47", "المغرب": "19:09", "العشاء": "20:40"},
    "2026-05-31": {"hijri": "15 ذو الحجة", "الفجر": "03:14", "الظهر": "12:05", "Alloc": "15:47", "المغرب": "19:09", "العشاء": "20:40"}
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

async def scheduled_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        now = datetime.now(BAGHDAD_TZ)
        date_key = now.strftime("%Y-%m-%d")
        now_str = now.strftime("%H:%M")
        current_subs = load_subscribers()

        if now_str == "07:00":
            for uid in current_subs:
                try: await context.bot.send_message(uid, TXT_AZKAR_SABAH, parse_mode="Markdown")
                except: pass

        if date_key in PRAYER_DATABASE:
            day_data = PRAYER_DATABASE[date_key]
            
            maghrib_time_obj = datetime.strptime(day_data["المغرب"], "%H:%M")
            massa_time_obj = datetime.combine(datetime.today(), maghrib_time_obj.time()) - timedelta(minutes=20)
            if now_str == massa_time_obj.strftime("%H:%M"):
                for uid in current_subs:
                    try: await context.bot.send_message(uid, TXT_AZKAR_MASSA, parse_mode="Markdown")
                    except: pass

            for name in ["الفجر", "الظهر", "العصر", "المغرب", "العشاء"]:
                p_time = day_data[name]
                p_time_obj = datetime.strptime(p_time, "%H:%M")
                alert_str = (datetime.combine(datetime.today(), p_time_obj.time()) - timedelta(minutes=10)).strftime("%H:%M")

                if now_str == alert_str:
                    for uid in current_subs:
                        try: await context.bot.send_message(uid, f"⏳ بقي 10 دقائق على أذان *{name}* في بغداد.", parse_mode="Markdown")
                        except: pass

                if now_str == p_time:
                    for uid in current_subs:
                        try: await context.bot.send_message(uid, f"🕌 حان الآن وقت أذان *{name}* في بغداد.", parse_mode="Markdown")
                        except: pass

        target_dua_times = ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
        if now_str in target_dua_times:
            dua_index = target_dua_times.index(now_str) % len(DUA_LIST)
            for uid in current_subs:
                try: await context.bot.send_message(uid, DUA_LIST[dua_index], parse_mode="Markdown")
                except: pass
    except Exception as e:
        logging.error(f"Error in job: {e}")

# --- الواجهة والمعالجات ---
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱️ المواقيت الدقيقة للجدول", callback_data='prayer')],
        [InlineKeyboardButton("☀️ أذكار الصباح والمساء", callback_data='azkar')],
        [InlineKeyboardButton("🤲 أدعية الشفاء والهم", callback_data='duas')],
        [InlineKeyboardButton("🕋 اتجاه القِبلة في بغداد", callback_data='qibla')]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_subscriber(update.effective_user.id)
    await update.message.reply_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        total = len(load_subscribers())
        await update.message.reply_text(f"📊 *إحصائيات البوت الدائمة:*\n\nعدد المشتركين: `{total}`", parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    save_subscriber(query.from_user.id)
    back_kb = [[InlineKeyboardButton("🔙 عودة للقائمة", callback_data='main')]]
    
    if query.data == 'prayer':
        await query.edit_message_text(get_prayer_text(), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'azkar':
        await query.edit_message_text(f"{TXT_AZKAR_SABAH}\n\n-----------\n\n{TXT_AZKAR_MASSA}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'duas':
        await query.edit_message_text(TXT_DUAS_PAGE, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'qibla':
        await query.edit_message_text(TXT_QIBLA, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'main':
        await query.edit_message_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=get_main_keyboard())

# --- سيرفر ويب لخداع Render ---
app = Flask(__name__)
@app.route('/')
def home(): 
    return "Prayer Bot Running Successfully"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # تشغيل سيرفر ويب كـ Thread مستقل
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # تشغيل البوت بالطريقة الرسمية والمستقرة
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button_click))
    
    if application.job_queue:
        application.job_queue.run_repeating(scheduled_alerts_job, interval=30, first=10)
    
    # تشغيل استقبال الرسائل بشكل مباشر يمنع التعليق
    application.run_polling(drop_pending_updates=True)
