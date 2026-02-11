"""OpenRouter AI provider adapter"""

import os
import json
import time
import requests
from typing import List, Dict
from .base import AIProviderAdapter

_NO_API_KEY_MSG = "✗ No API key configured"
_CONTENT_TYPE = "application/json"
_HTTP_REFERER = "https://github.com/myusufkuncie/ai-reviewer"
_X_TITLE = "AI Code Reviewer"


class OpenRouterProvider(AIProviderAdapter):
    """Adapter for OpenRouter API"""

    def __init__(
        self,
        model: str = "z-ai/glm-4.5-air",
        max_tokens: int = 4000,
        temperature: float = 0.3,
    ):
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

    def _build_headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": _CONTENT_TYPE,
            "HTTP-Referer": _HTTP_REFERER,
            "X-Title": _X_TITLE,
        }

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
            print(_NO_API_KEY_MSG)
            return []

        try:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": context}],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            print("Calling OpenRouter API...")
            _t0 = time.time()
            response = requests.post(
                self.api_url,
                headers=self._build_headers(),
                json=data,
                timeout=(10, 120),
            )
            _api_elapsed = time.time() - _t0

            if response.status_code != 200:
                print(
                    f"✗ API returned status {response.status_code}"
                    f" (+{_api_elapsed:.2f}s)"
                )
                print(f"Response: {response.text[:200]}")
                return []

            result = response.json()
            review_text = result["choices"][0]["message"]["content"]

            # Extract JSON from response
            start = review_text.find("[")
            end = review_text.rfind("]") + 1

            if start >= 0 and end > start:
                comments = json.loads(review_text[start:end])
                print(
                    f"✓ Received {len(comments)} comments from AI"
                    f" (+{_api_elapsed:.2f}s)"
                )
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

    def review_batch(self, batch_context: str) -> List[Dict]:
        """Send a single API call covering multiple files (batch mode).

        Args:
            batch_context: Pre-built context string from
                ContextBuilder.build_batch_context()

        Returns:
            Flat list of review comments across all files in the batch
        """
        if not self.api_key:
            print(_NO_API_KEY_MSG)
            return []

        try:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": batch_context}],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            print("Calling OpenRouter API (batch)...")
            _t0 = time.time()
            response = requests.post(
                self.api_url,
                headers=self._build_headers(),
                json=data,
                timeout=(10, 120),
            )
            _api_elapsed = time.time() - _t0

            if response.status_code != 200:
                print(
                    f"✗ Batch API returned status {response.status_code}"
                    f" (+{_api_elapsed:.2f}s)"
                )
                print(f"Response: {response.text[:200]}")
                return []

            result = response.json()
            review_text = result["choices"][0]["message"]["content"]

            start = review_text.find("[")
            end = review_text.rfind("]") + 1

            if start >= 0 and end > start:
                comments = json.loads(review_text[start:end])
                print(
                    f"✓ Batch received {len(comments)} comments"
                    f" (+{_api_elapsed:.2f}s)"
                )
                return comments
            else:
                print("⚠ No valid JSON found in batch response")
                return []

        except requests.exceptions.RequestException as e:
            print(f"✗ Batch API request failed: {e}")
            return []

        except json.JSONDecodeError as e:
            print(f"✗ Failed to parse batch JSON response: {e}")
            return []

        except Exception as e:
            print(f"✗ Error during batch review: {e}")
            return []

    def verify_issue(self, verification_prompt: str) -> dict:
        """Verify a single issue with additional context

        Args:
            verification_prompt: Prompt with issue and evidence

        Returns:
            Verification result as dict
        """
        VERIFICATION_FAILED = "Verification failed - keeping issue"

        if not self.api_key:
            print(_NO_API_KEY_MSG)
            return {"confirmed": True, "reasoning": "Cannot verify - no API key"}

        try:
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": verification_prompt}
                ],
                "max_tokens": 1000,  # Shorter response for verification
                "temperature": 0.2,  # Lower temperature for consistency
            }

            print("Calling OpenRouter API (verify)...")
            _t0 = time.time()
            response = requests.post(
                self.api_url,
                headers=self._build_headers(),
                json=data,
                timeout=(10, 60),
            )
            _api_elapsed = time.time() - _t0
            print(f"  → Verify API response: +{_api_elapsed:.2f}s")

            if response.status_code != 200:
                print(
                    f"✗ Verification API returned status"
                    f" {response.status_code}"
                )
                return {"confirmed": True, "reasoning": VERIFICATION_FAILED}

            result = response.json()
            response_text = result["choices"][0]["message"]["content"]

            # Extract JSON from response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1

            if start >= 0 and end > start:
                verification_result = json.loads(response_text[start:end])
                return verification_result
            else:
                print("⚠ No valid JSON in verification response")
                return {
                    "confirmed": True,
                    "reasoning": "Could not parse verification",
                }

        except requests.exceptions.RequestException as e:
            print(f"✗ Verification API request failed: {e}")
            return {"confirmed": True, "reasoning": VERIFICATION_FAILED}

        except json.JSONDecodeError as e:
            print(f"✗ Failed to parse verification JSON: {e}")
            return {"confirmed": True, "reasoning": VERIFICATION_FAILED}

        except Exception as e:
            print(f"✗ Error during verification: {e}")
            return {"confirmed": True, "reasoning": VERIFICATION_FAILED}
