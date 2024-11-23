import json
import logging
import random
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
)
from redis import asyncio as aioredis
from telegramify_markdown import markdownify
from app.ai import get_gpt_assistant_response
from app.config import settings
from app.db import Chat, Message, Role, init_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

redis = aioredis.from_url(settings.redis_url)


async def post_init(application: Application) -> None:
    await init_db()
    logger.info("Database initialized successfully.")


async def get_last_messages_from_cache(chat_id: int, n: int) -> list[Message]:
    cache_key = f"chat:{chat_id}:messages"
    messages = await redis.lrange(cache_key, -n, -1)
    return [Message(**json.loads(msg)) for msg in messages]


async def save_message_to_cache(chat_id: int, message: Message):
    cache_key = f"chat:{chat_id}:messages"
    await redis.rpush(cache_key, message.model_dump_json())
    await redis.ltrim(cache_key, -50, -1)


async def save_message_to_db(message: Message):
    await message.insert()


async def save_chat_to_db(chat_id: int, timestamp: datetime):
    existing_chat = await Chat.find_one(Chat.id == chat_id)
    if not existing_chat:
        chat = Chat(id=chat_id, timestamp=timestamp)
        await chat.insert()


async def handle_start_command(update: Update, context: CallbackContext):
    try:
        message = update.message

        system_message = Message(
            chat_id=message.chat_id,
            sender=Role.SYSTEM,
            content=settings.messenger_bot_start_message,
            timestamp=message.date,
        )

        await save_chat_to_db(message.chat_id, message.date)
        await save_message_to_db(system_message)
        await save_message_to_cache(message.chat_id, system_message)

        await message.reply_text(settings.messenger_bot_start_message)
    except Exception as e:
        logger.error(f"Error handling /start command: {e}")
        error_message = random.choice(settings.messenger_bot_error_messages)
        await update.message.reply_text(error_message)


async def handle_user_message(update: Update, context: CallbackContext):
    try:
        message = update.message

        user_message = Message(
            chat_id=message.chat_id,
            sender=Role.USER,
            content=message.text,
            timestamp=message.date,
        )
        await save_chat_to_db(message.chat_id, message.date)
        await save_message_to_db(user_message)
        await save_message_to_cache(message.chat_id, user_message)

        thinking_message = await message.reply_text(
            settings.messenger_bot_thinking_message
        )

        N = 20
        last_messages = await get_last_messages_from_cache(message.chat_id, N)

        chat_history = [
            {"role": msg.sender.value, "content": msg.content} for msg in last_messages
        ]

        gpt_response = await get_gpt_assistant_response(chat_history)

        bot_response = Message(
            chat_id=message.chat_id,
            sender=Role.SYSTEM,
            content=gpt_response,
            timestamp=datetime.now(),
        )
        await save_message_to_db(bot_response)
        await save_message_to_cache(message.chat_id, bot_response)

        await thinking_message.delete()
        await message.reply_text(
            markdownify(gpt_response), parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Error handling user message: {e}")
        error_message = random.choice(settings.messenger_bot_error_messages)
        await update.message.reply_text(error_message)


def main():
    application = (
        ApplicationBuilder()
        .token(settings.messenger_bot_api_token)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", handle_start_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message)
    )

    application.run_polling()


if __name__ == "__main__":
    main()
