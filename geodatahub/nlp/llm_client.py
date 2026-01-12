import os
import json
import requests
from typing import Optional
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """
        Generate completion for the given prompt.

        Args:
            prompt: Input prompt text

        Returns:
            Generated text response
        """
        pass


class GroqClient(BaseLLMClient):
    """
    Groq API client - fast inference with free tier available.

    Groq provides ultra-fast inference with generous free tier limits.
    Recommended for cloud-based deployments.

    API Key: Set GROQ_API_KEY environment variable
    Get API key from: https://console.groq.com/
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
            model: Model to use (default: llama-3.1-8b-instant)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not provided. Set GROQ_API_KEY environment variable.")

        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = model

    def complete(self, prompt: str) -> str:
        """Generate completion using Groq API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 500
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            return response.json()["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Groq API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Groq API response parsing failed: {e}")


class OllamaClient(BaseLLMClient):
    """
    Ollama local client - privacy-focused local LLM inference.

    Ollama allows running LLMs locally without sending data to external APIs.
    Recommended for privacy-sensitive deployments.

    Setup: Install Ollama from https://ollama.ai/
    Run: ollama pull llama3 (or mistral, phi3, etc.)
    """

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client.

        Args:
            model: Model name (e.g., llama3, mistral, phi3)
            base_url: Ollama API base URL (default: http://localhost:11434)
        """
        self.model = model
        self.base_url = base_url.rstrip('/')

    def complete(self, prompt: str) -> str:
        """Generate completion using Ollama"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            return response.json()["response"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama request failed: {e}. Is Ollama running?")
        except KeyError as e:
            raise Exception(f"Ollama response parsing failed: {e}")


class OpenRouterClient(BaseLLMClient):
    """
    OpenRouter client - access to multiple LLM providers including free models.

    OpenRouter provides access to various LLM providers with some free models available.

    API Key: Set OPENROUTER_API_KEY environment variable
    Get API key from: https://openrouter.ai/
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/llama-3.1-8b-instruct:free"):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
            model: Model to use (default: meta-llama/llama-3.1-8b-instruct:free)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable.")

        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = model

    def complete(self, prompt: str) -> str:
        """Generate completion using OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/geodatahub/geodatahub",
            "X-Title": "GeoDataHub"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            return response.json()["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenRouter API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise Exception(f"OpenRouter API response parsing failed: {e}")


def get_llm_client(provider: str = "auto") -> Optional[BaseLLMClient]:
    """
    Factory function to get appropriate LLM client.

    Tries providers in order of availability:
    1. Groq (if GROQ_API_KEY is set)
    2. Ollama (if running locally)
    3. OpenRouter (if OPENROUTER_API_KEY is set)

    Args:
        provider: Provider name ("groq", "ollama", "openrouter", "auto")
                 "auto" tries all providers in order

    Returns:
        LLM client instance or None if no provider available

    Example:
        >>> client = get_llm_client("auto")
        >>> if client:
        ...     response = client.complete("Extract data from: ...")
    """

    if provider == "groq":
        try:
            return GroqClient()
        except ValueError as e:
            print(f"Groq client initialization failed: {e}")
            return None

    if provider == "ollama":
        try:
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.ok:
                return OllamaClient()
        except requests.exceptions.RequestException:
            print("Ollama not available. Is it running? Install from https://ollama.ai/")
            return None

    if provider == "openrouter":
        try:
            return OpenRouterClient()
        except ValueError as e:
            print(f"OpenRouter client initialization failed: {e}")
            return None

    # Auto mode: try all providers
    if provider == "auto":
        # Try Groq first (fastest)
        if os.getenv("GROQ_API_KEY"):
            try:
                client = GroqClient()
                print("Using Groq for natural language parsing")
                return client
            except Exception:
                pass

        # Try Ollama (local, private)
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.ok:
                client = OllamaClient()
                print("Using Ollama for natural language parsing")
                return client
        except Exception:
            pass

        # Try OpenRouter
        if os.getenv("OPENROUTER_API_KEY"):
            try:
                client = OpenRouterClient()
                print("Using OpenRouter for natural language parsing")
                return client
            except Exception:
                pass

        print("No LLM provider available. Will use regex-based parsing.")
        return None

    return None
