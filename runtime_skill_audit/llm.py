from __future__ import annotations

import json
import os
import time
from http.client import IncompleteRead
from typing import Any
from urllib import error, request

from .models import LLMConfig


def strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return text


def parse_json_response(text: str) -> Any:
    return json.loads(strip_json_fences(text))


class OllamaCloudClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def _is_bedrock(self) -> bool:
        return "bedrock" in self.config.base_url.lower()

    def _complete_bedrock(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
    ) -> str:
        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise ValueError(f"Missing API key in env var {self.config.api_key_env}")

        base_url = self.config.base_url.rstrip("/")
        endpoint = f"{base_url}/model/{self.config.model}/converse"
        payload: dict[str, Any] = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            "inferenceConfig": {
                "maxTokens": 4096,
                "temperature": self.config.temperature if temperature is None else temperature,
            },
        }
        if system_prompt:
            payload["system"] = [{"text": system_prompt}]

        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        body: dict[str, Any] | None = None
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries):
            try:
                with request.urlopen(req, timeout=self.config.timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                break
            except IncompleteRead as exc:
                last_error = exc
                try:
                    body = json.loads(exc.partial.decode("utf-8"))
                    break
                except Exception:
                    pass
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"Bedrock HTTP {exc.code}: {detail}") from exc
            except error.URLError as exc:
                last_error = exc
            if attempt < self.config.max_retries - 1:
                time.sleep(float(attempt + 1))

        if body is None:
            raise RuntimeError(f"Failed to reach Bedrock API: {last_error}")

        content = body.get("output", {}).get("message", {}).get("content", [])
        text_parts = [item.get("text", "") for item in content if isinstance(item, dict) and isinstance(item.get("text"), str)]
        text = "\n".join(part for part in text_parts if part).strip()
        if not text:
            raise RuntimeError(f"Unexpected Bedrock response: {body}")
        return text

    def complete(self, *, prompt: str, system_prompt: str | None = None, temperature: float | None = None) -> str:
        if self._is_bedrock():
            return self._complete_bedrock(prompt=prompt, system_prompt=system_prompt, temperature=temperature)

        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise ValueError(f"Missing API key in env var {self.config.api_key_env}")

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
        }
        payload["options"] = {"temperature": self.config.temperature if temperature is None else temperature}

        req = request.Request(
            self.config.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )

        body: dict[str, Any] | None = None
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries):
            try:
                with request.urlopen(req, timeout=self.config.timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                break
            except IncompleteRead as exc:
                last_error = exc
                try:
                    body = json.loads(exc.partial.decode("utf-8"))
                    break
                except Exception:
                    pass
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
            except error.URLError as exc:
                last_error = exc
            if attempt < self.config.max_retries - 1:
                time.sleep(float(attempt + 1))

        if body is None:
            raise RuntimeError(f"Failed to reach Ollama cloud API: {last_error}")

        content = body.get("message", {}).get("content")
        if not isinstance(content, str):
            raise RuntimeError(f"Unexpected Ollama response: {body}")
        return content.strip()

    def complete_json(self, *, prompt: str, system_prompt: str | None = None, temperature: float | None = None) -> Any:
        return parse_json_response(self.complete(prompt=prompt, system_prompt=system_prompt, temperature=temperature))
