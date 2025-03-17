import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from threading import Thread
import os
import logging
import json
import re
from dotenv import load_dotenv
import requests
import time
import schedule

# إعداد التسجيل (Logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تحميل المتغيرات من ملف .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 5435422706  # معرف الأدمن (@Hobby98)
ADMIN_USERNAME = "@Hobby98"
KEEP_ALIVE_CHAT_ID = 7619467372  # المعرف الأساسي لرسائل التشغيل (@Hima_money)
KEEP_ALIVE_BACKUP_CHAT_ID = 725542446  # المعرف البديل لرسائل التشغيل (@HemaHendy)
CHANNEL_USERNAME = "@KanzInternetFree"
BOT_USERNAME = "@KanzInternetFreeBot"

# إعداد البوت
bot = telebot.TeleBot(TOKEN)

# إعداد Flask للـ Webhook
app = Flask(__name__)

# متغيرات العروض
OFFER_PACKAGES_TITLE = "📋 عروض الباقات"
CONTACT_US_TITLE = "📲 تواصل معنا"
REQUEST_CREDIT_TITLE = "💰 طلب رصيد"
SUBSCRIBE_TITLE = "📩 اشتراك"
SPECIAL_DISCOUNT_FLEX_260_TITLE = "📢 خصم خاص لباقة فليكس 260"

OFFER_BUSINESS_TITLE = "📌 عروض فودافون بيزنس"
OFFER_FLEX_TITLE = "📌 عروض فودافون فليكس"
OFFER_ORANGE_TITLE = "📌 عروض الإنترنت المنزلي (أورانج)"
OFFER_WE_TITLE = "📌 عروض WE"

VODAFONE_BUSINESS_LINE_PURCHASE = "📌 شراء خط فودافون بيزنس"
VODAFONE_BUSINESS_DETAILS = {
    "160": {
        "price": "160 جنيه (شامل أول شهر)",
        "conditions": """
📌 الشروط والأحكام:
- يجب شحن الباقة قبل انتهائها لضمان استمرار الخدمة.
- غرامات التأخير:
  - حتى 6 أيام: لا غرامة.
  - من 7 إلى 15 يومًا: غرامة 20 جنيه.
  - من 16 إلى 30 يومًا: غرامة 30 جنيه.
  - بعد 30 يومًا: يتم إيقاف الخط نهائيًا.
- يمكن دفع مبلغ تأمين اختياري بقيمة الباقة لمنع توقف الخدمة المفاجئ.
"""
    },
    "65": {
        "price": "65 جنيه",
        "package": "باقة 2500 فليكس",
        "details": "✅ 2500 فليكس شهريًا\n✅ 500 ميجا فيسبوك\n✅ 1500 دقيقة + واتساب مجاني داخل المجموعة"
    },
    "110": {
        "price": "110 جنيه",
        "package": "باقة 3500 فليكس",
        "details": "✅ 3500 فليكس شهريًا\n✅ 1000 ميجا فيسبوك\n✅ 1500 دقيقة + واتساب مجاني داخل المجموعة"
    },
    "6000": {
        "price": "160 جنيه",
        "package": "باقة 6000 فليكس",
        "details": "✅ 6000 فليكس شهريًا\n✅ 1500 ميجا فيسبوك\n✅ 1500 دقيقة + واتساب مجاني داخل المجموعة"
    }
}

VODAFONE_FLEX_DETAILS = {
    "13000": {"price": "170 جنيه", "package": "باقة 13,000 فليكس"},
    "5200": {"price": "70 جنيه", "package": "باقة 5,200 فليكس"},
    "2600": {"price": "50 جنيه", "package": "باقة 2,600 فليكس"},
    "260": {"price": "250 جنيه", "package": "باقة 260 فليكس", "details": "✅ 13,000 فليكس للخط الرئيسي\n✅ 5,200 فليكس للفردين بدون خصم من فليكسات الخط الرئيسي"}
}

ORANGE_HOME_DETAILS = {
    "200": {"price": "185 جنيه (بدل 330.6 جنيه)", "package": "باقة 200 جيجابايت"},
    "500": {"price": "230 جنيه (بدل 410.4 جنيه)", "package": "باقة 500 جيجابايت (250+250)"},
    "600": {"price": "268 جنيه (بدل 649.8 جنيه)", "package": "باقة 600 جيجابايت (300+300)"},
    "1000": {"price": "338 جنيه (بدل 1550.4 جنيه)", "package": "باقة 1000 جيجابيت (500+500)"}
}
ORANGE_CONTACT = "📢 الاشتراك عن طريق '📲 تواصل معنا' (@Hobby98)"

WE_OFFER_TEXT = "📢 قريبًا، تابع القناة للمزيد!"
VODAFONE_CASH_NUMBER = "01091603375"

# متغيرات لحفظ الحالة
menu_history = {}
temp_data = {}
credit_history = {}  # لتخزين الحسابات السابقة للرصيد

# دالة لإنشاء الأزرار الثابتة
def create_fixed_buttons():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    return markup

# دالة للتحقق من الاشتراك في القناة
def check_subscription(chat_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, chat_id)
        logger.info(f"Member status for chat_id {chat_id}: {member.status}")
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking subscription for chat_id {chat_id}: {e}")
        return False

# دالة لتحديث تاريخ القوايم
def update_menu_history(chat_id, menu):
    if chat_id not in menu_history:
        menu_history[chat_id] = []
    if menu not in menu_history[chat_id]:
        menu_history[chat_id].append(menu)

# دالة للرجوع للقايمة السابقة
def get_previous_menu(chat_id):
    if chat_id in menu_history and len(menu_history[chat_id]) > 1:
        menu_history[chat_id].pop()
        return menu_history[chat_id][-1]
    return "main"

# دالة لإنشاء القايمة الرئيسية
def create_main_menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(OFFER_PACKAGES_TITLE, callback_data="offers"))
    markup.row(InlineKeyboardButton(CONTACT_US_TITLE, url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton(REQUEST_CREDIT_TITLE, callback_data="credit"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    update_menu_history(chat_id, "main")
    if chat_id in temp_data:
        del temp_data[chat_id]
    return markup

# دالة لإنشاء قائمة العروض
def create_offers_menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(OFFER_BUSINESS_TITLE, callback_data="vodafone_business"))
    markup.row(InlineKeyboardButton(OFFER_FLEX_TITLE, callback_data="vodafone_flex"))
    markup.row(InlineKeyboardButton(OFFER_ORANGE_TITLE, callback_data="orange_home"))
    markup.row(InlineKeyboardButton(OFFER_WE_TITLE, callback_data="we_offer"))
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    update_menu_history(chat_id, "offers")
    if chat_id in temp_data:
        del temp_data[chat_id]
    return markup

# دالة لإنشاء تفاصيل عروض فودافون بيزنس
def create_vodafone_business_menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(VODAFONE_BUSINESS_LINE_PURCHASE, callback_data="vodafone_business_160"))
    markup.row(InlineKeyboardButton(f"💰 {VODAFONE_BUSINESS_DETAILS['65']['price']} - {VODAFONE_BUSINESS_DETAILS['65']['package']}", callback_data="vodafone_business_65"))
    markup.row(InlineKeyboardButton(f"💰 {VODAFONE_BUSINESS_DETAILS['110']['price']} - {VODAFONE_BUSINESS_DETAILS['110']['package']}", callback_data="vodafone_business_110"))
    markup.row(InlineKeyboardButton(f"💰 {VODAFONE_BUSINESS_DETAILS['6000']['price']} - {VODAFONE_BUSINESS_DETAILS['6000']['package']}", callback_data="vodafone_business_6000"))
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    update_menu_history(chat_id, "vodafone_business")
    if chat_id in temp_data:
        del temp_data[chat_id]
    return markup

# دالة لإنشاء تفاصيل باقة معينة (فودافون بيزنس)
def create_package_details(chat_id, package_type, package_id):
    markup = InlineKeyboardMarkup()
    if package_type == "vodafone_business" and package_id == "160":
        text = f"{VODAFONE_BUSINESS_LINE_PURCHASE}\n{VODAFONE_BUSINESS_DETAILS[package_id]['price']}\n{VODAFONE_BUSINESS_DETAILS[package_id]['conditions']}"
    else:
        details = VODAFONE_BUSINESS_DETAILS[package_id]
        text = f"📌 تفاصيل الباقة:\n{details['price']} - {details['package']}\n{details.get('details', '')}"
        markup.row(InlineKeyboardButton(SUBSCRIBE_TITLE, callback_data=f"subscribe_vodafone_business_{package_id}"))
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    update_menu_history(chat_id, f"vodafone_business_{package_id}")
    return markup, text

# دالة لإنشاء تفاصيل عروض فودافون فليكس
def create_vodafone_flex_menu(chat_id):
    markup = InlineKeyboardMarkup()
    for package_id, details in VODAFONE_FLEX_DETAILS.items():
        markup.row(InlineKeyboardButton(f"💰 {details['price']} - {details['package']}", callback_data=f"vodafone_flex_{package_id}"))
    markup.row(InlineKeyboardButton(SPECIAL_DISCOUNT_FLEX_260_TITLE, callback_data="discount_flex_260"))
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    update_menu_history(chat_id, "vodafone_flex")
    if chat_id in temp_data:
        del temp_data[chat_id]
    return markup

# دالة لإنشاء تفاصيل باقة فودافون فليكس
def create_vodafone_flex_details(chat_id, package_id):
    details = VODAFONE_FLEX_DETAILS[package_id]
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(SUBSCRIBE_TITLE, callback_data=f"subscribe_vodafone_flex_{package_id}"))
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    update_menu_history(chat_id, f"vodafone_flex_{package_id}")
    if chat_id in temp_data:
        del temp_data[chat_id]
    return markup, f"📌 تفاصيل الباقة:\n{details['price']} - {details['package']}\n{details.get('details', '')}"

# دالة لإنشاء قائمة خصم خاص لباقة فودافون فليكس
def create_discount_menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(CONTACT_US_TITLE, url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    update_menu_history(chat_id, "discount_flex_260")
    if chat_id in temp_data:
        del temp_data[chat_id]
    return markup

# دالة لإنشاء تفاصيل عروض أورانج
def create_orange_home_menu(chat_id):
    markup = InlineKeyboardMarkup()
    for package_id, details in ORANGE_HOME_DETAILS.items():
        markup.row(InlineKeyboardButton(f"💰 {details['price']} - {details['package']}", callback_data=f"orange_home_{package_id}"))
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    update_menu_history(chat_id, "orange_home")
    if chat_id in temp_data:
        del temp_data[chat_id]
    return markup

# دالة لإنشاء تفاصيل عروض أورانج (باقة معينة)
def create_orange_home_details(chat_id, package_id):
    details = ORANGE_HOME_DETAILS[package_id]
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(SUBSCRIBE_TITLE, callback_data=f"subscribe_orange_home_{package_id}"))
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    update_menu_history(chat_id, f"orange_home_{package_id}")
    if chat_id in temp_data:
        del temp_data[chat_id]
    return markup, f"📌 تفاصيل الباقة:\n{details['price']} - {details['package']}\n{ORANGE_CONTACT}"

# دالة للتحقق من رقم فودافون
def is_valid_vodafone_number(number):
    return bool(re.match(r'^01\d{9}$', number))

# دالة للتحقق من الباسورد
def is_valid_password(password):
    if ' ' in password:
        return False
    pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z\d])[A-Za-z\d@!#$%^&*()_+\-=\[\]{};:\'\\|,.<>/?~`]{8,}$'
    return bool(re.match(pattern, password))

# دالة لحساب الرصيد مع 20% عمولة
def calculate_credit(amount_str):
    try:
        # تنظيف الإدخال من المسافات
        amount_str = amount_str.strip()
        # التأكد إن الإدخال كله أرقام
        if not amount_str.replace('.', '', 1).isdigit():
            return None, None
        amount = float(amount_str)
        if amount <= 0:
            return None, None
        commission = amount * 0.20  # 20% عمولة
        total = amount + commission
        return amount, total
    except (ValueError, AttributeError):
        return None, None

# دالة لإرسال البيانات للأدمن
def send_to_admin(chat_id, data, package_type=None, package_id=None, client_mention=None):
    subscription_type = f"📌 نوع الخدمة: اشتراك {package_type}" if package_id else "📌 نوع الخدمة: طلب رصيد"
    if package_id:
        subscription_type += f" - {package_id}"

    # إذا لم يتم تمرير client_mention، نجيب المعرف هنا
    if client_mention is None:
        try:
            user = bot.get_chat(chat_id)
            username = user.username if hasattr(user, 'username') and user.username else None
            if username:
                client_mention = f"[@{username}](tg://user?id={chat_id})"
                logger.info(f"Username detected and processed: {username}")
            else:
                client_mention = f"معرف العميل: {chat_id} (لا يوجد username)"
                logger.info(f"No username, using Chat ID: {chat_id}")
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            client_mention = f"معرف العميل: {chat_id} (خطأ في جلب البيانات)"

    message_text = f"📩 طلب جديد من عميل:\n{subscription_type}\n{chr(10).join(data)}\nالعميل: {client_mention}\nالبوت: {BOT_USERNAME}"
    try:
        bot.send_message(ADMIN_ID, message_text, parse_mode="Markdown", disable_web_page_preview=True)
        logger.info(f"Message sent to admin for chat_id: {chat_id} with mention: {client_mention}")
    except Exception as e:
        logger.error(f"Failed to send message to admin ({ADMIN_ID}): {e}")
        # إذا فشل الإرسال للأدمن، بنحاول نبعت رسالة تحذير للأدمن نفسه
        try:
            bot.send_message(ADMIN_ID, f"⚠️ خطأ: فشل في إرسال بيانات طلب من العميل {chat_id}. السبب: {str(e)}")
            logger.info(f"Sent error notification to admin ({ADMIN_ID})")
        except Exception as e2:
            logger.error(f"Failed to send error notification to admin ({ADMIN_ID}): {e2}")

# دالة لإرسال رسالة التأكيد للأدمن
def send_confirmation_to_admin(chat_id, confirmation_message):
    try:
        bot.send_message(ADMIN_ID, confirmation_message, parse_mode="Markdown", disable_web_page_preview=True)
        logger.info(f"Confirmation message sent to admin ({ADMIN_ID}) for chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Failed to send confirmation message to admin ({ADMIN_ID}): {e}")

# دالة لإرسال رسالة كل 4 دقايق و30 ثانية للحفاظ على نشاط البوت
def send_keep_alive_message():
    try:
        bot.send_message(KEEP_ALIVE_CHAT_ID, "📢 البوت شغال الآن!")
        logger.info(f"Sent keep-alive message to {KEEP_ALIVE_CHAT_ID} (@Hima_money)")
    except Exception as e:
        logger.error(f"Error sending keep-alive message to {KEEP_ALIVE_CHAT_ID} (@Hima_money): {e}")
        # إذا فشل الإرسال للمعرف الأساسي، نحاول المعرف البديل
        try:
            bot.send_message(KEEP_ALIVE_BACKUP_CHAT_ID, "📢 البوت شغال الآن! (تم الإرسال للمعرف البديل بسبب فشل المعرف الأساسي)")
            logger.info(f"Sent keep-alive message to backup {KEEP_ALIVE_BACKUP_CHAT_ID} (@HemaHendy)")
        except Exception as e2:
            logger.error(f"Error sending keep-alive message to backup {KEEP_ALIVE_BACKUP_CHAT_ID} (@HemaHendy): {e2}")

# معالجة الأوامر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    logger.info(f"Received /start command from chat_id: {chat_id}")
    if not check_subscription(chat_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_subscription"))
        bot.send_message(chat_id, f"مرحبًا! لاستخدام البوت، يرجى الاشتراك في قناتنا أولاً: {CHANNEL_USERNAME}", reply_markup=markup)
        logger.info(f"Sent subscription prompt to chat_id: {chat_id}")
    else:
        bot.send_message(chat_id, "مرحبًا! اختر من القائمة التالية:", reply_markup=create_main_menu(chat_id))
        logger.info(f"Sent main menu to chat_id: {chat_id}")

# أمر للتحقق من حالة الـ Webhook
@bot.message_handler(commands=['checkwebhook'])
def check_webhook_status(message):
    chat_id = message.chat.id
    try:
        webhook_info = bot.get_webhook_info()
        logger.info(f"Webhook info: {webhook_info}")
        bot.send_message(chat_id, f"حالة الـ Webhook:\n{webhook_info}")
    except Exception as e:
        logger.error(f"Error checking webhook status: {e}")
        bot.send_message(chat_id, f"حدث خطأ أثناء التحقق من الـ Webhook: {str(e)}")

# معالجة الضغط على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data
    logger.info(f"Received callback from chat_id {chat_id}: {data}")

    # التحقق من الاشتراك في القناة
    if data != "check_subscription" and not check_subscription(chat_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_subscription"))
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"يرجى الاشتراك في القناة أولاً: {CHANNEL_USERNAME}",
            reply_markup=markup
        )
        logger.info(f"Sent subscription prompt to chat_id: {chat_id}")
        return

    # معالجة زر "تحقق من الاشتراك"
    if data == "check_subscription":
        if check_subscription(chat_id):
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="مرحبًا! اختر من القائمة التالية:",
                reply_markup=create_main_menu(chat_id)
            )
            logger.info(f"User {chat_id} is subscribed, sent main menu")
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
            markup.add(InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_subscription"))
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"لم يتم الاشتراك بعد! يرجى الاشتراك في القناة أولاً: {CHANNEL_USERNAME}",
                reply_markup=markup
            )
            logger.info(f"User {chat_id} is not subscribed, sent subscription prompt")
        return

    # باقي الكود لمعالجة الأزرار الأخرى
    if data == "main":
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="القائمة الرئيسية:", reply_markup=create_main_menu(chat_id))
        logger.info(f"Sent main menu to chat_id: {chat_id}")
    elif data == "back":
        previous_menu = get_previous_menu(chat_id)
        if previous_menu == "main":
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="القائمة الرئيسية:", reply_markup=create_main_menu(chat_id))
            logger.info(f"Returned to main menu for chat_id: {chat_id}")
        elif previous_menu == "offers":
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="اختر عرضًا:", reply_markup=create_offers_menu(chat_id))
            logger.info(f"Returned to offers menu for chat_id: {chat_id}")
        elif previous_menu == "vodafone_business":
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="عروض فودافون بيزنس:", reply_markup=create_vodafone_business_menu(chat_id))
            logger.info(f"Returned to vodafone_business menu for chat_id: {chat_id}")
        elif previous_menu == "vodafone_flex":
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="عروض فودافون فليكس:", reply_markup=create_vodafone_flex_menu(chat_id))
            logger.info(f"Returned to vodafone_flex menu for chat_id: {chat_id}")
        elif previous_menu == "orange_home":
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="عروض أورانج المنزلي:", reply_markup=create_orange_home_menu(chat_id))
            logger.info(f"Returned to orange_home menu for chat_id: {chat_id}")
    elif data == "offers":
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="اختر عرضًا:", reply_markup=create_offers_menu(chat_id))
        logger.info(f"Sent offers menu to chat_id: {chat_id}")
    elif data == "vodafone_business":
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="عروض فودافون بيزنس:", reply_markup=create_vodafone_business_menu(chat_id))
        logger.info(f"Sent vodafone_business menu to chat_id: {chat_id}")
    elif data.startswith("vodafone_business_"):
        package_id = data.split("_")[-1]
        markup, text = create_package_details(chat_id, "vodafone_business", package_id)
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
        logger.info(f"Sent vodafone_business package details for package_id {package_id} to chat_id: {chat_id}")
    elif data == "vodafone_flex":
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="عروض فودافون فليكس:", reply_markup=create_vodafone_flex_menu(chat_id))
        logger.info(f"Sent vodafone_flex menu to chat_id: {chat_id}")
    elif data.startswith("vodafone_flex_"):
        package_id = data.split("_")[-1]
        markup, text = create_vodafone_flex_details(chat_id, package_id)
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
        logger.info(f"Sent vodafone_flex package details for package_id {package_id} to chat_id: {chat_id}")
    elif data == "discount_flex_260":
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="📢 خصم خاص لباقة فليكس 260:\nتواصل معنا للحصول على العرض!", reply_markup=create_discount_menu(chat_id))
        logger.info(f"Sent discount_flex_260 message to chat_id: {chat_id}")
    elif data == "orange_home":
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="عروض أورانج المنزلي:", reply_markup=create_orange_home_menu(chat_id))
        logger.info(f"Sent orange_home menu to chat_id: {chat_id}")
    elif data.startswith("orange_home_"):
        package_id = data.split("_")[-1]
        markup, text = create_orange_home_details(chat_id, package_id)
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
        logger.info(f"Sent orange_home package details for package_id {package_id} to chat_id: {chat_id}")
    elif data == "we_offer":
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=WE_OFFER_TEXT, reply_markup=create_fixed_buttons())
        logger.info(f"Sent WE offer message to chat_id: {chat_id}")
    elif data == "credit":
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="📝 من فضلك، أدخل المبلغ المطلوب:", reply_markup=create_fixed_buttons())
        bot.register_next_step_handler_by_chat_id(chat_id, handle_credit_request)
        logger.info(f"Prompted for credit amount from chat_id: {chat_id}")
    elif data.startswith("subscribe_vodafone_business_"):
        package_id = data.split("_")[-1]
        handle_subscription(chat_id, call.message, "vodafone_business", package_id)
        logger.info(f"Started subscription for vodafone_business for chat_id: {chat_id}")
    elif data.startswith("subscribe_vodafone_flex_"):
        package_id = data.split("_")[-1]
        handle_subscription(chat_id, call.message, "vodafone_flex", package_id)
        logger.info(f"Started subscription for vodafone_flex for chat_id: {chat_id}")
    elif data.startswith("subscribe_orange_home_"):
        package_id = data.split("_")[-1]
        handle_subscription(chat_id, call.message, "orange_home", package_id)
        logger.info(f"Started subscription for orange_home for chat_id: {chat_id}")
    elif data == "copy_vodafone_cash":
        bot.answer_callback_query(call.id, text=f"تم نسخ الرقم: {VODAFONE_CASH_NUMBER}", show_alert=True)
        logger.info(f"Copied Vodafone Cash number for chat_id: {chat_id}")
    elif data.startswith("next_to_paid_vodafone_cash_"):
        next_to_paid_vodafone_cash(call)
        logger.info(f"Prompted for paid Vodafone Cash number for chat_id: {chat_id}")
    elif data == "recalculate_credit":
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="📝 من فضلك، أدخل المبلغ المطلوب:", reply_markup=create_fixed_buttons())
        bot.register_next_step_handler_by_chat_id(chat_id, handle_credit_request)
        logger.info(f"Prompted for credit recalculation for chat_id: {chat_id}")
    elif data == "clear_credit":
        if chat_id in credit_history:
            del credit_history[chat_id]
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="🗑️ تم مسح الحساب السابق.\nاختر من القائمة التالية:", reply_markup=create_main_menu(chat_id))
        logger.info(f"Cleared credit history for chat_id: {chat_id}")
    elif data.startswith("proceed_to_recharge_"):
        amount, total = credit_history.get(chat_id, {}).get("amount"), credit_history.get(chat_id, {}).get("total")
        if amount is None or total is None:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="❌ حدث خطأ، من فضلك ابدأ من جديد.", reply_markup=create_fixed_buttons())
            logger.error(f"Error: Credit history missing for chat_id {chat_id}")
            return
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton(f"📋 اضغط لنسخ رقم فودافون كاش: {VODAFONE_CASH_NUMBER}", callback_data="copy_vodafone_cash"))
        markup.row(InlineKeyboardButton("➡️ التالي", callback_data=f"next_to_recharge_vodafone_cash_{chat_id}"))
        markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
        markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
        markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"📝 هذا رقم فودافون كاش الخاص بنا للدفع:\n{VODAFONE_CASH_NUMBER}\nاضغط على 'التالي' للمتابعة:", reply_markup=markup)
        logger.info(f"Prompted for recharge Vodafone Cash number for chat_id: {chat_id}")
    elif data.startswith("next_to_recharge_vodafone_cash_"):
        next_to_recharge_vodafone_cash(call)
        logger.info(f"Prompted for recharge Vodafone Cash number for chat_id: {chat_id}")
    elif data.startswith("next_to_recharge_number_"):
        next_to_recharge_number(call)
        logger.info(f"Prompted for recharge number for chat_id: {chat_id}")

# دالة لمعالجة الاشتراك
def handle_subscription(chat_id, message, package_type=None, package_id=None):
    markup = create_fixed_buttons()

    if package_type == "vodafone_business" and package_id:
        # جلب معرف العميل بنفس الطريقة المستخدمة في "طلب رصيد"
        try:
            user = bot.get_chat(chat_id)
            username = user.username if hasattr(user, 'username') and user.username else None
            if username:
                client_mention = f"[@{username}](tg://user?id={chat_id})"
                logger.info(f"Username detected and processed: {username}")
            else:
                client_mention = f"معرف العميل: {chat_id} (لا يوجد username)"
                logger.info(f"No username, using Chat ID: {chat_id}")
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            client_mention = f"معرف العميل: {chat_id} (خطأ في جلب البيانات)"

        package_details = VODAFONE_BUSINESS_DETAILS[package_id]
        subscription_details = f"📌 تفاصيل الباقة:\n{package_details['price']} - {package_details['package']}\n{package_details.get('details', '')}"
        send_to_admin(chat_id, [subscription_details], package_type, package_id, client_mention)
        confirmation_message = f"📩 تم إرسال طلبك بنجاح!\nجاري تفعيل باقة {package_details['package']} الآن.\n📲 تواصل مع {ADMIN_USERNAME} لتأكيد البيانات والتفعيل النهائي."
        bot.send_message(chat_id, confirmation_message, reply_markup=markup)
        send_confirmation_to_admin(chat_id, confirmation_message)
    elif package_type == "vodafone_flex" and package_id:
        temp_data[chat_id] = {"package_type": package_type, "package_id": package_id, "data": []}
        bot.send_message(chat_id, "📝 من فضلك، أدخل رقم تطبيق أنا فودافون (يبدأ بـ 01 ويتكون من 11 رقمًا):", reply_markup=markup)
        update_menu_history(chat_id, f"subscribe_{package_type}_{package_id}_step1")
        bot.register_next_step_handler_by_chat_id(chat_id, process_ana_vodafone_number, chat_id)
    elif package_type == "orange_home" and package_id:
        # جلب معرف العميل بنفس الطريقة المستخدمة في "طلب رصيد"
        try:
            user = bot.get_chat(chat_id)
            username = user.username if hasattr(user, 'username') and user.username else None
            if username:
                client_mention = f"[@{username}](tg://user?id={chat_id})"
                logger.info(f"Username detected and processed: {username}")
            else:
                client_mention = f"معرف العميل: {chat_id} (لا يوجد username)"
                logger.info(f"No username, using Chat ID: {chat_id}")
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            client_mention = f"معرف العميل: {chat_id} (خطأ في جلب البيانات)"

        package_details = ORANGE_HOME_DETAILS[package_id]
        subscription_details = f"📌 تفاصيل الباقة:\n{package_details['price']} - {package_details['package']}"
        send_to_admin(chat_id, [subscription_details], package_type, package_id, client_mention)
        confirmation_message = f"📩 تم إرسال طلبك بنجاح!\nجاري تفعيل باقة {package_details['package']} الآن.\n📲 تواصل مع {ADMIN_USERNAME} لتأكيد البيانات والتفعيل النهائي."
        bot.send_message(chat_id, confirmation_message, reply_markup=markup)
        send_confirmation_to_admin(chat_id, confirmation_message)

# دالة لمعالجة رقم أنا فودافون
def process_ana_vodafone_number(message, chat_id):
    if chat_id not in temp_data:
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ حدث خطأ، من فضلك ابدأ من جديد باستخدام /start", reply_markup=markup)
        logger.error(f"Error: temp_data missing for chat_id {chat_id} in process_ana_vodafone_number")
        return
    number = message.text.strip()
    if not is_valid_vodafone_number(number):
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ رقم أنا فودافون غير صحيح! يجب أن يبدأ بـ 01 ويتكون من 11 رقمًا فقط (بدون حروف أو مسافات). حاول مرة أخرى:", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, process_ana_vodafone_number, chat_id)
        logger.info(f"Invalid Vodafone number entered by chat_id {chat_id}: {number}")
        return
    temp_data[chat_id]["data"].append(f"رقم أنا فودافون: {number}")
    markup = create_fixed_buttons()
    bot.send_message(chat_id, "📝 من فضلك، أدخل الرقم السري (الباسورد) لحساب أنا فودافون:\n- يجب أن يحتوي على حروف كبيرة وصغيرة (إنجليزية).\n- يحتوي على أرقام.\n- يحتوي على علامات خاصة (مثل @، !، #، $).\n- بدون مسافات.", reply_markup=markup)
    update_menu_history(chat_id, f"subscribe_{temp_data[chat_id]['package_type']}_{temp_data[chat_id]['package_id']}_step2")
    bot.register_next_step_handler_by_chat_id(chat_id, process_password, chat_id)
    logger.info(f"Processed Vodafone number for chat_id {chat_id}: {number}")

# دالة لمعالجة الرقم السري
def process_password(message, chat_id):
    if chat_id not in temp_data:
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ حدث خطأ، من فضلك ابدأ من جديد باستخدام /start", reply_markup=markup)
        logger.error(f"Error: temp_data missing for chat_id {chat_id} in process_password")
        return
    password = message.text.strip()
    if not is_valid_password(password):
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ الباسورد غير صحيح! يجب أن يحتوي على:\n- حروف كبيرة وصغيرة (إنجليزية).\n- أرقام.\n- علامات خاصة (مثل @، !، #، $).\n- بدون مسافات.\nحاول مرة أخرى:", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, process_password, chat_id)
        logger.info(f"Invalid password entered by chat_id {chat_id}")
        return
    temp_data[chat_id]["data"].append(f"الرقم السري: {password}")
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(f"📋 اضغط لنسخ رقم فودافون كاش: {VODAFONE_CASH_NUMBER}", callback_data="copy_vodafone_cash"))
    markup.row(InlineKeyboardButton("➡️ التالي", callback_data=f"next_to_paid_vodafone_cash_{chat_id}"))
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))
    bot.send_message(chat_id, f"📝 هذا رقم فودافون كاش الخاص بنا للدفع:\n{VODAFONE_CASH_NUMBER}\nاضغط على 'التالي' للمتابعة:", reply_markup=markup)
    update_menu_history(chat_id, f"subscribe_{temp_data[chat_id]['package_type']}_{temp_data[chat_id]['package_id']}_step3")
    logger.info(f"Processed password for chat_id {chat_id}")

# دالة لمعالجة الانتقال إلى طلب رقم فودافون كاش المدفوع منه (للاشتراك في فودافون فليكس)
def next_to_paid_vodafone_cash(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    if chat_id not in temp_data:
        markup = create_fixed_buttons()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="❌ حدث خطأ، من فضلك ابدأ من جديد باستخدام /start", reply_markup=markup)
        logger.error(f"Error: temp_data missing for chat_id {chat_id} in next_to_paid_vodafone_cash")
        return
    markup = create_fixed_buttons()
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="📝 من فضلك، أدخل رقم فودافون كاش المدفوع منه (يبدأ بـ 01 ويتكون من 11 رقمًا):", reply_markup=markup)
    update_menu_history(chat_id, f"subscribe_{temp_data[chat_id]['package_type']}_{temp_data[chat_id]['package_id']}_step4")
    bot.register_next_step_handler_by_chat_id(chat_id, process_paid_vodafone_cash, chat_id)
    logger.info(f"Prompted for paid Vodafone Cash number for chat_id: {chat_id}")

# دالة لمعالجة رقم فودافون كاش المدفوع منه (للاشتراك في فودافون فليكس)
def process_paid_vodafone_cash(message, chat_id):
    if chat_id not in temp_data:
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ حدث خطأ، من فضلك ابدأ من جديد باستخدام /start", reply_markup=markup)
        logger.error(f"Error: temp_data missing for chat_id {chat_id} in process_paid_vodafone_cash")
        return
    number = message.text.strip()
    if not is_valid_vodafone_number(number):
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ رقم فودافون كاش غير صحيح! يجب أن يبدأ بـ 01 ويتكون من 11 رقمًا فقط (بدون حروف أو مسافات). حاول مرة أخرى:", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, process_paid_vodafone_cash, chat_id)
        logger.info(f"Invalid paid Vodafone Cash number entered by chat_id {chat_id}: {number}")
        return
    package_type = temp_data[chat_id]["package_type"]
    package_id = temp_data[chat_id]["package_id"]
    data = temp_data[chat_id]["data"]
    data.append(f"رقم فودافون كاش المدفوع منه: {number}")

    # جلب معرف العميل بنفس الطريقة المستخدمة في "طلب رصيد"
    try:
        user = bot.get_chat(chat_id)
        username = user.username if hasattr(user, 'username') and user.username else None
        if username:
            client_mention = f"[@{username}](tg://user?id={chat_id})"
            logger.info(f"Username detected and processed: {username}")
        else:
            client_mention = f"معرف العميل: {chat_id} (لا يوجد username)"
            logger.info(f"No username, using Chat ID: {chat_id}")
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        client_mention = f"معرف العميل: {chat_id} (خطأ في جلب البيانات)"

    markup = create_fixed_buttons()

    package_details = VODAFONE_FLEX_DETAILS[package_id]
    subscription_details = f"📌 تفاصيل الباقة:\n{package_details['price']} - {package_details['package']}\n{package_details.get('details', '')}"
    data.insert(0, subscription_details)
    send_to_admin(chat_id, data, package_type, package_id, client_mention)

    confirmation_message = f"📩 تم إرسال طلبك بنجاح!\nجاري تفعيل باقة {package_details['package']} الآن.\n📲 يرجى متابعة الطلب مع {ADMIN_USERNAME} لتأكيد البيانات والتفعيل النهائي."
    bot.send_message(
        chat_id,
        confirmation_message,
        reply_markup=markup
    )
    send_confirmation_to_admin(chat_id, confirmation_message)

    if chat_id in temp_data:
        del temp_data[chat_id]
    logger.info(f"Successfully processed payment number for chat_id: {chat_id}")

# دالة لمعالجة طلب الرصيد
def handle_credit_request(message):
    chat_id = message.chat.id
    amount_str = message.text.strip()
    logger.info(f"Received credit request from chat_id {chat_id}: Amount = {amount_str}")

    amount, total = calculate_credit(amount_str)

    if amount is None or total is None:
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ المبلغ غير صحيح! يرجى إدخال رقم صحيح وأكبر من 0 (بدون حروف أو مسافات).", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, handle_credit_request)
        logger.info(f"Invalid credit amount entered by chat_id {chat_id}: {amount_str}")
        return

    credit_history[chat_id] = {"amount": amount, "total": total}  # تخزين الحساب
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔄 إعادة الحساب", callback_data="recalculate_credit"))
    markup.row(InlineKeyboardButton("🗑️ مسح الحساب", callback_data="clear_credit"))
    markup.row(InlineKeyboardButton("💳 شحن", callback_data=f"proceed_to_recharge_{chat_id}"))
    markup.row(InlineKeyboardButton("📲 تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    markup.row(InlineKeyboardButton("🔙 القائمة السابقة", callback_data="back"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main"))

    # إزالة "بعد العمولة 20%"
    bot.send_message(chat_id, f"📝 الحساب:\nالمبلغ المطلوب: {amount} جنيه\nالمبلغ الإجمالي: {total} جنيه\nاختر الخطوة التالية:", reply_markup=markup)
    logger.info(f"Processed credit request for chat_id {chat_id}: Amount = {amount}, Total = {total}")

# دالة لمعالجة الانتقال إلى طلب رقم فودافون كاش المدفوع منه (لطلب رصيد)
def next_to_recharge_vodafone_cash(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    markup = create_fixed_buttons()
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="📝 من فضلك، أدخل رقم فودافون كاش المدفوع منه (يبدأ بـ 01 ويتكون من 11 رقمًا):", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_recharge_vodafone_cash, chat_id)
    logger.info(f"Prompted for recharge Vodafone Cash number for chat_id: {chat_id}")

# دالة لمعالجة رقم فودافون كاش المدفوع منه (لطلب رصيد)
def process_recharge_vodafone_cash(message, chat_id):
    number = message.text.strip()
    if not is_valid_vodafone_number(number):
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ رقم فودافون كاش غير صحيح! يجب أن يبدأ بـ 01 ويتكون من 11 رقمًا فقط (بدون حروف أو مسافات). حاول مرة أخرى:", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, process_recharge_vodafone_cash, chat_id)
        logger.info(f"Invalid recharge Vodafone Cash number entered by chat_id {chat_id}: {number}")
        return
    temp_data[chat_id] = {"paid_number": number}
    markup = create_fixed_buttons()
    bot.send_message(chat_id, "📝 من فضلك، أدخل رقم فودافون الذي تريد شحنه (يبدأ بـ 01 ويتكون من 11 رقمًا):", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_recharge_number, chat_id)
    logger.info(f"Processed recharge Vodafone Cash number for chat_id: {chat_id}")

# دالة لمعالجة الانتقال إلى طلب رقم فودافون اللي هيتشحن عليه (لطلب رصيد)
def next_to_recharge_number(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    markup = create_fixed_buttons()
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="📝 من فضلك، أدخل رقم فودافون الذي تريد شحنه (يبدأ بـ 01 ويتكون من 11 رقمًا):", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_recharge_number, chat_id)
    logger.info(f"Prompted for recharge number for chat_id: {chat_id}")

# دالة لمعالجة رقم فودافون اللي هيتشحن عليه (لطلب رصيد)
def process_recharge_number(message, chat_id):
    number = message.text.strip()
    if not is_valid_vodafone_number(number):
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ رقم فودافون غير صحيح! يجب أن يبدأ بـ 01 ويتكون من 11 رقمًا فقط (بدون حروف أو مسافات). حاول مرة أخرى:", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, process_recharge_number, chat_id)
        logger.info(f"Invalid recharge number entered by chat_id {chat_id}: {number}")
        return
    amount = credit_history.get(chat_id, {}).get("amount")
    total = credit_history.get(chat_id, {}).get("total")
    if amount is None or total is None:
        markup = create_fixed_buttons()
        bot.send_message(chat_id, "❌ حدث خطأ، من فضلك ابدأ من جديد باستخدام /start", reply_markup=markup)
        logger.error(f"Error: Credit history missing for chat_id {chat_id}")
        return
    paid_number = temp_data[chat_id]["paid_number"]
    data = [
        f"المبلغ المطلوب: {amount} جنيه",
        f"المبلغ الإجمالي: {total} جنيه",
        f"رقم فودافون كاش المدفوع منه: {paid_number}",
        f"رقم فودافون المطلوب شحنه: {number}"
    ]
    send_to_admin(chat_id, data, "credit")
    markup = create_fixed_buttons()
    confirmation_message = "📢 سيتم الشحن في أقرب وقت، يرجى الانتظار."
    bot.send_message(chat_id, confirmation_message, reply_markup=markup)
    send_confirmation_to_admin(chat_id, confirmation_message)
    if chat_id in temp_data:
        del temp_data[chat_id]
    if chat_id in credit_history:
        del credit_history[chat_id]
    logger.info(f"Processed recharge request for chat_id: {chat_id}")

# دالة لـ UptimeRobot Health Check (للحفاظ على البوت حي)
@app.route('/', methods=['GET'])
def health_check():
    logger.info("Health check requested by UptimeRobot - Bot is alive!")
    return "Bot is alive!", 200

# دالة للـ Webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            update = telebot.types.Update.de_json(request.get_json())
            logger.info(f"Received update via webhook: {update}")
            bot.process_new_updates([update])
            logger.info("Webhook processed successfully")
            return "OK", 200
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return "Error", 500
    logger.warning("Webhook received non-POST request")
    return "Method not allowed", 405

# دالة لتشغيل Flask في Thread منفصل
def run_flask():
    app.run(host='0.0.0.0', port=8080)

# دالة لتشغيل البوت وFlask معًا
def keep_alive():
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    logger.info("Flask server started on port 8080 - Bot is now running via Webhook")

# دالة لجدولة إرسال الرسائل كل 4 دقايق و30 ثانية
def schedule_keep_alive_messages():
    schedule.every(270).seconds.do(send_keep_alive_message)  # 4 دقايق و30 ثانية = 270 ثانية
    logger.info("Scheduled keep-alive messages every 270 seconds")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in keep-alive scheduler: {e}")
            time.sleep(10)  # نعيد المحاولة بعد 10 ثواني لو حصل خطأ

# الدالة الرئيسية (نظام Webhook فقط)
if __name__ == "__main__":
    try:
        # إزالة أي Webhook قديم
        bot.delete_webhook()
        logger.info("Old webhook removed successfully")

        # جلب الـ URL من ملف .env
        replit_url = os.getenv("REPL_URL")
        token = os.getenv("TOKEN")

        if not replit_url or not token:
            logger.error("REPL_URL or TOKEN not set in environment variables")
            raise ValueError("REPL_URL or TOKEN is missing in .env file")

        # تنظيف REPL_URL من أي أجزاء زيادة
        replit_url = replit_url.strip()
        if replit_url.startswith("https://"):
            replit_url = replit_url[len("https://"):]
        if replit_url.endswith("/"):
            replit_url = replit_url[:-1]

        # التأكد من إن REPL_URL شكله صحيح (دعم النطاقات الطويلة من Replit)
        if not re.match(r'^[a-zA-Z0-9-]+\.replit\.dev$|^[a-z0-9-]+\-[a-z0-9-]+\.[a-z]+\.replit\.dev$', replit_url):
            logger.error(f"Invalid REPL_URL format: {replit_url}. It should be like 'project-name.replit.dev' or 'uuid-xxx.region.replit.dev'")
            raise ValueError("Invalid REPL_URL format. It should be like 'project-name.replit.dev' or 'uuid-xxx.region.replit.dev'")

        # تشغيل Flask أولاً
        logger.info("Starting Flask server before setting webhook...")
        keep_alive()  # تشغيل Flask لاستقبال التحديثات عبر Webhook

        # بناء الـ Webhook URL
        webhook_url = f"https://{replit_url}/{token}"
        logger.info(f"Setting webhook URL: {webhook_url}")

        # اختبار الـ URL بعد تشغيل Flask
        response = requests.get(f"https://{replit_url}", timeout=10)
        if response.status_code != 200:
            logger.error(f"Server is not responding. Status code: {response.status_code}")
            raise Exception("Server is not responding. Check if Flask is running and the URL is correct")

        # إعداد الـ Webhook
        bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set successfully to: {webhook_url}")
        logger.info(f"Note: To keep the bot alive, add this URL (https://{replit_url}) to UptimeRobot with 5-minute checks.")

        # تشغيل جدولة الرسائل للحفاظ على نشاط البوت
        keep_alive_thread = Thread(target=schedule_keep_alive_messages)
        keep_alive_thread.start()

    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        raise

    logger.info("Bot started, listening for updates via Webhook...")