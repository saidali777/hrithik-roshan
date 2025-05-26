import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

async def auto_approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.chat_join_request.approve()
    logging.info(f"Approved join request from {update.chat_join_request.from_user.id}")

if __name__ == '__main__':
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    app = ApplicationBuilder().token('7611125537:AAGLicQpwAEMVwFTXoTPOYjLC5qGjvEcg94').build()
    app.add_handler(ChatJoinRequestHandler(auto_approve_join_request))
    app.run_polling()
