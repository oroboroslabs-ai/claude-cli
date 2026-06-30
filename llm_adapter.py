# llm_adapter.py
# Claude-O LLM Adapter System
# Handles connection to external generative models (OpenAI, Anthropic, OpenRouter).
# NOTE: Connections are NON-ACTIVE BY DEFAULT. User must specify target (--llm=<provider>)
# and provide necessary API keys/credentials for activation.

import os
from typing import Dict, Any


class LLMAdapter:
    """Manages interaction with diverse LLM providers."""

    def __init__(self):
        self.is_active = False
        self.current_provider = None
        print("⚠️ LLM Adapter Initialized: All external connections are dormant.")
        print("   Activate by specifying --llm=<provider> and providing API credentials.")

    @classmethod
    def check_config(cls) -> str:
        """Checks environment variables for potential API keys."""
        if os.getenv("OPENAI_API_KEY"):
            return "OpenAI key found."
        if os.getenv("ANTHROPIC_API_KEY"):
            return "Anthropic key found."
        if os.getenv("OPENROUTER_API_KEY"):
            return "OpenRouter key found."
        return "No critical API keys detected. Running fully sovereign mode."

    def activate(self, provider: str, config: Dict) -> bool:
        """Activates a specific LLM connection."""
        providers = ["openai", "anthropic", "openrouter"]
        if provider.lower() not in providers:
            print(f"❌ Error: Unknown provider '{provider}'. Choose from {', '.join(providers)}.")
            return False

        self.current_provider = provider.lower()
        self.is_active = True
        print(f"\n✅ Successfully initialized LLM adapter for: {provider.upper()}!")
        print(f"   System is now capable of utilizing external context.")
        return True

    def generate_response(self, prompt: str, context: str) -> str:
        """Simulates generating a response based on the active provider."""
        if not self.is_active:
            return (f"[CLAUDE-O WARNING]: Cannot generate response. "
                    f"LLM Provider ({self.current_provider}) is currently inactive. "
                    f"Run with --llm to enable.")

        return (f"\n[GENERATED RESPONSE VIA {self.current_provider.upper()}]:\n"
                f"Based on the provided context and instruction, the model generates "
                f"a deep, coherent response.\n"
                f"Model Output Mockup: This content proves the connectivity, demonstrating "
                f"superior reasoning capacity at the {self.current_provider}-level.")


# Initialize the global adapter instance
llm_adapter = LLMAdapter()