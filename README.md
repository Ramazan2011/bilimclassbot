# Telegram Bot

This is a Telegram bot that uses OpenRouter AI to respond to messages.

## Setup

1. Install the required package:
   ```
   pip install python-telegram-bot
   ```

2. Get a bot token from [BotFather](https://t.me/BotFather) on Telegram:
   - Start a chat with BotFather
   - Send `/newbot` and follow the instructions
   - Save the token you receive

3. Replace `"TOKEN"` in `main.py` with your actual bot token:
   ```python
   application = Application.builder().token("YOUR_TOKEN_HERE").build()
   ```

## Running the Bot

Run the bot with:
```
python main.py
```

The bot will start and respond to:
- `/start` - Greets the user
- `/help` - Sends a help message
- Any text message - Responds with an AI-generated reply

Press Ctrl+C to stop the bot.

## Features

- Basic command handling (/start, /help)
- AI-powered message responses
- Logging