import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    ChatJoinRequestHandler,
    CommandHandler,
)
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pending_requests = {}
auto_accept_chats = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = context.bot.username
    keyboard = [
        [InlineKeyboardButton("➕ Add Bot to Group", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("👥 Support Group", url="https://t.me/colonel_support")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/YOUR_USERNAME_HERE")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Hello! I'm your friendly auto-join request approval bot.\n\n"
        "✅ Add me to groups and use /accept to auto-approve join requests.",
        reply_markup=reply_markup,
    )

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Use this in a group.")
        return

    bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
    if not bot_member.can_invite_users:
        await update.message.reply_text("❌ I need 'Invite Users' permission.")
        return

    auto_accept_chats.add(chat.id)
    count = 0

    if chat.id in pending_requests:
        for req in pending_requests[chat.id][:]:
            try:
                await req.approve()
                count += 1
                user = req.from_user
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=f"✅ Welcome, {user.mention_html()}!",
                    parse_mode=ParseMode.HTML,
                )
                pending_requests[chat.id].remove(req)
            except Exception as e:
                logger.error(f"Failed to approve: {e}")

    await update.message.reply_text(f"✅ Auto-accept enabled. Approved {count} pending requests.")

async def auto_approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.chat_join_request.chat.id
    user = update.chat_join_request.from_user

    if chat_id not in pending_requests:
        pending_requests[chat_id] = []
    pending_requests[chat_id].append(update.chat_join_request)

    logger.info(f"Join request from {user.id} in chat {chat_id}")

    if chat_id in auto_accept_chats:
        try:
            await update.chat_join_request.approve()
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Welcome, {user.mention_html()}!",
                parse_mode=ParseMode.HTML,
            )
            pending_requests[chat_id].remove(update.chat_join_request)
        except Exception as e:
            logger.error(f"Approval failed: {e}")

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not set")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("accept", accept))
    app.add_handler(ChatJoinRequestHandler(auto_approve_join_request))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        webhook_url=os.getenv("WEBHOOK_URL"),
    )
