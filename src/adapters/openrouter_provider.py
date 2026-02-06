"""OpenRouter AI provider adapter"""

import os
import json
import requests
from typing import List, Dict
from .base import AIProviderAdapter


class OpenRouterProvider(AIProviderAdapter):
    """Adapter for OpenRouter API"""

    def __init__(self, model: str = "anthropic/claude-sonnet-4.5", max_tokens: int = 4000, temperature: float = 0.3):
        """Initialize OpenRouter provider

        Args:
            model: Model name
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        print(f"✓ OpenRouter configured with model: {self.model}")

        if not self.api_key:
            print("✗ OPENROUTER_API_KEY not set!")

    def test_connection(self) -> bool:
        """Test connection to OpenRouter"""
        if not self.api_key:
            return False

        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"✗ Connection test failed: {e}")
            return False

    def review(self, context: str) -> List[Dict]:
        """Get AI review for context

        Args:
            context: Review context

        Returns:
            List of review comments
        """
        if not self.api_key:
            print("✗ No API key configured")
            return []

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/ai-reviewer",
                "X-Title": "AI Code Reviewer",
            }

            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": context}],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            print(f"Calling OpenRouter API...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=120
            )

            if response.status_code != 200:
                print(f"✗ API returned status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return []

            result = response.json()
            review_text = result["choices"][0]["message"]["content"]

            # Extract JSON from response
            start = review_text.find("[")
            end = review_text.rfind("]") + 1

            if start >= 0 and end > start:
                comments = json.loads(review_text[start:end])
                print(f"✓ Received {len(comments)} comments from AI")
                return comments
            else:
                print("⚠ No valid JSON found in response")
                return []

        except requests.exceptions.RequestException as e:
            print(f"✗ API request failed: {e}")
            return []

        except json.JSONDecodeError as e:
            print(f"✗ Failed to parse JSON response: {e}")
            return []

        except Exception as e:
            print(f"✗ Error during review: {e}")
            return []
