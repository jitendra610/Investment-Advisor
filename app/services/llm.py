from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm():

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key.get_secret_value(),
        temperature=0,
        timeout=60,
        max_retries=2,
    )