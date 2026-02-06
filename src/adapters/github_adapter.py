"""GitHub platform adapter"""

import os
from typing import List, Dict, Optional
from github import Github, GithubException
from .base import PlatformAdapter


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
        print(f"GITHUB_TOKEN: {'✓ Set' if self.github_token else '✗ Missing'}")
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
            raise Exception("Not authenticated. Call authenticate() first.")

        pr = self.repo.get_pull(int(pr_number))
        files = pr.get_files()

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
            # Get contents of directory at specific ref
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
            print(f"  Warning: Could not get directory tree for {directory}: {e}")
            return []

    def post_comments(self, pr_number: str, comments: List[Dict]) -> None:
        """Post review comments to pull request"""
        if not self.repo:
            raise Exception("Not authenticated. Call authenticate() first.")

        pr = self.repo.get_pull(int(pr_number))

        severity_emoji = {
            "critical": "🚨",
            "major": "⚠️",
            "minor": "💡",
            "suggestion": "💭",
        }

        # Get latest commit for review
        commit = pr.get_commits().reversed[0]

        for comment in comments:
            emoji = severity_emoji.get(comment.get("severity", "suggestion"), "💬")
            body = f"{emoji} **{comment['severity'].upper()}**: {comment['comment']}"

            try:
                # GitHub API requires comments to be on lines that are part of the diff
                # The 'line' should be the line number in the new version of the file
                pr.create_review_comment(
                    body=body,
                    commit=commit,
                    path=comment['filepath'],
                    line=comment["line"],
                    side="RIGHT"  # RIGHT = new version, LEFT = old version
                )
                print(f"  ✓ Posted {emoji} comment on {comment['filepath']}:{comment['line']}")
            except Exception as e:
                print(f"  ✗ Error posting comment on {comment['filepath']}:{comment['line']}: {e}")
                print(f"      Comment: {comment['comment'][:100]}...")

    def post_summary(self, pr_number: str, stats: Dict, comments: List[Dict]) -> None:
        """Post review summary to pull request"""
        if not self.repo:
            raise Exception("Not authenticated. Call authenticate() first.")

        pr = self.repo.get_pull(int(pr_number))

        if comments:
            critical = sum(1 for c in comments if c.get("severity") == "critical")
            major = sum(1 for c in comments if c.get("severity") == "major")
            minor = sum(1 for c in comments if c.get("severity") == "minor")
            suggestions = sum(1 for c in comments if c.get("severity") == "suggestion")

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

        pr.create_issue_comment(summary)
        print(f"✓ Posted review summary")
