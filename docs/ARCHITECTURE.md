# Modular Architecture Documentation

## Overview

The AI Code Reviewer has been refactored into a modular, maintainable architecture with clear separation of concerns.

## Directory Structure

```
ai-reviewer/
├── src/
│   ├── __init__.py
│   ├── core/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── cache.py           # Caching system
│   │   └── reviewer.py        # Main review orchestrator
│   │
│   ├── adapters/               # External service adapters
│   │   ├── __init__.py
│   │   ├── base.py            # Base adapter classes
│   │   ├── gitlab_adapter.py  # GitLab integration
│   │   ├── github_adapter.py  # GitHub integration
│   │   └── openrouter_provider.py  # OpenRouter AI
│   │
│   ├── analyzers/              # Code analysis
│   │   ├── __init__.py
│   │   ├── language_detector.py  # Language detection
│   │   └── context_builder.py    # Context building
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── file_utils.py      # File operations
│
├── main_gitlab.py              # GitLab entry point
├── main_github.py              # GitHub entry point
└── requirements.txt
```

## Module Descriptions

### Core Modules (`src/core/`)

#### config.py - ConfigLoader
**Purpose**: Load and manage configuration from `.ai-review-config.json`

**Key Features**:
- Default configuration fallback
- Recursive config merging
- Dot notation access (`config.get('review_settings.severity_threshold')`)
- Language-specific settings
- Exclusion rules

**Usage**:
```python
config = ConfigLoader()
model = config.get_model()
exclusions = config.get_exclusions()
```

#### cache.py - CacheManager
**Purpose**: Cache review results to reduce API costs

**Key Features**:
- MD5-based cache keys
- TTL-based expiration
- Automatic cleanup
- File-based storage

**Usage**:
```python
cache = CacheManager(cache_dir=".review_cache", ttl_days=7)
cached = cache.get(cache_key)
if not cached:
    result = expensive_operation()
    cache.set(cache_key, result)
```

#### reviewer.py - CodeReviewer
**Purpose**: Orchestrate the review process

**Key Features**:
- Platform-agnostic review logic
- Exclusion filtering
- Statistics tracking
- Comment aggregation

**Usage**:
```python
reviewer = CodeReviewer(
    platform_adapter=platform,
    ai_provider=ai_provider,
    context_builder=context_builder
)
stats = reviewer.review_pull_request(pr_id)
```

### Adapter Modules (`src/adapters/`)

#### base.py - Base Classes
**Purpose**: Define interfaces for platform and AI adapters

**Classes**:
- `PlatformAdapter`: Abstract base for GitHub/GitLab
- `AIProviderAdapter`: Abstract base for AI providers

**Benefits**:
- Easy to add new platforms
- Consistent interface
- Type safety

#### gitlab_adapter.py - GitLabAdapter
**Purpose**: GitLab API integration

**Key Methods**:
- `authenticate()`: Connect to GitLab
- `get_changes()`: Fetch MR changes
- `post_comments()`: Post review comments
- `post_summary()`: Post summary comment

#### github_adapter.py - GitHubAdapter
**Purpose**: GitHub API integration

**Key Methods**:
- `authenticate()`: Connect to GitHub
- `get_changes()`: Fetch PR changes
- `post_comments()`: Post review comments
- `post_summary()`: Post summary comment

#### openrouter_provider.py - OpenRouterProvider
**Purpose**: OpenRouter AI API integration

**Key Methods**:
- `review()`: Get AI review for context
- `test_connection()`: Verify API access

### Analyzer Modules (`src/analyzers/`)

#### language_detector.py - LanguageDetector
**Purpose**: Detect language and framework from files

**Key Features**:
- Extension-based detection
- Content-based framework detection
- Support for 15+ languages

**Usage**:
```python
detector = LanguageDetector()
lang_info = detector.get_language_info('app.py', content)
# Returns: {'language': 'python', 'framework': 'django'}
```

#### context_builder.py - ContextBuilder
**Purpose**: Build comprehensive context for AI review

**Key Features**:
- File before/after comparison
- Language-specific instructions
- Diff formatting
- Framework-aware prompts

## Design Patterns

### 1. Adapter Pattern
Used for platform (GitHub/GitLab) and AI provider integration:
```python
class PlatformAdapter(ABC):
    @abstractmethod
    def get_changes(self, pr_id: str) -> List[Dict]:
        pass
```

### 2. Strategy Pattern
Different review strategies for different languages:
```python
lang_info = language_detector.get_language_info(filepath)
context = context_builder.build_context(lang_info)
```

### 3. Dependency Injection
Components are injected rather than hardcoded:
```python
reviewer = CodeReviewer(
    platform_adapter=platform,  # Injected
    ai_provider=ai_provider,    # Injected
    context_builder=context     # Injected
)
```

## Data Flow

```
1. main_gitlab.py / main_github.py
   ↓
2. Initialize ConfigLoader
   ↓
3. Initialize PlatformAdapter (GitLab/GitHub)
   ↓
4. Authenticate with platform
   ↓
5. Initialize AIProvider (OpenRouter)
   ↓
6. Initialize ContextBuilder
   ↓
7. Initialize CacheManager
   ↓
8. Create CodeReviewer with dependencies
   ↓
9. CodeReviewer.review_pull_request(pr_id)
   ├─ Get changes from platform
   ├─ For each file:
   │  ├─ Check exclusions
   │  ├─ Check cache
   │  ├─ Build context
   │  ├─ Get AI review
   │  └─ Cache result
   ├─ Post comments to platform
   └─ Post summary to platform
   ↓
10. Return statistics
```

## Adding New Features

### Add New Platform (e.g., Bitbucket)

1. Create `src/adapters/bitbucket_adapter.py`:
```python
from .base import PlatformAdapter

class BitbucketAdapter(PlatformAdapter):
    def authenticate(self) -> bool:
        # Implement
        pass

    def get_changes(self, pr_id: str) -> List[Dict]:
        # Implement
        pass

    # ... other methods
```

2. Create `main_bitbucket.py`:
```python
from src.adapters import BitbucketAdapter

platform = BitbucketAdapter()
# ... rest of setup
```

### Add New AI Provider (e.g., Anthropic Direct)

1. Create `src/adapters/anthropic_provider.py`:
```python
from .base import AIProviderAdapter

class AnthropicProvider(AIProviderAdapter):
    def review(self, context: str) -> List[Dict]:
        # Call Anthropic API directly
        pass
```

2. Update main files to support provider selection:
```python
provider_name = config.get_ai_provider()
if provider_name == "openrouter":
    ai_provider = OpenRouterProvider(...)
elif provider_name == "anthropic":
    ai_provider = AnthropicProvider(...)
```

### Add New Language Support

1. Update `src/analyzers/language_detector.py`:
```python
LANGUAGE_MAP = {
    # ... existing
    '.scala': 'scala',
}

FRAMEWORK_PATTERNS = {
    'scala': {
        'play': ['import play.api'],
        'akka': ['import akka.actor'],
    }
}
```

2. Update language-specific prompts in `context_builder.py`

## Testing

### Unit Tests Structure
```
tests/
├── test_core/
│   ├── test_config.py
│   ├── test_cache.py
│   └── test_reviewer.py
├── test_adapters/
│   ├── test_gitlab_adapter.py
│   ├── test_github_adapter.py
│   └── test_openrouter.py
└── test_analyzers/
    ├── test_language_detector.py
    └── test_context_builder.py
```

### Running Tests
```bash
# Install dev dependencies
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific module
pytest tests/test_core/test_config.py
```

## Migration Guide

### From Old ai_reviewer.py

**Old**:
```python
# Monolithic class
reviewer = AICodeReviewer()
reviewer.post_review()
```

**New**:
```python
# Modular components
from src.core import ConfigLoader, CodeReviewer
from src.adapters import GitLabAdapter, OpenRouterProvider
from src.analyzers import ContextBuilder

config = ConfigLoader()
platform = GitLabAdapter()
ai_provider = OpenRouterProvider()
context_builder = ContextBuilder(platform, config)

reviewer = CodeReviewer(platform, ai_provider, context_builder)
reviewer.review_pull_request(mr_iid)
```

## Benefits of Modular Architecture

1. **Separation of Concerns**: Each module has a single responsibility
2. **Testability**: Easy to unit test individual components
3. **Extensibility**: Add new platforms/providers without changing core
4. **Maintainability**: Changes isolated to specific modules
5. **Reusability**: Components can be used independently
6. **Type Safety**: Clear interfaces with abstract base classes

## Configuration Examples

### Minimal Setup
```json
{
  "enabled": true,
  "model": "anthropic/claude-sonnet-4.5"
}
```

### Full Setup
```json
{
  "enabled": true,
  "ai_provider": "openrouter",
  "model": "anthropic/claude-sonnet-4.5",
  "max_tokens": 4000,
  "temperature": 0.3,
  "exclusions": {
    "directories": ["node_modules"],
    "file_patterns": ["*.lock"]
  },
  "cache_settings": {
    "enabled": true,
    "ttl_days": 7
  }
}
```

## Future Improvements

- [ ] Add async/await for parallel file reviews
- [ ] Implement distributed caching (Redis)
- [ ] Add more AI providers (Anthropic, OpenAI, Gemini)
- [ ] Plugin system for custom analyzers
- [ ] Web dashboard for analytics
- [ ] GraphQL API for integrations

---

**Version**: 2.0.0
**Last Updated**: 2026-02-06
