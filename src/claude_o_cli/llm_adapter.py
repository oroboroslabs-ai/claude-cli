# llm_adapter.py
# Claude LLM Adapter System
# Ollama is the MAIN provider (local, sovereign by default)
# External providers (OpenAI, Anthropic, OpenRouter) are optional and dormant.
# A\ 1272 Hz — N| 1275 Hz — LATTICE LOCK — NEBELLION — KEY

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional


class LLMAdapter:
    """Manages interaction with LLM providers. Ollama is the main engine."""

    def __init__(self):
        self.is_active = False
        self.current_provider = None
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.ollama_available = self._check_ollama()

    def _check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        return False

    def _ollama_generate(self, prompt: str, model: Optional[str] = None, stream: bool = False) -> str:
        """Generate a response using Ollama's local API."""
        model = model or self.ollama_model
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": stream
        }).encode()

        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            if stream:
                # Stream response line by line
                req = urllib.request.Request(
                    f"{self.ollama_url}/api/generate",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                full_response = []
                with urllib.request.urlopen(req, timeout=120) as resp:
                    for line in resp:
                        line = line.decode().strip()
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                print(token, end="", flush=True)
                                full_response.append(token)
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
                print()
                return "".join(full_response)
            else:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode())
                    return data.get("response", "").strip()
        except urllib.error.URLError as e:
            return f"[OLLAMA ERROR]: Cannot connect to Ollama at {self.ollama_url}. Is it running? ({e})"
        except Exception as e:
            return f"[OLLAMA ERROR]: {e}"

    def _ollama_chat(self, messages: list, model: Optional[str] = None, stream: bool = True) -> str:
        """Chat with Ollama using message history."""
        model = model or self.ollama_model
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "stream": stream
        }).encode()

        req = urllib.request.Request(
            f"{self.ollama_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            if stream:
                full_response = []
                with urllib.request.urlopen(req, timeout=120) as resp:
                    for line in resp:
                        line = line.decode().strip()
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("message", {}).get("content", "")
                            if token:
                                print(token, end="", flush=True)
                                full_response.append(token)
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
                print()
                return "".join(full_response)
            else:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode())
                    return data.get("message", {}).get("content", "").strip()
        except urllib.error.URLError as e:
            return f"[OLLAMA ERROR]: Cannot connect to Ollama at {self.ollama_url}. Is it running? ({e})"
        except Exception as e:
            return f"[OLLAMA ERROR]: {e}"

    def _ollama_list_models(self) -> list:
        """List available Ollama models."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []

    @classmethod
    def check_config(cls) -> str:
        """Check all provider availability."""
        adapter = llm_adapter
        parts = []

        if adapter.ollama_available:
            models = adapter._ollama_list_models()
            model_list = ", ".join(models[:5]) if models else "no models loaded"
            parts.append(f"Ollama: ACTIVE ({adapter.ollama_url}) — models: {model_list}")
        else:
            parts.append(f"Ollama: OFFLINE ({adapter.ollama_url}) — start with 'ollama serve'")

        if os.getenv("OPENAI_API_KEY"):
            parts.append("OpenAI: key found (dormant)")
        if os.getenv("ANTHROPIC_API_KEY"):
            parts.append("Anthropic: key found (dormant)")
        if os.getenv("OPENROUTER_API_KEY"):
            parts.append("OpenRouter: key found (dormant)")

        if not any([os.getenv("OPENAI_API_KEY"), os.getenv("ANTHROPIC_API_KEY"), os.getenv("OPENROUTER_API_KEY")]):
            parts.append("External LLMs: none configured (sovereign mode)")

        return " | ".join(parts)

    def activate(self, provider: str, config: Dict) -> bool:
        """Activate a specific LLM provider."""
        provider = provider.lower()

        if provider == "ollama":
            self.ollama_available = self._check_ollama()
            if self.ollama_available:
                self.current_provider = "ollama"
                self.is_active = True
                if "model" in config:
                    self.ollama_model = config["model"]
                print(f"\n✅ Ollama activated: {self.ollama_url} — model: {self.ollama_model}")
                return True
            else:
                print(f"\n❌ Ollama not available at {self.ollama_url}. Start it with 'ollama serve'")
                return False

        providers = ["openai", "anthropic", "openrouter"]
        if provider not in providers:
            print(f"❌ Unknown provider '{provider}'. Choose from: ollama, {', '.join(providers)}")
            return False

        self.current_provider = provider
        self.is_active = True
        print(f"\n✅ LLM adapter activated: {provider.upper()}")
        return True

    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate a response using the active provider."""
        # Ollama is the main engine — use it if available even without explicit activation
        if self.current_provider == "ollama" or (self.ollama_available and not self.is_active):
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            return self._ollama_generate(full_prompt)

        if not self.is_active:
            return (f"[CLAUDE]: No active LLM. Ollama is {'available' if self.ollama_available else 'offline'}. "
                    f"Use --llm=ollama to activate, or start Ollama with 'ollama serve'")

        return (f"[GENERATED RESPONSE VIA {self.current_provider.upper()}]:\n"
                f"Based on the provided context and instruction, the model generates a response.")


# Initialize the global adapter instance
llm_adapter = LLMAdapter()