import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from telegram.constants import ParseMode

# Basic logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Telegram Bot Logic ---
async def auto_approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_join_request:
        await update.chat_join_request.approve()
        logger.info(f"Approved join request from {update.chat_join_request.from_user.id} in chat {update.chat_join_request.chat.id}")

        # Optional: Send a welcome message to the user
        try:
            # You might want to get the chat_id from the approved request if sending to the user directly
            # For simplicity, sending to the chat where the request originated
            await context.bot.send_message(
                chat_id=update.chat_join_request.chat.id,
                text=f"Welcome, {update.chat_join_request.from_user.mention_html()}! Your join request has been approved.",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Sent welcome message to {update.chat_join_request.from_user.id}")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")

# --- Telegram Application Initialization (Helper Function) ---
# This function creates and configures the Telegram Application instance.
# It will be called from wsgi.py when handling webhook requests.
def create_telegram_application():
    """Initializes and configures the Telegram Application."""
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set. Please set it to run the bot.")
        # In a production webhook setup, it's better to raise an error
        # or return None to indicate misconfiguration.
        return None

    application = ApplicationBuilder().token(bot_token).build()

    # Add your handlers here.
    application.add_handler(ChatJoinRequestHandler(auto_approve_join_request))

    return application

# No Flask app instance (`app = Flask(__name__)`) here.
# No @app.route decorators here.
# No `if __name__ == '__main__':` block here (for production deployment).
# This file now focuses purely on the bot's logic and handler setup.
