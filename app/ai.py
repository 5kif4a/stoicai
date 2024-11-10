from openai import OpenAI

from app.config import settings

__all__ = ("client", "get_gpt_assistant_response")

client = OpenAI(api_key=settings.openai_api_key)

CHAT_MODEL_ID = settings.openai_chat_model_id


def get_gpt_assistant_response(chat_history):
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL_ID,
            messages=chat_history,
            max_tokens=settings.openai_max_tokens,
            n=1,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {e}"
