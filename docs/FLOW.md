# AI Code Reviewer - System Flow and Architecture

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Developer Workflow                            │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │   GitHub PR Created   │       │  GitLab MR Created    │
        └───────────┬───────────┘       └───────────┬───────────┘
                    │                               │
                    │ Webhook/CI Trigger            │
                    │                               │
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │  GitHub Actions Run   │       │   GitLab CI Run       │
        └───────────┬───────────┘       └───────────┬───────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │   AI Reviewer Container   │
                    │      (Docker/Python)      │
                    └───────────┬───────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Config Load  │  │  Diff Fetch  │  │ Context Build│
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                  │
           └────────┬────────┴────────┬─────────┘
                    │                 │
                    ▼                 ▼
            ┌──────────────┐  ┌──────────────┐
            │  Cache Check │  │ AI Provider  │
            └──────┬───────┘  └──────┬───────┘
                   │                 │
                   └────────┬────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Review Processing   │
                └───────────┬───────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌───────────────────┐   ┌───────────────────┐
    │  GitHub Comments  │   │  GitLab Comments  │
    └───────────────────┘   └───────────────────┘
```

## Detailed Component Flow

### 1. Platform Detection and Initialization

```
┌─────────────────────────────────────────────────────┐
│              Application Entry Point                 │
│                   (main.py)                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ Environment Variables  │
        │    Detection           │
        └────────┬───────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
     ▼                       ▼
┌────────────┐        ┌────────────┐
│  GitHub?   │        │  GitLab?   │
│ GITHUB_*   │        │   CI_*     │
└─────┬──────┘        └─────┬──────┘
      │                     │
      ▼                     ▼
┌────────────┐        ┌────────────┐
│  GitHub    │        │  GitLab    │
│  Adapter   │        │  Adapter   │
└────────────┘        └────────────┘
```

**Environment Variables:**

GitHub:
- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY`
- `GITHUB_EVENT_PATH`
- `GITHUB_SHA`

GitLab:
- `GITLAB_TOKEN`
- `CI_SERVER_URL`
- `CI_PROJECT_ID`
- `CI_MERGE_REQUEST_IID`

### 2. Configuration Loading Flow

```
┌─────────────────────────────────────────────────────┐
│              Configuration Loader                    │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ Check for             │
        │ .ai-review-config.json│
        └────────┬───────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
     ▼                       ▼
┌────────────┐        ┌────────────┐
│   Found    │        │ Not Found  │
└─────┬──────┘        └─────┬──────┘
      │                     │
      ▼                     ▼
┌────────────┐        ┌────────────┐
│ Load JSON  │        │  Use       │
│ Parse      │        │  Defaults  │
└─────┬──────┘        └─────┬──────┘
      │                     │
      └──────────┬──────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Merge with Defaults│
        │ Validate Schema    │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Configuration      │
        │ Object Ready       │
        └────────────────────┘
```

### 3. File Change Detection and Filtering

```
┌─────────────────────────────────────────────────────┐
│            Fetch PR/MR Changes                       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Get Diff from API     │
        │  (base...head)         │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Parse Changed Files   │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │   For Each File        │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Apply Exclusion Rules │
        └────────┬───────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
     ▼                       ▼
┌────────────┐        ┌────────────┐
│  Excluded  │        │  Include   │
│  (Skip)    │        │  (Review)  │
└────────────┘        └─────┬──────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ Detect Language│
                   └────────┬───────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  Build Context │
                   └────────────────┘

**Exclusion Rules:**
1. Check directory exclusions
2. Check file pattern exclusions
3. Check file prefix exclusions
4. Check binary files
5. Check file size limits
```

### 4. Context Building Flow

```
┌─────────────────────────────────────────────────────┐
│              Context Builder                         │
│           (for each file to review)                  │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┴───────────┬──────────────┐
         │                       │              │
         ▼                       ▼              ▼
┌──────────────────┐   ┌──────────────┐  ┌──────────────┐
│  Fetch File      │   │ Fetch File   │  │  Parse Diff  │
│  Before (base)   │   │ After (head) │  │   Changes    │
└────────┬─────────┘   └──────┬───────┘  └──────┬───────┘
         │                    │                  │
         └────────────┬───────┴──────────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │  Extract Metadata       │
         │  - Imports              │
         │  - Functions            │
         │  - Classes              │
         │  - Constants            │
         └────────┬────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    │             │             │             │
    ▼             ▼             ▼             ▼
┌────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐
│ README │  │ Related │  │ Docker  │  │  Tests   │
│ Files  │  │ Files   │  │ Config  │  │  Files   │
└───┬────┘  └────┬────┘  └────┬────┘  └────┬─────┘
    │            │            │            │
    └────────────┴────────────┴────────────┘
                  │
                  ▼
         ┌─────────────────────┐
         │  Analyze Impact     │
         │  - Scope            │
         │  - Risk Areas       │
         │  - Breaking Changes │
         └────────┬────────────┘
                  │
                  ▼
         ┌─────────────────────┐
         │  Build Prompt       │
         │  (Context String)   │
         └─────────────────────┘
```

### 5. AI Review Processing Flow

```
┌─────────────────────────────────────────────────────┐
│              Review Processor                        │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Generate Cache Key    │
        │  (hash of diff)        │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │   Check Cache          │
        └────────┬───────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
     ▼                       ▼
┌────────────┐        ┌────────────┐
│Cache Hit   │        │ Cache Miss │
│(Return)    │        │            │
└────────────┘        └─────┬──────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ Select AI      │
                   │ Provider       │
                   └────────┬───────┘
                            │
        ┌───────────────────┼──────────────────┐
        │                   │                  │
        ▼                   ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  OpenRouter  │  │ Claude API   │  │  OpenAI API  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └─────────────────┴──────────────────┘
                         │
                         ▼
                ┌────────────────┐
                │  Call AI API   │
                │  (with prompt) │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │  Parse Response│
                │  Extract JSON  │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │  Validate      │
                │  Comments      │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │  Save to Cache │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │ Return Comments│
                └────────────────┘
```

### 6. Comment Posting Flow

```
┌─────────────────────────────────────────────────────┐
│              Comment Poster                          │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Aggregate All         │
        │  Review Comments       │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Sort by Severity      │
        │  and Line Number       │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Apply Filters         │
        │  (max per file, etc)   │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Format Comments       │
        │  (add emoji, style)    │
        └────────┬───────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
     ▼                       ▼
┌────────────┐        ┌────────────┐
│  GitHub    │        │  GitLab    │
│  Adapter   │        │  Adapter   │
└─────┬──────┘        └─────┬──────┘
      │                     │
      ▼                     ▼
┌────────────┐        ┌────────────┐
│ Post Inline│        │ Create     │
│ Comments   │        │ Discussion │
└─────┬──────┘        └─────┬──────┘
      │                     │
      └──────────┬──────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  Generate Summary  │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  Post Summary      │
        │  Comment           │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  Update Status     │
        │  (if configured)   │
        └────────────────────┘
```

## Language-Specific Flow

```
┌─────────────────────────────────────────────────────┐
│              Language Detector                       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Check File Extension  │
        └────────┬───────────────┘
                 │
    ┌────────────┼────────────┬────────────┐
    │            │            │            │
    ▼            ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ .py    │  │ .dart  │  │  .go   │  │  .js   │
│ Python │  │Flutter │  │Golang  │  │  JS/TS │
└───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘
    │           │           │           │
    ▼           ▼           ▼           ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ Python │  │ Dart   │  │   Go   │  │   JS   │
│Analyzer│  │Analyzer│  │Analyzer│  │Analyzer│
└───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘
    │           │           │           │
    │           │           │           │
    └───────────┴───────────┴───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Language-Specific  │
        │ Review Rules       │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Generate Prompt    │
        │ with Language      │
        │ Context            │
        └────────────────────┘
```

### Python/Django Review Flow
```
File detected: .py
    ↓
Check for Django imports
    ↓
Load Django-specific rules:
    - Check Models for migrations
    - Validate serializers
    - Check view permissions
    - SQL injection in raw queries
    - XSS in templates
    - CSRF protection
    ↓
Add Django context to prompt
    ↓
Review with Django expertise
```

### Flutter/Dart Review Flow
```
File detected: .dart
    ↓
Check pubspec.yaml
    ↓
Load Flutter-specific rules:
    - Widget best practices
    - State management patterns
    - Build method optimization
    - Memory leak (dispose)
    - Platform-specific code
    - Accessibility
    ↓
Add Flutter context to prompt
    ↓
Review with Flutter expertise
```

### Go Review Flow
```
File detected: .go
    ↓
Check go.mod
    ↓
Load Go-specific rules:
    - Error handling patterns
    - Goroutine safety
    - Context usage
    - Interface design
    - Defer placement
    - Race conditions
    ↓
Add Go context to prompt
    ↓
Review with Go expertise
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────┐
│              Error Occurs                            │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Classify Error Type   │
        └────────┬───────────────┘
                 │
    ┌────────────┼────────────┬────────────┐
    │            │            │            │
    ▼            ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  API    │ │ Network │ │  Auth   │ │  Parse  │
│  Error  │ │ Timeout │ │  Error  │ │  Error  │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │           │           │           │
     ▼           ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Retry   │ │ Retry   │ │  Fail   │ │  Skip   │
│ 3x      │ │ 2x      │ │  Fast   │ │  File   │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │           │           │           │
     └───────────┴───────────┴───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  Log Error         │
        │  (with context)    │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  Continue or Exit  │
        │  (based on severity)│
        └────────┬───────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
     ▼                       ▼
┌────────────┐        ┌────────────┐
│ Continue   │        │  Exit with │
│ Review     │        │  Error Msg │
└────────────┘        └────────────┘
```

## Caching Strategy

```
┌─────────────────────────────────────────────────────┐
│              Cache System                            │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│ Local Cache  │          │ Remote Cache │
│ (File-based) │          │ (Optional)   │
└──────┬───────┘          └──────┬───────┘
       │                         │
       ▼                         ▼
Cache Key Generation:
    hash(filename + diff + version)
       │
       ▼
┌────────────────────────┐
│  Cache Entry           │
│  {                     │
│    "key": "abc123",    │
│    "comments": [...],  │
│    "timestamp": ...,   │
│    "version": "v3"     │
│  }                     │
└────────────────────────┘

Cache Invalidation:
- File content changed
- Config changed
- Version changed
- TTL expired (7 days)
```

## Performance Optimization Flow

```
Optimization Strategy:

1. Parallel Processing
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │  File 1  │  │  File 2  │  │  File 3  │
   │  Review  │  │  Review  │  │  Review  │
   └────┬─────┘  └────┬─────┘  └────┬─────┘
        └────────────┬─────────────┘
                     │
              (Run in parallel)

2. Context Truncation
   - README: max 3000 chars
   - Related files: max 2000 chars each
   - Full file: max 2000 chars
   - Total context: ~ 15-20K tokens

3. Smart File Selection
   - Related files: max 5
   - Same directory: max 10 files scanned
   - Test files: max 2

4. Request Batching
   - Group similar files
   - Batch comments posting
   - Reduce API calls
```

## Security Flow

```
┌─────────────────────────────────────────────────────┐
│              Security Checks                         │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│ Credentials  │          │ Code Content │
│ Handling     │          │ Sanitization │
└──────┬───────┘          └──────┬───────┘
       │                         │
       ▼                         ▼
┌────────────────┐      ┌────────────────┐
│ - Env vars only│      │ - Remove secrets│
│ - No logging   │      │ - Truncate logs│
│ - Secure store │      │ - Audit trail  │
└────────────────┘      └────────────────┘

Security Patterns Detected:
    ↓
┌────────────────────────┐
│ - SQL Injection        │
│ - XSS                  │
│ - Hardcoded secrets    │
│ - Weak crypto          │
│ - Path traversal       │
│ - Command injection    │
│ - SSRF                 │
│ - Insecure deserialize │
└────────────────────────┘
```

## Summary Statistics Flow

```
After all files reviewed:
    ↓
Aggregate Statistics:
    ↓
┌────────────────────────┐
│ - Total files reviewed │
│ - Files skipped        │
│ - Files excluded       │
│ - Total comments       │
│ - By severity:         │
│   • Critical: N        │
│   • Major: N           │
│   • Minor: N           │
│   • Suggestion: N      │
│ - Review time          │
│ - Cache hit rate       │
│ - API calls made       │
│ - Tokens used          │
└────────┬───────────────┘
         │
         ▼
Format Summary Comment
         │
         ▼
Post to PR/MR
```

## Complete End-to-End Flow

```
1. Developer pushes code
         ↓
2. PR/MR created
         ↓
3. CI pipeline triggered
         ↓
4. AI Reviewer starts
         ↓
5. Load configuration
         ↓
6. Detect platform (GitHub/GitLab)
         ↓
7. Fetch changed files
         ↓
8. Filter files (exclusions)
         ↓
9. For each file:
    a. Detect language
    b. Build context
    c. Check cache
    d. Call AI (if needed)
    e. Parse response
    f. Validate comments
         ↓
10. Aggregate all comments
         ↓
11. Post inline comments
         ↓
12. Post summary
         ↓
13. Update status/checks
         ↓
14. Exit with status code
```

## Retry and Resilience Strategy

```
API Call Failed
    ↓
Check Error Type
    ↓
    ├─ 429 (Rate Limit)
    │   → Wait with exponential backoff
    │   → Retry up to 5 times
    │
    ├─ 500/502/503 (Server Error)
    │   → Retry up to 3 times
    │   → 2s, 4s, 8s delays
    │
    ├─ 401/403 (Auth Error)
    │   → Fail fast
    │   → Log error
    │   → Exit
    │
    └─ Network Timeout
        → Retry up to 2 times
        → 5s, 10s delays

All retries failed
    ↓
Skip file and continue
    ↓
Log detailed error
    ↓
Mark in summary as "review failed"
```
