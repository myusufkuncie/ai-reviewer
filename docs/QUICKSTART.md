# Quick Start Guide

Get AI Code Reviewer running in under 5 minutes!

## Choose Your Platform

### GitHub (Fastest Setup)

1. **Copy workflow file**
   ```bash
   mkdir -p .github/workflows
   curl -o .github/workflows/ai-review.yml \
     https://raw.githubusercontent.com/myusufkuncie/ai-reviewer/main/templates/github-actions/multi-language.yml
   ```

2. **Add OpenRouter API key**
   - Get key from https://openrouter.ai/keys
   - Go to your repo → Settings → Secrets → Actions
   - Add secret: `OPENROUTER_API_KEY`

3. **Commit and push**
   ```bash
   git add .github/workflows/ai-review.yml
   git commit -m "Add AI code reviewer"
   git push
   ```

4. **Create a test PR** - The AI reviewer will automatically comment!

### GitLab (Simple Setup)

1. **Add to .gitlab-ci.yml**
   ```yaml
   include:
     - remote: 'https://raw.githubusercontent.com/myusufkuncie/ai-reviewer/main/templates/gitlab-ci/multi-language.yml'
   ```

2. **Add CI/CD variables**
   - Go to Settings → CI/CD → Variables
   - Add `GITLAB_TOKEN` (get from Settings → Access Tokens with `api` scope)
   - Add `OPENROUTER_API_KEY` (get from https://openrouter.ai/keys)

3. **Commit and push**
   ```bash
   git add .gitlab-ci.yml
   git commit -m "Add AI code reviewer"
   git push
   ```

4. **Create a test MR** - Check the pipeline!

## Language-Specific Setup

### Flutter
```bash
# Clone templates
git clone https://github.com/myusufkuncie/ai-reviewer.git /tmp/ai-reviewer-setup

# Copy GitHub workflow
cp /tmp/ai-reviewer-setup/templates/github-actions/flutter.yml .github/workflows/ai-review.yml

# Copy config
cp /tmp/ai-reviewer-setup/.ai-review-config.flutter.json .ai-review-config.json
```

### Django
```bash
# Clone templates
git clone https://github.com/myusufkuncie/ai-reviewer.git /tmp/ai-reviewer-setup

# Copy GitHub workflow
cp /tmp/ai-reviewer-setup/templates/github-actions/python-django.yml .github/workflows/ai-review.yml

# Copy config
cp /tmp/ai-reviewer-setup/.ai-review-config.django.json .ai-review-config.json
```

### Go
```bash
# Clone templates
git clone https://github.com/myusufkuncie/ai-reviewer.git /tmp/ai-reviewer-setup

# Copy GitHub workflow
cp /tmp/ai-reviewer-setup/templates/github-actions/golang.yml .github/workflows/ai-review.yml

# Copy config
cp /tmp/ai-reviewer-setup/.ai-review-config.golang.json .ai-review-config.json
```

## What Happens Next?

When you create a PR/MR, the AI reviewer will:

1. ✅ Analyze all changed files
2. ✅ Check for security vulnerabilities
3. ✅ Review code quality and best practices
4. ✅ Post inline comments with suggestions
5. ✅ Add a summary comment with statistics

## Example Output

```
🤖 AI Code Review Summary

Review Statistics
- Files Reviewed: 5
- Total Comments: 8

Findings by Severity
- 🚨 Critical: 1
- ⚠️ Major: 3
- 💡 Minor: 3
- 💭 Suggestions: 1
```

Inline comments will appear on specific lines:

```
🚨 CRITICAL: SQL injection vulnerability detected

Use parameterized queries instead of string concatenation.

Fix:
  cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

## Customization

Create `.ai-review-config.json` in your repo:

### Minimal
```json
{
  "enabled": true,
  "model": "anthropic/claude-sonnet-4.5"
}
```

### With Exclusions
```json
{
  "enabled": true,
  "model": "anthropic/claude-sonnet-4.5",
  "exclusions": {
    "directories": ["node_modules", "vendor"],
    "file_patterns": ["*.lock", "*.min.js"]
  }
}
```

## Troubleshooting

**No comments appearing?**
- Check GitHub Actions / GitLab CI logs
- Verify API keys are set correctly
- Check exclusion rules in config

**Too many comments?**
```json
{
  "review_settings": {
    "severity_threshold": "major",
    "max_comments_per_file": 5
  }
}
```

**Rate limits?**
```json
{
  "cache_settings": {
    "enabled": true
  }
}
```

## Cost Estimate

Average PR (5 files, 500 lines):
- **~$0.10** with Claude Sonnet
- **~$0.02** with Claude Haiku
- **60% cheaper** with caching enabled

## Next Steps

1. ✅ Test with a small PR
2. ✅ Adjust configuration as needed
3. ✅ Add language-specific rules
4. ✅ Check out [SETUP.md](SETUP.md) for advanced options

## Need Help?

- 📖 [Full Documentation](../README.md)
- 🔧 [Detailed Setup Guide](SETUP.md)
- 🏗️ [Architecture & Flow](ARCHITECTURE.md)
- 🤝 [Contributing Guide](CONTRIBUTING.md)

**Happy coding with AI assistance!** 🚀
