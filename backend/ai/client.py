"""
NILA Gemini Client Wrapper
Modern google-genai SDK wrapper with robust error handling and zero-secret guarantee.
Owned by: Gugaan
"""

import os
from typing import Optional
from google import genai


class GeminiClient:
    """
    Safe wrapper for the Google GenAI SDK.
    Handles authentication, generation, rate limits, and network errors gracefully.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3.8-flash"
    ):
        from backend.core.config import settings
        # Retrieve key strictly from parameter if provided, otherwise from environment or settings
        if api_key is not None:
            self.api_key = api_key.strip()
        else:
            self.api_key = (os.environ.get("GEMINI_API_KEY", "").strip() or settings.GEMINI_API_KEY)
        self.model_name = os.environ.get("GEMINI_MODEL", model_name)
        self._client: Optional[genai.Client] = None

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                self._client = None

    def is_available(self) -> bool:
        """Returns True if the client was initialized with an API key."""
        return self._client is not None and bool(self.api_key)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Optional[str]:
        """
        Generates grounded text response from Gemini.
        Returns None if generation fails or client is unavailable.
        """
        if not self.is_available() or self._client is None:
            return None

        try:
            config = {}
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config if config else None
            )
            if response and hasattr(response, "text") and response.text:
                return response.text.strip()
            return None
        except Exception:
            # Catch API errors, timeouts, or invalid keys without crashing backend
            return None
