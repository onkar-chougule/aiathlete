import os
import asyncio
import logging
import sqlite3
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from google import genai

from maslow import constants

# ------------------ Setup ------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(constants.LOG_FILE),
        logging.StreamHandler()
    ]
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# ------------------ DB Helper ------------------

def init_db():
    conn = sqlite3.connect(constants.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_message TEXT NOT NULL,
            bot_reply TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_message(user_id, user_message, bot_reply):
    conn = sqlite3.connect(constants.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO messages (user_id, user_message, bot_reply)
        VALUES (?, ?, ?)
    ''', (user_id, user_message, bot_reply))
    conn.commit()
    conn.close()

# Initialize DB once
init_db()

# ------------------ Handler ------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id

    logging.info(f"User {user_id}: {user_message}")

    try:
        # Gemini call (non-blocking)
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-3-flash-preview",
            contents=user_message
        )

        reply = response.text

        logging.info(f"Bot: {reply}")

        # DB write (also move to thread)
        await asyncio.to_thread(
            insert_message,
            user_id,
            user_message,
            reply
        )

        await update.message.reply_text(reply)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Something went wrong. Try again.")

# ------------------ Error Handler ------------------

async def error_handler(update, context):
    logging.error(f"Update {update} caused error {context.error}")

# ------------------ App Setup ------------------

request = HTTPXRequest(
    connect_timeout=15.0,
    read_timeout=30.0,
    write_timeout=15.0,
)

app = (
    ApplicationBuilder()
    .token(TELEGRAM_TOKEN)
    .request(request)
    .build()
)

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_error_handler(error_handler)

# ------------------ Run ------------------

print("Bot running...")
app.run_polling()