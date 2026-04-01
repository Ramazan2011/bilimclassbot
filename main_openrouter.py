import logging
from telegram import Update, ForceReply, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import requests
import html
from flask import Flask
import threading

# --- КЕЕP ALIVE СЕРВЕРІ (RENDER ҮШІН) ---
app = Flask('')

@app.route('/')
def home():
    return "Бот жұмыс істеп тұр! (Bilim AI)"

def run():
    # Render әдетте PORT айнымалысын қолданады, егер ол жоқ болса 8080 қолданамыз
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True # Бағдарлама тоқтағанда thread-тің де тоқтауы үшін
    t.start()

# Логтарды қосу
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
ADMIN_IDS = [5664187652] 
# ҚАУІПСІЗДІК: Токендерді Environment Variables-ке салған дұрыс
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8332495617:AAEKHCFUA06aTyV9OOrANlTZI6HFyf6qnMM")
# ---------------------

def get_admin_reply_text(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} админ жауап берді"
    else:
        return f"{count} админ жауап берді"

STRINGS = {
    'kz': {
        'welcome': "👋 <b>Сәлем! Bilim AI 🎓 оқу көмекшісіне қош келдіңіз!</b>\n\nМен сізге сабақ кестесі, үй тапсырмасы және кез-келген оқу сұрақтары бойынша көмектесемін.",
        'help': "🤖 <b>Мен Bilim AI оқу көмекшісімін!</b>\n\n1. 📋 <b>Сабақ кестесі</b>\n2. 📚 <b>Үй тапсырмасы</b>\n3. 💡 <b>Кез-келген сұрақ</b>",
        'schedule_btn': "📋 Сабақ кестесі",
        'homework_btn': "📚 Үй тапсырмасы",
        'help_btn': "🆘 Көмек 📕",
        'support_btn': "🆘 Қолдау 💬",
        'lang_selected': "Тіл таңдалды: Қазақша 🇰🇿",
        'support_prompt': "✍️ Хабарламаңызды жазыңыз. Біз сізге тезірек жауап береміз!",
        'support_sent': "✅ Сіздің хабарламаңыз жіберілді.",
        'support_reply_header': "📢 <b>Қолдау қызметінің жауабы:</b>\n\n"
    },
    'ru': {
        'welcome': "👋 <b>Привет! Добро пожаловать в Bilim AI 🎓 — твой учебный помощник!</b>",
        'help': "🤖 <b>Я твой ИИ помощник Bilim!</b>\n\n1. 📋 <b>Расписание</b>\n2. 📚 <b>Домашка</b>\n3. 💡 <b>Любой вопрос</b>",
        'schedule_btn': "📋 Расписание",
        'homework_btn': "📚 Домашка",
        'help_btn': "🆘 Помощь 📕",
        'support_btn': "🆘 Поддержка 💬",
        'lang_selected': "Язык выбран: Русский 🇷🇺",
        'support_prompt': "✍️ Напишите ваше сообщение. Мы ответим как можно скорее!",
        'support_sent': "✅ Ваше сообщение отправлено.",
        'support_reply_header': "📢 <b>Ответ поддержки:</b>\n\n"
    }
}

def get_main_menu_keyboard(lang: str):
    s = STRINGS.get(lang, STRINGS['kz'])
    keyboard = [
        [KeyboardButton(s['schedule_btn']), KeyboardButton(s['homework_btn'])],
        [KeyboardButton(s['help_btn']), KeyboardButton(s['support_btn'])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("🇰🇿 Қазақша"), KeyboardButton("🇷🇺 Русский")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("📚 <b>Bilim AI</b>\n\nТілді таңдаңыз / Выберите язык:", reply_markup=reply_markup, parse_mode='HTML')

def read_data_file(filename: str, default_text: str = "") -> str:
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except: return "Error reading file."
    return default_text

def get_ai_response(message: str, lang: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    schedule = read_data_file("schedule.txt", "Кесте бос.")
    homework = read_data_file("homework.txt", "Үй тапсырмасы жоқ.")
    
    lang_inst = "Answer in Kazakh." if lang == 'kz' else "Answer in Russian."
    system_prompt = f"You are a helpful academic bot. {lang_inst} Context: Schedule: {schedule}, Homework: {homework}"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "stepfun/step-3.5-flash:free", # Тегін модель
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"OpenRouter қатесі: {str(e)}"

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # --- ADMIN REPLY ---
    if user_id in ADMIN_IDS and update.message.reply_to_message:
        orig = update.message.reply_to_message.text or ""
        if "USER_ID:" in orig:
            target_id = int(orig.split("USER_ID:")[1].split("\n")[0].strip())
            header = f"📢 <b>Жауап келді:</b>\n\n"
            await context.bot.send_message(chat_id=target_id, text=f"{header}{user_message}", parse_mode='HTML')
            await update.message.reply_text("✅ Жауап жіберілді.")
            return

    # Тіл таңдау
    if user_message == "🇰🇿 Қазақша":
        context.user_data['lang'] = 'kz'
        await update.message.reply_text(STRINGS['kz']['welcome'], reply_markup=get_main_menu_keyboard('kz'), parse_mode='HTML')
        return
    elif user_message == "🇷🇺 Русский":
        context.user_data['lang'] = 'ru'
        await update.message.reply_text(STRINGS['ru']['welcome'], reply_markup=get_main_menu_keyboard('ru'), parse_mode='HTML')
        return

    lang = context.user_data.get('lang')
    if not lang:
        await start(update, context)
        return

    s = STRINGS[lang]

    # Қолдау қызметі
    if user_message in [s['support_btn'], "/support"]:
        context.user_data['state'] = 'SUPPORT'
        await update.message.reply_text(s['support_prompt'], reply_markup=ReplyKeyboardRemove())
        return

    if context.user_data.get('state') == 'SUPPORT':
        admin_msg = f"📩 <b>Жаңа хабарлама!</b>\nКімнен: {update.effective_user.full_name}\nID: {user_id}\n\n{user_message}\n\nUSER_ID: {user_id}"
        for admin in ADMIN_IDS:
            await context.bot.send_message(chat_id=admin, text=admin_msg, parse_mode='HTML')
        await update.message.reply_text(s['support_sent'], reply_markup=get_main_menu_keyboard(lang))
        context.user_data['state'] = None
        return

    # Мәліметтер
    if user_message in ["📋 Сабақ кестесі", "📋 Расписание"]:
        await update.message.reply_text(read_data_file("schedule.txt"), reply_markup=get_main_menu_keyboard(lang))
    elif user_message in ["📚 Үй тапсырмасы", "📚 Домашка"]:
        await update.message.reply_text(read_data_file("homework.txt"), reply_markup=get_main_menu_keyboard(lang))
    else:
        # OpenRouter-ге жіберу
        reply = get_ai_response(user_message, lang)
        await update.message.reply_text(reply, reply_markup=get_main_menu_keyboard(lang))

def main():
    keep_alive()
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))
    app_bot.run_polling()

if __name__ == "__main__":
    main()
