"""GitHub platform adapter"""

import os
from typing import List, Dict, Optional
from github import Github, GithubException
from .base import PlatformAdapter

_BOT_MARKER = "<!-- @kuncie-aireviewer -->"
_NOT_AUTH = "Not authenticated. Call authenticate() first."


class GitHubAdapter(PlatformAdapter):
    """Adapter for GitHub Actions/API"""

    def __init__(self):
        """Initialize GitHub adapter from environment variables"""
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repository_name = os.getenv("GITHUB_REPOSITORY")
        self.pr_number = os.getenv("GITHUB_PR_NUMBER")
        self.base_ref = os.getenv("GITHUB_BASE_REF")
        self.head_ref = os.getenv("GITHUB_HEAD_REF")

        print("=" * 80)
        print("GitHub Adapter Initialization")
        print("=" * 80)
        print(
            f"GITHUB_TOKEN:"
            f" {'✓ Set' if self.github_token else '✗ Missing'}"
        )
        print(f"GITHUB_REPOSITORY: {self.repository_name or '✗ Missing'}")
        print(f"GITHUB_PR_NUMBER: {self.pr_number or '✗ Missing'}")
        print(f"GITHUB_BASE_REF: {self.base_ref or '✗ Missing'}")
        print(f"GITHUB_HEAD_REF: {self.head_ref or '✗ Missing'}")
        print("=" * 80)

        self.gh = None
        self.repo = None
        self.pr = None

    def authenticate(self) -> bool:
        """Authenticate with GitHub"""
        try:
            print("Connecting to GitHub...")
            self.gh = Github(self.github_token)

            print("Authenticating with GitHub...")
            user = self.gh.get_user()
            print(f"✓ Authenticated as: {user.login}")

            print(f"Fetching repository {self.repository_name}...")
            self.repo = self.gh.get_repo(self.repository_name)
            print(f"✓ Repository loaded: {self.repo.full_name}")

            return True

        except GithubException as e:
            print(f"✗ GitHub Authentication Error: {e}")
            print("\nPossible causes:")
            print("1. GITHUB_TOKEN is invalid or expired")
            print("2. Token doesn't have required permissions")
            print("3. Repository not accessible")
            return False

        except Exception as e:
            print(f"✗ Error authenticating with GitHub: {e}")
            return False

    def get_changes(self, pr_number: str) -> List[Dict]:
        """Get changes from pull request"""
        if not self.repo:
            raise RuntimeError(_NOT_AUTH)

        pr = self.repo.get_pull(int(pr_number))
        # Convert PaginatedList to list to ensure all files are fetched
        files = list(pr.get_files())

        changes = []
        for file in files:
            changes.append({
                'filepath': file.filename,
                'diff': file.patch or "",
                'binary': file.patch is None,
                'base_sha': pr.base.sha,
                'head_sha': pr.head.sha,
                'pr': pr
            })

        return changes

    def get_file_content(self, filepath: str, ref: str) -> Optional[str]:
        """Get file content at specific ref"""
        if not self.repo:
            return None

        try:
            content = self.repo.get_contents(filepath, ref=ref)
            return content.decoded_content.decode('utf-8')
        except Exception:
            return None

    def get_directory_tree(self, directory: str, ref: str) -> List[Dict]:
        """Get directory tree (list of files)"""
        if not self.repo:
            return []

        try:
            contents = self.repo.get_contents(directory, ref=ref)
            if not isinstance(contents, list):
                contents = [contents]

            return [
                {
                    'path': item.path,
                    'name': item.name,
                    'type': 'blob' if item.type == 'file' else 'tree'
                }
                for item in contents
            ]
        except Exception as e:
            print(
                f"  Warning: Could not get directory tree"
                f" for {directory}: {e}"
            )
            return []

    def post_comments(self, pr_number: str, comments: List[Dict]) -> None:
        """Post review comments to pull request"""
        if not self.repo:
            raise RuntimeError(_NOT_AUTH)

        pr = self.repo.get_pull(int(pr_number))

        severity_emoji = {
            "critical": "🚨",
            "major": "⚠️",
            "minor": "💡",
            "suggestion": "💭",
        }

        # Get latest commit for review
        commits = pr.get_commits()
        commit = commits[commits.totalCount - 1]

        for comment in comments:
            severity = comment.get("severity", "suggestion")
            emoji = severity_emoji.get(severity, "💬")
            body = (
                f"{_BOT_MARKER}\n"
                f"{emoji} **{comment['severity'].upper()}**:"
                f" {comment['comment']}"
            )

            try:
                # RIGHT = new version, LEFT = old version
                pr.create_review_comment(
                    body=body,
                    commit=commit,
                    path=comment['filepath'],
                    line=comment["line"],
                    side="RIGHT",
                )
                print(
                    f"  ✓ Posted {emoji} comment on"
                    f" {comment['filepath']}:{comment['line']}"
                )
            except Exception as e:
                print(
                    f"  ✗ Error posting comment on"
                    f" {comment['filepath']}:{comment['line']}: {e}"
                )
                print(f"      Comment: {comment['comment'][:100]}...")

    def clear_bot_comments(self, pr_number: str) -> int:
        """Delete all previous bot comments from the pull request"""
        if not self.repo:
            raise RuntimeError(_NOT_AUTH)

        pr = self.repo.get_pull(int(pr_number))
        deleted = 0

        # Delete inline review comments posted by the bot
        for rc in pr.get_review_comments():
            if _BOT_MARKER in rc.body:
                try:
                    rc.delete()
                    deleted += 1
                except Exception as e:
                    print(f"  ⚠ Could not delete review comment {rc.id}: {e}")

        # Delete issue comments (summary) posted by the bot
        for ic in pr.get_issue_comments():
            if _BOT_MARKER in ic.body:
                try:
                    ic.delete()
                    deleted += 1
                except Exception as e:
                    print(f"  ⚠ Could not delete issue comment {ic.id}: {e}")

        if deleted:
            print(f"✓ Cleared {deleted} previous bot comment(s)")
        else:
            print("⊘ No previous bot comments to clear")

        return deleted

    def post_summary(
        self, pr_number: str, stats: Dict, comments: List[Dict]
    ) -> None:
        """Post review summary to pull request"""
        if not self.repo:
            raise RuntimeError(_NOT_AUTH)

        pr = self.repo.get_pull(int(pr_number))

        if comments:
            critical = sum(
                1 for c in comments if c.get("severity") == "critical"
            )
            major = sum(
                1 for c in comments if c.get("severity") == "major"
            )
            minor = sum(
                1 for c in comments if c.get("severity") == "minor"
            )
            suggestions = sum(
                1 for c in comments if c.get("severity") == "suggestion"
            )

            summary = f"""## 🤖 AI Code Review Summary

### Review Statistics
- **Files Reviewed**: {stats['files_reviewed']}
- **Files Skipped**: {stats['files_skipped']}
- **Files Excluded**: {stats['files_excluded']}
- **Total Comments**: {len(comments)}

### Findings by Severity
- 🚨 **Critical**: {critical}
- ⚠️ **Major**: {major}
- 💡 **Minor**: {minor}
- 💭 **Suggestions**: {suggestions}

### Review Approach
This review analyzed:
- Full file context (before and after changes)
- Project documentation
- Related files and dependencies
- Project architecture and patterns
- Change impact and potential risks

Please review the inline comments for details."""
        else:
            summary = f"""## 🤖 AI Code Review

### Review Statistics
- **Files Reviewed**: {stats['files_reviewed']}
- **Files Skipped**: {stats['files_skipped']}
- **Files Excluded**: {stats['files_excluded']}

✅ **No issues found**. Code looks good!"""

        pr.create_issue_comment(f"{_BOT_MARKER}\n{summary}")
        print("✓ Posted review summary")
