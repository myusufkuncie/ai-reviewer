"""GitLab platform adapter"""

import os
import gitlab
from typing import List, Dict, Optional
from .base import PlatformAdapter

_BOT_MARKER = "<!-- @kuncie-aireviewer -->"
_NOT_AUTH = "Not authenticated. Call authenticate() first."


class GitLabAdapter(PlatformAdapter):
    """Adapter for GitLab CI/API"""

    def __init__(self):
        """Initialize GitLab adapter from environment variables"""
        self.gitlab_token = os.getenv("GITLAB_TOKEN")
        self.ci_server_url = os.getenv("CI_SERVER_URL")
        self.ci_project_id = os.getenv("CI_PROJECT_ID")
        self.ci_mr_iid = os.getenv("CI_MERGE_REQUEST_IID")

        print("=" * 80)
        print("GitLab Adapter Initialization")
        print("=" * 80)
        print(
            f"GITLAB_TOKEN:"
            f" {'✓ Set' if self.gitlab_token else '✗ Missing'}"
        )
        print(f"CI_SERVER_URL: {self.ci_server_url or '✗ Missing'}")
        print(f"CI_PROJECT_ID: {self.ci_project_id or '✗ Missing'}")
        print(
            f"CI_MERGE_REQUEST_IID: {self.ci_mr_iid or '✗ Missing'}"
        )
        print("=" * 80)

        self.gl = None
        self.project = None
        self.mr = None

    def authenticate(self) -> bool:
        """Authenticate with GitLab"""
        try:
            print(f"Connecting to GitLab at {self.ci_server_url}...")
            self.gl = gitlab.Gitlab(
                url=self.ci_server_url,
                private_token=self.gitlab_token,
            )

            print("Authenticating with GitLab...")
            self.gl.auth()
            print(f"✓ Authenticated as: {self.gl.user.username}")

            print(f"Fetching project {self.ci_project_id}...")
            self.project = self.gl.projects.get(self.ci_project_id)
            print(f"✓ Project loaded: {self.project.name}")

            return True

        except gitlab.exceptions.GitlabAuthenticationError as e:
            print(f"✗ GitLab Authentication Error: {e}")
            print("\nPossible causes:")
            print("1. GITLAB_TOKEN is invalid or expired")
            print("2. Token doesn't have 'api' or 'read_api' scope")
            print("3. Token doesn't have access to this project")
            return False

        except Exception as e:
            print(f"✗ Error authenticating with GitLab: {e}")
            return False

    def get_changes(self, mr_iid: str) -> List[Dict]:
        """Get changes from merge request"""
        if not self.project:
            raise RuntimeError(_NOT_AUTH)

        mr = self.project.mergerequests.get(mr_iid)
        changes_data = mr.changes()

        changes = []
        for change in changes_data["changes"]:
            changes.append({
                'filepath': change["new_path"],
                'diff': change["diff"],
                'binary': change.get("binary", False),
                'base_sha': mr.diff_refs["base_sha"],
                'head_sha': mr.diff_refs["head_sha"],
                'mr': mr
            })

        return changes

    def get_file_content(self, filepath: str, ref: str) -> Optional[str]:
        """Get file content at specific ref"""
        if not self.project:
            return None

        try:
            file_content = self.project.files.get(
                file_path=filepath, ref=ref
            )
            return file_content.decode().decode('utf-8')
        except Exception:
            return None

    def get_directory_tree(self, directory: str, ref: str) -> List[Dict]:
        """Get directory tree (list of files)"""
        if not self.project:
            return []

        try:
            items = self.project.repository_tree(
                path=directory,
                ref=ref,
                recursive=False,
                get_all=True,
            )
            return [
                {
                    'path': item['path'],
                    'name': item['name'],
                    'type': item['type'],
                }
                for item in items
            ]
        except Exception as e:
            print(
                f"  Warning: Could not get directory tree"
                f" for {directory}: {e}"
            )
            return []

    def post_comments(self, mr_iid: str, comments: List[Dict]) -> None:
        """Post review comments to merge request"""
        if not self.project:
            raise RuntimeError(_NOT_AUTH)

        mr = self.project.mergerequests.get(mr_iid)

        severity_emoji = {
            "critical": "🚨",
            "major": "⚠️",
            "minor": "💡",
            "suggestion": "💭",
        }

        for comment in comments:
            severity = comment.get("severity", "suggestion")
            emoji = severity_emoji.get(severity, "💬")
            body = (
                f"{_BOT_MARKER}\n"
                f"{emoji} **{comment['severity'].upper()}**:"
                f" {comment['comment']}"
            )

            try:
                mr.discussions.create({
                    "body": body,
                    "position": {
                        "base_sha": mr.diff_refs["base_sha"],
                        "start_sha": mr.diff_refs["start_sha"],
                        "head_sha": mr.diff_refs["head_sha"],
                        "position_type": "text",
                        "new_path": comment['filepath'],
                        "new_line": comment["line"],
                        "old_path": comment['filepath'],
                    },
                })
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

    def _delete_discussion_note(
        self, mr, discussion_id: str, note_id: int
    ) -> bool:
        """Delete a single discussion note. Returns True on success."""
        try:
            discussion_obj = mr.discussions.get(discussion_id)
            discussion_obj.notes.delete(note_id)
            return True
        except Exception as e:
            print(f"  ⚠ Could not delete discussion note {note_id}: {e}")
            return False

    def _delete_mr_note(self, mr, note_id: int) -> bool:
        """Delete a single MR note. Returns True on success."""
        try:
            mr.notes.delete(note_id)
            return True
        except Exception as e:
            print(f"  ⚠ Could not delete note {note_id}: {e}")
            return False

    def _clear_bot_discussions(self, mr) -> int:
        """Delete bot inline discussion notes. Returns count deleted."""
        deleted = 0
        for discussion in mr.discussions.list(get_all=True):
            for note in discussion.attributes.get('notes', []):
                is_bot = _BOT_MARKER in note.get('body', '')
                if is_bot and self._delete_discussion_note(
                    mr, discussion.id, note['id']
                ):
                    deleted += 1
        return deleted

    def _clear_bot_notes(self, mr) -> int:
        """Delete bot general MR notes. Returns count deleted."""
        deleted = 0
        for note in mr.notes.list(get_all=True):
            if _BOT_MARKER in note.body and self._delete_mr_note(
                mr, note.id
            ):
                deleted += 1
        return deleted

    def clear_bot_comments(self, mr_iid: str) -> int:
        """Delete all previous bot comments from the merge request"""
        if not self.project:
            raise RuntimeError(_NOT_AUTH)

        mr = self.project.mergerequests.get(mr_iid)
        deleted = (
            self._clear_bot_discussions(mr) + self._clear_bot_notes(mr)
        )

        if deleted:
            print(f"✓ Cleared {deleted} previous bot comment(s)")
        else:
            print("⊘ No previous bot comments to clear")

        return deleted

    def post_summary(
        self, mr_iid: str, stats: Dict, comments: List[Dict]
    ) -> None:
        """Post review summary to merge request"""
        if not self.project:
            raise RuntimeError(_NOT_AUTH)

        mr = self.project.mergerequests.get(mr_iid)

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

        mr.notes.create({"body": f"{_BOT_MARKER}\n{summary}"})
        print("✓ Posted review summary")
