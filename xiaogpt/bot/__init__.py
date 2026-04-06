from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from xiaogpt.config import Config

if TYPE_CHECKING:
    from xiaogpt.bot.base_bot import BaseBot
    from xiaogpt.bot.chatgptapi_bot import ChatGPTBot
    from xiaogpt.bot.doubao_bot import DoubaoBot
    from xiaogpt.bot.gemini_bot import GeminiBot
    from xiaogpt.bot.glm_bot import GLMBot
    from xiaogpt.bot.langchain_bot import LangChainBot
    from xiaogpt.bot.llama_bot import LlamaBot
    from xiaogpt.bot.moonshot_bot import MoonshotBot
    from xiaogpt.bot.qwen_bot import QwenBot
    from xiaogpt.bot.yi_bot import YiBot

BOT_IMPORTS: dict[str, tuple[str, str]] = {
    "chatgptapi": ("xiaogpt.bot.chatgptapi_bot", "ChatGPTBot"),
    "glm": ("xiaogpt.bot.glm_bot", "GLMBot"),
    "gemini": ("xiaogpt.bot.gemini_bot", "GeminiBot"),
    "qwen": ("xiaogpt.bot.qwen_bot", "QwenBot"),
    "langchain": ("xiaogpt.bot.langchain_bot", "LangChainBot"),
    "doubao": ("xiaogpt.bot.doubao_bot", "DoubaoBot"),
    "moonshot": ("xiaogpt.bot.moonshot_bot", "MoonshotBot"),
    "yi": ("xiaogpt.bot.yi_bot", "YiBot"),
    "llama": ("xiaogpt.bot.llama_bot", "LlamaBot"),
}


def get_bot(config: Config) -> BaseBot:
    try:
        module_name, class_name = BOT_IMPORTS[config.bot]
    except KeyError:
        raise ValueError(
            f"Unsupported bot {config.bot}, must be one of {list(BOT_IMPORTS)}"
        )
    module = import_module(module_name)
    bot_cls = getattr(module, class_name)
    return bot_cls.from_config(config)


__all__ = ["get_bot"]
