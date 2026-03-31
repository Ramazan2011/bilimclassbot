# 🎓 Bilim AI - Academic Assistant Telegram Bot

Bilim AI is a feature-rich, multilingual Telegram bot designed to assist students with their academic needs. It provides quick access to schedules and homework while offering an AI-powered tutor experience in both **Kazakh** and **Russian**.

## 🚀 Key Features

- 🌍 **Multilingual Support**: Fully localized interface in Kazakh (`🇰🇿 Қазақша`) and Russian (`🇷🇺 Русский`).
- 🤖 **Dual AI Backends**:
  - `main.py`: Uses local **Ollama** (`gemma3:4b`) for privacy and offline core logic.
  - `main_openrouter.py`: Uses **OpenRouter** (`stepfun/step-3.5-flash:free`) for cloud-based performance.
- 📋 **Academic Context**: Automatically reads `schedule.txt` and `homework.txt` to provide context-aware answers.
- 🆘 **Advanced Support System**:
  - **Support Tickets**: Users can send tickets directly to admins.
  - **Global Admin Sync**: When one admin replies, the status updates across **all** admin chats.
  - **Follow-up Support**: Users can reply directly to admin messages to continue the conversation thread.
  - **Admin Identity**: Support replies include the name and username of the responding admin.
- 🔒 **Security First**: Uses HTML escaping to prevent message parsing errors and includes built-in security notices for users.

## 🛠️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) (if using `main.py`)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Install Dependencies
```bash
pip install python-telegram-bot requests
```

### 3. Configuration
Open `main.py` or `main_openrouter.py` and update the following:
- `ADMIN_IDS`: List of Telegram IDs (User or Group) for the support team.
- `TOKEN`: Replace the placeholder with your BotFather token.
- `OpenRouter API Key`: (Only in `main_openrouter.py`).

### 4. Data Files
Create the following files in the project root:
- `schedule.txt`: Current class schedule.
- `homework.txt`: Current homework assignments.

## 📖 Usage

1. **Start the Bot**:
   ```bash
   python main.py
   # OR
   python main_openrouter.py
   ```
2. **Commands**:
   - `/start`: Reset and choose language.
   - `/help`: Show academic help.
   - `/support`: Contact the administration.

## 📦 Project Structure

- `main.py`: Local AI version (Ollama).
- `main_openrouter.py`: Cloud AI version (OpenRouter).
- `schedule.txt`: Data source for schedules.
- `homework.txt`: Data source for homework.
- `README.md`: Project documentation.

---
*Created with ❤️ for students.*