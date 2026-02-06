# Product Requirements Document: Universal AI Code Reviewer

## Overview

**Product Name**: AI Code Reviewer
**Version**: 2.0
**Last Updated**: 2026-02-06
**Status**: Planning

## Executive Summary

AI Code Reviewer is an automated code review tool that integrates with GitHub and GitLab CI/CD pipelines to provide intelligent, context-aware code reviews for multiple programming languages including Flutter/Dart, Django/Python, Go, JavaScript/TypeScript, and more.

## Problem Statement

### Current Challenges
1. Manual code reviews are time-consuming and resource-intensive
2. Code quality varies across teams and projects
3. Best practices and security vulnerabilities are often missed
4. Small teams lack dedicated reviewers
5. Context switching between different language ecosystems

### Target Users
- **Primary**: Development teams (2-50 developers)
- **Secondary**: Solo developers, Open source maintainers
- **Use Cases**: Pull Requests, Merge Requests, Pre-commit hooks

## Goals and Objectives

### Primary Goals
1. Provide automated, context-aware code reviews
2. Support multiple programming languages and frameworks
3. Easy integration with GitHub Actions and GitLab CI
4. Customizable review rules per project
5. Cost-effective using efficient AI models

### Success Metrics
- 90% of PRs/MRs reviewed within 2 minutes
- 70% of issues found are actionable
- 50% reduction in reviewer time
- Support for 5+ programming languages

## Features and Requirements

### Core Features

#### 1. Multi-Platform Support
**Priority**: P0 (Must Have)

- **GitHub Actions Integration**
  - Automatic PR comment posting
  - GitHub API authentication
  - Status checks integration
  - Review approval workflows

- **GitLab CI Integration** (existing)
  - Merge Request discussions
  - GitLab API authentication
  - Pipeline integration

#### 2. Multi-Language Support
**Priority**: P0 (Must Have)

| Language | Framework Support | Status |
|----------|------------------|---------|
| Python | Django, Flask, FastAPI | ✅ Implemented |
| JavaScript/TypeScript | React, Vue, Angular, Next.js | ✅ Implemented |
| Dart/Flutter | Flutter framework | 🔄 To Add |
| Go | Standard library, Gin, Echo | 🔄 To Add |
| Java | Spring, Spring Boot | 🔄 To Add |
| Rust | Actix, Rocket | 🔄 To Add |

#### 3. Intelligent Context Analysis
**Priority**: P0 (Must Have)

- Full file context (before/after changes)
- Related file detection via imports
- Project architecture understanding
- README and documentation parsing
- Docker configuration analysis
- Dependency analysis
- Test file correlation

#### 4. Configurable Review Rules
**Priority**: P0 (Must Have)

**Configuration File**: `.ai-review-config.json`

```json
{
  "enabled": true,
  "ai_provider": "openrouter",
  "model": "anthropic/claude-sonnet-4.5",
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
    }
  },

  "exclusions": {
    "directories": ["node_modules", "vendor", "build"],
    "file_patterns": ["*.lock", "*.min.js"],
    "file_prefixes": ["test_", "_test"]
  },

  "review_settings": {
    "severity_threshold": "minor",
    "auto_approve_minor": false,
    "require_tests": true,
    "check_security": true,
    "check_performance": true
  },

  "comment_settings": {
    "style": "detailed",
    "include_examples": true,
    "max_comments_per_file": 10
  }
}
```

#### 5. Smart Caching
**Priority**: P1 (Should Have)

- Cache reviews based on diff hash
- Invalidate on file changes
- Local and distributed cache support
- Cache expiration policies

#### 6. Security and Performance Analysis
**Priority**: P0 (Must Have)

- OWASP Top 10 vulnerability detection
- SQL injection patterns
- XSS vulnerabilities
- Authentication/Authorization issues
- Performance anti-patterns
- Memory leak detection
- N+1 query detection

### Advanced Features

#### 7. AI Provider Flexibility
**Priority**: P1 (Should Have)

Support multiple AI providers:
- OpenRouter (current)
- Anthropic Claude API
- OpenAI GPT-4
- Google Gemini
- Self-hosted models (Ollama)

#### 8. Review Modes
**Priority**: P2 (Nice to Have)

- **Quick Mode**: Fast, surface-level review
- **Standard Mode**: Balanced depth and speed
- **Deep Mode**: Comprehensive analysis
- **Security Focus**: Security-only review
- **Performance Focus**: Performance-only review

#### 9. Learning and Improvement
**Priority**: P2 (Nice to Have)

- Feedback loop for review quality
- Team-specific pattern learning
- False positive reduction
- Custom rule suggestions

#### 10. Reporting and Analytics
**Priority**: P2 (Nice to Have)

- Review statistics dashboard
- Code quality trends
- Most common issues
- Time saved metrics
- Cost tracking

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   Git Platform                          │
│              (GitHub / GitLab)                          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ Webhook / CI Trigger
                  ▼
┌─────────────────────────────────────────────────────────┐
│                CI/CD Pipeline                           │
│         (GitHub Actions / GitLab CI)                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ Execute ai-reviewer
                  ▼
┌─────────────────────────────────────────────────────────┐
│              AI Reviewer Core                           │
│  ┌────────────────────────────────────────────────┐    │
│  │  1. Configuration Loader                       │    │
│  │  2. Platform Adapter (GitHub/GitLab)           │    │
│  │  3. Language Detector                          │    │
│  │  4. Context Builder                            │    │
│  │  5. AI Provider Adapter                        │    │
│  │  6. Review Processor                           │    │
│  │  7. Comment Poster                             │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ API Calls
                  ▼
┌─────────────────────────────────────────────────────────┐
│              AI Provider                                │
│    (OpenRouter / Claude / GPT-4 / Gemini)              │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. PR/MR Created
   ↓
2. CI Triggered
   ↓
3. Fetch Changes (diff)
   ↓
4. Build Context
   ├─ Parse Config
   ├─ Detect Language
   ├─ Load Related Files
   ├─ Analyze Architecture
   └─ Check Cache
   ↓
5. Generate Review Prompt
   ↓
6. Call AI Provider
   ↓
7. Parse AI Response
   ↓
8. Filter and Validate Comments
   ↓
9. Post Comments to PR/MR
   ↓
10. Update Summary and Stats
```

## User Experience

### Setup Flow

#### For GitHub
```bash
# 1. Add to repository
curl -o .github/workflows/ai-review.yml \
  https://raw.githubusercontent.com/YOUR_ORG/ai-reviewer/main/templates/github-action.yml

# 2. Configure secrets
# GITHUB_TOKEN (automatic)
# OPENROUTER_API_KEY (add in repo settings)

# 3. Customize (optional)
cp .ai-review-config.example.json .ai-review-config.json

# 4. Commit and push
git add .github/workflows/ai-review.yml .ai-review-config.json
git commit -m "Add AI code reviewer"
git push
```

#### For GitLab
```bash
# 1. Add to .gitlab-ci.yml
curl -o .gitlab-ci-review.yml \
  https://raw.githubusercontent.com/YOUR_ORG/ai-reviewer/main/templates/gitlab-ci.yml

# Include in main .gitlab-ci.yml
echo "include: .gitlab-ci-review.yml" >> .gitlab-ci.yml

# 2. Configure CI/CD variables
# GITLAB_TOKEN
# OPENROUTER_API_KEY

# 3. Customize (optional)
cp .ai-review-config.example.json .ai-review-config.json

# 4. Commit and push
git add .gitlab-ci.yml .gitlab-ci-review.yml .ai-review-config.json
git commit -m "Add AI code reviewer"
git push
```

### Review Experience

1. Developer creates PR/MR
2. AI Reviewer runs automatically (1-2 minutes)
3. Inline comments appear on specific lines
4. Summary comment shows statistics
5. Developer addresses feedback
6. AI Reviewer re-runs on updates

### Comment Format

```markdown
🚨 **CRITICAL**: SQL injection vulnerability detected

The user input is directly concatenated into the SQL query without sanitization.

**Issue**: Line 42
query = f"SELECT * FROM users WHERE id = {user_id}"

**Fix**: Use parameterized queries
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))

**References**:
- OWASP SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection
- Django QuerySet API: https://docs.djangoproject.com/en/stable/ref/models/querysets/
```

## Implementation Plan

### Phase 1: Core Refactoring (Week 1-2)
- [ ] Abstract GitLab-specific code to platform adapter
- [ ] Create GitHub adapter
- [ ] Implement configuration system
- [ ] Add language detection

### Phase 2: Language Support (Week 3-4)
- [ ] Add Flutter/Dart language rules
- [ ] Add Go language rules
- [ ] Add Java language rules
- [ ] Create language-specific prompts

### Phase 3: GitHub Integration (Week 5-6)
- [ ] GitHub Actions workflow template
- [ ] GitHub API integration
- [ ] PR comment posting
- [ ] Status check integration

### Phase 4: Polish and Documentation (Week 7-8)
- [ ] Comprehensive README
- [ ] Setup guides per platform
- [ ] Configuration examples
- [ ] Video tutorials

## Non-Functional Requirements

### Performance
- Review completion: < 2 minutes for standard PR
- API response time: < 30 seconds per file
- Cache hit rate: > 60% for unchanged files

### Security
- Secure credential storage
- No code sent to unauthorized endpoints
- Audit logging for all API calls
- Support for self-hosted AI models

### Scalability
- Handle PRs with up to 50 files
- Support repositories up to 100k files
- Concurrent review support
- Rate limiting and backoff

### Reliability
- 99% uptime for CI integration
- Graceful degradation on API failures
- Retry logic for transient errors
- Clear error messages

## Dependencies and Constraints

### Technical Dependencies
- Python 3.8+
- Git CLI
- GitHub/GitLab API access
- AI provider API access

### Constraints
- API rate limits (GitHub: 5000/hour, GitLab: 300/min)
- AI provider costs
- Token context limits (varies by model)
- CI/CD execution time limits

### Assumptions
- Users have basic Git knowledge
- Users can configure CI/CD
- Users have API access to their repos
- Users are willing to share code with AI provider

## Success Criteria

### Launch Criteria
- [ ] Works on GitHub and GitLab
- [ ] Supports 5+ languages
- [ ] < 5 minute setup time
- [ ] Clear documentation
- [ ] Working examples for each language

### Post-Launch Metrics (3 months)
- 100+ active installations
- 1000+ PRs reviewed
- 4+ star rating (if applicable)
- < 10% error rate
- Positive user testimonials

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| AI provider costs too high | High | Medium | Support multiple providers, caching |
| False positives annoy users | High | High | Configurable severity, feedback loop |
| API rate limits hit | Medium | Medium | Caching, request batching |
| Security concerns | High | Low | Clear privacy policy, self-hosted option |
| Complex setup | Medium | Medium | Templates, documentation, videos |

## Open Questions

1. Should we support Bitbucket?
2. Should we offer a hosted SaaS version?
3. Should we build a web dashboard?
4. How to handle private/proprietary language frameworks?
5. Should we integrate with Slack/Discord for notifications?

## Appendix

### Glossary
- **PR**: Pull Request (GitHub)
- **MR**: Merge Request (GitLab)
- **CI/CD**: Continuous Integration/Continuous Deployment
- **OWASP**: Open Web Application Security Project

### References
- GitHub Actions: https://docs.github.com/en/actions
- GitLab CI: https://docs.gitlab.com/ee/ci/
- OpenRouter: https://openrouter.ai/docs
- Anthropic Claude: https://docs.anthropic.com/
