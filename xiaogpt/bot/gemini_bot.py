"""Google Gemini bot."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin
from xiaogpt.utils import split_sentences

generation_config = {
    "temperature": 0.7,
    "topP": 1,
    "topK": 1,
    "maxOutputTokens": 4096,
}

DEFAULT_MODEL = "gemini-2.0-flash-lite"
DEFAULT_SEARCH_MODEL = "gemini-2.0-flash"

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]


class GeminiBot(ChatHistoryMixin, BaseBot):
    name = "Gemini"
    default_options = generation_config

    def __init__(
        self,
        gemini_key: str,
        gemini_api_domain: str,
        gemini_model: str,
        gemini_google_search: bool = False,
        proxy: str | None = None,
    ) -> None:
        self.gemini_key = gemini_key
        self.gemini_api_domain = gemini_api_domain.strip().rstrip("/")
        self.gemini_google_search = gemini_google_search
        self.proxy = proxy
        self.history = []
        self.gemini_model = gemini_model or (
            DEFAULT_SEARCH_MODEL if gemini_google_search else DEFAULT_MODEL
        )
        if self.gemini_api_domain:
            print("Use custom gemini_api_domain: " + self.gemini_api_domain)

    @classmethod
    def from_config(cls, config):
        return cls(
            gemini_key=config.gemini_key,
            gemini_api_domain=config.gemini_api_domain,
            gemini_model=config.gemini_model,
            gemini_google_search=config.gemini_google_search,
            proxy=config.proxy,
        )

    def _base_url(self) -> str:
        if self.gemini_api_domain:
            if self.gemini_api_domain.startswith(("http://", "https://")):
                return self.gemini_api_domain
            return "https://" + self.gemini_api_domain
        return "https://generativelanguage.googleapis.com"

    def _endpoint(self, stream: bool) -> str:
        action = "streamGenerateContent" if stream else "generateContent"
        url = f"{self._base_url()}/v1beta/models/{self.gemini_model}:{action}"
        if stream:
            url += "?alt=sse"
        return url

    def _httpx_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"trust_env": True}
        if self.proxy:
            kwargs["proxies"] = self.proxy
        return kwargs

    @staticmethod
    def _make_content(role: str, text: str) -> dict[str, Any]:
        return {"role": role, "parts": [{"text": text}]}

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        texts: list[str] = []
        for candidate in payload.get("candidates", []):
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = part.get("text")
                if text:
                    texts.append(text)
        return "".join(texts)

    @staticmethod
    def _extract_grounding_metadata(payload: dict[str, Any]) -> dict[str, Any] | None:
        for candidate in payload.get("candidates", []):
            metadata = candidate.get("groundingMetadata")
            if metadata:
                return metadata
        return None

    def _maybe_print_grounding(self, payload: dict[str, Any]) -> None:
        metadata = self._extract_grounding_metadata(payload)
        if not metadata:
            return
        queries = metadata.get("webSearchQueries") or []
        chunks = metadata.get("groundingChunks") or []
        if queries:
            print(f"Gemini Google Search queries: {queries}")
        if chunks:
            refs = []
            for chunk in chunks[:5]:
                web = chunk.get("web") or {}
                title = web.get("title")
                uri = web.get("uri")
                if title or uri:
                    refs.append({"title": title, "uri": uri})
            if refs:
                print("Gemini grounding sources:", refs)

    def _request_payload(self, query: str, **options: Any) -> dict[str, Any]:
        config = self._normalize_generation_config({**self.default_options, **options})
        contents = [*self.get_messages(), self._make_content("user", query)]
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": config,
            "safetySettings": safety_settings,
        }
        if self.gemini_google_search:
            payload["tools"] = [{"google_search": {}}]
        return payload

    @staticmethod
    def _normalize_generation_config(options: dict[str, Any]) -> dict[str, Any]:
        key_map = {
            "top_p": "topP",
            "top_k": "topK",
            "max_output_tokens": "maxOutputTokens",
            "candidate_count": "candidateCount",
            "stop_sequences": "stopSequences",
            "response_mime_type": "responseMimeType",
            "response_schema": "responseSchema",
        }
        normalized: dict[str, Any] = {}
        for key, value in options.items():
            normalized[key_map.get(key, key)] = value
        normalized.pop("model", None)
        return normalized

    async def ask(self, query, **options):
        payload = self._request_payload(query, **options)
        headers = {
            "x-goog-api-key": self.gemini_key,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(**self._httpx_kwargs()) as sess:
            response = await sess.post(self._endpoint(stream=False), headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        message = self._extract_text(data).strip()
        self.add_message(query, message)
        self._maybe_print_grounding(data)
        print(message)
        return message

    async def ask_stream(self, query: str, **options: Any) -> AsyncGenerator[str, None]:
        payload = self._request_payload(query, **options)
        headers = {
            "x-goog-api-key": self.gemini_key,
            "Content-Type": "application/json",
        }

        async def text_gen() -> AsyncGenerator[str, None]:
            async with httpx.AsyncClient(timeout=None, **self._httpx_kwargs()) as sess:
                async with sess.stream(
                    "POST",
                    self._endpoint(stream=True),
                    headers=headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    final_payload: dict[str, Any] | None = None
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        payload_chunk = json.loads(data)
                        final_payload = payload_chunk
                        text = self._extract_text(payload_chunk)
                        if text:
                            print(text, end="")
                            yield text
                    if final_payload:
                        self._maybe_print_grounding(final_payload)

        message = ""
        try:
            async for sentence in split_sentences(text_gen()):
                message += sentence
                yield sentence
        finally:
            print()
            self.add_message(query, message)
