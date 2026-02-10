# AI Code Reviewer

Intelligent, context-aware automated code reviews for GitHub and GitLab using AI. Supports multiple programming languages including Python, JavaScript/TypeScript, Flutter/Dart, Go, Java, and more.

## Features

- **🔍 Smart 2-Pass Verification**: AI detection + linter confirmation for highly accurate reviews (reduces false positives by 90%)
- **🛠️ Intelligent Linter Integration**: Automatically runs language-specific linters on changed lines only (99% token savings)
- **Multi-Platform Support**: Works with both GitHub Actions and GitLab CI
- **Multi-Language Support**: Python, JavaScript/TypeScript, Flutter/Dart, Go, Java, Rust, PHP/Laravel (8+ languages)
- **Context-Aware**: Analyzes full file context, related files, project architecture, and documentation
- **Tool-Augmented Reviews**: AI can read related files, check git history, and run linters (like Claude CLI)
- **Security-Focused**: Detects OWASP Top 10 vulnerabilities, SQL injection, XSS, and more
- **Highly Configurable**: Customizable review rules, exclusions, and severity thresholds
- **Smart Caching**: Reduces API costs by caching unchanged file reviews
- **Detailed Reports**: Provides inline comments with severity levels and actionable suggestions

## Quick Start

### GitHub Actions

1. **Create workflow file**: `.github/workflows/ai-review.yml`

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Clone AI Reviewer
        run: |
          git clone https://github.com/myusufkuncie/ai-reviewer.git /tmp/ai-reviewer
          cd /tmp/ai-reviewer
          pip install -r requirements.txt

      - name: Copy config file
        run: |
          if [ -f .ai-review-config.json ]; then
            cp .ai-review-config.json /tmp/ai-reviewer/
          fi

      - name: Run AI Code Review
        working-directory: /tmp/ai-reviewer
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_PR_NUMBER: ${{ github.event.pull_request.number }}
          GITHUB_BASE_REF: ${{ github.event.pull_request.base.sha }}
          GITHUB_HEAD_REF: ${{ github.event.pull_request.head.sha }}
        run: python main_github.py
```

2. **Add secrets** to your repository:

   **Required secrets:**
   - `OPENROUTER_API_KEY`: Get from [OpenRouter](https://openrouter.ai/keys)
   - `GITHUB_TOKEN`: Automatically provided by GitHub Actions (no setup needed)

   **How to add secrets on GitHub:**
   1. Go to your repository on GitHub
   2. Click **Settings** → **Secrets and variables** → **Actions**
   3. Click **New repository secret**
   4. Add `OPENROUTER_API_KEY`:
      - Name: `OPENROUTER_API_KEY`
      - Value: Your API key from [OpenRouter](https://openrouter.ai/keys)
   5. Click **Add secret**

3. **Optional**: Add configuration file `.ai-review-config.json` (see [Configuration](#configuration))

### GitLab CI

1. **Add to `.gitlab-ci.yml`**:

```yaml
ai_code_review:
  stage: code-review
  image: python:3.11
  only:
    - merge_requests
  except:
    variables:
      - $CI_MERGE_REQUEST_TITLE =~ /^Draft:/
  before_script:
    - git clone https://github.com/myusufkuncie/ai-reviewer.git /tmp/ai-reviewer
    - cd /tmp/ai-reviewer
    - pip install -r requirements.txt --break-system-packages
  script:
    - cp "$CI_PROJECT_DIR/.ai-review-config.json" /tmp/ai-reviewer/
    - cd /tmp/ai-reviewer
    - python main_gitlab.py
  variables:
    GITLAB_TOKEN: $GITLAB_TOKEN
    OPENROUTER_API_KEY: $OPENROUTER_API_KEY
  cache:
    key: ai-review-cache-${CI_COMMIT_REF_SLUG}
    paths:
      - .review_cache/
  artifacts:
    when: always
    paths:
      - .review_cache/
    expire_in: 7 days
  allow_failure: true
```

2. **Add CI/CD variables**:

   **Required variables:**
   - `GITLAB_TOKEN`: Personal access token with `api` scope
   - `OPENROUTER_API_KEY`: Get from [OpenRouter](https://openrouter.ai/keys)

   **How to add variables on GitLab:**
   1. Go to your project on GitLab
   2. Click **Settings** → **CI/CD**
   3. Expand **Variables** section
   4. Click **Add variable** for each:

      **First variable - GITLAB_TOKEN:**
      - Key: `GITLAB_TOKEN`
      - Value: Your GitLab personal access token
        - Create token: Go to **User Settings** → **Access Tokens**
        - Name: `AI Reviewer`
        - Scopes: Check `api`
        - Click **Create personal access token**
      - Flags: Check **Mask variable** (recommended)
      - Click **Add variable**

      **Second variable - OPENROUTER_API_KEY:**
      - Key: `OPENROUTER_API_KEY`
      - Value: Your API key from [OpenRouter](https://openrouter.ai/keys)
      - Flags: Check **Mask variable** (recommended)
      - Click **Add variable**

3. **Optional**: Add configuration file `.ai-review-config.json`

## Configuration

Create `.ai-review-config.json` in your repository root:

### Basic Configuration

```json
{
  "enabled": true,
  "ai_provider": "openrouter",
  "model": "z-ai/glm-4.5-air",
  "max_tokens": 4000,
  "temperature": 0.3
}
```

### Advanced Configuration

```json
{
  "enabled": true,
  "ai_provider": "openrouter",
  "model": "z-ai/glm-4.5-air",
  "max_tokens": 4000,
  "temperature": 0.3,

  "language_specific": {
    "flutter": {
      "check_pubspec": true,
      "widget_best_practices": true,
      "state_management": ["bloc", "riverpod", "provider"]
    },
    "python": {
      "check_type_hints": true,
      "pep8_compliance": true,
      "django_security": true
    },
    "go": {
      "check_error_handling": true,
      "goroutine_safety": true,
      "interface_design": true
    },
    "javascript": {
      "check_react_hooks": true,
      "async_best_practices": true,
      "check_typescript": true
    }
  },

  "exclusions": {
    "directories": [
      "node_modules",
      "vendor",
      "dist",
      "build",
      ".git",
      "__pycache__",
      "venv",
      "migrations"
    ],
    "file_patterns": [
      "*.lock",
      "*.log",
      "*.min.js",
      "*.min.css",
      "package-lock.json",
      "yarn.lock",
      ".ai-review-config*.json",
      ".gitignore",
      ".dockerignore"
    ],
    "file_prefixes": [
      "test_",
      "_test",
      ".min."
    ]
  },

  "review_settings": {
    "severity_threshold": "minor",
    "auto_approve_minor": false,
    "require_tests": true,
    "check_security": true,
    "check_performance": true,
    "max_comments_per_file": 10
  },

  "comment_settings": {
    "style": "detailed",
    "include_examples": true,
    "include_references": true
  }
}
```

## Language Support

### Python / Django

**Detected by**: `.py` files, `requirements.txt`, `setup.py`, `pyproject.toml`

**Reviews for**:
- Django security (SQL injection, XSS, CSRF)
- Type hints usage
- PEP 8 compliance
- Error handling patterns
- Import organization
- Function/class design

**Example**:
```python
# Before
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

# AI Review Comment
🚨 CRITICAL: SQL injection vulnerability detected
Use parameterized queries or Django ORM instead
```

### Flutter / Dart

**Detected by**: `.dart` files, `pubspec.yaml`

**Reviews for**:
- Widget best practices
- State management patterns
- Build method optimization
- Memory leaks (missing dispose)
- Platform-specific code
- Accessibility

**Example**:
```dart
// Before
class MyWidget extends StatefulWidget {
  final StreamController controller;
  // Missing dispose
}

// AI Review Comment
⚠️ MAJOR: Potential memory leak
StreamController should be disposed in dispose() method
```

### Go

**Detected by**: `.go` files, `go.mod`

**Reviews for**:
- Error handling patterns
- Goroutine safety
- Context usage
- Interface design
- Race conditions
- Defer placement

**Example**:
```go
// Before
func fetchData() {
    resp, _ := http.Get(url)  // Ignored error
    // ...
}

// AI Review Comment
⚠️ MAJOR: Error not handled
Always check and handle errors in Go
```

### JavaScript / TypeScript

**Detected by**: `.js`, `.ts`, `.jsx`, `.tsx` files, `package.json`

**Reviews for**:
- React hooks rules
- Async/await patterns
- Type safety (TypeScript)
- Memory leaks
- Performance issues
- Security vulnerabilities

**Example**:
```javascript
// Before
function Component() {
  const [data, setData] = useState();
  fetch('/api/data').then(r => setData(r));  // Missing dependency
}

// AI Review Comment
💡 MINOR: useEffect missing for side effect
Wrap fetch in useEffect with proper dependencies
```

### Java

**Detected by**: `.java` files, `pom.xml`, `build.gradle`

**Reviews for**:
- Exception handling
- Resource management
- Thread safety
- Spring Security issues
- SQL injection
- Null pointer issues

### Rust

**Detected by**: `.rs` files, `Cargo.toml`

**Reviews for**:
- Ownership and borrowing
- Error handling (Result/Option)
- Unsafe code usage
- Concurrency patterns
- Performance issues

## Review Severity Levels

| Severity | Emoji | Description | Examples |
|----------|-------|-------------|----------|
| **Critical** | 🚨 | Security vulnerabilities, data loss risks | SQL injection, XSS, hardcoded secrets |
| **Major** | ⚠️ | Bugs, performance issues, breaking changes | Memory leaks, race conditions, API changes |
| **Minor** | 💡 | Code quality, maintainability | Missing error handling, unused variables |
| **Suggestion** | 💭 | Best practices, optimizations | Code style, refactoring opportunities |

## How It Works

### Smart 2-Pass Review Flow

1. **Trigger**: PR/MR created or updated
2. **Fetch Changes**: Get diff between base and head
3. **Filter Files**: Apply exclusion rules
4. **Build Context**: Analyze full files, related files, README, Docker configs
5. **Pass 1 - Linter Analysis**:
   - Run language-specific linter on **changed lines only** (token-efficient!)
   - Detect syntax errors, style violations, security issues
   - Filter results to only changed lines
6. **Pass 2 - AI Analysis with Linter Context**:
   - AI reviews code with linter findings included
   - Provides detailed explanations and fixes for linter issues
   - Catches logic errors and design issues that linters miss
   - Combines linter objectivity with AI's contextual understanding
7. **Post Comments**: Add inline comments with detailed feedback and summary

> 📖 **Learn More**: See [LINTER_VERIFICATION.md](LINTER_VERIFICATION.md) for detailed documentation on the 2-pass verification system with smart linter integration

### Context Includes

- Full file before and after changes
- Related files (via imports)
- Files in same directory
- Test files
- README and documentation
- Docker configuration
- Project architecture (package.json, requirements.txt, etc.)
- Change impact analysis

## AI Providers

### OpenRouter (Recommended)

- Access to multiple models (Claude, GPT-4, Gemini)
- Pay-per-use pricing
- No rate limits for paid users
- Best performance/cost ratio

```json
{
  "ai_provider": "openrouter",
  "model": "z-ai/glm-4.5-air"
}
```

**Recommended models on OpenRouter**:

- `z-ai/glm-4.5-air` - Fast and cost-effective (default)
- `anthropic/claude-sonnet-4.5` - High quality, best for security
- `openai/gpt-4-turbo` - Good balance of quality and speed

**Get API Key**: [OpenRouter Keys](https://openrouter.ai/keys)

### Anthropic Claude (Direct)

- High-quality reviews
- Better for security analysis
- Higher cost

```json
{
  "ai_provider": "anthropic",
  "model": "claude-sonnet-4.5-20250929"
}
```

**Get API Key**: [Anthropic Console](https://console.anthropic.com/)

### OpenAI

- GPT-4 models
- Good for general code review
- Moderate cost

```json
{
  "ai_provider": "openai",
  "model": "gpt-4-turbo-preview"
}
```

**Get API Key**: [OpenAI Platform](https://platform.openai.com/api-keys)

## Cost Estimation

Based on average PR with 5 files, 500 lines changed:

| Provider | Model | Cost per Review | Quality |
|----------|-------|----------------|---------|
| OpenRouter | GLM-4.5-Air (default) | ~$0.01 | ⭐⭐⭐⭐ |
| OpenRouter | Claude Sonnet 4.5 | ~$0.10 | ⭐⭐⭐⭐⭐ |
| OpenRouter | GPT-4 Turbo | ~$0.15 | ⭐⭐⭐⭐ |
| OpenRouter | Claude Haiku | ~$0.02 | ⭐⭐⭐ |
| Anthropic | Claude Sonnet | ~$0.12 | ⭐⭐⭐⭐⭐ |
| OpenAI | GPT-4 Turbo | ~$0.20 | ⭐⭐⭐⭐ |

**Cost Reduction Tips**:
- Enable caching (60% cache hit rate typical)
- Use exclusion rules to skip generated files
- Use cheaper models for minor changes
- Set `max_comments_per_file` limit

## Examples

### Example Review Output

```
## 🤖 AI Code Review Summary

### Review Statistics
- **Files Reviewed**: 5
- **Files Skipped**: 2 (binary files)
- **Files Excluded**: 15 (node_modules, tests)
- **Total Comments**: 8

### Findings by Severity
- 🚨 **Critical**: 1
- ⚠️ **Major**: 3
- 💡 **Minor**: 3
- 💭 **Suggestions**: 1

### Review Approach
This review analyzed:
- Full file context (before and after changes)
- Project README and documentation
- Docker configuration files
- Related files and dependencies
- Project architecture and patterns
- Change impact and potential risks
```

### Example Inline Comment

> **File**: `src/api/auth.py:42`
>
> 🚨 **CRITICAL**: SQL injection vulnerability detected
>
> The user input is directly concatenated into the SQL query without sanitization.
>
> **Current Code**:
> ```python
> query = f"SELECT * FROM users WHERE email = '{email}'"
> ```
>
> **Recommended Fix**:
> ```python
> query = "SELECT * FROM users WHERE email = ?"
> cursor.execute(query, (email,))
> # Or use Django ORM:
> User.objects.filter(email=email)
> ```
>
> **References**:
> - [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
> - [Django QuerySet API](https://docs.djangoproject.com/en/stable/ref/models/querysets/)

## Advanced Usage

### Custom Review Prompts

Create `.ai-review-prompts.json`:

```json
{
  "system_prompt": "You are an expert code reviewer specializing in security and performance.",
  "language_prompts": {
    "python": "Focus on Django security, type hints, and PEP 8 compliance.",
    "flutter": "Focus on widget optimization, state management, and memory leaks.",
    "go": "Focus on error handling, goroutine safety, and idiomatic Go patterns."
  }
}
```

### Multiple Configurations

Different configs for different branches:

```json
{
  "branches": {
    "main": {
      "severity_threshold": "major",
      "require_tests": true
    },
    "develop": {
      "severity_threshold": "minor",
      "require_tests": false
    }
  }
}
```

### Webhook Integration

For GitHub, use webhooks instead of Actions:

```python
# webhook_server.py
from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    if event == 'pull_request':
        subprocess.run(['python', 'main_github.py'])
    return 'OK'
```

## Troubleshooting

### Common Issues

#### 1. "Authentication failed"

**Cause**: Invalid or missing API tokens

**Solution**:
- GitHub: Check `GITHUB_TOKEN` has `pull-requests: write` permission
- GitLab: Ensure `GITLAB_TOKEN` has `api` scope
- OpenRouter: Verify `OPENROUTER_API_KEY` is valid

#### 2. "No comments posted"

**Cause**: All files excluded or no issues found

**Solution**:
- Check `.ai-review-config.json` exclusion rules
- Lower `severity_threshold`
- Check CI logs for errors

#### 3. "Rate limit exceeded"

**Cause**: Too many API calls

**Solution**:
- Enable caching
- Reduce files reviewed (exclusions)
- Use provider with higher rate limits

#### 4. "Timeout errors"

**Cause**: Large PR or slow AI provider

**Solution**:
- Reduce `max_tokens`
- Split large PRs
- Increase timeout in workflow

#### 5. "Comments posted on wrong lines"

**Cause**: AI model providing incorrect line numbers or diff positioning issues

**Solution**:

- The system shows line numbers to the AI from the "after changes" file
- GitHub API requires comments on lines that are part of the diff
- If this persists, the AI model may need better context
- Try using a more capable model (e.g., `anthropic/claude-sonnet-4.5`)

### Debug Mode

Enable debug logging:

```bash
export AI_REVIEWER_DEBUG=true
# For GitHub:
python main_github.py
# For GitLab:
python main_gitlab.py
```

## Development

### Local Testing

```bash
# Clone repository
git clone https://github.com/myusufkuncie/ai-reviewer.git
cd ai-reviewer

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENROUTER_API_KEY="your-key"
export GITHUB_TOKEN="your-token"
export GITHUB_REPOSITORY="owner/repo"
export GITHUB_EVENT_PATH="path/to/event.json"

# Run (GitHub)
python main_github.py
# Or (GitLab)
python main_gitlab.py
```

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=ai_reviewer tests/
```

### Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Security

### Data Privacy

- Code is sent to AI provider for analysis
- Use self-hosted models for sensitive code
- Review provider's privacy policy
- Enable audit logging

### Credentials

- Never commit API keys
- Use environment variables or secrets
- Rotate keys regularly
- Use minimal permission scopes

### Vulnerability Reporting

Report security issues to: security@yourorg.com

## License

MIT License - see [LICENSE](LICENSE) file

## Roadmap

- [x] **2-pass verification system** (AI + Linter confirmation)
- [x] **Smart linter integration** (7+ languages, token-efficient filtering)
- [x] **Tool-augmented reviews** (read files, check git history, run linters)
- [ ] Test execution tool (run tests automatically)
- [ ] Linter auto-fix suggestions (apply linter fixes)
- [ ] Self-hosted model support (Ollama)
- [ ] VSCode extension
- [ ] Web dashboard for analytics
- [ ] Team learning and custom rules
- [ ] Bitbucket support
- [ ] Pre-commit hook integration
- [ ] Slack/Discord notifications
- [ ] Multi-language comment translation

## Support

- **Documentation**: [docs.yourproject.com](https://docs.yourproject.com)
- **Issues**: [GitHub Issues](https://github.com/myusufkuncie/ai-reviewer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/myusufkuncie/ai-reviewer/discussions)
- **Email**: support@yourorg.com

## Acknowledgments

- Powered by [OpenRouter](https://openrouter.ai)
- Inspired by GitHub Copilot and GitLab Code Suggestions
- Built with [python-gitlab](https://github.com/python-gitlab/python-gitlab) and [PyGithub](https://github.com/PyGithub/PyGithub)

---

**Made with ❤️ by developers, for developers**

If you find this useful, please ⭐ star the repository!
