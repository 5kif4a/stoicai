from openai import AsyncOpenAI

from app.config import settings

__all__ = ("client", "get_gpt_assistant_response")

client = AsyncOpenAI(api_key=settings.openai_api_key)

CHAT_MODEL_ID = settings.openai_chat_model_id

SYSTEM_PROMPT = {
    "role": "system",
    "content": settings.openai_prompt_content,
}

async def get_gpt_assistant_response(chat_history: list[dict[str, str]]) -> str:
    try:
        response = await client.chat.completions.create(
            model=CHAT_MODEL_ID,
            messages=[SYSTEM_PROMPT] + chat_history,
            max_tokens=settings.openai_max_tokens,
            n=1,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {e}"
