"""Language detection from file extensions and content"""

from pathlib import Path
from typing import Optional, Dict


class LanguageDetector:
    """Detects programming language from file"""

    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.dart': 'dart',
        '.go': 'go',
        '.java': 'java',
        '.kt': 'kotlin',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cs': 'csharp',
        '.swift': 'swift',
    }

    FRAMEWORK_PATTERNS = {
        'python': {
            'django': ['django', 'from django', 'import django'],
            'flask': ['from flask', 'import flask', 'Flask('],
            'fastapi': ['from fastapi', 'import fastapi', 'FastAPI('],
        },
        'javascript': {
            'react': ['from react', 'import React', 'useState', 'useEffect'],
            'vue': ['from vue', 'import Vue', 'createApp'],
            'angular': ['@angular', 'import { Component }'],
            'next': ['from next', 'import Next'],
        },
        'dart': {
            'flutter': ['import \'package:flutter', 'import "package:flutter'],
        }
    }

    def detect_language(self, filepath: str) -> Optional[str]:
        """Detect language from file extension

        Args:
            filepath: Path to file

        Returns:
            Language name or None
        """
        ext = Path(filepath).suffix.lower()
        return self.LANGUAGE_MAP.get(ext)

    def detect_framework(self, filepath: str, content: str) -> Optional[str]:
        """Detect framework from file content

        Args:
            filepath: Path to file
            content: File content

        Returns:
            Framework name or None
        """
        language = self.detect_language(filepath)
        if not language:
            return None

        patterns = self.FRAMEWORK_PATTERNS.get(language, {})

        for framework, keywords in patterns.items():
            if any(keyword in content for keyword in keywords):
                return framework

        return None

    def get_language_info(self, filepath: str, content: str = "") -> Dict[str, Optional[str]]:
        """Get complete language information

        Args:
            filepath: Path to file
            content: File content (optional)

        Returns:
            Dict with language and framework
        """
        language = self.detect_language(filepath)
        framework = self.detect_framework(filepath, content) if content else None

        return {
            'language': language,
            'framework': framework
        }
