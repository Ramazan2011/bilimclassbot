import logging
from telegram import Update, ForceReply, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

import os
import requests
import html

# Define a few command handlers. These usually take the two arguments update and
# context.
from telegram import ReplyKeyboardMarkup, KeyboardButton

# --- CONFIGURATION ---
ADMIN_IDS = [1156688745, 789509485]  # ADD ALL ADMIN IDs (User or Group) to this list
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
        'welcome': "👋 <b>Сәлем! Bilim AI 🎓 оқу көмекшісіне қош келдіңіз!</b>\n\nМен сізге сабақ кестесі, үй тапсырмасы және кез-келген оқу сұрақтары бойынша көмектесемін.\n\n<b>Не істей аламын?</b>\n• Төмендегі батырмаларды пайдаланыңыз\n• Немесе маған кез-келген сұрақ қойыңыз!",
        'help': "🤖 <b>Мен Bilim AI оқу көмекшісімін!</b>\n\nНе істей аламын:\n1. 📋 <b>Сабақ кестесі</b> — расписаниені алу.\n2. 📚 <b>Үй тапсырмасы</b> — үй тапсырмасын білу.\n3. 💡 <b>Кез-келген сұрақ</b> — сұрағыңызды жазыңыз!",
        'schedule_btn': "📋 Сабақ кестесі",
        'homework_btn': "📚 Үй тапсырмасы",
        'help_btn': "🆘 Көмек 📕",
        'support_btn': "🆘 Қолдау 💬",
        'lang_selected': "Тіл таңдалды: Қазақша 🇰🇿. Енді жұмысты бастай аламыз!",
        'support_prompt': "⚠️ <b>Әкімшілік ешқашан жеке деректерді (құпия сөздерді және т.б.) сұрамайды.</b>\n\n✍️ Хабарламаңызды жазыңыз. Мүмкін болса, барлық ойларыңызды бір хабарламаға сыйғызуға тырысыңыз. Біз сізге тезірек жауап береміз!",
        'support_sent': "✅ Сіздің хабарламаңыз жіберілді. Жауапты күтіңіз.",
        'support_reply_header': "📢 <b>Қолдау көрсету қызметі жауап берді:</b>\n\n"
    },
    'ru': {
        'welcome': "👋 <b>Привет! Добро пожаловать в Bilim AI 🎓 — твой учебный помощник!</b>\n\nЯ помогу тебе с расписанием, домашними заданиями и любыми учебными вопросами.\n\n<b>Как я могу помочь?</b>\n• Нажми на кнопки ниже для быстрого доступа\n• Или просто напиши мне любой вопрос по учебе!",
        'help': "🤖 <b>Я твой ИИ помощник по учебе Bilim!</b>\n\nВот что я могу:\n1. 📋 <b>Расписание</b> — получить график занятий.\n2. 📚 <b>Домашка</b> — узнать текущее домашнее задание.\n3. 💡 <b>Любой вопрос</b> — просто напиши, и я помогу тебе разобраться в теме!",
        'schedule_btn': "📋 Расписание",
        'homework_btn': "📚 Домашка",
        'help_btn': "🆘 Помощь 📕",
        'support_btn': "🆘 Поддержка 💬",
        'lang_selected': "Язык выбран: Русский 🇷🇺. Теперь мы можем начать работу!",
        'support_prompt': "⚠️ <b>Администрация никогда не запрашивает персональные данные (пароли и т.д.).</b>\n\n✍️ Напишите ваше сообщение. Пожалуйста, постарайтесь изложить все свои мысли в одном сообщении. Мы ответим вам как можно скорее!",
        'support_sent': "✅ Ваше сообщение отправлено. Ожидайте ответа.",
        'support_reply_header': "📢 <b>Поддержка ответила:</b>\n\n"
    }
}

def get_main_menu_keyboard(lang: str):
    """Return the persistent main menu keyboard localized."""
    s = STRINGS.get(lang, STRINGS['kz'])
    keyboard = [
        [KeyboardButton(s['schedule_btn']), KeyboardButton(s['homework_btn'])],
        [KeyboardButton(s['help_btn']), KeyboardButton(s['support_btn'])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send language choice buttons at start."""
    keyboard = [
        [KeyboardButton("🇰🇿 Қазақша"), KeyboardButton("🇷🇺 Русский")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📚 <b>Bilim AI</b>\n\nТілді таңдаңыз / Выберите язык:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a localized help message based on the user's language."""
    lang = context.user_data.get('lang', None)
    if not lang:
        await start(update, context) # Force choice if not set
        return
    
    s = STRINGS[lang]
    await update.message.reply_text(s['help'], reply_markup=get_main_menu_keyboard(lang), parse_mode='HTML')

def read_data_file(filename: str, default_text: str = "") -> str:
    """Helper to read data from a file with a fallback."""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            return f"Error reading {filename}"
    return default_text

def get_ai_response(message: str, lang: str) -> str:
    """Get a response from the AI model (using Ollama locally) with file context."""
    # Ollama Local API
    url = "http://localhost:11434/api/chat"
    model = "gemma3:4b"  # Local model
    
    # Read context from files
    schedule = read_data_file("schedule.txt", "No schedule available.")
    homework = read_data_file("homework.txt", "No homework available.")
    
    lang_instruction = "You must answer in Kazakh." if lang == 'kz' else "You must answer in Russian."
    
    system_prompt = (
        "You are a useful assistant skilled in both Russian and Kazakh. "
        f"{lang_instruction} "
        "You are an academic helpful bot for students. Help the user, and if possible, try educating them without giving away the answer instantly. "
        "\n\n### CONTEXT DATA ###\n"
        f"Current Schedule:\n{schedule}\n\n"
        f"Current Homework:\n{homework}\n"
    )
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        return result['message']['content']
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}. Make sure Ollama is running."

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection buttons, support tickets, and regular AI analysis."""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # --- ADMIN REPLY LOGIC ---
    if user_id in ADMIN_IDS and update.message.reply_to_message:
        original_msg = update.message.reply_to_message
        original_msg_text = original_msg.text or original_msg.caption
        if original_msg_text and "USER_ID:" in original_msg_text:
            try:
                target_user_id = int(original_msg_text.split("USER_ID:")[1].split("\n")[0].strip())
                
                # Get the admin's info
                admin_name = html.escape(update.effective_user.full_name)
                admin_username = html.escape(update.effective_user.username or "Unknown")
                
                # Dynamic header including admin name/username
                header = f"📢 <b>Поддержка ответила ({admin_name} @{admin_username}):</b>\n\n"
                
                safe_reply = html.escape(user_message)
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"{header}{safe_reply}",
                    parse_mode='HTML'
                )
                
                # --- GLOBAL REPLY TRACKING LOGIC ---
                count = 1
                ticket_id = None
                if "TICKET_ID:" in original_msg_text:
                    ticket_id = original_msg_text.split("TICKET_ID:")[1].strip()
                
                # Try to get synchronized tracking from bot_data
                tickets = context.bot_data.get('tickets', {})
                ticket_info = tickets.get(ticket_id) if ticket_id else None
                
                if ticket_info:
                    ticket_info['count'] += 1
                    count = ticket_info['count']
                    base_text = ticket_info['base_text']
                    tracking_list = ticket_info['tracking']
                else:
                    # Fallback if bot restarted or no ticket_id
                    base_text = original_msg_text
                    if "✅ " in original_msg_text:
                        try:
                            line = [l for l in original_msg_text.split("\n") if "ответил" in l][0]
                            count = int(''.join(filter(str.isdigit, line))) + 1
                            base_text = original_msg_text.replace(line, "").strip()
                        except: pass
                    tracking_list = [(update.effective_chat.id, original_msg.message_id)] # Only update current

                counter_line = f"\n\n✅ {get_admin_reply_text(count)}"
                new_admin_text = f"{base_text}{counter_line}"
                
                # Update all admin messages (globally)
                for admin_chat_id, msg_id in tracking_list:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=admin_chat_id,
                            message_id=msg_id,
                            text=new_admin_text,
                            parse_mode='HTML'
                        )
                    except: pass
                return
            except Exception as e:
                await update.message.reply_text(f"❌ Қате: {str(e)}")
                return
    
    # Check for language selection
    if user_message == "🇰🇿 Қазақша":
        context.user_data['lang'] = 'kz'
        s = STRINGS['kz']
        await update.message.reply_text(s['lang_selected'], reply_markup=get_main_menu_keyboard('kz'))
        await update.message.reply_text(s['welcome'], reply_markup=get_main_menu_keyboard('kz'), parse_mode='HTML')
        return
    elif user_message == "🇷🇺 Русский":
        context.user_data['lang'] = 'ru'
        s = STRINGS['ru']
        await update.message.reply_text(s['lang_selected'], reply_markup=get_main_menu_keyboard('ru'))
        await update.message.reply_text(s['welcome'], reply_markup=get_main_menu_keyboard('ru'), parse_mode='HTML')
        return

    # Check for current language preference
    lang = context.user_data.get('lang', None)
    if not lang:
        await start(update, context)
        return
    
    s = STRINGS[lang]
    
    # Check if this is a follow-up reply to a support message
    is_support_followup = False
    if update.message.reply_to_message:
        replied_text = update.message.reply_to_message.text or ""
        # We check plain text because .text doesn't contain HTML tags
        ru_header = "📢 Поддержка ответила:"
        kz_header = "📢 Қолдау көрсету қызметі жауап берді:"
        if replied_text.startswith(ru_header) or replied_text.startswith(kz_header):
            is_support_followup = True

    # --- SUPPORT FLOW ---
    if context.user_data.get('state') == 'SUPPORT' or is_support_followup:
        # Forward the message to admins with metadata using HTML to avoid parsing errors
        full_name = html.escape(update.effective_user.full_name)
        username = html.escape(update.effective_user.username or "Unknown")
        safe_message = html.escape(user_message)
        
        prefix = "📩 <b>New Support Ticket</b>" if not is_support_followup else "🔄 <b>Support Follow-up</b>"
        ticket_id = f"T_{user_id}_{update.message.message_id}"
        
        admin_meta = (
            f"{prefix}\n"
            f"From: {full_name}\n"
            f"Username: @{username}\n\n"
            f"{safe_message}\n\n"
            f"---\n"
            f"USER_ID: {user_id}"
        )
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=admin_meta, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Failed to send ticket to admin {admin_id}: {e}")
        
        await update.message.reply_text(s['support_sent'], reply_markup=get_main_menu_keyboard(lang))
        context.user_data['state'] = None # Clear state
        return

    # User clicks Support button
    if user_message in ["🆘 Қолдау 💬", "🆘 Поддержка 💬"] or user_message == "/support":
        context.user_data['state'] = 'SUPPORT'
        await update.message.reply_text(s['support_prompt'], reply_markup=ReplyKeyboardRemove()) # Remove keyboard to focus on typing
        return

    # Check for regular data requests
    if user_message in [STRINGS['kz']['schedule_btn'], STRINGS['ru']['schedule_btn'], "Сабақ кестесі", "Расписание"]:
        schedule_text = read_data_file("schedule.txt", "Schedule file not found.")
        await update.message.reply_text(schedule_text, reply_markup=get_main_menu_keyboard(lang))
    elif user_message in [STRINGS['kz']['homework_btn'], STRINGS['ru']['homework_btn'], "Үй тапсырмасы", "Домашка"]:
        homework_text = read_data_file("homework.txt", "Homework file not found.")
        await update.message.reply_text(homework_text, reply_markup=get_main_menu_keyboard(lang))
    elif user_message in [STRINGS['kz']['help_btn'], STRINGS['ru']['help_btn']]:
        await help_command(update, context)
    else:
        ai_reply = get_ai_response(user_message, lang)
        await update.message.reply_text(ai_reply, reply_markup=get_main_menu_keyboard(lang))

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
   
    application = Application.builder().token("8332495617:AAEKHCFUA06aTyV9OOrANlTZI6HFyf6qnMM").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
