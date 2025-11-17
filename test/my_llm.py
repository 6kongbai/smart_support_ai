from langchain.chat_models import init_chat_model

from app.core.config import settings

# llm = init_chat_model(
#     model="gpt-4o-mini",
#     model_provider="openai",
#     api_key=settings.OPENAI_API_KEY,
#     base_url=settings.OPENAI_API_BASE,
# )

llm = init_chat_model(
    model="qwen-plus",
    model_provider="openai",
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.DASHSCOPE_API_BASE,
    temperature=0.7,
)

if __name__ == '__main__':
    full = None  # None | AIMessageChunk
    for chunk in llm.stream("介绍一下机器学习"):
        full = chunk if full is None else full + chunk
        print(full.text)

    print(full.content_blocks)
