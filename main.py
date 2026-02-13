import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
import phonenumbers
from phonenumbers import geocoder, carrier
import requests
import hashlib
import datetime
import pytz

bot = telebot.TeleBot("8421308485:AAF6wxM8QnLvFbkPHfOjbzCpb76zLsFhNJg")
user_state = {}

# ========== Поиск по IP ==========
def get_ip_info(ip):
    try:
        r = requests.get(f"http://ipwho.is/{ip}", timeout=5)
        data = r.json()

        if not data.get("success", False):
            return None

        return {
            "country": data.get("country", "Неизвестно"),
            "city": data.get("city", "Неизвестно"),
            "region": data.get("region", "Неизвестно"),
            "isp": data.get("connection", {}).get("isp", "Неизвестно"),
            "lat": data.get("latitude", 0),
            "lon": data.get("longitude", 0)
        }
    except Exception as e:
        print(f"IP API Error: {e}")
        return None

def is_ip(text):
    return re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", text) is not None

# ========== Поиск по номеру ==========
def get_country_flag(country_code):
    """Конвертируем код страны в флаг эмодзи"""
    if not country_code:
        return "🌍"
    return ''.join(chr(ord(c) + 127397) for c in country_code.upper())

def check_messenger(link):
    """Проверяем существует ли аккаунт в мессенджере"""
    try:
        r = requests.get(link, timeout=3, allow_redirects=False)
        return r.status_code != 404
    except:
        return False

def get_phone_extra_info(phone):
    """Дополнительные ссылки для поиска по номеру"""
    clean = re.sub(r'\D', '', phone)
    
    return {
        "banks": {
        },
        "epieos": f"https://epieos.com/?q={clean}",
        "bots": {
            "GetContact": "@whoose_contact_bot",
            "Truecaller": "@TrueCaller1Bot",
            "LeakCheck": "@LeakCheck1_bot"
        },
        "search": {
            "Яндекс": f"https://yandex.ru/search/?text={clean}",
            "Google": f"https://www.google.com/search?q={clean}"
        }
    }

def get_phone_deep_search(phone):
    """РАСШИРЕННЫЙ поиск по номеру (ФИО, утечки, бизнес)"""
    clean = re.sub(r'\D', '', phone)
    
    return {
        # Утечки паролей и данных
        "leaks": {
            "LeakCheck": f"https://leakcheck.io/search?query={clean}",
            "LeakBase": f"https://leakbase.io/search?q={clean}",
            "BreachDirectory": f"https://breachdirectory.org/search?q={clean}",
            "SnusBase": f"https://snusbase.com/search?q={clean}"
        },
        
        # Объявления (ФИО часто в описании)
        "ads": {
            "Авито": f"https://www.avito.ru/items?q={clean}",
            "Юла": f"https://youla.ru/search?q={clean}",
            "Авто.ру": f"https://auto.ru/search?query={clean}",
            "Дром": f"https://www.drom.ru/search/?query={clean}"
        },
        
        # Бизнес и ИП (ФИО, ИНН)
        "business": {
            
        },
        
        # Соцсети (поиск по номеру)
        "social": {
            "VK": f"https://vk.com/search?c%5Bq%5D={clean}",
            "ОК": f"https://ok.ru/search?st.query={clean}",
            "Facebook": f"https://www.facebook.com/search/people/?q={clean}",
            "Twitter": f"https://twitter.com/search?q={clean}"
        },
        
        # Код и форумы
        "code": {
            "GitHub": f"https://github.com/search?q={clean}",
            "GitLab": f"https://gitlab.com/search?search={clean}",
            "Habr": f"https://habr.com/ru/search/?q={clean}",
            "Pikabu": f"https://pikabu.ru/search?q={clean}"
        },
        
        # Государственные реестры
        "gov": {
            
        }
    }

def get_phone_info(phone):
    try:
        parsed = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(parsed):
            return None
        
        country_code = phonenumbers.region_code_for_number(parsed)
        country_name = geocoder.country_name_for_number(parsed, "ru")
        operator_name = carrier.name_for_number(parsed, "ru")
        
        # Получаем часовой пояс страны
        try:
            country_tz = pytz.country_timezones.get(country_code, ['UTC'])[0]
            local_time = datetime.datetime.now(pytz.timezone(country_tz)).strftime("%H:%M")
        except:
            local_time = "Неизвестно"
            country_tz = "Неизвестно"
        
        # Очищаем номер от всего кроме цифр для ссылок
        clean_number = re.sub(r'\D', '', phone)
        if clean_number.startswith('8') and country_code == 'RU':
            clean_number = '7' + clean_number[1:]
        
        # Проверяем WhatsApp
        wa_check = check_messenger(f"https://web.whatsapp.com/send?phone={clean_number}")
        
        return {
            "country": country_name,
            "country_code": country_code,
            "flag": get_country_flag(country_code),
            "operator": operator_name,
            "type": phonenumbers.number_type(parsed),
            "international": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            ),
            "national": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            ),
            "local_time": local_time,
            "timezone": country_tz,
            "clean_number": clean_number,
            "wa_active": wa_check
        }
    except Exception as e:
        print(f"Phone error: {e}")
        return None

def phone_type_to_text(t):
    types = {
        0: "Фиксированный",
        1: "Мобильный",
        2: "Фиксированный / мобильный",
        3: "Только для данных",
        4: "Премиум",
        5: "VoIP",
        6: "Пейджер",
        7: "Бесплатный",
        8: "Платный",
        9: "Личный",
        10: "Неизвестно"
    }
    return types.get(t, "Неизвестно")

# ========== Поиск по никнейму ==========
def is_username(text):
    return re.match(r"^[a-zA-Z0-9_.]{3,32}$", text) is not None

def get_username_info(username):
    return {
        "telegram": f"https://t.me/{username}",
        "instagram": f"https://instagram.com/{username}",
        "tiktok": f"https://tiktok.com/@{username}",
        "github": f"https://github.com/{username}",
        "youtube": f"https://youtube.com/@{username}",
        "twitter": f"https://twitter.com/{username}",
        "twitch": f"https://twitch.tv/{username}",
        "discord": f"https://discord.com/users/{username}",
        "possible_name": username.replace("_", " ").title()
    }

# ========== Поиск по Email ==========
def is_email(text):
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", text) is not None

def check_hibp(email):
    """Проверка утечек через haveibeenpwned"""
    try:
        email_hash = hashlib.sha1(email.encode('utf-8')).hexdigest()
        prefix = email_hash[:5]
        suffix = email_hash[5:].upper()
        
        r = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
        if r.status_code == 200:
            hashes = [line.split(':')[0] for line in r.text.splitlines()]
            if suffix in hashes:
                return True
        return False
    except:
        return False

def get_gravatar(email):
    """Получение Gravatar (аватар)"""
    try:
        email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?d=404"
    except:
        return None

def get_email_info(email):
    return {
        "email": email,
        "domain": email.split('@')[1],
        "username": email.split('@')[0],
        "breached": check_hibp(email),
        "gravatar": get_gravatar(email)
    }

def get_email_deep_search(email):
    """Расширенный поиск по Email"""
    return {
        "leaks": {
            "LeakCheck": f"https://leakcheck.io/search?query={email}",
            "BreachDirectory": f"https://breachdirectory.org/search?q={email}"
        },
        "social": {
            "Gravatar": f"https://en.gravatar.com/{hashlib.md5(email.lower().encode('utf-8')).hexdigest()}",
            "Hunter": f"https://hunter.io/email-verifier/{email}"
        }
    }

# ========== Проверки ==========
def is_phone(text):
    return re.match(r"^\+?\d{10,15}$", text) is not None

# ========== Меню ==========
go_back_markup = InlineKeyboardMarkup()
go_back_markup.add(InlineKeyboardButton("⬅ Назад", callback_data="back"))

menu_markup = InlineKeyboardMarkup()
menu_markup.add(
    InlineKeyboardButton("📞 Проверка номера", callback_data="phone_number"),
    InlineKeyboardButton("👤 Поиск по никнейму", callback_data="user_name")
)
menu_markup.add(
    InlineKeyboardButton("🌐 IP/Домен", callback_data="ip_and_domen"),
    InlineKeyboardButton("📧 Поиск по Email", callback_data="email_search")
)
menu_markup.add(InlineKeyboardButton("🔍 Полный поиск", callback_data="all_search"))
menu_markup.add(InlineKeyboardButton("ℹ️ Помощь", callback_data="help"))

# ========== Старт ==========
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "<b>Добро пожаловать в FSearch</b>\n\nВыберите действие:",
        parse_mode="html",
        reply_markup=menu_markup
    )

# ========== Callback ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "phone_number":
        user_state[call.from_user.id] = "wait_phone"
        bot.edit_message_text(
            "📞 <b>Поиск по номеру</b>\n\nОтправьте номер:\n\n"
            "<i>Форматы: +79001234567, 89001234567</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="html",
            reply_markup=go_back_markup
        )
    elif call.data == "ip_and_domen":
        user_state[call.from_user.id] = "wait_ip"
        bot.edit_message_text(
            "🌐 <b>IP геолокация</b>\n\nОтправьте IP адрес:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="html",
            reply_markup=go_back_markup
        )
    elif call.data == "user_name":
        user_state[call.from_user.id] = "wait_username"
        bot.edit_message_text(
            "👤 <b>Поиск по никнейму</b>\n\nОтправьте ник:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="html",
            reply_markup=go_back_markup
        )
    elif call.data == "email_search":
        user_state[call.from_user.id] = "wait_email"
        bot.edit_message_text(
            "📧 <b>Поиск по Email</b>\n\nОтправьте email:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="html",
            reply_markup=go_back_markup
        )
    elif call.data == "all_search":
        user_state[call.from_user.id] = "wait_all"
        bot.edit_message_text(
            "🔍 <b>Полный поиск</b>\n\nОтправьте никнейм, номер или email:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="html",
            reply_markup=go_back_markup
        )
    elif call.data == "back":
        if call.from_user.id in user_state:
            user_state.pop(call.from_user.id)
        bot.edit_message_text(
            "Выберите действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=menu_markup
        )
    elif call.data == "help":
        bot.edit_message_text(
            "ℹ️ <b>FSearch v3.0</b>\n\n"
            "<b>📞 Проверка номера:</b>\n"
            "• Страна, оператор, тип\n"
            "• Местное время\n"
            "• WhatsApp, Telegram\n"
            "• Утечки паролей\n"
            "• Объявления\n"
            "• Бизнес/ИП (ФИО)\n"
            "• Соцсети\n"
            "• Госреестры\n\n"
            
            "<b>👤 Поиск по никнейму:</b>\n"
            "• 10+ соцсетей\n\n"
            
            "<b>🌐 IP геолокация:</b>\n"
            "• Точное местоположение\n"
            "• Провайдер, карта\n\n"
            
            "<b>📧 Поиск по Email:</b>\n"
            "• Утечки паролей\n"
            "• Gravatar\n\n"
            
            "<i>Поиск только по публичным источникам</i>\n"
            "<i>ФИО ищется через объявления, бизнес и утечки</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="html",
            reply_markup=go_back_markup
        )

# ========== Текст ==========
@bot.message_handler(content_types=["text"])
def text_handler(message):
    state = user_state.get(message.from_user.id)
    if state is None:
        bot.send_message(message.chat.id, "❌ Сначала выберите действие в меню", reply_markup=menu_markup)
        return
        
    text = message.text.strip()

    # ===== IP поиск =====
    if state in ["wait_ip"] and is_ip(text):
        info = get_ip_info(text)
        if not info:
            bot.send_message(message.chat.id, "❌ IP не найден", reply_markup=go_back_markup)
            return
        text_msg = (
            "🌐 <b>Информация по IP</b>\n\n"
            f"📍 IP: <code>{text}</code>\n"
            f"🌍 Страна: {info['country']}\n"
            f"🏙 Регион: {info['region']}\n"
            f"🏢 Город: {info['city']}\n"
            f"📡 Провайдер: {info['isp']}\n"
            f"🗺 Координаты: {info['lat']}, {info['lon']}\n"
            f"🔗 Карта: https://www.google.com/maps?q={info['lat']},{info['lon']}"
        )
        bot.send_message(message.chat.id, text_msg, parse_mode="html", disable_web_page_preview=True, reply_markup=go_back_markup)
        user_state.pop(message.from_user.id, None)
        return

    # ===== Поиск по номеру =====
    if state in ["wait_phone", "wait_all"] and is_phone(text):
        info = get_phone_info(text)
        if not info:
            bot.send_message(message.chat.id, "❌ Номер не найден", reply_markup=go_back_markup)
            return
        
        wa_status = "✅ Активен" if info['wa_active'] else "❓ Не проверено"
        
        text_msg = (
            "📞 <b>Информация по номеру</b>\n\n"
            f"{info['flag']} <b>Страна:</b> {info['country'] or 'Неизвестно'} ({info['country_code']})\n"
            f"📡 <b>Оператор:</b> {info['operator'] or 'Неизвестно'}\n"
            f"📱 <b>Тип:</b> {phone_type_to_text(info['type'])}\n"
            f"🕐 <b>Местное время:</b> {info['local_time']} ({info['timezone']})\n"
            f"🔢 <b>Международный:</b> <code>{info['international']}</code>\n"
            f"🔢 <b>Национальный:</b> <code>{info['national']}</code>\n\n"
            "<b>📱 Мессенджеры:</b>\n"
            f"• WhatsApp: {wa_status}\n"
            f"• Telegram: https://t.me/{info['clean_number']}\n"
        )
        
        # Базовые доп проверки
        extra = get_phone_extra_info(text)
        
        text_msg += "\n<b>🔍 Базовые проверки:</b>\n"
        text_msg += f"\n💰 <b>Банки (увидят имя при переводе):</b>\n"
        for bank, url in extra["banks"].items():
            text_msg += f"• {bank}: {url}\n"
        text_msg += f"\n🌐 <b>Регистрации в соцсетях:</b>\n• EPIEOS: {extra['epieos']}\n"
        text_msg += f"\n🤖 <b>Боты-помощники:</b>\n"
        for name, bot_username in extra["bots"].items():
            text_msg += f"• {name}: {bot_username}\n"
        
        # РАСШИРЕННЫЙ поиск (ФИО, утечки, бизнес)
        deep = get_phone_deep_search(text)
        
        text_msg += "\n<b>🔎 ГЛУБОКИЙ ПОИСК (ФИО, утечки, бизнес):</b>\n"
        
        text_msg += "\n📦 <b>Утечки паролей и данных:</b>\n"
        for name, url in deep["leaks"].items():
            text_msg += f"• {name}: {url}\n"
        
        text_msg += "\n🏪 <b>Объявления (часто есть ФИО):</b>\n"
        for name, url in deep["ads"].items():
            text_msg += f"• {name}: {url}\n"
        
        text_msg += "\n🏢 <b>Бизнес и ИП (ФИО, ИНН):</b>\n"
        for name, url in deep["business"].items():
            text_msg += f"• {name}: {url}\n"
        
        text_msg += "\n🌍 <b>Соцсети:</b>\n"
        for name, url in deep["social"].items():
            text_msg += f"• {name}: {url}\n"
        
        text_msg += "\n💻 <b>Код и форумы:</b>\n"
        for name, url in deep["code"].items():
            text_msg += f"• {name}: {url}\n"
        
        text_msg += "\n🏛 <b>Государственные реестры:</b>\n"
        for name, url in deep["gov"].items():
            text_msg += f"• {name}: {url}\n"
        
        bot.send_message(message.chat.id, text_msg, parse_mode="html", disable_web_page_preview=True, reply_markup=go_back_markup)
        user_state.pop(message.from_user.id, None)
        return

    # ===== Поиск по никнейму =====
    if state in ["wait_username", "wait_all"] and is_username(text):
        info = get_username_info(text)
        text_msg = (
            "👤 <b>Результат поиска по никнейму</b>\n\n"
            f"🆔 Ник: <code>{text}</code>\n"
            f"📨 Telegram: {info['telegram']}\n"
            f"📸 Instagram: {info['instagram']}\n"
            f"🎵 TikTok: {info['tiktok']}\n"
            f"💻 GitHub: {info['github']}\n"
            f"▶️ YouTube: {info['youtube']}\n"
            f"🐦 Twitter: {info['twitter']}\n"
            f"🎮 Twitch: {info['twitch']}\n"
            f"💬 Discord: {info['discord']}\n"
            f"🧑 Возможное имя: {info['possible_name']}\n\n"
            "⚠️ <i>Совпадение никнейма не гарантирует одного человека</i>\n"
            "<i>• Ссылки могут вести на разных людей</i>\n"
            "<i>• Проверяйте аватарки и описание профиля</i>"
        )
        bot.send_message(message.chat.id, text_msg, parse_mode="html", disable_web_page_preview=True, reply_markup=go_back_markup)
        user_state.pop(message.from_user.id, None)
        return

    # ===== Поиск по Email =====
    if state in ["wait_email", "wait_all"] and is_email(text):
        info = get_email_info(text)
        
        breach_status = "✅ Не найден в утечках" if not info['breached'] else "⚠️ Найден в утечках паролей!"
        
        text_msg = (
            "📧 <b>Информация по Email</b>\n\n"
            f"📨 Email: <code>{info['email']}</code>\n"
            f"👤 Логин: {info['username']}\n"
            f"🌐 Домен: {info['domain']}\n"
            f"🔐 Утечки: {breach_status}\n"
        )
        
        if info['gravatar']:
            text_msg += f"🖼 Gravatar: {info['gravatar']}\n"
        
        # Расширенный поиск по Email
        email_deep = get_email_deep_search(text)
        
        text_msg += "\n<b>🔎 Глубокий поиск:</b>\n"
        text_msg += "\n📦 <b>Утечки:</b>\n"
        for name, url in email_deep["leaks"].items():
            text_msg += f"• {name}: {url}\n"
        
        text_msg += "\n🔗 <b>Дополнительно:</b>\n"
        for name, url in email_deep["social"].items():
            text_msg += f"• {name}: {url}\n"
            
        text_msg += "\n⚠️ <i>• В утечках может быть ФИО, пароли, другие данные</i>\n"
        text_msg += "<i>• Некоторые сервисы платные</i>"
        
        bot.send_message(message.chat.id, text_msg, parse_mode="html", disable_web_page_preview=True, reply_markup=go_back_markup)
        user_state.pop(message.from_user.id, None)
        return

    # Если ничего не подошло
    bot.send_message(message.chat.id, "❌ Неверный формат ввода", reply_markup=go_back_markup)

bot.polling(non_stop=True)