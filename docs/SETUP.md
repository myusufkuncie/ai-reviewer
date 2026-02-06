# Setup Guide

Detailed setup instructions for AI Code Reviewer on different platforms.

## Table of Contents
- [GitHub Setup](#github-setup)
- [GitLab Setup](#gitlab-setup)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## GitHub Setup

### Step 1: Get OpenRouter API Key

1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up or log in
3. Navigate to [Keys](https://openrouter.ai/keys)
4. Create a new API key
5. Copy the key (you'll need it in Step 3)

### Step 2: Add Workflow File

Create `.github/workflows/ai-review.yml`:

**Option A: Quick Setup (Auto-detect language)**
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
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Clone and run AI Review
        run: |
          git clone https://github.com/myusufkuncie/ai-reviewer.git /tmp/ai-reviewer
          cd /tmp/ai-reviewer
          pip install -r requirements.txt
          python main_github.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_PR_NUMBER: ${{ github.event.pull_request.number }}
          GITHUB_BASE_REF: ${{ github.event.pull_request.base.sha }}
          GITHUB_HEAD_REF: ${{ github.event.pull_request.head.sha }}
```

**Option B: Language-Specific**

Copy from:
- Python/Django: `templates/github-actions/python-django.yml`
- Flutter: `templates/github-actions/flutter.yml`
- Go: `templates/github-actions/golang.yml`
- JavaScript/TypeScript: `templates/github-actions/javascript.yml`

### Step 3: Add Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add `OPENROUTER_API_KEY` with your API key from Step 1
5. `GITHUB_TOKEN` is automatically provided by GitHub

### Step 4: Configure (Optional)

Add `.ai-review-config.json` to your repository root:

```json
{
  "enabled": true,
  "ai_provider": "openrouter",
  "model": "anthropic/claude-sonnet-4.5",
  "review_settings": {
    "severity_threshold": "minor",
    "max_comments_per_file": 10
  }
}
```

See examples in:
- `.ai-review-config.example.json` (full options)
- `.ai-review-config.minimal.json` (minimal setup)
- `.ai-review-config.flutter.json` (Flutter-specific)
- `.ai-review-config.django.json` (Django-specific)

### Step 5: Test

1. Create a test branch
2. Make some changes
3. Open a Pull Request
4. Watch the AI reviewer in action!

## GitLab Setup

### Step 1: Get API Keys

1. **OpenRouter API Key**: Same as GitHub Step 1
2. **GitLab Token**:
   - Go to GitLab → Settings → Access Tokens
   - Create token with scopes: `api`, `read_api`, `read_repository`, `write_repository`
   - Copy the token

### Step 2: Add CI Configuration

**Option A: Standalone File**

Create `.gitlab-ci-ai-review.yml`:

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

Then include in main `.gitlab-ci.yml`:
```yaml
include:
  - local: '.gitlab-ci-ai-review.yml'
```

**Option B: Language-Specific**

Copy from:
- Python/Django: `templates/gitlab-ci/python-django.yml`
- Flutter: `templates/gitlab-ci/flutter.yml`
- Go: `templates/gitlab-ci/golang.yml`
- JavaScript: `templates/gitlab-ci/javascript.yml`

### Step 3: Add CI/CD Variables

1. Go to your GitLab project
2. Click **Settings** → **CI/CD**
3. Expand **Variables**
4. Add variables:
   - `GITLAB_TOKEN`: Your GitLab access token
   - `OPENROUTER_API_KEY`: Your OpenRouter API key
5. Mark both as **Masked**

### Step 4: Configure (Optional)

Same as GitHub Step 4 - add `.ai-review-config.json`

### Step 5: Test

1. Create a merge request
2. Watch the pipeline run
3. Check for AI review comments

## Configuration

### Minimal Configuration

```json
{
  "enabled": true,
  "ai_provider": "openrouter",
  "model": "anthropic/claude-sonnet-4.5"
}
```

### Production Configuration

```json
{
  "enabled": true,
  "ai_provider": "openrouter",
  "model": "anthropic/claude-sonnet-4.5",
  "max_tokens": 4000,
  "temperature": 0.3,

  "exclusions": {
    "directories": ["node_modules", "vendor", "build"],
    "file_patterns": ["*.lock", "*.min.js"]
  },

  "review_settings": {
    "severity_threshold": "minor",
    "check_security": true,
    "check_performance": true,
    "max_comments_per_file": 10
  }
}
```

### Language-Specific Configuration

For Flutter projects, add:
```json
{
  "language_specific": {
    "flutter": {
      "check_pubspec": true,
      "widget_best_practices": true,
      "state_management_patterns": ["bloc", "riverpod"]
    }
  }
}
```

For Django projects, add:
```json
{
  "language_specific": {
    "python": {
      "django_security": true,
      "check_type_hints": true,
      "pep8_compliance": true
    }
  }
}
```

## Testing

### Test Locally (GitHub)

```bash
# Set environment variables
export GITHUB_TOKEN="your-token"
export OPENROUTER_API_KEY="your-key"
export GITHUB_REPOSITORY="owner/repo"
export GITHUB_PR_NUMBER="123"
export GITHUB_BASE_REF="main"
export GITHUB_HEAD_REF="feature-branch"

# Run
python ai_reviewer_github.py
```

### Test Locally (GitLab)

```bash
# Set environment variables
export GITLAB_TOKEN="your-token"
export OPENROUTER_API_KEY="your-key"
export CI_SERVER_URL="https://gitlab.com"
export CI_PROJECT_ID="12345"
export CI_MERGE_REQUEST_IID="1"

# Run
python ai_reviewer.py
```

### Dry Run Mode

To test without posting comments:

```bash
export AI_REVIEWER_DRY_RUN=true
python ai_reviewer.py
```

## Troubleshooting

### Issue: "Authentication failed"

**For GitHub:**
- Check `GITHUB_TOKEN` has `pull-requests: write` permission
- Verify token is not expired

**For GitLab:**
- Ensure `GITLAB_TOKEN` has `api` scope
- Verify token has access to the project

### Issue: "No comments posted"

**Possible causes:**
1. All files excluded by configuration
2. No issues found
3. Severity threshold too high

**Solutions:**
- Check `.ai-review-config.json` exclusions
- Lower `severity_threshold` to "suggestion"
- Check CI logs for actual review output

### Issue: "Rate limit exceeded"

**Solutions:**
- Enable caching in config
- Add more exclusion rules
- Use a paid API plan with higher limits

### Issue: "Timeout"

**Solutions:**
- Reduce files per review (split large PRs)
- Reduce `max_tokens` in config
- Increase workflow timeout:

```yaml
timeout-minutes: 15
```

### Issue: "Model not found"

**Solution:**
Check model name is correct for your provider:
- OpenRouter: `anthropic/claude-sonnet-4.5`
- Anthropic: `claude-sonnet-4.5-20250929`
- OpenAI: `gpt-4-turbo-preview`

### Getting Help

If issues persist:
1. Enable debug mode: `export AI_REVIEWER_DEBUG=true`
2. Check CI/workflow logs
3. Open an issue with:
   - Platform (GitHub/GitLab)
   - Language
   - Error messages
   - Configuration file
   - Relevant logs

## Advanced Setup

### Multiple Configurations

Use different configs for different branches:

```yaml
# .github/workflows/ai-review.yml
- name: Select config
  run: |
    if [[ "${{ github.base_ref }}" == "main" ]]; then
      cp .ai-review-config.prod.json .ai-review-config.json
    else
      cp .ai-review-config.dev.json .ai-review-config.json
    fi
```

### Self-Hosted Runners

For private code, use self-hosted runners:

**GitHub:**
```yaml
runs-on: self-hosted
```

**GitLab:**
```yaml
tags:
  - self-hosted
```

### Custom AI Models

To use self-hosted models (Ollama):

```json
{
  "ai_provider": "ollama",
  "model": "codellama",
  "api_url": "http://localhost:11434"
}
```

## Next Steps

- Customize configuration for your needs
- Add language-specific rules
- Set up notifications (Slack/Discord)
- Monitor review quality and adjust settings

For more information, see [README.md](README.md)
