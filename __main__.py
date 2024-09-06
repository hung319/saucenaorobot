import logging

from telegram import (
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PicklePersistence,
    MessageHandler,
    filters,
)

from saucecontext import SauceContext

from os import getenv

__import__("dotenv").load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs.log")
    ]
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

TOKEN = getenv("6762432858:AAHhe8Ht9Am4-TIQNNMRC3DGUt6jvEOCcOA")


async def start(update: Update, context: SauceContext):
    await update.effective_message.reply_text(
        "Start"
    )

async def photo_handler(update: Update, context: SauceContext):
    file = await context.bot.get_file(update.effective_message.photo[-1].file_id)
    await send_sauce(update, context, file.file_path)


async def video_handler(update: Update, context: SauceContext):
    file = await context.bot.get_file(update.effective_message.video.thumbnail.file_id)
    await send_sauce(update, context, file.file_path)

async def gif_handler(update: Update, context: SauceContext):
    if update.effective_message.animation:
        file = await context.bot.get_file(update.effective_message.animation.thumbnail.file_id)
        await send_sauce(update, context, file.file_path)
    else:
        update.effective_message.reply_text("Unsupported")

async def sticker_handler(update: Update, context: SauceContext):
    file = await context.bot.get_file(update.effective_message.sticker.file_id)
    await send_sauce(update, context, file.file_path)

async def animated_sticker_handler(update: Update, context: SauceContext):
    file = await context.bot.get_file(update.effective_message.sticker.thumbnail.file_id)
    await send_sauce(update, context, file.file_path)


async def send_sauce(update: Update, context: SauceContext, file_path: str):
    await context.get_sauce(
        file_path,
        await update.effective_message.reply_text(
            "Searching for sauce...",
            do_quote=True,
            reply_markup=context.build_search_keyboard(file_path)
        )
    )

async def api_key_command(update: Update, context: SauceContext):
    if not context.args:
        await update.effective_message.reply_text("Syntax:\n/api_key <your_api_key>\n\nGet yours at https://saucenao.com/user.php?page=search-api after logging in")
        return
    context.api_key = context.args[0]
    await update.effective_message.reply_text("Api key set")


def main():
    application = (
        Application
        .builder()
        .token(TOKEN)
        .persistence(PicklePersistence("persistence.pickle"))
        .context_types(ContextTypes(SauceContext))
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("api_key", api_key_command))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(MessageHandler(filters.VIDEO, video_handler))
    application.add_handler(MessageHandler(filters.ANIMATION, gif_handler))
    application.add_handler(MessageHandler(filters.Sticker.STATIC, sticker_handler))
    application.add_handler(MessageHandler(filters.Sticker.ANIMATED | filters.Sticker.VIDEO, animated_sticker_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
