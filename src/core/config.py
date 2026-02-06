"""Configuration management for AI Code Reviewer"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any


class ConfigLoader:
    """Loads and manages configuration from .ai-review-config.json"""

    DEFAULT_CONFIG = {
        "enabled": True,
        "ai_provider": "openrouter",
        "model": "anthropic/claude-sonnet-4.5",
        "max_tokens": 4000,
        "temperature": 0.3,
        "language_specific": {},
        "exclusions": {
            "directories": [
                "node_modules", "vendor", "dist", "build", ".git",
                "__pycache__", ".pytest_cache", "coverage", "venv",
                "env", ".venv", "migrations", "target", "bin", "obj"
            ],
            "file_prefixes": [
                "test_", "_test", ".min.", "bundle.", "vendor.",
                "legacy_", "deprecated_"
            ],
            "file_patterns": [
                "*.lock", "*.log", "*.pyc", "*.pyo", "*.so", "*.dylib",
                "*.dll", "*.exe", "*.o", "*.a", "package-lock.json",
                "yarn.lock", "poetry.lock", "Pipfile.lock", "Gemfile.lock",
                "*.min.js", "*.min.css", "*.map"
            ]
        },
        "review_settings": {
            "severity_threshold": "minor",
            "auto_approve_minor": False,
            "require_tests": True,
            "check_security": True,
            "check_performance": True,
            "max_comments_per_file": 10
        },
        "comment_settings": {
            "style": "detailed",
            "include_examples": True,
            "include_references": True
        },
        "cache_settings": {
            "enabled": True,
            "ttl_days": 7,
            "cache_location": ".review_cache"
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize config loader

        Args:
            config_path: Path to config file. If None, looks for .ai-review-config.json
        """
        self.config_path = config_path or ".ai-review-config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        config = self.DEFAULT_CONFIG.copy()

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    custom_config = json.load(f)
                    config = self._merge_configs(config, custom_config)
                    print(f"✓ Loaded config from {self.config_path}")
            except json.JSONDecodeError as e:
                print(f"⚠ Invalid JSON in {self.config_path}: {e}")
                print("Using default configuration")
            except Exception as e:
                print(f"⚠ Error loading config: {e}")
                print("Using default configuration")
        else:
            print(f"⚠ Config file not found: {self.config_path}")
            print("Using default configuration")

        return config

    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Recursively merge custom config into default config"""
        result = default.copy()

        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def is_enabled(self) -> bool:
        """Check if reviewer is enabled"""
        return self.get('enabled', True)

    def get_exclusions(self) -> Dict:
        """Get exclusion rules"""
        return self.get('exclusions', {})

    def get_language_config(self, language: str) -> Dict:
        """Get language-specific configuration"""
        return self.get(f'language_specific.{language}', {})

    def get_ai_provider(self) -> str:
        """Get AI provider name"""
        return self.get('ai_provider', 'openrouter')

    def get_model(self) -> str:
        """Get AI model name"""
        return self.get('model', 'anthropic/claude-sonnet-4.5')

    def get_review_settings(self) -> Dict:
        """Get review settings"""
        return self.get('review_settings', {})

    def get_cache_settings(self) -> Dict:
        """Get cache settings"""
        return self.get('cache_settings', {})
