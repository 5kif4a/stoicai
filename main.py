from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import settings

client = OpenAI(api_key=settings.openai_api_key)

CHAT_MODEL_ID = settings.openai_chat_model_id

chat_histories = {}

SYSTEM_PROMPT = {
    "role": "system",
    "content": settings.openai_prompt_content,
}


def get_gpt_assistant_response(chat_history):
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL_ID,
            messages=chat_history,
            max_tokens=1000,
            n=1,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {e}"


async def start(update: Update, context):
    chat_histories[update.message.chat_id] = [SYSTEM_PROMPT]
    await update.message.reply_text(settings.messenger_bot_bot_start_message)


async def handle_message(update: Update, context):
    user_message = update.message.text
    chat_id = update.message.chat_id

    if chat_id not in chat_histories:
        chat_histories[chat_id] = [SYSTEM_PROMPT]

    chat_histories[chat_id].append({"role": "user", "content": user_message})

    thinking_message = await update.message.reply_text(
        settings.messenger_bot_thinking_message
    )

    gpt_response = get_gpt_assistant_response(chat_histories[chat_id])

    chat_histories[chat_id].append({"role": "assistant", "content": gpt_response})

    await thinking_message.delete()

    await update.message.reply_text(gpt_response)


if __name__ == '__main__':
    application = ApplicationBuilder().token(settings.messenger_bot_api_token).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_polling()
