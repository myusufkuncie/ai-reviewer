# AI Code Reviewer

Intelligent, context-aware automated code reviews for GitHub and GitLab using AI. Supports multiple programming languages including Python, JavaScript/TypeScript, Flutter/Dart, Go, Java, Rust, PHP/Laravel, and more.

## Features

- **Batch AI Review**: All changed files are sent in a single AI call — no per-file round trips
- **Linter-First Pipeline**: Language-specific linters run before AI, on changed lines only
- **2-Pass Verification**: Critical and major findings are cross-checked against linter output, git history, and related files
- **Explainer + Quiz**: After inline comments, a PR-level summary with a plain-language explanation and understanding quiz is posted
- **Idempotent Re-runs**: Previous bot comments are cleared before each new review
- **Multi-Platform**: GitHub Actions and GitLab CI
- **Multi-Language**: Python, JavaScript/TypeScript, Flutter/Dart, Go, Java, Rust, PHP/Laravel (8+ languages)
- **Context-Aware**: Full file context, related files, project architecture, README, and Docker configs
- **Security-Focused**: Detects OWASP Top 10 vulnerabilities, SQL injection, XSS, and more
- **Smart Caching**: Skips linter and AI entirely for unchanged files (MD5-keyed, 7-day TTL)
- **Configurable**: Exclusion rules, severity thresholds, model selection

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

   - `OPENROUTER_API_KEY`: Get from [OpenRouter](https://openrouter.ai/keys)
   - `GITHUB_TOKEN`: Automatically provided by GitHub Actions

   How to add: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

3. **Optional**: Add `.ai-review-config.json` (see [Configuration](#configuration))

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

2. **Add CI/CD variables** (**Settings** → **CI/CD** → **Variables**):

   - `GITLAB_TOKEN`: Personal access token with `api` scope
   - `OPENROUTER_API_KEY`: Get from [OpenRouter](https://openrouter.ai/keys)

3. **Optional**: Add `.ai-review-config.json`

## Configuration

Create `.ai-review-config.json` in your repository root. All fields are optional — hardcoded defaults apply if absent.

### Minimal

```json
{
  "model": "z-ai/glm-4.5-air"
}
```

### Full example

```json
{
  "model": "z-ai/glm-4.5-air",
  "temperature": 0.3,

  "exclusions": {
    "directories": [
      "node_modules", "vendor", "dist", "build",
      ".git", "__pycache__", "venv", "migrations"
    ],
    "file_patterns": [
      "*.lock", "*.log", "*.min.js", "*.min.css",
      "package-lock.json", "yarn.lock",
      ".ai-review-config*.json", ".gitignore", ".dockerignore"
    ],
    "file_prefixes": ["test_", "_test", ".min."]
  },

  "review_settings": {
    "severity_threshold": "minor",
    "max_comments_per_file": 10
  },

  "cache_settings": {
    "cache_location": ".review_cache",
    "ttl_days": 7
  }
}
```

Pre-made configs for common stacks are available in the repository root:
`.ai-review-config.django.json`, `.ai-review-config.flutter.json`, `.ai-review-config.golang.json`, `.ai-review-config.nextjs.json`, `.ai-review-config.react.json`

## How It Works

### Review Pipeline

1. **Trigger**: PR/MR opened or updated
2. **Filter files**: Apply exclusion rules; check cache — cache hits skip linter and AI entirely
3. **Pass 1 — Linter**: Language-specific linters run per language group in a single subprocess. Output is filtered to changed lines only to keep the AI context compact
4. **Pack batch**: All pending files are packed into a single AI context (PR title, README excerpt, Dockerfile, per-file diffs with embedded linter output)
5. **Pass 1 — AI batch call**: One API call reviews all files at once and returns inline comments plus an `explainer` block
6. **Pass 2 — Verification**: `critical` and `major` findings are cross-checked against cached linter results, git history (last 3 commits), and related files. Each finding is tagged `linter_confirmed: true/false`. No findings are dropped — verification only enriches metadata
7. **Post comments**: Previous bot comments are cleared (idempotent). Inline comments are posted. If the AI returned an explainer, a PR-level summary block with plain-language description and understanding quiz is posted

### Context Includes

- Full file (before and after changes)
- Related files (via imports)
- Files in the same directory
- README and documentation
- Docker configuration
- Project architecture (package.json, requirements.txt, go.mod, etc.)

## Language Support

| Language | Linter | Frameworks in Context |
| -------- | ------ | --------------------- |
| Python | pylint / flake8 | Django, Flask, FastAPI |
| JavaScript | eslint | React, Vue, Angular, Next.js |
| TypeScript | eslint | React, Next.js |
| Dart / Flutter | dart analyze | Flutter |
| Go | golangci-lint / go vet | Gin, Echo |
| Rust | cargo clippy | Actix, Rocket |
| Java | checkstyle | Spring |
| PHP | phpcs / php -l | Laravel |

Language is detected from file extension. Linters must be available in the CI environment — if absent, that step is skipped gracefully.

## Review Severity Levels

| Severity | Description | Examples |
| -------- | ----------- | -------- |
| **critical** | Security vulnerabilities, data loss risks | SQL injection, XSS, hardcoded secrets |
| **major** | Bugs, likely runtime errors, breaking changes | Memory leaks, race conditions, API changes |
| **minor** | Code quality, maintainability | Missing error handling, unused variables |
| **suggestion** | Best practices, optimizations | Code style, refactoring opportunities |

Only `critical` and `major` findings go through the 2-pass verification step.

## AI Provider

The implemented provider is **OpenRouter**, which gives access to any model on the OpenRouter platform.

```json
{
  "model": "anthropic/claude-sonnet-4-5"
}
```

**Recommended models**:

| Model | Cost per Review | Notes |
| ----- | --------------- | ----- |
| `z-ai/glm-4.5-air` | ~$0.01 | Default — fast and cheap |
| `anthropic/claude-sonnet-4-5` | ~$0.10 | Best for security reviews |
| `openai/gpt-4-turbo` | ~$0.15 | Good general-purpose |

Estimates based on a typical PR with 5 files and 500 lines changed, with ~60% cache hit rate.

**Get API Key**: [OpenRouter Keys](https://openrouter.ai/keys)

## Troubleshooting

### "Authentication failed"

- GitHub: check `GITHUB_TOKEN` has `pull-requests: write` permission
- GitLab: ensure `GITLAB_TOKEN` has `api` scope
- OpenRouter: verify `OPENROUTER_API_KEY` is valid

### "No comments posted"

- Check exclusion rules in `.ai-review-config.json`
- Lower `severity_threshold`
- Check CI logs for errors

### "Rate limit exceeded"

- Caching reduces repeat calls — confirm `.review_cache/` is being persisted in CI artifacts
- Tighten exclusion rules to skip generated files

### "Comments on wrong lines"

- GitHub API requires comments on lines that are part of the diff
- Try a more capable model (e.g., `anthropic/claude-sonnet-4-5`)

### Debug mode

```bash
export AI_REVIEWER_DEBUG=true
python main_github.py   # or main_gitlab.py
```

## Development

### Local testing

```bash
git clone https://github.com/myusufkuncie/ai-reviewer.git
cd ai-reviewer
pip install -r requirements.txt

export OPENROUTER_API_KEY="your-key"
export GITHUB_TOKEN="your-token"
export GITHUB_REPOSITORY="owner/repo"

python main_github.py   # or main_gitlab.py
```

### Project structure

```
src/
  adapters/       # Platform (GitHub/GitLab) and AI (OpenRouter) adapters
  analyzers/      # Language detection, context building
  core/           # Reviewer orchestrator, config, cache
  tools/          # File reader, git history, linter tools
  utils/          # File utils, step timers
  verification/   # 2-pass DoubleCheckVerifier
main_github.py
main_gitlab.py
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

- Code is sent to OpenRouter for analysis — review their privacy policy for sensitive codebases
- Never commit API keys; use environment variables or CI secrets
- Use minimal permission scopes for tokens

## Roadmap

- [x] Batch AI review (all files in one API call)
- [x] Linter-first pipeline (per-language, changed lines only)
- [x] 2-pass verification (linter + git history cross-check)
- [x] Explainer + understanding quiz posted to PR
- [x] Idempotent re-runs (clear previous bot comments)
- [x] Smart caching (MD5-keyed, 7-day TTL)
- [ ] Direct Anthropic / OpenAI / Ollama provider adapters
- [ ] Bitbucket support
- [ ] Linter auto-fix suggestions
- [ ] VSCode extension
- [ ] Web dashboard
- [ ] Slack / Discord notifications
- [ ] Pre-commit hook integration

## Support

- **Issues**: [GitHub Issues](https://github.com/myusufkuncie/ai-reviewer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/myusufkuncie/ai-reviewer/discussions)

## Acknowledgments

- Powered by [OpenRouter](https://openrouter.ai)
- Built with [python-gitlab](https://github.com/python-gitlab/python-gitlab) and [PyGithub](https://github.com/PyGithub/PyGithub)

---

**Made with ❤️ by developers, for developers**

If you find this useful, please ⭐ star the repository!
