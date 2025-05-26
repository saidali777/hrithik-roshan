import logging
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from telegram.constants import ParseMode

# Basic logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Flask App Setup ---
app = Flask(__name__)

# --- Telegram Bot Logic ---
async def auto_approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_join_request:
        await update.chat_join_request.approve()
        logger.info(f"Approved join request from {update.chat_join_request.from_user.id} in chat {update.chat_join_request.chat.id}")

        try:
            await context.bot.send_message(
                chat_id=update.chat_join_request.chat.id,
                text=f"Welcome, {update.chat_join_request.from_user.mention_html()}! Your join request has been approved.",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Sent welcome message to {update.chat_join_request.from_user.id}")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")

# --- Main Webhook Endpoint ---
@app.route("/", methods=["POST"])
async def telegram_webhook():
    """Handle incoming Telegram updates via webhook."""
    application = _get_telegram_application()
    if not application:
        return "Bot not configured", 500

    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

# --- Telegram Application Initialization (Helper Function) ---
def _get_telegram_application():
    """Initializes and configures the Telegram Application."""
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set. Exiting.")
        return None

    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(ChatJoinRequestHandler(auto_approve_join_request))
    return application

# --- Entry Point for Deployment ---
if __name__ == '__main__':
    # >>> MODIFICATION HERE <<<
    # It's best practice to use the PORT environment variable provided by the platform.
    # If the platform *guarantees* it will always be 8000, you can hardcode.
    # Otherwise, rely on the env var.
    # Using 8000 as a fallback IF PORT isn't set, which it will be on Koyeb/Heroku
    port = int(os.environ.get("PORT", 8000)) # Change default fallback to 8000 if PORT is not set

    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port)
