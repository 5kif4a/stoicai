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

from app.ai import get_gpt_assistant_response
from app.config import settings
from app.db import Chat, Message, Role, init_db

SYSTEM_PROMPT = {
    "role": "system",
    "content": settings.openai_prompt_content,
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    await init_db()
    logger.info("Database initialized successfully.")


async def get_or_create_chat(
    chat_id: int, message_id: int, system_message: str, timestamp: datetime
) -> Chat:
    existing_chat = await Chat.find_one(Chat.id == chat_id)
    if existing_chat:
        return existing_chat

    chat = Chat(
        id=chat_id,
        messages=[
            Message(
                id=message_id,
                sender=Role.ASSISTANT,
                content=system_message,
                timestamp=timestamp,
            )
        ],
    )
    await chat.insert()
    return chat


async def handle_start_command(update: Update, context: CallbackContext) -> None:
    try:
        message = update.message
        chat = await get_or_create_chat(
            chat_id=message.chat_id,
            message_id=message.message_id,
            system_message=settings.messenger_bot_start_message,
            timestamp=message.date,
        )

        chat.messages.append(
            Message(
                id=message.message_id,
                sender=Role.ASSISTANT,
                content=settings.messenger_bot_start_message,
                timestamp=message.date,
            )
        )
        await chat.save()
        await message.reply_text(settings.messenger_bot_start_message)

    except Exception as e:
        logger.error(f"Error handling user message: {e}")
        error_message = random.choice(settings.messenger_bot_error_messages)
        await update.message.reply_text(error_message)


async def handle_user_message(update: Update, context: CallbackContext) -> None:
    try:
        message = update.message
        chat = await get_or_create_chat(
            chat_id=message.chat_id,
            message_id=message.message_id,
            system_message=SYSTEM_PROMPT["content"],
            timestamp=message.date,
        )

        user_message = Message(
            id=message.message_id,
            sender=Role.USER,
            content=message.text,
            timestamp=message.date,
        )
        chat.messages.append(user_message)
        await chat.save()

        thinking_message = await message.reply_text(
            settings.messenger_bot_thinking_message
        )

        chat_history = [
            {"role": msg.sender.value, "content": msg.content} for msg in chat.messages
        ]
        gpt_response = get_gpt_assistant_response(chat_history)

        bot_response = Message(
            id=message.message_id,
            sender=Role.ASSISTANT,
            content=gpt_response,
            timestamp=message.date,
        )
        chat.messages.append(bot_response)
        await chat.save()

        await thinking_message.delete()
        await message.reply_text(gpt_response)

    except Exception as e:
        logger.error(f"Error handling /start command: {e}")
        error_message = random.choice(settings.messenger_bot_error_messages)
        await update.message.reply_text(error_message)


def main() -> None:
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


if __name__ == '__main__':
    main()
