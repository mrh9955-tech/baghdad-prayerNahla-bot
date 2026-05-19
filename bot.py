import logging
import asyncio
import threading
import pytz
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')
subscribed_users = set()

# --- النصوص الكاملة ---
TXT_KURSI = (
    "👑 *آية الكرسي*\n\n"
    "اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ."
)

TXT_MORNING = (
    "☀️ *أذكار الصباح*\n\n"
    "١. أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير.\n"
    "٢. اللهم إني أسألك علماً نافعاً، ورزقاً طيباً، وعملاً متقبلاً.\n"
    "٣. اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك النشور."
)

TXT_EVENING = (
    "🌙 *أذكار المساء*\n\n"
    "١. أمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير.\n"
    "٢. اللهم ما أمسى بي من نعمة أو بأحد من خلقك، فمنك وحدك لا شريك لك، فلك الحمد ولك الشكر.\n"
    "٣. بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم."
)

TXT_SHIFA = (
    "🤲 *أدعية الشفاء (بنية شفاء الوالدة)\n\n"
    "١. اللهم رب الناس أذهب البأس، اشفِ أنت الشافي، لا شفاء إلا شفاؤك، شفاءً لا يغادر سقماً.\n"
    "٢. أذهب البأس رب الناس، بيدك الشفاء، لا كاشف له إلا أنت يا رب العالمين.\n"
    "٣. اللهم إني أسألك من عظيم لطفك، وكرمك، وسترك الجميل، أن تشفيها وتمدها بالصحة والعافية."
)

# --- دالة عرض النصوص ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # ربط الأزرار بالنصوص الكاملة
    if query.data == 'q_kursi':
        await query.edit_message_text(text=TXT_KURSI, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='quran_menu')]]))
    elif query.data == 'v_morning':
        await query.edit_message_text(text=TXT_MORNING, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='azkar_menu')]]))
    elif query.data == 'v_evening':
        await query.edit_message_text(text=TXT_EVENING, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='azkar_menu')]]))
    elif query.data == 'v_shifa':
        await query.edit_message_text(text=TXT_SHIFA, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='duas_menu')]]))
    
    # ... (باقي كود الأزرار والقوائم كما في الكود السابق)

# --- إكمال التشغيل ---
# (استخدم نفس نظام التشغيل في الكود السابق لتشغيل البوت والمهام الدورية)
