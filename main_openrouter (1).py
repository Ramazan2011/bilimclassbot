import logging
import os
import requests
import httpx
import html
import json
import hashlib
from datetime import datetime
from telegram import Update, ForceReply, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Combine all known admin IDs (Your ID + any group or secondary IDs)
ADMIN_IDS = [5664187652, 1156688745] 
USERS_DATA_FILE = "users_data.json"
PENDING_DATA_FILE = "pending_data.json"
# ---------------------

def get_admin_reply_text(count: int) -> str:
    """Helper to return grammatically correct Russian pluralization."""
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} админ ответил"
    elif count % 10 in [2, 3, 4] and not (count % 100 in [12, 13, 14]):
        return f"{count} админа ответили"
    else:
        return f"{count} админов ответили"

# Localization strings
STRINGS = {
    'kz': {
        'welcome': "👋 <b>Сәлем! Bilim AI 🎓 (OpenRouter) оқу көмекшісіне қош келдіңіз!</b>\n\nМен сізге сабақ кестесі, үй тапсырмасы және кез-келген оқу сұрақтары бойынша көмектесемін.\n\n<b>Не істей аламын?</b>\n• Төмендегі батырмаларды пайдаланыңыз\n• Немесе маған кез-келген сұрақ қойыңыз!",
        'help': "🤖 <b>Мен Bilim AI оқу көмекшісімін! (OpenRouter)</b>\n\nНе істей аламын:\n1. 📋 <b>Сабақ кестесі</b> — расписаниені алу.\n2. 📚 <b>Үй тапсырмасы</b> — үй тапсырмасын білу.\n3. 💡 <b>Кез-келген сұрақ</b> — сұрағыңызды жазыңыз!",
        'schedule_btn': "📋 Сабақ кестесі",
        'homework_btn': "📚 Үй тапсырмасы",
        'help_btn': "🆘 Көмек 📕",
        'support_btn': "🆘 Қолдау 💬",
        'leaderboard_btn': "🏆 Лидерлер тақтасы",
        'lang_selected': "Тіл таңдалды: Қазақша 🇰🇿. Енді жұмысты бастай аламыз!",
        'support_prompt': "⚠️ <b>Әкімшілік ешқашан жеке деректерді (құпия сөздерді және т.б.) сұрамайды.</b>\n\n✍️ Хабарламаңызды жазыңыз. Мүмкін болса, барлық ойларыңызды бір хабарламаға сыйғызуға тырысыңыз. Біз сізге тезірек жауап береміз!",
        'support_sent': "✅ Сіздің хабарламаңыз жіберілді. Жауапты күтіңіз.",
        'support_reply_header': "📢 <b>Қолдау көрсету қызметі жауап берді:</b>\n\n",
        'leaderboard_title': "🏆 <b>Bilim AI Лидерлер тақтасы</b>\n\nЕң белсенді оқушылар топтамасы:",
        'xp': "XP",
        'cash': "Тиын",
        'hw_done_btn': "Орындалды ✅",
        'hw_verify_msg': "📸 <b>Үй тапсырмасын жіберіңіз!</b>\n\nОрындалғанын растау үшін маған фото жіберіңіз. Содан кейін сізге 1 XP және 10 тиын беріледі.",
        'hw_reward_msg': "🎊 <b>Жарайсың!</b>\n\nҮй тапсырмасы қабылданды. Сіз алдыңыз: +1 XP және +10 тиын! 🚀",
        'hw_already_done': "⚠️ Сіз бұл тапсырманы орындап қойдыңыз!",
        'hw_approved': "✅ <b>Сіздің үй тапсырмаңыз қабылданды!</b>\n\nТапсырма: <i>{task}</i>\nСіз алдыңыз: <b>+1 XP және +10 тиын!</b> 🚀",
        'hw_rejected': "❌ <b>Сіздің үй тапсырмаңыз қабылданбады.</b>\n\nТапсырма: <i>{task}</i>\nӨтінеміз, қайтадан жіберіңіз немесе қолдау көрсету қызметіне хабарласыңыз.",
        'hw_pending': "⏳ <b>Бұл тапсырма қазір тексерілуде!</b>\n\nМұғалім жауабын күтіңіз.",
        'hw_accepted_label': "(Қабылданды ✅)",
        'hw_rejected_label': "(Қабылданбады ❌ - Қайта тапсыру)",
        'premium_btn': "💎 Premium AI",
        'premium_menu': "<b>💎 Premium AI Мәзірі</b>\n\nСізде: <b>{uses}</b> премиум сұрақ бар.\n\nПремиум режим: <b>{status}</b>\n\n100 тиынға 10 премиум сұрақ сатып алуға болады.",
        'buy_premium_btn': "🛒 10 сұрақ сатып алу (100 тиын)",
        'toggle_premium_on': "✅ Премиум режимді қосу",
        'toggle_premium_off': "❌ Премиум режимді өшіру",
        'premium_bought': "✅ <b>Рақмет!</b>\n10 премиум сұрақ сатып алынды. Енді оны мәзірден қоса аласыз.",
        'no_cash': "❌ Сізде тиын жеткіліксіз (100 тиын қажет).",
        'profile_btn': "👤 Профиль",
        'shop_btn': "🎁 Shop",
        'broadcast_btn': "📢 Хабарландыру",
        'profile_text': "<b>📂 {name} Профилі</b>\n\n🏅 <b>Деңгей:</b> {level} ({title})\n🔥 <b>Стрик:</b> {streak} күн\n🥈 <b>XP:</b> {xp}\n💰 <b>Тиын:</b> {cash}\n🏆 <b>Рейтинг:</b> {rank}\n\n{progress_bar} ({xp_needed} XP келесі деңгейге)",
        'shop_text': "<b>🎁 Shop Мәзірі</b>\n\n💰 Баланс: <b>{cash} тиын</b>\n\n1. 🧊 <b>Стрик тоқтату (Streak Freeze)</b> — 150 тиын\n2. 🏅 <b>'Bilim Pro' Баджы</b> — 500 тиын\n\n<i>Сатып алу үшін нөмірді жазыңыз.</i>",
        'broadcast_prompt': "📢 <b>Барлық оқушыларға хабарлама жіберу</b>\n\nМәтінді жазыңыз:",
        'broadcast_sent': "✅ Хабарлама <b>{count}</b> оқушыға жіберілді.",
        'thinking': "🤖 <b>Bilim AI ойлануда...</b>",
        'admin_hw_request': "📩 <b>Жаңа үй тапсырмасын тексеру сұранысы</b>\n\nКімнен: {name} (@{username})\nТапсырма: {task}\n\n<i>Растау үшін 'y', қабылдамау үшін 'n' деп жауап беріңіз.</i>"
    },
    'ru': {
        'welcome': "👋 <b>Привет! Добро приветствуем в Bilim AI 🎓 (OpenRouter) — твой учебный помощник!</b>\n\nЯ помогу тебе с расписанием, домашними заданиями и любыми учебными вопросами.\n\n<b>Как я могу помочь?</b>\n• Нажми на кнопки ниже для быстрого доступа\n• Или просто напиши мне любой вопрос по учебе!",
        'help': "🤖 <b>Я твой ИИ помощник по учебе Bilim! (OpenRouter)</b>\n\nВот что я могу:\n1. 📋 <b>Расписание</b> — получить график занятий.\n2. 📚 <b>Домашка</b> — узнать текущее домашнее задание.\n3. 💡 <b>Любой вопрос</b> — просто напиши, и я помогу тебе разобраться в теме!",
        'schedule_btn': "📋 Расписание",
        'homework_btn': "📚 Домашка",
        'help_btn': "🆘 Помощь 📕",
        'support_btn': "🆘 Поддержка 💬",
        'leaderboard_btn': "🏆 Таблица лидеров",
        'lang_selected': "Язык выбран: Русский 🇷🇺. Теперь мы можем начать работу!",
        'support_prompt': "⚠️ <b>Администрация никогда не запрашивает персональные данные (пароли и т.д.).</b>\n\n✍️ Напишите ваше сообщение. Пожалуйста, постарайтесь изложить все свои мысли в одном сообщении. Мы ответим вам как можно скорее!",
        'support_sent': "✅ Ваше сообщение отправлено. Ожидайте ответа.",
        'support_reply_header': "📢 <b>Поддержка ответила:</b>\n\n",
        'leaderboard_title': "🏆 <b>Таблица лидеров Bilim AI</b>\n\nСамые активные ученики:",
        'xp': "XP",
        'cash': "Кэш",
        'hw_done_btn': "Сделано ✅",
        'hw_verify_msg': "📸 <b>Отправьте фото домашки!</b>\n\nДля подтверждения выполнения скиньте мне фото задания. После этого вы получите 1 XP и 10 кэш-поинтов.",
        'hw_reward_msg': "🎊 <b>Отлично!</b>\n\nДомашка принята. Вам начислено: +1 XP и +10 кэш-поинтов! 🚀",
        'hw_already_done': "⚠️ Вы уже выполнили это задание!",
        'hw_approved': "✅ <b>Ваша домашка принята!</b>\n\nЗадание: <i>{task}</i>\nВам начислено: <b>+1 XP и +10 кэш-поинтов!</b> 🚀",
        'hw_rejected': "❌ <b>Ваша домашка отклонена.</b>\n\nЗадание: <i>{task}</i>\nПожалуйста, попробуйте еще раз или напишите в поддержку.",
        'hw_pending': "⏳ <b>Это задание уже находится на проверке!</b>\n\nПожалуйста, дождитесь ответа учителя.",
        'hw_accepted_label': "(Принято ✅)",
        'hw_rejected_label': "(Отклонено ❌ - Переделайте)",
        'premium_btn': "💎 Premium AI",
        'premium_menu': "<b>💎 Premium AI Меню</b>\n\nУ вас: <b>{uses}</b> премиум вопросов.\n\nПремиум режим: <b>{status}</b>\n\nМожно купить 10 премиум вопросов за 100 кэш-поинтов.",
        'buy_premium_btn': "🛒 Купить 10 вопросов (100 кэш)",
        'toggle_premium_on': "✅ Включить Премиум режим",
        'toggle_premium_off': "❌ Выключить Премиум режим",
        'premium_bought': "✅ <b>Спасибо!</b>\n10 премиум вопросов добавлено. Теперь вы можете включить их в меню.",
        'no_cash': "❌ У вас недостаточно кэш-поинтов (нужно 100).",
        'profile_btn': "👤 Профиль",
        'shop_btn': "🎁 Shop",
        'broadcast_btn': "📢 Объявление",
        'profile_text': "<b>📂 Профиль: {name}</b>\n\n🏅 <b>Уровень:</b> {level} ({title})\n🔥 <b>Стрик:</b> {streak} дня/дней\n🥈 <b>XP:</b> {xp}\n💰 <b>Кэш:</b> {cash}\n🏆 <b>Рейтинг:</b> {rank}\n\n{progress_bar} ({xp_needed} XP до след. уровня)",
        'shop_text': "<b>🎁 Меню Shop</b>\n\n💰 Баланс: <b>{cash} кэш</b>\n\n1. 🧊 <b>Заморозка стрика (Streak Freeze)</b> — 150 кэш\n2. 🏅 <b>Бейдж 'Bilim Pro'</b> — 500 кэш\n\n<i>Для покупки введите номер товара.</i>",
        'broadcast_prompt': "📢 <b>Рассылка всем ученикам</b>\n\nВведите текст сообщения:",
        'broadcast_sent': "✅ Сообщение отправлено <b>{count}</b> ученикам.",
        'thinking': "🤖 <b>Bilim AI думает...</b>",
        'admin_hw_request': "📩 <b>Запрос на проверку домашки</b>\n\nОт: {name} (@{username})\nЗадание: {task}\n\n<i>Ответьте 'y' для подтверждения или 'n' для отклонения.</i>"
    }
}

# --- DATA MANAGEMENT ---
def load_users_data():
    if os.path.exists(USERS_DATA_FILE):
        try:
            with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users data: {e}")
    return {}

def save_users_data(data):
    try:
        with open(USERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving users data: {e}")

def load_pending_data():
    if os.path.exists(PENDING_DATA_FILE):
        try:
            with open(PENDING_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "homework" not in data: data["homework"] = {}
                if "tickets" not in data: data["tickets"] = {}
                if "user_hw_maps" not in data: data["user_hw_maps"] = {}
                return data
        except Exception as e:
            logger.error(f"Error loading pending data: {e}")
    return {"homework": {}, "tickets": {}, "user_hw_maps": {}}

def save_pending_data(data):
    try:
        with open(PENDING_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving pending data: {e}")

def clean_users_data():
    """FIX for Hackathon: Clean legacy instruction-polluted HW IDs."""
    data = load_users_data()
    changed = False
    for uid, stats in data.items():
        if "completed_hw" in stats:
            new_ids = []
            for hid in stats["completed_hw"]:
                clean_id = hid.split("\n")[0].strip()
                if clean_id not in new_ids: new_ids.append(clean_id)
            if stats["completed_hw"] != new_ids: stats["completed_hw"] = new_ids; changed = True
        if "rejected_hw" in stats:
            new_ids = []
            for hid in stats["rejected_hw"]:
                clean_id = hid.split("\n")[0].strip()
                if clean_id not in new_ids: new_ids.append(clean_id)
            if stats["rejected_hw"] != new_ids: stats["rejected_hw"] = new_ids; changed = True
    if changed: save_users_data(data)

def get_user_stats(user_id, full_name, username):
    data = load_users_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "name": full_name,
            "username": username,
            "xp": 0,
            "cash": 0,
            "completed_hw": [],
            "rejected_hw": [],
            "premium_uses": 0,
            "premium_mode": False,
            "streak": 0,
            "last_active": "Never"
        }
        save_users_data(data)
    else:
        # Standardize existing users
        if "rejected_hw" not in data[uid]: data[uid]["rejected_hw"] = []
        if "premium_uses" not in data[uid]: data[uid]["premium_uses"] = 0
        if "premium_mode" not in data[uid]: data[uid]["premium_mode"] = False
        if "streak" not in data[uid]: data[uid]["streak"] = 0
        if "last_active" not in data[uid]: data[uid]["last_active"] = "Never"
        data[uid]["name"] = full_name
        data[uid]["username"] = username
        save_users_data(data)
    return data[uid]

def update_user_stats(user_id, xp_gain=0, cash_gain=0, hw_id=None, reject=False, buy_premium=False, toggle_premium=None):
    data = load_users_data()
    uid = str(user_id)
    if uid in data:
        if buy_premium:
            if data[uid]["cash"] >= 100:
                data[uid]["cash"] -= 100
                data[uid]["premium_uses"] += 10
                save_users_data(data)
                return True
            return False
        
        if toggle_premium is not None:
            data[uid]["premium_mode"] = toggle_premium
            save_users_data(data)
            return True

        data[uid]["xp"] += xp_gain
        data[uid]["cash"] += cash_gain
        if "completed_hw" not in data[uid]: data[uid]["completed_hw"] = []
        if "rejected_hw" not in data[uid]: data[uid]["rejected_hw"] = []
        
        if hw_id:
            if reject:
                if hw_id not in data[uid]["rejected_hw"]:
                    data[uid]["rejected_hw"].append(hw_id)
            else:
                # Approval: move from rejected to completed
                if hw_id in data[uid]["rejected_hw"]:
                    data[uid]["rejected_hw"].remove(hw_id)
                if hw_id not in data[uid]["completed_hw"]:
                    data[uid]["completed_hw"].append(hw_id)
        save_users_data(data)

def get_main_menu_keyboard(lang: str, user_id: int = None):
    s = STRINGS.get(lang, STRINGS['kz'])
    keyboard = [
        [KeyboardButton(s['schedule_btn']), KeyboardButton(s['homework_btn'])],
        [KeyboardButton(s['profile_btn']), KeyboardButton(s['shop_btn'])],
        [KeyboardButton(s['leaderboard_btn']), KeyboardButton(s['support_btn'])],
        [KeyboardButton("⏳ Pomodoro"), KeyboardButton(s['premium_btn'])]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([KeyboardButton(s['broadcast_btn'])])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("🇰🇿 Қазақша"), KeyboardButton("🇷🇺 Русский")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "📚 <b>Bilim AI</b>\n\nТілді таңдаңыз / Выберите язык:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data.get('lang', 'kz')
    s = STRINGS.get(lang, STRINGS['kz'])
    await update.message.reply_text(s['help'], reply_markup=get_main_menu_keyboard(lang, user_id=user_id), parse_mode='HTML')

def read_data_file(filename: str, default_text: str = "") -> str:
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            return f"Error reading {filename}"
    return default_text

async def get_ai_stream(message: str, lang: str, is_premium: bool = False):
    api_key = "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"
    url = "https://openrouter.ai/api/v1/chat/completions"
    schedule_data = read_data_file("schedule.txt", "No schedule.")
    homework_data = read_data_file("homework.txt", "No homework.")
    lang_instr = "You must answer in Kazakh." if lang == 'kz' else "You must answer in Russian."
    model = "stepfun/step-3.5-flash:free"
    
    system_prompt = (
        "You are an academic helpful bot for students. Help the user, and if possible, try educating them without giving away the answer instantly. "
        f"{lang_instr} \n\n### CONTEXT DATA ###\nSchedule:\n{schedule_data}\n\nHomework:\n{homework_data}\n"
    )
    if is_premium:
        system_prompt += "\n\n💎 PREMIUM AI MODE: Provide a very deep and high-quality response."
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
        "stream": True
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]": break
                        try:
                            chunk = json.loads(data_str)
                            content = chunk['choices'][0]['delta'].get('content', "")
                            if content: yield content
                        except: pass
    except Exception as e:
        logger.error(f"OpenRouter Stream Error: {e}")
        yield f"Error: {str(e)}"

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_message = update.message.text if update.message else None
        user_id = update.effective_user.id
        full_name = update.effective_user.full_name
        username = update.effective_user.username or "Unknown"
        
        # --- LOG FOR CONFIGURATION ---
        if user_id not in ADMIN_IDS and user_message == "/id":
            await update.message.reply_text(f"Your ID: `{user_id}` (Add this to ADMIN_IDS if you are a teacher)", parse_mode='HTML')
            return

        # --- ADMIN REPLY LOGIC ---
        if user_id in ADMIN_IDS and update.message and update.message.reply_to_message and user_message:
            original_msg = update.message.reply_to_message
            original_msg_text = original_msg.text or original_msg.caption
            if original_msg_text and "USER_ID:" in original_msg_text:
                try:
                    target_user_id = int(original_msg_text.split("USER_ID:")[1].split("\n")[0].strip())
                    
                    # --- HOMEWORK VERIFICATION BY REPLY (y/n) ---
                    if "HW_ID:" in original_msg_text:
                        action_text = user_message.strip().lower()
                        # Match first word/char for better UX
                        is_approve = any(action_text.startswith(x) for x in ['y', 'yes', 'д', 'да', 'иә', 'и'])
                        is_reject = any(action_text.startswith(x) for x in ['n', 'no', 'н', 'нет', 'жоқ', 'ж'])
                        
                        if is_approve:
                            hw_id = original_msg_text.split("HW_ID:")[1].split("\n")[0].strip()
                            # Use improved update_user_stats (handles rejected_hw too)
                            update_user_stats(target_user_id, xp_gain=1, cash_gain=10, hw_id=hw_id, reject=False)
                            
                            # Get localized response
                            all_users = load_users_data()
                            user_info = all_users.get(str(target_user_id), {})
                            user_lang = user_info.get('lang', 'kz')
                            s = STRINGS.get(user_lang, STRINGS['kz'])
                            
                            task_text = "Home task"
                            if "Тапсырма: " in original_msg_text: task_text = original_msg_text.split("Тапсырма: ")[1].split("\n")[0]
                            elif "Задание: " in original_msg_text: task_text = original_msg_text.split("Задание: ")[1].split("\n")[0]
                            
                            msg = s['hw_approved'].format(task=task_text)
                            try: await context.bot.send_message(chat_id=target_user_id, text=msg, parse_mode='HTML')
                            except Exception as e: logger.error(f"Failed to notify user {target_user_id}: {e}")
                            
                            # Update admin message
                            clean_caption = original_msg_text.split("\n\n---\n")[0]
                            new_text = f"{clean_caption}\n\n✅ <b>APPROVED</b> by {html.escape(update.effective_user.full_name)}"
                            try: await context.bot.edit_message_caption(chat_id=update.effective_chat.id, message_id=original_msg.message_id, caption=new_text, parse_mode='HTML')
                            except: await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=original_msg.message_id, text=new_text, parse_mode='HTML')
                            
                            # Remove from pending
                            pending = load_pending_data()
                            pk = f"{target_user_id}_{hw_id}"
                            if pk in pending['homework']: del pending['homework'][pk]; save_pending_data(pending)
                            return

                        elif is_reject:
                            hw_id = original_msg_text.split("HW_ID:")[1].split("\n")[0].strip()
                            # Use improved update_user_stats
                            update_user_stats(target_user_id, hw_id=hw_id, reject=True)
                            
                            # Rejection Notification
                            all_users = load_users_data()
                            user_info = all_users.get(str(target_user_id), {})
                            user_lang = user_info.get('lang', 'kz')
                            s = STRINGS.get(user_lang, STRINGS['kz'])
                            
                            task_text = "Home task"
                            if "Тапсырма: " in original_msg_text: task_text = original_msg_text.split("Тапсырма: ")[1].split("\n")[0]
                            elif "Задание: " in original_msg_text: task_text = original_msg_text.split("Задание: ")[1].split("\n")[0]
                            
                            msg = s['hw_rejected'].format(task=task_text)
                            try: await context.bot.send_message(chat_id=target_user_id, text=msg, parse_mode='HTML')
                            except Exception as e: logger.error(f"Failed to notify user {target_user_id}: {e}")
                            
                            clean_caption = original_msg_text.split("\n\n---\n")[0]
                            new_text = f"{clean_caption}\n\n❌ <b>REJECTED</b> by {html.escape(update.effective_user.full_name)}"
                            try: await context.bot.edit_message_caption(chat_id=update.effective_chat.id, message_id=original_msg.message_id, caption=new_text, parse_mode='HTML')
                            except: await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=original_msg.message_id, text=new_text, parse_mode='HTML')
                            
                            # Remove from pending
                            pending = load_pending_data()
                            pk = f"{target_user_id}_{hw_id}"
                            if pk in pending['homework']: del pending['homework'][pk]; save_pending_data(pending)
                            return

                    # --- REGULAR SUPPORT REPLY ---
                    admin_name = html.escape(update.effective_user.full_name)
                    admin_username = html.escape(update.effective_user.username or "Unknown")
                    header = f"📢 <b>Поддержка ответила ({admin_name} @{admin_username}):</b>\n\n"
                    await context.bot.send_message(chat_id=target_user_id, text=f"{header}{html.escape(user_message)}", parse_mode='HTML')
                    
                    # Remove from pending tickets
                    pending = load_pending_data()
                    ticket_key = f"{target_user_id}"
                    if ticket_key in pending['tickets']:
                        del pending['tickets'][ticket_key]
                        save_pending_data(pending)

                    count = 1
                    ticket_id = original_msg_text.split("TICKET_ID:")[1].strip() if "TICKET_ID:" in original_msg_text else None
                    tickets = context.bot_data.get('tickets', {})
                    ticket_info = tickets.get(ticket_id) if ticket_id else None
                    if ticket_info:
                        ticket_info['count'] += 1
                        count = ticket_info['count']
                        base_text = ticket_info['base_text']
                        tracking_list = ticket_info['tracking']
                    else:
                        base_text = original_msg_text
                        if "✅ " in original_msg_text:
                            try:
                                line = [l for l in original_msg_text.split("\n") if "ответил" in l][0]
                                count = int(''.join(filter(str.isdigit, line))) + 1
                                base_text = original_msg_text.replace(line, "").strip()
                            except: pass
                        tracking_list = [(update.effective_chat.id, original_msg.message_id)]

                    new_admin_text = f"{base_text}\n\n✅ {get_admin_reply_text(count)}"
                    for admin_chat_id, msg_id in tracking_list:
                        try: await context.bot.edit_message_text(chat_id=admin_chat_id, message_id=msg_id, text=new_admin_text, parse_mode='HTML')
                        except: pass
                    return
                except: pass

        # --- LANGUAGE SELECTION ---
        if user_message == "🇰🇿 Қазақша":
            context.user_data['lang'] = 'kz'
            # PERSIST LANGUAGE CHOICE
            data = load_users_data()
            uid = str(user_id)
            if uid not in data: data[uid] = {"name": full_name, "username": username, "xp": 0, "cash": 0, "completed_hw": []}
            data[uid]['lang'] = 'kz'
            save_users_data(data)
            await update.message.reply_text(STRINGS['kz']['lang_selected'], reply_markup=get_main_menu_keyboard('kz', user_id=user_id))
            await update.message.reply_text(STRINGS['kz']['welcome'], reply_markup=get_main_menu_keyboard('kz', user_id=user_id), parse_mode='HTML')
            return
        elif user_message == "🇷🇺 Русский":
            context.user_data['lang'] = 'ru'
            # PERSIST LANGUAGE CHOICE
            data = load_users_data()
            uid = str(user_id)
            if uid not in data: data[uid] = {"name": full_name, "username": username, "xp": 0, "cash": 0, "completed_hw": []}
            data[uid]['lang'] = 'ru'
            save_users_data(data)
            await update.message.reply_text(STRINGS['ru']['lang_selected'], reply_markup=get_main_menu_keyboard('ru', user_id=user_id))
            await update.message.reply_text(STRINGS['ru']['welcome'], reply_markup=get_main_menu_keyboard('ru', user_id=user_id), parse_mode='HTML')
            return
    
        lang = context.user_data.get('lang', None)
        if not lang:
            # Try to restore from persistence
            data = load_users_data()
            user_info = data.get(str(user_id), {})
            lang = user_info.get('lang')
            if lang:
                context.user_data['lang'] = lang
            else:
                await start(update, context); return
        s = STRINGS[lang]

        # --- PHOTO VERIFICATION (REPLY) ---
        if update.message and update.message.photo:
            pending = load_pending_data()
            user_hw_map = pending.get("user_hw_maps", {}).get(str(user_id), {})
            # Check if it's a reply to a homework message
            if update.message.reply_to_message and str(update.message.reply_to_message.message_id) in user_hw_map:
                hw_id, task_text = user_hw_map[str(update.message.reply_to_message.message_id)]
                
                # --- DUPLICATE CHECK ---
                user_stats = get_user_stats(user_id, full_name, username)
                if hw_id in user_stats.get('completed_hw', []):
                    await update.message.reply_text(s['hw_already_done'], parse_mode='HTML')
                    return
                # Note: Rejected tasks CAN be re-submitted.
                
                pending = load_pending_data()
                if f"{user_id}_{hw_id}" in pending['homework']:
                    await update.message.reply_text(s['hw_pending'], parse_mode='HTML')
                    return
                # -----------------------

                # --- NOTIFY ADMIN FOR APPROVAL ---
                admin_text = s['admin_hw_request'].format(name=html.escape(full_name), username=html.escape(username), task=html.escape(task_text))
                admin_text += f"\n\n---\nUSER_ID: {user_id}\nHW_ID: {hw_id}\n\n✍️ Reply with 'y' to Approve or 'n' to Reject."
                
                success_count = 0
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_photo(
                            chat_id=admin_id,
                            photo=update.message.photo[-1].file_id,
                            caption=admin_text,
                            parse_mode='HTML'
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send homework photo to admin {admin_id}: {e}")
                
                if success_count > 0:
                    # Add to pending homework
                    pending = load_pending_data()
                    pending['homework'][f"{user_id}_{hw_id}"] = {
                        "user_id": user_id,
                        "full_name": full_name,
                        "username": username,
                        "task": task_text,
                        "hw_id": hw_id,
                        "photo_id": update.message.photo[-1].file_id,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_pending_data(pending)
                    await update.message.reply_text("📤 <b>Жіберілді! / Отправлено!</b>\nМұғалім тексергеннен кейін сізге хабарлама келеді. / Ожидайте проверки учителем.", parse_mode='HTML')
                else:
                    await update.message.reply_text("❌ Мұғалімге жіберу кезінде қате кетті. / Ошибка при отправке учителю.")
                return

        # --- SUPPORT FLOW ---
        is_support_followup = False
        if update.message and update.message.reply_to_message:
            replied_text = update.message.reply_to_message.text or ""
            if replied_text.startswith("📢 Поддержка ответила:") or replied_text.startswith("📢 Қолдау көрсету қызметі жауап берді:"):
                is_support_followup = True

        if context.user_data.get('state') == 'SUPPORT' or is_support_followup:
            prefix = "📩 <b>New Support Ticket</b>" if not is_support_followup else "🔄 <b>Support Follow-up</b>"
            admin_meta = f"{prefix}\nFrom: {html.escape(full_name)}\nUsername: @{html.escape(username or 'N/A')}\n\n{html.escape(user_message or '[Photo]')}\n\n---\nUSER_ID: {user_id}"
            
            # Add to pending tickets
            pending = load_pending_data()
            pending['tickets'][f"{user_id}"] = {
                "user_id": user_id,
                "full_name": full_name,
                "message": user_message or "[Photo]",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_pending_data(pending)

            for admin_id in ADMIN_IDS:
                try: await context.bot.send_message(chat_id=admin_id, text=admin_meta, parse_mode='HTML')
                except Exception as e: logger.error(f"Failed to send ticket: {e}")
            await update.message.reply_text(s['support_sent'], reply_markup=get_main_menu_keyboard(lang, user_id=user_id))
            context.user_data['state'] = None 
            return

        # --- MENU COMMANDS ---
        if user_message in ["🏆 Лидерлер тақтасы", "🏆 Таблица лидеров"] or user_message == "/leaderboard":
            data = load_users_data()
            sorted_users = sorted(data.items(), key=lambda x: x[1].get('xp', 0), reverse=True)
            leaderboard_text = s['leaderboard_title'] + "\n\n"
            for i, (uid, stats) in enumerate(sorted_users[:10], 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                leaderboard_text += f"{emoji} <b>{html.escape(stats.get('name', 'User'))}</b> — {stats.get('xp', 0)} {s['xp']} | {stats.get('cash', 0)} {s['cash']}\n"
            my_stats = get_user_stats(user_id, full_name, username)
            leaderboard_text += f"\n---\n👤 <b>Сіз / Вы:</b> {my_stats['xp']} {s['xp']} | {my_stats['cash']} {s['cash']}"
            await update.message.reply_text(leaderboard_text, reply_markup=get_main_menu_keyboard(lang, user_id=user_id), parse_mode='HTML')
        
        elif user_message in ["🆘 Қолдау 💬", "🆘 Поддержка 💬"] or user_message == "/support":
            context.user_data['state'] = 'SUPPORT'
            await update.message.reply_text(s['support_prompt'], reply_markup=ReplyKeyboardRemove())
            
        elif user_message in ["📋 Сабақ кестесі", "📋 Расписание"]:
            await update.message.reply_text(read_data_file("schedule.txt", "No schedule."), reply_markup=get_main_menu_keyboard(lang, user_id=user_id))
            
        elif user_message in ["📚 Үй тапсырмасы", "📚 Домашка"]:
            hw_content = read_data_file("homework.txt", "")
            if not hw_content: await update.message.reply_text("No homework available.", reply_markup=get_main_menu_keyboard(lang, user_id=user_id)); return
            user_stats = get_user_stats(user_id, full_name, username)
            await update.message.reply_text("📚 <b>Үй тапсырмасы / Домашнее задание:</b>", parse_mode='HTML')
            
            pending = load_pending_data()
            if "user_hw_maps" not in pending: pending["user_hw_maps"] = {}
            user_id_str = str(user_id)
            if user_id_str not in pending["user_hw_maps"]: pending["user_hw_maps"][user_id_str] = {}
            
            for line in [l.strip() for l in hw_content.split('\n') if l.strip()]:
                l_hash = hashlib.md5(line.encode()).hexdigest()[:10]
                is_done = l_hash in user_stats.get('completed_hw', [])
                is_rejected = l_hash in user_stats.get('rejected_hw', [])
                
                status_emoji = "✅" if is_done else "❌" if is_rejected else "📝"
                status_label = s['hw_accepted_label'] if is_done else s['hw_rejected_label'] if is_rejected else ""
                prompt_text = s['hw_verify_msg'].split('\n')[0].replace('<b>', '').replace('</b>', '')
                
                # Show instructions if not done (even if rejected)
                prompt = "" if is_done else f"\n\n💬 <i>{prompt_text}</i>"
                msg_text = f"{status_emoji} <b>{line}</b> {status_label}{prompt}"
                sent_msg = await update.message.reply_text(msg_text, parse_mode='HTML')
                if not is_done:
                    pending["user_hw_maps"][user_id_str][str(sent_msg.message_id)] = [l_hash, line]
            
            save_pending_data(pending)
                
        elif user_message in ["🆘 Көмек 📕", "🆘 Помощь 📕"]:
            await help_command(update, context)
        elif user_message == "⏳ Pomodoro":
            await start_pomodoro(update, context)
        
        # --- HACKATHON WINNER FEATURES ---
        elif user_message == s['profile_btn']:
            data = load_users_data()
            uid = str(user_id)
            stats = data.get(uid, {})
            # Streak check
            today_dt = datetime.now().date()
            today = today_dt.strftime("%Y-%m-%d")
            last_active = stats.get('last_active', "Never")
            
            if last_active != today:
                if last_active != "Never":
                    last_dt = datetime.strptime(last_active, "%Y-%m-%d").date()
                    if (today_dt - last_dt).days == 1:
                        stats['streak'] = stats.get('streak', 0) + 1
                    elif (today_dt - last_dt).days > 1:
                        stats['streak'] = 1 # Reset if missed a day
                else:
                    stats['streak'] = 1 # First time
                stats['last_active'] = today
                save_users_data(data)

            xp = stats.get('xp', 0)
            level = xp // 10 + 1
            titles = ["Novice", "Student", "Adept", "Scholar", "Genius", "Legend"]
            title = titles[min(level-1, len(titles)-1)]
            xp_needed = level * 10
            progress = xp % 10
            bar = "▓" * progress + "░" * (10 - progress)
            
            # Rank
            sorted_u = sorted(data.items(), key=lambda x: x[1].get('xp', 0), reverse=True)
            rank = "N/A"
            for i, (k, v) in enumerate(sorted_u, 1):
                if k == uid: rank = i; break
            
            msg = s['profile_text'].format(
                name=html.escape(full_name), level=level, title=title, streak=stats.get('streak', 0),
                xp=xp, cash=stats.get('cash', 0), rank=rank, progress_bar=bar, xp_needed=xp_needed - progress
            )
            await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard(lang, user_id=user_id), parse_mode='HTML')
            return

        elif user_message == s['shop_btn']:
            context.user_data['state'] = 'SHOP'
            stats = get_user_stats(user_id, full_name, username)
            await update.message.reply_text(s['shop_text'].format(cash=stats['cash']), reply_markup=get_main_menu_keyboard(lang, user_id=user_id), parse_mode='HTML')
            return

        if context.user_data.get('state') == 'SHOP':
            stats = get_user_stats(user_id, full_name, username)
            buy_msg = "✅ Сатып алынды! / Куплено!"
            if user_message == "1":
                if stats['cash'] >= 150:
                    update_user_stats(user_id, cash_gain=-150)
                    await update.message.reply_text(f"🧊 Streak Freeze {buy_msg}", reply_markup=get_main_menu_keyboard(lang, user_id=user_id))
                else: await update.message.reply_text(s['no_cash'], reply_markup=get_main_menu_keyboard(lang, user_id=user_id))
            elif user_message == "2":
                if stats['cash'] >= 500:
                    update_user_stats(user_id, cash_gain=-500)
                    await update.message.reply_text(f"🏅 Bilim Pro {buy_msg}", reply_markup=get_main_menu_keyboard(lang, user_id=user_id))
                else: await update.message.reply_text(s['no_cash'], reply_markup=get_main_menu_keyboard(lang, user_id=user_id))
            context.user_data['state'] = None
            return

        elif user_id in ADMIN_IDS and user_message == s['broadcast_btn']:
            context.user_data['state'] = 'BROADCAST'
            await update.message.reply_text(s['broadcast_prompt'], reply_markup=ReplyKeyboardRemove())
            return

        if context.user_data.get('state') == 'BROADCAST':
            count = 0
            users = load_users_data()
            for uid_str in users.keys():
                try:
                    await context.bot.send_message(chat_id=int(uid_str), text=f"📢 <b>Announcement:</b>\n\n{user_message}", parse_mode='HTML')
                    count += 1
                except: pass
            context.user_data['state'] = None
            await update.message.reply_text(s['broadcast_sent'].format(count=count), reply_markup=get_main_menu_keyboard(lang, user_id=user_id), parse_mode='HTML')
            return

        # --- EXISTING PREMIUM AI ---
        elif user_message == s['premium_btn']:
            stats = get_user_stats(user_id, full_name, username)
            mode_status = "ON ✅" if stats.get("premium_mode", False) else "OFF ❌"
            msg = s['premium_menu'].format(uses=stats.get("premium_uses", 0), status=mode_status)
            
            p_kb = [
                [KeyboardButton(s['buy_premium_btn'])],
                [KeyboardButton(s['toggle_premium_on'] if not stats.get("premium_mode") else s['toggle_premium_off'])],
                [KeyboardButton("⬅️ Артқа / Назад")]
            ]
            await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(p_kb, resize_keyboard=True), parse_mode='HTML')
            return

        elif user_message == s['buy_premium_btn']:
            success = update_user_stats(user_id, buy_premium=True)
            if success: await update.message.reply_text(s['premium_bought'], reply_markup=get_main_menu_keyboard(lang, user_id=user_id), parse_mode='HTML')
            else: await update.message.reply_text(s['no_cash'], reply_markup=get_main_menu_keyboard(lang, user_id=user_id))
            return

        elif user_message in [s['toggle_premium_on'], s['toggle_premium_off']]:
            new_mode = user_message == s['toggle_premium_on']
            update_user_stats(user_id, toggle_premium=new_mode)
            await update.message.reply_text(f"Премиум: {'ON' if new_mode else 'OFF'}", reply_markup=get_main_menu_keyboard(lang, user_id=user_id))
            return

        elif "Артқа / Назад" in user_message:
            await update.message.reply_text("🔙", reply_markup=get_main_menu_keyboard(lang, user_id=user_id))
            return

        elif user_message == "/pending_hw" and user_id in ADMIN_IDS:
            pending = load_pending_data()
            if not pending['homework']: await update.message.reply_text("No pending homework submissions.")
            else:
                text = "📊 <b>Pending Homework:</b>\n\n"
                for key, val in pending['homework'].items():
                    text += f"• <b>{val['full_name']}</b> - {val['task']} ({val['time']})\n"
                await update.message.reply_text(text, parse_mode='HTML')
        elif user_message == "/pending_tickets" and user_id in ADMIN_IDS:
            pending = load_pending_data()
            if not pending['tickets']: await update.message.reply_text("No pending support tickets.")
            else:
                text = "📩 <b>Pending Tickets:</b>\n\n"
                for key, val in pending['tickets'].items():
                    text += f"• <b>{val['full_name']}</b>: {val['message'][:30]}... ({val['time']})\n"
                await update.message.reply_text(text, parse_mode='HTML')
        elif user_message:
            stats = get_user_stats(user_id, full_name, username)
            premium_mode_on = stats.get("premium_mode", False)
            premium_credits = stats.get("premium_uses", 0)
            
            if premium_mode_on and premium_credits <= 0:
                # USER HAS PREMIUM ON BUT NO CREDITS - BLOCK AND NOTIFY
                update_user_stats(user_id, toggle_premium=False) # Auto-disable
                await update.message.reply_text(s['no_cash'], reply_markup=get_main_menu_keyboard(lang, user_id=user_id)) # Re-use no_cash or send specific msg
                return

            is_premium = premium_mode_on and premium_credits > 0
            
            placeholder = await update.message.reply_text(s['thinking'], parse_mode='HTML')
            full_reply = ""
            if is_premium: full_reply = "💎 [PREMIUM] "
            last_edit_time = datetime.now()
            
            async for chunk in get_ai_stream(user_message, lang, is_premium=is_premium):
                full_reply += chunk
                # Throttle: Only update every 1.5 seconds if there's new content
                if (datetime.now() - last_edit_time).total_seconds() > 1.5:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=placeholder.message_id,
                            text=full_reply + " ✍️",
                            parse_mode='HTML'
                        )
                        last_edit_time = datetime.now()
                    except: pass
            
            # Final Edit (Premium subtraction logic remains)
            if is_premium:
                all_data = load_users_data()
                all_data[str(user_id)]["premium_uses"] -= 1
                if all_data[str(user_id)]["premium_uses"] <= 0:
                    all_data[str(user_id)]["premium_mode"] = False
                save_users_data(all_data)
                
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=placeholder.message_id,
                text=full_reply, # Final text without emoji
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Error in ai_response: {e}", exc_info=True)
        if update.message: await update.message.reply_text("❌ Кешіріңіз, қате пайда болды. / Произошла ошибка.")

async def pomodoro_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(chat_id=job.data, text="🔔 <b>Время вышло!</b> Пора сделать перерыв (5 минут).", parse_mode='HTML')

async def start_pomodoro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_message.chat_id
    lang = context.user_data.get('lang', 'ru')
    text = "⏳ <b>Pomodoro запущен!</b>" if lang == 'ru' else "⏳ <b>Pomodoro басталды!</b>"
    context.job_queue.run_once(pomodoro_callback, 1500, data=chat_id, name=str(chat_id))
    await update.message.reply_text(text, parse_mode='HTML')

def main() -> None:
    clean_users_data()
    application = Application.builder().token("8332495617:AAEKHCFUA06aTyV9OOrANlTZI6HFyf6qnMM").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("pomodoro", start_pomodoro))
    application.add_handler(CommandHandler("leaderboard", ai_response))
    application.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, ai_response))
    application.run_polling()

if __name__ == "__main__":
    main()
