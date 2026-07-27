# Features

## Platform Support

| Platform | Status |
| --- | --- |
| GitHub Actions | Supported |
| GitLab CI | Supported |
| Bitbucket Pipelines | Planned |

## Language Support

| Language | Linter | Frameworks in Context |
| --- | --- | --- |
| Python | pylint / flake8 | Django, Flask, FastAPI |
| JavaScript | eslint | React, Vue, Angular, Next.js |
| TypeScript | eslint | React, Next.js |
| Dart / Flutter | dart analyze | Flutter |
| Go | golangci-lint / go vet | Gin, Echo |
| Rust | cargo clippy | Actix, Rocket |
| Java | checkstyle | Spring |
| PHP | phpcs / php -l | Laravel |

Language is detected from file extension. Linters must be available in the CI environment; if absent, that step is skipped gracefully.

## Review Pipeline

### Batch AI Review

All pending files are sent in one API call rather than one call per file. This reduces latency and cost significantly on PRs with many changed files. The batch context includes PR title, README excerpt, Dockerfile context, and per-file diffs with embedded linter output.

### Linter-First (Pass 1)

Before the AI call, linters run for each language group in a single subprocess. Issues are filtered to changed lines only to keep the AI context compact. Linter output is embedded in the batch prompt so the AI can see static-analysis findings alongside the diff.

### 2-Pass Verification

For `critical` and `major` findings, the `DoubleCheckVerifier` cross-checks each issue against:

- Cached linter results (line-number match)
- Git history of the file (last 3 commits)
- Related files mentioned in the issue text

Issues are tagged `linter_confirmed: true/false`. Minor and suggestion findings pass through unchanged. No issues are dropped by verification — it only enriches metadata.

### Explainer + Understanding Quiz

After inline comments are posted, a PR-level summary block is posted containing:

- A plain-language description of what changed
- An understanding quiz for reviewers

This is separate from inline comments and is only posted when the AI returns an `explainer` field.

## Caching

- MD5-based cache keys per file: `hash(filepath + diff + version)`
- File-backed storage with TTL expiration (default 7 days)
- Cache hits skip the linter and AI entirely for that file
- Current cache version: `v6-linter-first`

## Severity Levels

| Level | Description |
| --- | --- |
| critical | Security vulnerabilities, data integrity risks |
| major | Bugs, likely runtime errors, breaking changes |
| minor | Code quality, missing error handling |
| suggestion | Style, refactoring, best-practice nudges |

Only `critical` and `major` findings go through the verification step.

## AI Provider

The only implemented provider is **OpenRouter** (`openrouter_provider.py`). It exposes any model available on the OpenRouter platform.

Default model: `z-ai/glm-4.5-air`. Change via config:

```json
{
  "model": "anthropic/claude-sonnet-4-5"
}
```

Temperature defaults to `0.3`. `max_tokens` defaults to `null` (model uses its full context window).

## Configuration

All settings live in `.ai-review-config.json` at the repo root. The file is optional — hardcoded defaults apply if absent.

### Exclusions

```json
{
  "exclusions": {
    "directories": ["node_modules", "vendor", "build"],
    "file_patterns": ["*.lock", "*.min.js"],
    "file_prefixes": ["test_"]
  }
}
```

### Review settings

```json
{
  "review_settings": {
    "severity_threshold": "minor",
    "max_comments_per_file": 10
  }
}
```

### Cache settings

```json
{
  "cache_settings": {
    "cache_location": ".review_cache",
    "ttl_days": 7
  }
}
```

## Comment Posting

- Previous bot comments are cleared before posting new ones (idempotent re-runs)
- Inline comments are posted at the specific diff line
- A single PR-level summary or explainer block is posted after inline comments

## Planned / Not Yet Implemented

- Bitbucket support
- Direct Anthropic / OpenAI / Ollama provider adapters
- Web dashboard
- Slack / Discord notifications
- VSCode extension
- Distributed cache (Redis)
