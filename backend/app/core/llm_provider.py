import logging
from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any, cast

from app.core.config import Settings
from app.core.exceptions import ProviderException

logger = logging.getLogger("kisan_mitra_ai")

class BaseLLMProvider(ABC):
    """
    Abstract Base Class for LLM providers. Swappable without changing agent code.
    """
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> str:
        """
        Generate a text response based on a prompt and optional system instructions.
        """
        pass

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> Generator[str, None, None]:
        """
        Stream a text response based on a prompt.
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the currently active model.
        """
        pass

class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider used for unit testing, dry runs, and local orchestration tests.
    """
    def __init__(self, model_name: str = "mock-model") -> None:
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> str:
        logger.info(f"[MockLLM] generate called for model: {self.model_name}")
        return f"Mock response for prompt: '{prompt[:30]}...' using instruction: '{system_instruction}'"

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> Generator[str, None, None]:
        logger.info(f"[MockLLM] generate_stream called for model: {self.model_name}")
        yield f"Mock stream chunk for prompt: '{prompt[:20]}...'"
        yield " - continuation"
        yield " - completed."

    def get_model_name(self) -> str:
        return self.model_name

class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider wrapper.
    """
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro", temperature: float = 0.2) -> None:
        if not api_key:
            raise ProviderException("Gemini API key is not configured.")
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self._client: Any = None

    def _init_client(self) -> None:
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
            except ImportError as e:
                raise ProviderException("google-generativeai package is not installed.", details={"error": str(e)})

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> str:
        self._init_client()
        temp = temperature if temperature is not None else self.temperature
        try:
            model = self._client.GenerativeModel(
                model_name=self.model_name,
                generation_config={"temperature": temp},
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return cast(str, response.text)
        except Exception as e:
            raise ProviderException(f"Gemini generation failed: {e!s}")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> Generator[str, None, None]:
        self._init_client()
        temp = temperature if temperature is not None else self.temperature
        try:
            model = self._client.GenerativeModel(
                model_name=self.model_name,
                generation_config={"temperature": temp},
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                yield chunk.text
        except Exception as e:
            raise ProviderException(f"Gemini streaming failed: {e!s}")

    def get_model_name(self) -> str:
        return self.model_name

class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI LLM provider wrapper.
    """
    def __init__(self, api_key: str, model_name: str = "gpt-4o", temperature: float = 0.2) -> None:
        if not api_key:
            raise ProviderException("OpenAI API key is not configured.")
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self._client: Any = None

    def _init_client(self) -> None:
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError as e:
                raise ProviderException("openai package is not installed.", details={"error": str(e)})

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> str:
        self._init_client()
        temp = temperature if temperature is not None else self.temperature
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp
            )
            content = response.choices[0].message.content
            return content if content is not None else ""
        except Exception as e:
            raise ProviderException(f"OpenAI generation failed: {e!s}")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> Generator[str, None, None]:
        self._init_client()
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
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            raise ProviderException(f"OpenAI streaming failed: {e!s}")

    def get_model_name(self) -> str:
        return self.model_name

class ClaudeLLMProvider(BaseLLMProvider):
    """
    Anthropic Claude LLM provider wrapper.
    """
    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-latest", temperature: float = 0.2) -> None:
        if not api_key:
            raise ProviderException("Anthropic API key is not configured.")
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self._client: Any = None

    def _init_client(self) -> None:
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError as e:
                raise ProviderException("anthropic package is not installed.", details={"error": str(e)})

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> str:
        self._init_client()
        temp = temperature if temperature is not None else self.temperature
        try:
            params = {
                "model": self.model_name,
                "max_tokens": 4096,
                "temperature": temp,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_instruction:
                params["system"] = system_instruction

            response = self._client.messages.create(**params)
            # Anthropic returns a list of ContentBlock elements
            content = response.content[0].text
            return cast(str, content)
        except Exception as e:
            raise ProviderException(f"Claude generation failed: {e!s}")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> Generator[str, None, None]:
        self._init_client()
        temp = temperature if temperature is not None else self.temperature
        try:
            params = {
                "model": self.model_name,
                "max_tokens": 4096,
                "temperature": temp,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_instruction:
                params["system"] = system_instruction

            with self._client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise ProviderException(f"Claude streaming failed: {e!s}")

    def get_model_name(self) -> str:
        return self.model_name

class OllamaLLMProvider(BaseLLMProvider):
    """
    Ollama local LLM provider wrapper using direct HTTP endpoints.
    """
    def __init__(self, host: str = "http://localhost:11434", model_name: str = "llama3", temperature: float = 0.2) -> None:
        self.host = host.rstrip("/")
        self.model_name = model_name
        self.temperature = temperature
        self._client: Any = None

    def _init_client(self) -> None:
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(base_url=self.host, timeout=60.0)
            except ImportError as e:
                raise ProviderException("httpx package is not installed.", details={"error": str(e)})

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None
    ) -> str:
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

        try:
            response = self._client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return cast(str, data.get("response", ""))
        except Exception as e:
            raise ProviderException(f"Ollama generation failed: {e!s}")

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
            # We use an independent request block for streaming
            with self._client.stream("POST", "/api/generate", json=payload) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line.strip():
                        import json
                        chunk = json.loads(line)
                        val = chunk.get("response", "")
                        if val:
                            yield val
        except Exception as e:
            raise ProviderException(f"Ollama streaming failed: {e!s}")

    def get_model_name(self) -> str:
        return self.model_name

class LLMProviderFactory:
    """
    Factory to resolve the concrete BaseLLMProvider instance dynamically.
    """
    @staticmethod
    def create_provider(provider_name: str, settings: "Settings") -> BaseLLMProvider:
        name = provider_name.strip().lower()
        if name == "mock":
            return MockLLMProvider()
        elif name == "gemini":
            return GeminiLLMProvider(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_MODEL,
                temperature=settings.LLM_TEMPERATURE
            )
        elif name == "openai":
            return OpenAILLMProvider(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.OPENAI_MODEL,
                temperature=settings.LLM_TEMPERATURE
            )
        elif name == "claude":
            return ClaudeLLMProvider(
                api_key=settings.CLAUDE_API_KEY,
                model_name=settings.CLAUDE_MODEL,
                temperature=settings.LLM_TEMPERATURE
            )
        elif name == "ollama":
            return OllamaLLMProvider(
                host=settings.OLLAMA_HOST,
                model_name=settings.OLLAMA_MODEL,
                temperature=settings.LLM_TEMPERATURE
            )
        else:
            raise ProviderException(f"Unsupported LLM provider: {provider_name}")
