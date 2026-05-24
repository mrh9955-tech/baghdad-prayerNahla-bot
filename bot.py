import logging
import os
import time
from datetime import datetime, timedelta
import pytz
from flask import Flask, request
import telebot
from threading import Thread

# --- الإعدادات الأساسية ---
logging.basicConfig(level=logging.INFO)
TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"
WEBHOOK_URL = "https://baghdad-prayernahla-bot-1.onrender.com"
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

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

# --- النصوص والبيانات الثابتة ---
TXT_WELCOME = "🕌 *بوت العبادات لمدينة بغداد وضواحيها*\nصدقة جارية بنية شفاء الوالدة. اختر قسماً من القائمة:"
TXT_DUAS_PAGE = "🤲 *أدعية الشفاء وتفريج الهم*\n\n١. اللهم رب الناس أذهب البأس، اشفِ أنت الشافي، لا شفاء إلا شفاؤك، شفاءً لا يغادر سقماً.\n٢. لا إله إلا أنت سبحانك إني كنت من الظالمين.\n٣. اللهم فرج همنا واكشف غمنا واشِف مرضانا."
TXT_QIBLA = "🕋 *اتجاه القِبلة لمدينة بغداد وضواحيها:*\n\n• اتجاه القبلة في مدينة بغداد هو نحو *الجنوب الغربي* تقريباً.\n• الزاوية الجغرافية الدقيقة (الإنحراف): *204° درجة*.\n\n💡 يمكنك استخدام تطبيق البوصلة في هاتفك وتوجيهه نحو الدرجة 204 لتحديد مكان القبلة الصحيح تماماً."

TXT_AZKAR_SABAH = "☀️ *أذكار الصباح كاملة (تذكير يومي):*\n\n1. *آية الكرسي*\n2. *المعوذات (3 مرات)*\n3. أصبحنا وأصبح الملك لله والحمد لله...\n4. *سيد الإستغفار:* اللهم أنت ربي لا إله إلا أنت..."
TXT_AZKAR_MASSA = "🌙 *أذكار المساء كاملة (تذكير قبل المغرب):*\n\n1. *آية الكرسي*\n2. *المعوذات (3 مرات)*\n3. أمسينا وأمسي الملك لله والحمد لله...\n4. *سيد الإستغفار:* اللهم أنت ربي لا إله إلا أنت..."

DUA_LIST = [
    "🤲 *دعاء الساعة:* اللهم اشفِ والدتي وعافها وألبسها ثوب الصحة والعافية يا رب العالمين.",
    "🤲 *دعاء الساعة:* اللهم فرج همومنا، واقضِ ديوننا، واجعل التوفيق حليفنا في كل خطوة.",
    "🤲 *دعاء الساعة:* اللهم صلِّ وسلم وبارك على نبينا محمد وعلى آله وصحبه أجمعين.",
    "🤲 *دعاء الساعة:* يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين."
]

PRAYER_DATABASE = {
    "2026-05-24": {"hijri": "8 ذو الحجة", "الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:05", "العشاء": "20:34"},
    "2026-05-25": {"hijri": "9 ذو الحجة", "الفجر": "03:18", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:06", "العشاء": "20:35"},  
    "2026-05-26": {"hijri": "10 ذو الحجة", "الفجر": "03:17", "الظهر": "12:04", "الصر": "15:46", "المغرب": "19:06", "العشاء": "20:36"}, 
    "2026-05-27": {"hijri": "11 ذو الحجة", "الفجر": "03:16", "الظهر": "12:05", "العصر": "15:46", "المغرب": "19:07", "العشاء": "20:37"},
    "2026-05-28": {"hijri": "12 ذو الحجة", "الفجر": "03:16", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:07", "العشاء": "20:38"},
    "2026-05-29": {"hijri": "13 ذو الحجة", "الفجر": "03:15", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:08", "العشاء": "20:39"},
    "2026-05-30": {"hijri": "14 ذو الحجة", "الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"},
    "2026-05-31": {"hijri": "15 ذو الحجة", "الفجر": "03:14", "الظهر": "12:05", "العصر": "15:47", "المغرب": "19:09", "العشاء": "20:40"}
}

def get_prayer_text():
    now_time = datetime.now(BAGHDAD_TZ)
    date_key = now_time.strftime("%Y-%m-%d")
    m_date = now_time.strftime("%d/%m/%Y")
    day_data = PRAYER_DATABASE.get(date_key, {"hijri": "---", "الفجر": "03:19", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:05", "العشاء": "20:34"})
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

def get_main_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("⏱️ المواقيت الدقيقة للجدول", callback_data='prayer'))
    markup.row(telebot.types.InlineKeyboardButton("☀️ أذكار الصباح والمساء", callback_data='azkar'))
    markup.row(telebot.types.InlineKeyboardButton("🤲 أدعية الشفاء والهم", callback_data='duas'))
    markup.row(telebot.types.InlineKeyboardButton("🕋 اتجاه القِبلة في بغداد", callback_data='qibla'))
    return markup

def get_back_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("🔙 عودة للقائمة", callback_data='main'))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_subscriber(message.chat.id)
    bot.send_message(message.chat.id, TXT_WELCOME, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['stats'])
def send_stats(message):
    if message.chat.id == ADMIN_ID:
        total = len(load_subscribers())
        bot.send_message(message.chat.id, f"📊 *إحصائيات البوت الدائمة:*\n\nعدد المشتركين: `{total}`")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    save_subscriber(call.message.chat.id)
    if call.data == 'prayer':
        bot.edit_message_text(get_prayer_text(), call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard())
    elif call.data == 'azkar':
        bot.edit_message_text(f"{TXT_AZKAR_SABAH}\n\n-----------\n\n{TXT_AZKAR_MASSA}", call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard())
    elif call.data == 'duas':
        bot.edit_message_text(TXT_DUAS_PAGE, call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard())
    elif call.data == 'qibla':
        bot.edit_message_text(TXT_QIBLA, call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard())
    elif call.data == 'main':
        bot.edit_message_text(TXT_WELCOME, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard())

# --- خيط الخلفية المسؤول عن الإشعارات الدقيقة لمنع التكرار ---
def scheduler_loop():
    last_sent_minute = ""
    
    while True:
        try:
            now = datetime.now(BAGHDAD_TZ)
            date_key = now.strftime("%Y-%m-%d")
            now_str = now.strftime("%H:%M")
            
            # إذا كنا لا نزال في نفس الدقيقة التي أرسلنا فيها مسبقاً، نتخطى الفحص
            if now_str == last_sent_minute:
                time.sleep(10)
                continue

            current_subs = load_subscribers()
            sent_this_loop = False

            # أذكار الصباح
            if now_str == "07:00":
                for uid in current_subs:
                    try: bot.send_message(uid, TXT_AZKAR_SABAH)
                    except: pass
                sent_this_loop = True

            if date_key in PRAYER_DATABASE:
                day_data = PRAYER_DATABASE[date_key]
                
                # أذكار المساء (قبل المغرب بـ 20 دقيقة)
                maghrib_time_obj = datetime.strptime(day_data["المغرب"], "%H:%M")
                massa_time_obj = datetime.combine(datetime.today(), maghrib_time_obj.time()) - timedelta(minutes=20)
                if now_str == massa_time_obj.strftime("%H:%M"):
                    for uid in current_subs:
                        try: bot.send_message(uid, TXT_AZKAR_MASSA)
                        except: pass
                    sent_this_loop = True

                # إشعارات مواقيت الصلاة
                for name in ["الفجر", "الظهر", "العصر", "المغرب", "العشاء"]:
                    p_time = day_data[name]
                    p_time_obj = datetime.strptime(p_time, "%H:%M")
                    alert_str = (datetime.combine(datetime.today(), p_time_obj.time()) - timedelta(minutes=10)).strftime("%H:%M")

                    if now_str == alert_str:
                        for uid in current_subs:
                            try: bot.send_message(uid, f"⏳ بقي 10 دقائق على أذان *{name}* في بغداد.")
                            except: pass
                        sent_this_loop = True

                    if now_str == p_time:
                        for uid in current_subs:
                            try: bot.send_message(uid, f"🕌 حان الآن وقت أذان *{name}* في بغداد.")
                            except: pass
                        sent_this_loop = True

            # أدعية الساعات
            target_dua_times = ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
            if now_str in target_dua_times:
                dua_index = target_dua_times.index(now_str) % len(DUA_LIST)
                for uid in current_subs:
                    try: bot.send_message(uid, DUA_LIST[dua_index])
                    except: pass
                sent_this_loop = True

            # إذا تم إرسال أي إشعار بنجاح، نقوم بحفظ الدقيقة الحالية لمنع التكرار
            if sent_this_loop:
                last_sent_minute = now_str

        except Exception as e:
            logging.error(f"Error in scheduler: {e}")
        
        time.sleep(10) # فحص متقارب وسريع لكل 10 ثوانٍ لضمان لقط الدقيقة فوراً بدون تكرار

@app.route(f'/{TOKEN}', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    return "Prayer Bot Cloud Server is Live 100%", 200

sched_thread = Thread(target=scheduler_loop)
sched_thread.daemon = True
sched_thread.start()
