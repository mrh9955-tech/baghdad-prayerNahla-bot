import logging, os, threading, asyncio
from flask import Flask
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات الأساسية ---
logging.basicConfig(level=logging.INFO)
TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# قائمة المشتركين (لحفظهم وإرسال التنبيهات لهم)
subscribed_users = set()

# --- النصوص الكاملة ---
TXT_WELCOME = "🕌 *بوت العبادات لبغداد*\nصدقة جارية بنية شفاء الوالدة. اختر قسماً:"
TXT_PRAYER = "🕌 *مواقيت الصلاة لبغداد*\n📅 19/05/2026 م | 2 ذو الحجة 1447 هـ\n\n🕋 الفجر: 03:23\n☀️ الظهر: 12:04\n🎯 العصر: 15:46\n🌙 المغرب: 19:01\n🌌 العشاء: 20:29"
TXT_AZKAR = "☀️ *أذكار الصباح والمساء*\n\n*أذكار الصباح:* أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير.\n\n*أذكار المساء:* أمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير."
TXT_DUAS = "🤲 *أدعية الشفاء والهم*\n\n(١) اللهم رب الناس أذهب البأس، اشفِ أنت الشافي، لا شفاء إلا شفاؤك، شفاءً لا يغادر سقماً.\n(٢) لا إله إلا أنت سبحانك إني كنت من الظالمين."

PRAYER_TIMES = {"الفجر": "03:23", "الظهر": "12:04", "العصر": "15:46", "المغرب": "19:01", "العشاء": "20:29"}
DUA_LIST = ["اللهم اشفِ والدتي وعافها يا رب", "اللهم فرج همنا وارزقنا من حيث لا نحتسب", "اللهم صلِ على محمد وعلى آله وصحبه وسلم"]

# --- محرك التنبيهات الذكي في الخلفية ---
async def schedule_checker(application: Application):
    last_dua_hour = -1
    last_notified = {}
    
    while True:
        try:
            now = datetime.now(BAGHDAD_TZ)
            now_str = now.strftime("%H:%M")
            
            # 1. تنبيهات الصلاة (عند الأذان وقبله بـ 10 دقائق)
            for name, p_time in PRAYER_TIMES.items():
                p_time_obj = datetime.strptime(p_time, "%H:%M")
                alert_time = (datetime.combine(datetime.today(), p_time_obj.time()) - timedelta(minutes=10)).strftime("%H:%M")
                
                # قبل الأذان بـ 10 دقائق
                if now_str == alert_time and last_notified.get(name) != "before":
                    for uid in list(subscribed_users):
                        try: await application.bot.send_message(uid, f"⏳ بقي 10 دقائق على أذان {name} في بغداد.")
                        except: pass
                    last_notified[name] = "before"
                
                # عند الأذان بالضبط
                elif now_str == p_time and last_notified.get(name) != "azan":
                    for uid in list(subscribed_users):
                        try: await application.bot.send_message(uid, f"🕌 حان الآن وقت أذان {name} في بغداد.")
                        except: pass
                    last_notified[name] = "azan"
            
            # 2. أذكار الصباح والمساء التلقائية
            if now.hour == 6 and now.minute == 0 and last_notified.get("sabah") != now.day:
                for uid in list(subscribed_users):
                    try: await application.bot.send_message(uid, f"☀️ *تذكير بأذكار الصباح:*\n\n{TXT_AZKAR}")
                    except: pass
                last_notified["sabah"] = now.day
                
            if now.hour == 17 and now.minute == 0 and last_notified.get("masaa") != now.day:
                for uid in list(subscribed_users):
                    try: await application.bot.send_message(uid, f"🌙 *تذكير بأذكار المساء:*\n\n{TXT_AZKAR}")
                    except: pass
                last_notified["masaa"] = now.day

            # 3. دعاء دوري كل 3 ساعات
            if now.hour % 3 == 0 and now.hour != last_dua_hour:
                last_dua_hour = now.hour
                for uid in list(subscribed_users):
                    try: await application.bot.send_message(uid, f"🤲 *دعاء الساعة:* {DUA_LIST[now.hour % len(DUA_LIST)]}")
                    except: pass
                    
        except Exception as e:
            logging.error(f"Error in background task: {e}")
            
        await asyncio.sleep(30) # فحص نصف دقيقة لحفظ موارد السيرفر

# --- دوال البوت الأساسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribed_users.add(update.effective_user.id)
    kb = [
        [InlineKeyboardButton("⏱️ المواقيت", callback_data='prayer')],
        [InlineKeyboardButton("☀️ الأذكار", callback_data='azkar')],
        [InlineKeyboardButton("🤲 الأدعية", callback_data='duas')],
        [InlineKeyboardButton("🧭 القبلة", callback_data='qibla')]
    ]
    await update.message.reply_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    back_kb = [[InlineKeyboardButton("🔙 عودة للقائمة", callback_data='main')]]
    
    if query.data == 'prayer':
        await query.edit_message_text(TXT_PRAYER, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'azkar':
        await query.edit_message_text(TXT_AZKAR, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'duas':
        await query.edit_message_text(TXT_DUAS, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'qibla':
        await query.edit_message_text("🧭 *القبلة:* https://qiblafinder.withgoogle.com", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
    elif query.data == 'main':
        kb = [
            [InlineKeyboardButton("⏱️ المواقيت", callback_data='prayer')],
            [InlineKeyboardButton("☀️ الأذكار", callback_data='azkar')],
            [InlineKeyboardButton("🤲 الأدعية", callback_data='duas')],
            [InlineKeyboardButton("🧭 القبلة", callback_data='qibla')]
        ]
        await query.edit_message_text(TXT_WELCOME, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# --- تشغيل الخدمة على Render ---
def run_flask():
    app = Flask(__name__)
    @app.route('/')
    def home(): return "Bot Active"
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    # تشغيل محرك التنبيهات في خيط (Thread) مستقل كلياً
    threading.Thread(target=lambda: asyncio.run(schedule_checker(application)), daemon=True).start()
    
    application.run_polling()
