# System Flow

## High-Level Architecture

```mermaid
flowchart LR
    dev[Developer] -->|push| pr[PR / MR]
    pr -->|webhook / CI trigger| ci[GitHub Actions\nor GitLab CI]
    ci --> reviewer[AI Reviewer\nPython container]
    reviewer --> platform[Platform Adapter\nGitHub / GitLab]
    reviewer --> openrouter[OpenRouter API\nLLM]
    reviewer --> linter[Local Linters\npylint · eslint · dart · golangci-lint …]
    platform -->|inline comments + explainer| pr
```

## End-to-End Review Flow

```mermaid
flowchart TD
    A[Start: PR/MR ID] --> B[Load .ai-review-config.json]
    B --> C[platform.get_changes]
    C --> D{For each changed file}

    D -->|excluded / binary / too large| SKIP[Skip file]
    D -->|cache hit v6-linter-first| CACHED[Use cached comments]
    D -->|needs review| PENDING[Add to pending_items]

    PENDING --> LINT[Pass 1 — _run_batched_linters\none subprocess per language group\nresults attached to each item]

    LINT --> CTX[build_batch_context\none prompt for ALL pending files\nincludes linter results inline]
    CTX --> AI[review_batch — single OpenRouter call\nreturns comments + explainer text]

    AI --> MAP[Map comments back to files\nCache each file individually]
    CACHED --> MERGE[Merge all comments]
    MAP --> MERGE

    MERGE --> VER{enable_verification?}
    VER -->|yes| VERIFIER[DoubleCheckVerifier\ncritical + major only\nlinter line-match · git history · related files]
    VER -->|no| CLEAR
    VERIFIER --> CLEAR[platform.clear_bot_comments]

    CLEAR --> POST[platform.post_comments\ninline on each diff line]
    POST --> EXPLAIN{explainer text returned?}
    EXPLAIN -->|yes| EXP[post_explainer_summary\nExplainer + Understanding Quiz]
    EXPLAIN -->|no| SUM[post_summary\nStats only]
```

## Pass 1 — Linter Batching

```mermaid
flowchart LR
    items[pending_items] --> group{Group by language}
    group -->|python files| pylint[pylint --output-format=json]
    group -->|js/ts files| eslint[eslint --format=json]
    group -->|dart files| dart[dart analyze --format=json]
    group -->|go files| golangci[golangci-lint --out-format=json]
    group -->|rust files| clippy[cargo clippy --message-format=json]
    pylint --> filter[Filter issues to changed lines only]
    eslint --> filter
    dart --> filter
    golangci --> filter
    clippy --> filter
    filter --> attach[Attach linter_results to each item]
```

One subprocess per language — not one per file. If a linter is not installed, that language group is skipped gracefully.

## Pass 2 — Batch AI Review

All pending files are sent in a single API call. The response is a JSON object:

```json
{
  "comments": [
    {
      "filepath": "src/auth.py",
      "line": 42,
      "severity": "critical",
      "message": "SQL query is not parameterised",
      "suggestion": "Use db.execute(query, params) instead"
    }
  ],
  "explainer": "## What changed in this PR\n..."
}
```

Comments are mapped back to individual files. Each file's comments are cached separately so partial cache hits work on the next run.

## Verification Flow

```mermaid
flowchart TD
    issues[All AI comments] --> split{Severity}
    split -->|minor / suggestion| passthru[Pass through unchanged]
    split -->|critical / major| verify[DoubleCheckVerifier]

    verify --> lcheck{Linter flagged\nsame line?}
    lcheck -->|yes| confirmed[linter_confirmed: true\nlinter_evidence attached]
    lcheck -->|no| kept[linter_confirmed: false\nstill included]

    confirmed --> final[Final issue list]
    kept --> final
    passthru --> final
```

Verification never removes issues — it enriches them with `linter_confirmed` metadata so reviewers know which findings have static-analysis backing.

## Caching Strategy

Cache key: `MD5(filepath + diff + version_string)`

- Version `v6-linter-first` — current pipeline (linter + batch AI)
- Version `v3` — legacy (no linter, per-file AI)

A cache miss on one file does not invalidate others. Stale entries expire after `ttl_days` (default 7).

## Configuration Loading

```mermaid
flowchart LR
    start[ConfigLoader] --> check{.ai-review-config.json\nexists?}
    check -->|yes| load[Load JSON]
    check -->|no| defaults[Use defaults]
    load --> merge[Deep merge with defaults]
    defaults --> merge
    merge --> ready[Config ready]
```

## File Filtering

Applied before any linting or AI call:

1. Hardcoded: skip `.ai-review-config*.json` itself
2. Config `exclusions.directories` — path contains excluded dir
3. Config `exclusions.file_prefixes` — filename starts with prefix
4. Config `exclusions.file_patterns` — glob match on filename or path
5. Binary flag from platform diff API
6. Diff length > 10 000 chars

## Comment Posting

```mermaid
flowchart TD
    comments[All comments] --> clear[clear_bot_comments\nremove previous bot round]
    clear --> inline[post_comments\none inline comment per finding]
    inline --> summary{explainer?}
    summary -->|yes| exp[post_explainer_summary\nmarkdown block: what changed + quiz]
    summary -->|no| stats[post_summary\nfiles reviewed · comments · cache hits]
```

The explainer is a markdown block posted as a single PR-level comment, separate from inline findings. It includes a short description of what changed and a quiz to help reviewers confirm understanding.
