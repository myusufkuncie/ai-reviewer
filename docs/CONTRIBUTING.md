# Contributing to AI Code Reviewer

Thank you for considering contributing to AI Code Reviewer! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, platform)
- Relevant logs or error messages

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature has already been requested
- Describe the use case clearly
- Explain why this feature would be useful
- Provide examples if possible

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/myusufkuncie/ai-reviewer.git
   cd ai-reviewer
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the coding style (PEP 8 for Python)
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   pytest tests/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: your feature description"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Setup

### Prerequisites
- Python 3.8+
- Git
- pip

### Installation

```bash
# Clone repository
git clone https://github.com/myusufkuncie/ai-reviewer.git
cd ai-reviewer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_reviewer tests/

# Run specific test
pytest tests/test_context_builder.py
```

### Code Style

We follow PEP 8 with some exceptions:
- Line length: 100 characters
- Use double quotes for strings

```bash
# Format code
black src/

# Check style
flake8 src/

# Type checking
mypy src/
```

## Project Structure

```
ai-reviewer/
├── src/
│   ├── core/                # Core business logic
│   ├── adapters/            # Platform & AI integrations
│   ├── analyzers/           # Code analysis
│   └── utils/               # Utility functions
├── main_gitlab.py           # GitLab entry point
├── main_github.py           # GitHub entry point
├── docs/                    # Documentation
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   └── ...
├── templates/
│   ├── github-actions/      # GitHub workflow templates
│   └── gitlab-ci/           # GitLab CI templates
├── tests/                   # Test files
└── README.md                # User documentation
```

## Adding New Language Support

To add support for a new programming language:

1. **Add language detection** in `src/analyzers/language_detector.py`
2. **Add import/function extraction** patterns
3. **Add language-specific rules** in configuration
4. **Create template workflow** in `templates/`
5. **Update documentation** in README.md
6. **Add tests** for the new language

Example:

```python
# In src/analyzers/language_detector.py
LANGUAGE_MAP = {
    # ... existing mappings
    '.rb': 'ruby',
}

FRAMEWORK_PATTERNS = {
    'ruby': {
        'rails': ['ActiveRecord::Base', 'ActionController'],
    }
}
```

## Adding New AI Provider

To add a new AI provider:

1. **Create provider adapter** in `src/adapters/`
2. **Extend base class** `AIProviderAdapter`
3. **Implement API call logic**
4. **Add error handling**
5. **Update documentation**

Example:

```python
# src/adapters/my_provider.py
from .base import AIProviderAdapter

class MyProvider(AIProviderAdapter):
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def review(self, context: str) -> List[Dict]:
        # Implement provider-specific API call
        pass

    def test_connection(self) -> bool:
        # Test API connection
        pass
```

## Coding Guidelines

### General
- Write clear, self-documenting code
- Add docstrings for functions and classes
- Keep functions small and focused
- Use type hints where appropriate

### Error Handling
- Always handle exceptions gracefully
- Log errors with context
- Provide helpful error messages
- Don't swallow exceptions silently

### Testing
- Write tests for new features
- Maintain test coverage above 80%
- Use meaningful test names
- Test edge cases and error conditions

### Documentation
- Update README for user-facing changes
- Update docstrings for code changes
- Add comments for complex logic
- Keep examples up to date

## Commit Message Guidelines

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(github): add GitHub Actions support
fix(cache): resolve cache invalidation bug
docs(readme): update configuration examples
```

## Review Process

1. **Automated checks**: CI runs tests and linters
2. **Code review**: Maintainer reviews code
3. **Feedback**: Address review comments
4. **Approval**: Maintainer approves PR
5. **Merge**: PR merged to main branch

## Community

- Be respectful and professional
- Help others when you can
- Share your knowledge
- Give credit where due

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion in GitHub Discussions
- Reach out to maintainers

Thank you for contributing!
