from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Literal

import yaml

from xiaogpt.utils import validate_proxy

LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"
WAKEUP_KEYWORD = "小爱同学"

HARDWARE_COMMAND_DICT = {
    # hardware: (tts_command, wakeup_command)
    "LX06": ("5-1", "5-5"),
    "L05B": ("5-3", "5-4"),
    "S12": ("5-1", "5-5"),  # 第一代小爱，型号 MDZ-25-DA
    "S12A": ("5-1", "5-5"),
    "LX01": ("5-1", "5-5"),
    "L06A": ("5-1", "5-5"),
    "LX04": ("5-1", "5-4"),
    "L05C": ("5-3", "5-4"),
    "L17A": ("7-3", "7-4"),
    "X08E": ("7-3", "7-4"),
    "LX05A": ("5-1", "5-5"),  # 小爱红外版
    "LX5A": ("5-1", "5-5"),  # 小爱红外版
    "L07A": ("5-1", "5-5"),  # Redmi 小爱音箱 Play(l7a)
    "L15A": ("7-3", "7-4"),
    "X6A": ("7-3", "7-4"),  # 小米智能家庭屏 6
    "X10A": ("7-3", "7-4"),  # 小米智能家庭屏 10
    # add more here
}

DEFAULT_COMMAND = ("5-1", "5-5")

KEY_WORD = ("帮我", "请")
CHANGE_PROMPT_KEY_WORD = ("更改提示词",)
PROMPT = "以下请用 300 字以内回答，请只回答文字不要带链接"
# simulate_xiaoai_question
MI_ASK_SIMULATE_DATA = {
    "code": 0,
    "message": "Success",
    "data": '{"bitSet":[0,1,1],"records":[{"bitSet":[0,1,1,1,1],"answers":[{"bitSet":[0,1,1,1],"type":"TTS","tts":{"bitSet":[0,1],"text":"Fake Answer"}}],"time":1677851434593,"query":"Fake Question","requestId":"fada34f8fa0c3f408ee6761ec7391d85"}],"nextEndTime":1677849207387}',
}


@dataclass
class Config:
    hardware: str = "LX06"
    account: str = os.getenv("MI_USER", "")
    password: str = os.getenv("MI_PASS", "")
    mi_user_id: str = os.getenv("MI_USER_ID", "")
    mi_device_id: str = os.getenv("MI_DEVICE_ID", "")
    pass_token: str = os.getenv("MI_PASS_TOKEN", "")
    openai_key: str = os.getenv("OPENAI_API_KEY", "")
    moonshot_api_key: str = os.getenv("MOONSHOT_API_KEY", "")
    yi_api_key: str = os.getenv("YI_API_KEY", "")
    llama_api_key: str = os.getenv("GROQ_API_KEY", "")  # use groq
    glm_key: str = os.getenv("CHATGLM_KEY", "")
    gemini_key: str = os.getenv("GEMINI_KEY", "")  # keep the old rule
    gemini_model: str = os.getenv("GEMINI_MODEL", "")  # keep the old rule
    gemini_google_search: bool = os.getenv("GEMINI_GOOGLE_SEARCH", "").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    qwen_key: str = os.getenv("DASHSCOPE_API_KEY", "")  # keep the old rule
    serpapi_api_key: str = os.getenv("SERPAPI_API_KEY", "")
    gemini_api_domain: str = os.getenv(
        "GEMINI_API_DOMAIN", ""
    )  # 自行部署的 Google Gemini 代理
    volc_access_key: str = os.getenv("VOLC_ACCESS_KEY", "")
    volc_secret_key: str = os.getenv("VOLC_SECRET_KEY", "")
    volc_api_key: str = os.getenv("volc_api_key", "")
    proxy: str | None = None
    mi_did: str = os.getenv("MI_DID", "")
    keyword: Iterable[str] = KEY_WORD
    change_prompt_keyword: Iterable[str] = CHANGE_PROMPT_KEY_WORD
    prompt: str = PROMPT
    mute_xiaoai: bool = False
    bot: str = "chatgptapi"
    cookie: str = ""
    api_base: str | None = None
    deployment_id: str | None = None
    use_command: bool = False
    verbose: int = 0
    start_conversation: str = "开始持续对话"
    end_conversation: str = "结束持续对话"
    stream: bool = False
    tts: Literal[
        "mi", "edge", "azure", "openai", "baidu", "google", "volc", "minimax", "fish"
    ] = "mi"
    tts_options: dict[str, Any] = field(default_factory=dict)
    gpt_options: dict[str, Any] = field(default_factory=dict)

    def masked_dict(self) -> dict[str, Any]:
        data = asdict(self)
        secret_keys = {
            "account",
            "password",
            "pass_token",
            "cookie",
            "openai_key",
            "moonshot_api_key",
            "yi_api_key",
            "llama_api_key",
            "glm_key",
            "gemini_key",
            "qwen_key",
            "serpapi_api_key",
            "volc_access_key",
            "volc_secret_key",
            "volc_api_key",
        }
        for key in secret_keys:
            value = data.get(key)
            if isinstance(value, str) and value:
                data[key] = self._mask_secret(value)
        tts_options = data.get("tts_options") or {}
        if isinstance(tts_options, dict):
            data["tts_options"] = {
                key: (
                    self._mask_secret(value)
                    if isinstance(value, str)
                    and any(token in key.lower() for token in ("key", "token", "secret", "password"))
                    and value
                    else value
                )
                for key, value in tts_options.items()
            }
        return data

    @staticmethod
    def _mask_secret(value: str) -> str:
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}...{value[-4:]}"

    def __post_init__(self) -> None:
        if self.proxy:
            validate_proxy(self.proxy)
        if self.cookie and any([self.account, self.password, self.pass_token]):
            raise Exception("cookie login is enabled; please do not also set pass_token or account/password")
        if self.pass_token and any([self.account, self.password]):
            raise Exception("passToken login is enabled; please do not also set account/password")
        if self.pass_token and not self.mi_user_id:
            raise Exception("Using passToken login needs mi_user_id")
        if self.pass_token and not self.mi_device_id:
            raise Exception("Using passToken login needs mi_device_id")
        if self.cookie and not self.mi_did:
            raise Exception("Using cookie login needs mi_did")
        if bool(self.account) ^ bool(self.password):
            raise Exception("account/password login needs both account and password")
        if (
            self.api_base
            and self.api_base.endswith(("openai.azure.com", "openai.azure.com/"))
            and not self.deployment_id
        ):
            raise Exception(
                "Using Azure OpenAI needs deployment_id, read this: "
                "https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/chatgpt?pivots=programming-language-chat-completions"
            )
        if self.bot in ["chatgptapi"]:
            if not self.openai_key:
                raise Exception(
                    "Using GPT api needs openai API key, please google how to"
                )
        if self.bot == "gemini":
            if not self.gemini_key:
                raise Exception(
                    "Using Gemini api needs gemini API key, please google how to"
                )
            if self.gemini_google_search and not self.gemini_model:
                self.gemini_model = "gemini-2.0-flash"

    @property
    def tts_command(self) -> str:
        return HARDWARE_COMMAND_DICT.get(self.hardware, DEFAULT_COMMAND)[0]

    @property
    def wakeup_command(self) -> str:
        return HARDWARE_COMMAND_DICT.get(self.hardware, DEFAULT_COMMAND)[1]

    @classmethod
    def from_options(cls, options: argparse.Namespace) -> Config:
        config = {}
        if options.config:
            config = cls.read_from_file(options.config)
        for key, value in vars(options).items():
            if value is not None and key in cls.__dataclass_fields__:
                config[key] = value
        if config.get("tts") == "volc":
            config.setdefault("tts_options", {}).setdefault(
                "access_key", config.get("volc_access_key")
            )
            config.setdefault("tts_options", {}).setdefault(
                "secret_key", config.get("volc_secret_key")
            )
        elif config.get("tts") == "fish":
            config.setdefault("tts_options", {}).setdefault(
                "api_key", config.get("fish_api_key")
            )
            if voice := config.get("fish_voice_key"):
                config.setdefault("tts_options", {}).setdefault("voice", voice)

        return cls(**config)

    @classmethod
    def read_from_file(cls, config_path: str) -> dict:
        result = {}
        with open(config_path, "rb") as f:
            if config_path.endswith(".json"):
                config = json.load(f)
            else:
                config = yaml.safe_load(f)
            for key, value in config.items():
                if value is None:
                    continue
                if key == "keyword":
                    if not isinstance(value, list):
                        value = [value]
                    value = [kw for kw in value if kw]
                elif key == "use_chatgpt_api":
                    key, value = "bot", "chatgptapi"
                elif key == "use_newbing":
                    key, value = "bot", "newbing"
                elif key == "use_glm":
                    key, value = "bot", "glm"
                elif key == "use_gemini":
                    key, value = "bot", "gemini"
                elif key == "use_qwen":
                    key, value = "bot", "qwen"
                elif key == "use_doubao":
                    key, value = "bot", "doubao"
                elif key == "use_moonshot":
                    key, value = "bot", "moonshot"
                elif key == "use_yi":
                    key, value = "bot", "yi"
                elif key == "use_llama":
                    key, value = "bot", "llama"
                elif key == "use_langchain":
                    key, value = "bot", "langchain"
                elif key == "enable_edge_tts":
                    key, value = "tts", "edge"
                if key in cls.__dataclass_fields__:
                    result[key] = value
        return result
