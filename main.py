import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import json
from datetime import datetime
import requests
import base64
import os
from keep_alive import start_keep_alive

# بدء عملية الحفاظ على النشاط
if 'RENDER' in os.environ:
    start_keep_alive()

# ... باقي الكود ...

# ===== تكوين الثوابت والإعدادات =====
ADMIN_IDS = [5222039643, 1937595344]  # ضع هنا معرف المشرف الخاص بك
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = "NR4U"
REPO_NAME = "Bot-telegram"
FILE_PATH = "auto_replies.json"

# ===== وظائف إدارة الملفات =====
def load_replies():
    """تحميل الردود من GitHub"""
    try:
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get(
            f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}',
            headers=headers
        )
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return json.loads(content)
    except Exception as e:
        print(f"Error loading replies: {e}")
        return {}

def save_replies(replies):
    """حفظ الردود في GitHub"""
    try:
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        current_file = requests.get(
            f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}',
            headers=headers
        ).json()

        content = base64.b64encode(json.dumps(replies, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        data = {
            'message': 'تحديث الردود',
            'content': content,
            'sha': current_file['sha']
        }
        
        requests.put(
            f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}',
            headers=headers,
            json=data
        )
    except Exception as e:
        print(f"Error saving replies: {e}")

# تحميل الردود عند بدء البوت
auto_replies = load_replies()

# ===== وظائف المساعدة =====
def is_admin(user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم مشرفًا"""
    return user_id in ADMIN_IDS

# ===== معالجات الأوامر الأساسية =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر البداية"""
    keyboard = [
        [InlineKeyboardButton("📝 إضافة رد", callback_data='help_add'),
         InlineKeyboardButton("📋 قائمة الردود", callback_data='list')],
        [InlineKeyboardButton("❌ حذف رد", callback_data='help_remove')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = "مرحبا عزيزي اختار من الازرار الي تحت"

    if update.message.chat.type == 'private':
        if is_admin(update.message.from_user.id):
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text("البوت مخصص لمجموعة متجر WOLF PLUS")
    else:
        await update.message.reply_text("مرحباً! أنا بوت الردود التلقائية.")

async def add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة رد نصي"""
    if not is_admin(update.message.from_user.id):
        return

    try:
        text = update.message.text.replace("/add ", "")
        keyword, reply = text.split("|")
        keyword = keyword.strip()
        reply = reply.strip()

        auto_replies[keyword] = {
            "type": "text",
            "content": reply,
            "added_by": update.message.from_user.id,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_replies(auto_replies)
        await update.message.reply_text(f"✅ تم إضافة الرد:\n🔑 الكلمة: {keyword}\n💬 الرد: {reply}")
    except:
        await update.message.reply_text("❌ خطأ في الصيغة\nالصيغة الصحيحة: /add الكلمة | الرد")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع أنواع الوسائط"""
    if not is_admin(update.message.from_user.id):
        return

    message = update.message

    try:
        # للصور والفيديو
        if message.caption:
            if message.photo and message.caption.startswith('/addphoto'):
                keyword = message.caption.replace("/addphoto", "").strip()
                file_id = message.photo[-1].file_id
                media_type = "photo"

            elif message.video and message.caption.startswith('/addvideo'):
                keyword = message.caption.replace("/addvideo", "").strip()
                file_id = message.video.file_id
                media_type = "video"
            else:
                return

        # للملصقات
        elif message.sticker and message.reply_to_message:
            if message.reply_to_message.text and message.reply_to_message.text.startswith('/addsticker'):
                keyword = message.reply_to_message.text.replace("/addsticker", "").strip()
                file_id = message.sticker.file_id
                media_type = "sticker"
            else:
                return
        else:
            return

        # تأكد من وجود كلمة مفتاحية
        if not keyword:
            await message.reply_text("❌ يجب تحديد كلمة مفتاحية!")
            return

        auto_replies[keyword] = {
            "type": media_type,
            "content": file_id,
            "added_by": message.from_user.id,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_replies(auto_replies)
        await message.reply_text(f"✅ تم إضافة {media_type} للكلمة: {keyword}")

    except Exception as e:
        error_msg = f"""❌ حدث خطأ!

طريقة الاستخدام:
• للصور: أرسل الصورة مع تعليق /addphoto الكلمة
• للفيديو: أرسل الفيديو مع تعليق /addvideo الكلمة
• للملصقات: 
  1. اكتب أولاً: /addsticker الكلمة
  2. ثم رد على رسالتك بالملصق"""
        await message.reply_text(error_msg)

async def remove_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف رد"""
    if not is_admin(update.message.from_user.id):
        return

    try:
        keyword = update.message.text.replace("/remove ", "").strip()
        if keyword in auto_replies:
            del auto_replies[keyword]
            save_replies(auto_replies)
            await update.message.reply_text(f"✅ تم حذف الرد للكلمة: {keyword}")
        else:
            await update.message.reply_text("❌ الكلمة غير موجودة!")
    except:
        await update.message.reply_text("❌ خطأ في الصيغة\nالصيغة الصحيحة: /remove الكلمة")

async def list_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة الردود"""
    if not is_admin(update.message.from_user.id):
        return

    if not auto_replies:
        await update.message.reply_text("لا توجد ردود مضافة!")
        return

    reply_text = "📋 قائمة الردود:\n\n"
    for keyword, data in auto_replies.items():
        media_type = data.get("type", "text")
        reply_text += f"🔑 الكلمة: {keyword}\n💭 النوع: {media_type}\n➖➖➖➖➖\n"

    await update.message.reply_text(reply_text)

# ===== معالج الرسائل العادية =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل العادية والرد عليها"""
    if update.message.chat.type not in ['group', 'supergroup']:
        return

    if not update.message.text:
        return

    message_text = update.message.text.lower()
    for keyword, data in auto_replies.items():
        if keyword.lower() in message_text:
            media_type = data.get("type", "text")
            content = data.get("content", "")

            try:
                if media_type == "text":
                    await update.message.reply_text(content)
                elif media_type == "photo":
                    await update.message.reply_photo(content)
                elif media_type == "video":
                    await update.message.reply_video(content)
                elif media_type == "sticker":
                    await update.message.reply_sticker(content)
            except Exception as e:
                print(f"Error sending {media_type}: {e}")
            break

# ===== معالج الأزرار =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأزرار التفاعلية"""
    query = update.callback_query
    await query.answer()

    if query.data == 'help_add':
        help_text = """طريقة إضافة الردود:

1️⃣ رد نصي:
/add الكلمة | الرد

2️⃣ صورة:
ارسل الصورة مع تعليق:
/addphoto الكلمة

3️⃣ فيديو:
ارسل الفيديو مع تعليق:
/addvideo الكلمة

4️⃣ ملصق:
1. اكتب: /addsticker الكلمة
2. ثم رد على رسالتك بالملصق"""
        await query.message.edit_text(help_text)

    elif query.data == 'help_remove':
        await query.message.edit_text(
            "لحذف رد، استخدم الأمر:\n"
            "/remove الكلمة"
        )

    elif query.data == 'list':
        if auto_replies:
            reply_text = "📋 قائمة الردود:\n\n"
            for keyword, data in auto_replies.items():
                media_type = data.get("type", "text")
                reply_text += f"🔑 الكلمة: {keyword}\n💭 النوع: {media_type}\n➖➖➖➖➖\n"
            await query.message.edit_text(reply_text)
        else:
            await query.message.edit_text("لا توجد ردود مضافة!")

# ===== الدالة الرئيسية =====
def main():
    """الدالة الرئيسية لتشغيل البوت"""
    TOKEN = os.environ.get("BOT_TOKEN")
    application = Application.builder().token(TOKEN).build()

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_reply))
    application.add_handler(CommandHandler("remove", remove_reply))
    application.add_handler(CommandHandler("list", list_replies))

    # إضافة معالج الوسائط
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & ~filters.TEXT, 
        handle_media
    ))

    # إضافة معالج الأزرار والرسائل العادية
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # تشغيل البوت
    print("🤖 جاري تشغيل البوت...")
    application.run_polling()

if __name__ == '__main__':
    main()
