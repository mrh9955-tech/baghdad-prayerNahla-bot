import logging, os, threading
from flask import Flask
from datetime import datetime, time
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8804058766:AAH-FQxlVenlDxii1WWEuCn0_TDzRBxMKhs"
ADMIN_ID = 56567867 # ضع الأيدي الخاص بك هنا للتحكم
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# --- دوال المساعدة ---
async def broadcast(context, message):
    # هذه الدالة ترسل رسالة لكل المشتركين
    # ملاحظة: يجب تخزين أرقام المستخدمين في ملف أو قاعدة بيانات
    pass 

# --- نظام التنبيهات (Job Queue) ---
async def send_dua_task(context):
    await context.bot.send_message(chat_id=context.job.chat_id, text="🤲 *دعاء اليوم:* اللهم اشفِ كل مريض وألبسه ثوب الصحة والعافية.")

async def day_before_arafah(context):
    await context.bot.send_message(chat_id=context.job.chat_id, text="🌙 *تذكير:* غداً يوم عرفة، فضل صيامه عظيم، لا تنسوا النية!")

# --- التحكم (الإرسال من الأدمن) ---
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        # هنا يمكنك إضافة كود لإرسال رسالة أو صورة لكل المشتركين
        await update.message.reply_text("تم إرسال رسالتك للجميع.")

# --- التصميم الجديد (الواجهة) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # إضافة تنبيهات تلقائية للمستخدم عند البدء
    context.job_queue.run_repeating(send_dua_task, interval=10800, first=60, chat_id=update.effective_user.id)
    
    kb = [
        [InlineKeyboardButton("⏱️ المواقيت", callback_data='prayer')],
        [InlineKeyboardButton("☀️ أذكار الصباح والمساء", callback_data='azkar')],
        [InlineKeyboardButton("🤲 أدعية عرفة والشفاء", callback_data='duas')]
    ]
    await update.message.reply_text("🕌 مرحباً بك في بوت العبادات.\nنحن معك في كل وقت.", reply_markup=InlineKeyboardMarkup(kb))

# --- تشغيل البوت ---
if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    
    # ربط الدوال
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", admin_broadcast)) # للأدمن
    
    # تشغيل السيرفر الجانبي لـ Render
    threading.Thread(target=lambda: Flask(__name__).run(host='0.0.0.0', port=8080), daemon=True).start()
    
    application.run_polling()
