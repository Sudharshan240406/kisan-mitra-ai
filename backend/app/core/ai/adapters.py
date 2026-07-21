import logging
import time
from collections.abc import Generator
from typing import Any

from app.core.ai.base import AIPlatformException, IProviderAdapter, NormalizedAIResponse

logger = logging.getLogger("kisan_mitra_ai.ai.adapters")


def _is_mock_credential(value: str) -> bool:
    normalized = (value or "").strip().lower()
    return (
        not normalized
        or "api-key" in normalized
        or "your" in normalized
        or "mock" in normalized
        or normalized in {"test", "dummy"}
    )

def estimate_tokens(text: str) -> int:
    """
    Estimates token count based on standard English character bounds (approx 4 chars per token).
    """
    if not text:
        return 0
    return max(1, len(text) // 4)

class BaseAdapter(IProviderAdapter):
    """
    Common helper functions shared across all model adapters.
    """
    def __init__(self, provider_name: str, model_name: str, is_mock: bool = False) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.is_mock = is_mock

    def _generate_mock(self, prompt: str, system_instruction: str | None = None) -> NormalizedAIResponse:
        """
        Synthesizes a standardized mock response for testing when API keys are absent.
        """
        start_time = time.time()
        mock_output = (
            f"[Mock Provider: {self.provider_name.upper()} | Model: {self.model_name}]\n"
            f"Advisory response for prompt context: '{prompt[:40]}...'\n"
            f"Active system instructions: '{system_instruction or 'None'}'"
        )
        latency = (time.time() - start_time) * 1000.0
        prompt_t = estimate_tokens(prompt)
        completion_t = estimate_tokens(mock_output)

        return NormalizedAIResponse(
            content=mock_output,
            model_name=self.model_name,
            provider_name=self.provider_name,
            prompt_tokens=prompt_t,
            completion_tokens=completion_t,
            latency_ms=latency,
            metadata={"is_mock": True}
        )

    def _generate_mock_stream(self, prompt: str) -> Generator[str, None, None]:
        yield f"[Mock Stream {self.provider_name.upper()} | {self.model_name}]: "
        yield f"Processing request payload containing {len(prompt)} characters. "
        yield "Finalizing mock execution stream."


class GeminiAdapter(BaseAdapter):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro", temperature: float = 0.2) -> None:
        is_mock = _is_mock_credential(api_key)
        super().__init__("gemini", model_name, is_mock)
        self.api_key = api_key
        self.temperature = temperature
        self._client: Any = None

    def _init_client(self) -> None:
        if self.is_mock:
            return
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
            except ImportError:
                logger.warning("google-generativeai package missing. Defaulting to Mock fallback.")
                self.is_mock = True

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> NormalizedAIResponse:
        self._init_client()
        if self.is_mock:
            return self._generate_mock(prompt, system_instruction)

        temp = temperature if temperature is not None else self.temperature
        start_time = time.time()
        try:
            model = self._client.GenerativeModel(
                model_name=self.model_name,
                generation_config={"temperature": temp},
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            latency = (time.time() - start_time) * 1000.0

            # Extract text content
            content = response.text or ""
            prompt_t = estimate_tokens(prompt)
            completion_t = estimate_tokens(content)

            # Try parsing actual token counts if supported by response metadata
            try:
                if hasattr(response, "usage_metadata"):
                    prompt_t = response.usage_metadata.prompt_token_count
                    completion_t = response.usage_metadata.candidates_token_count
            except Exception:
                pass

            return NormalizedAIResponse(
                content=content,
                model_name=self.model_name,
                provider_name=self.provider_name,
                prompt_tokens=prompt_t,
                completion_tokens=completion_t,
                latency_ms=latency
            )
        except Exception as e:
            raise AIPlatformException(f"Gemini adapter execution failed: {e!s}")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> Generator[str, None, None]:
        self._init_client()
        if self.is_mock:
            yield from self._generate_mock_stream(prompt)
            return

        temp = temperature if temperature is not None else self.temperature
        try:
            model = self._client.GenerativeModel(
                model_name=self.model_name,
                generation_config={"temperature": temp},
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise AIPlatformException(f"Gemini streaming failed: {e!s}")


class OpenAIAdapter(BaseAdapter):
    def __init__(self, api_key: str, model_name: str = "gpt-4o", temperature: float = 0.2, base_url: str | None = None) -> None:
        is_mock = _is_mock_credential(api_key)
        super().__init__("openai", model_name, is_mock)
        self.api_key = api_key
        self.temperature = temperature
        self.base_url = base_url
        self._client: Any = None

    def _init_client(self) -> None:
        if self.is_mock:
            return
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                logger.warning("openai package missing. Defaulting to Mock fallback.")
                self.is_mock = True

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> NormalizedAIResponse:
        self._init_client()
        if self.is_mock:
            return self._generate_mock(prompt, system_instruction)

        temp = temperature if temperature is not None else self.temperature
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp
            )
            latency = (time.time() - start_time) * 1000.0
            content = response.choices[0].message.content or ""

            prompt_t = response.usage.prompt_tokens if response.usage else estimate_tokens(prompt)
            completion_t = response.usage.completion_tokens if response.usage else estimate_tokens(content)

            return NormalizedAIResponse(
                content=content,
                model_name=self.model_name,
                provider_name=self.provider_name,
                prompt_tokens=prompt_t,
                completion_tokens=completion_t,
                latency_ms=latency
            )
        except Exception as e:
            raise AIPlatformException(f"OpenAI adapter execution failed: {e!s}")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> Generator[str, None, None]:
        self._init_client()
        if self.is_mock:
            yield from self._generate_mock_stream(prompt)
            return

        temp = temperature if temperature is not None else self.temperature
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                stream=True
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise AIPlatformException(f"OpenAI streaming failed: {e!s}")


class ClaudeAdapter(BaseAdapter):
    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-latest", temperature: float = 0.2) -> None:
        is_mock = _is_mock_credential(api_key)
        super().__init__("claude", model_name, is_mock)
        self.api_key = api_key
        self.temperature = temperature
        self._client: Any = None

    def _init_client(self) -> None:
        if self.is_mock:
            return
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("anthropic package missing. Defaulting to Mock fallback.")
                self.is_mock = True

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> NormalizedAIResponse:
        self._init_client()
        if self.is_mock:
            return self._generate_mock(prompt, system_instruction)

        temp = temperature if temperature is not None else self.temperature
        params = {
            "model": self.model_name,
            "max_tokens": 4096,
            "temperature": temp,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_instruction:
            params["system"] = system_instruction

        start_time = time.time()
        try:
            response = self._client.messages.create(**params)
            latency = (time.time() - start_time) * 1000.0
            content = response.content[0].text or ""

            prompt_t = response.usage.input_tokens if response.usage else estimate_tokens(prompt)
            completion_t = response.usage.output_tokens if response.usage else estimate_tokens(content)

            return NormalizedAIResponse(
                content=content,
                model_name=self.model_name,
                provider_name=self.provider_name,
                prompt_tokens=prompt_t,
                completion_tokens=completion_t,
                latency_ms=latency
            )
        except Exception as e:
            raise AIPlatformException(f"Claude adapter execution failed: {e!s}")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> Generator[str, None, None]:
        self._init_client()
        if self.is_mock:
            yield from self._generate_mock_stream(prompt)
            return

        temp = temperature if temperature is not None else self.temperature
        params = {
            "model": self.model_name,
            "max_tokens": 4096,
            "temperature": temp,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_instruction:
            params["system"] = system_instruction

        try:
            with self._client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise AIPlatformException(f"Claude streaming failed: {e!s}")


class OllamaAdapter(BaseAdapter):
    def __init__(self, host: str = "http://localhost:11434", model_name: str = "llama3", temperature: float = 0.2) -> None:
        super().__init__("ollama", model_name, False)
        self.host = host.rstrip("/")
        self.temperature = temperature
        self._client: Any = None

    def _init_client(self) -> None:
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(base_url=self.host, timeout=30.0)
            except ImportError:
                raise AIPlatformException("httpx package must be installed to run Ollama provider.")

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> NormalizedAIResponse:
        self._init_client()
        temp = temperature if temperature is not None else self.temperature
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "options": {"temperature": temp},
            "stream": False
        }
        if system_instruction:
            payload["system"] = system_instruction

        start_time = time.time()
        try:
            response = self._client.post("/api/generate", json=payload)
            response.raise_for_status()
            latency = (time.time() - start_time) * 1000.0
            data = response.json()
            content = data.get("response", "")

            # Approximate local tokens
            prompt_t = data.get("prompt_eval_count", estimate_tokens(prompt))
            completion_t = data.get("eval_count", estimate_tokens(content))

            return NormalizedAIResponse(
                content=content,
                model_name=self.model_name,
                provider_name=self.provider_name,
                prompt_tokens=prompt_t,
                completion_tokens=completion_t,
                latency_ms=latency
            )
        except Exception as e:
            logger.warning(f"Ollama server offline at {self.host}: {e}")
            raise AIPlatformException(f"Ollama server offline at {self.host}: {e!s}")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> Generator[str, None, None]:
        self._init_client()
        temp = temperature if temperature is not None else self.temperature
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "options": {"temperature": temp},
            "stream": True
        }
        if system_instruction:
            payload["system"] = system_instruction

        try:
            with self._client.stream("POST", "/api/generate", json=payload) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line.strip():
                        import json
                        chunk = json.loads(line)
                        val = chunk.get("response", "")
                        if val:
                            yield val
        except Exception:
            yield from self._generate_mock_stream(prompt)
