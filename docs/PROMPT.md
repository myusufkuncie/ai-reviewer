# AI Prompt Reference

This document describes the exact prompts sent to the AI model during a review.

There are two separate AI calls: the **main review call** and the **verification call**.

---

## 1. Main Review Prompt

**Source**: `src/analyzers/context_builder.py` → `build_batch_context()`  
**Used in**: `src/adapters/openrouter_provider.py` → `review_batch()`  
**API shape**:

```json
{
  "model": "<configured model>",
  "messages": [{ "role": "user", "content": "<full context below>" }],
  "temperature": 0.3
}
```

The content is assembled in sections in this order:

---

### Section 1 — Batch Header

```text
# BATCH CODE REVIEW

Reviewing N file(s) in this batch.

## Pull Request: {pr_title}

**PR Description**: {pr_description}
```

---

### Section 2 — Shared Project Context (fetched once per PR)

```text
## Project Overview (from README.md)
...readme content...

## Docker Configuration
### Dockerfile
...dockerfile content...

## Docker Compose
...compose content...

## Project Architecture
- Language: python
- Framework: django
- Key dependencies: requests, celery, redis, ...
```

---

### Section 3 — Per-file blocks (repeated for each changed file)

````text
# FILE N: {filepath}
**Language**: python | **Framework**: django | **Change scope**: MAJOR

**Risks**: api_change, auth_logic

**Imports**: os, json, requests, ...

### Changed Symbols — BEFORE
```
<code before change>
```

### Changed Symbols — AFTER (with line numbers)
**IMPORTANT**: Use the line numbers from the full file listing below for inline comments.
```
<code after change>
```

### Full File AFTER (with line numbers)
```
   1 | import os
   2 | ...
```

### Callers in this PR (N file(s) that import this file)
**other_file.py**
```
<caller file content>
```

### Linter Results (N issues)
- Line 42: ERROR - undefined variable 'x'
  Rule: E0602

### Diff
```diff
- old line
+ new line
```
````

---

### Section 4 — Review Instructions (the actual prompt)

````text
## Review Instructions

You are an expert code reviewer. Do two things in a single response:

**PART 1 — Inline Comments (JSON)**
Find all bugs, security issues, performance problems, and style issues.

**PART 2 — PR Explainer + Understanding Quiz (Markdown)**
Write a structured PR explainer with this exact format:

### 1. Explainer

**Background**
Briefly explain the existing system/code this PR touches. What was already there?
What concepts does a reader need before looking at the diff?

**Goal & Intuition**
In plain language, what is this PR trying to achieve?
Explain the core idea before showing any code.

**Literate Walkthrough**
Walk through the important changes in logical order (not file order).
For each major change:
- Explain *why* it was done this way
- Show a small relevant code snippet
- Point out key decisions, trade-offs, or gotchas

### 2. Review Comments
Summarize the most important issues you found. If none, say so clearly.

### 3. Understanding Quiz
Write 4-6 short questions the author/reviewer must answer before merging.
Test real understanding, not trivia:
- Why was approach X chosen over Y?
- What happens in edge case Z?
- Which invariant does this change preserve or risk breaking?
- Where exactly does the new state transition happen?

---

Return a single JSON object with this structure:
{
  "comments": [
    {
      "filepath": "<exact filepath from FILE N header>",
      "line": <line_number from the Full File AFTER section>,
      "comment": "<detailed comment>",
      "severity": "critical|major|minor|suggestion"
    }
  ],
  "explainer": "<the full Explainer + Quiz markdown as a single escaped string>"
}

Use empty array for "comments" if code looks good. Always include "explainer".
````

---

## 2. Verification Prompt (2nd-pass)

**Source**: `src/verification/verifier.py` → `_build_verification_prompt()`  
**Used in**: `src/adapters/openrouter_provider.py` → `verify_issue()`  
**Triggered**: only for high-severity comments when `enable_verification=True`  
**API shape**:

```json
{
  "model": "<configured model>",
  "messages": [{ "role": "user", "content": "<prompt below>" }],
  "max_tokens": 1000,
  "temperature": 0.2
}
```

### Prompt

````text
You are re-verifying a potential code issue. Your job is to determine if this is a REAL issue or a FALSE POSITIVE.

FILE: {filepath}

ORIGINAL ISSUE DETECTED:
- Severity: {severity}
- Message: {message}
- Line: {line}
- Suggestion: {suggestion}

GATHERED EVIDENCE:

### Git History:
- abc1234: commit message (author, date)
- ...

### Related Files (N files):

#### other_file.py:
```
<file content excerpt>
```

ORIGINAL REVIEW CONTEXT (excerpt):
{first 1500 chars of the main review context}...

YOUR TASK:
Carefully analyze the issue with the evidence provided. Answer these questions:
1. Is this a REAL issue that will cause problems?
2. Does the evidence (git history, related files) change your assessment?
3. Is the severity level appropriate?

Respond in JSON format:
{
    "confirmed": true/false,
    "reasoning": "Detailed explanation of your decision",
    "updated_severity": "critical/major/minor/suggestion",
    "confidence": "high/medium/low"
}

Be strict - only confirm issues that are DEFINITELY problems. When in doubt, dismiss as false positive.
````

---

## Flow Summary

```text
build_batch_context()        ← all sections assembled here
       │
       ▼
review_batch(context)        ← single API call, temperature 0.3
       │
       ▼
parse {"comments", "explainer"}
       │
       ├── for each high-severity comment:
       │       verify_issue(verification_prompt)   ← separate call, temperature 0.2
       │       parse {"confirmed", "reasoning", "updated_severity", "confidence"}
       │
       ▼
post_comments() + post_explainer_summary()
```

---

## Customising the Prompt

The review instructions (Section 4) are hardcoded in `context_builder.py:920-970`. To change what the AI focuses on, edit that string directly. There is also support for a `.ai-review-prompts.json` file for language-specific guidance — see [FEATURES.md](FEATURES.md#configuration).
