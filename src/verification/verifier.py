"""Double-check verification orchestrator with linter integration"""

import json
from typing import List, Dict, Any, Optional
from ..tools.registry import ToolRegistry


class DoubleCheckVerifier:
    """Orchestrates 2-pass verification for code review issues"""

    def __init__(self, ai_provider, tool_registry: ToolRegistry, language_detector=None, config=None):
        """Initialize verifier

        Args:
            ai_provider: AI provider adapter
            tool_registry: Tool registry with available tools
            language_detector: Language detector for determining file language
            config: Configuration loader (optional)
        """
        self.ai_provider = ai_provider
        self.tool_registry = tool_registry
        self.language_detector = language_detector
        self.config = config

        # Severity levels that trigger verification
        self.verify_severities = {'critical', 'major'}

    def verify_issues(
        self,
        initial_issues: List[Dict],
        context: str,
        filepath: str,
        language: str = None,
        changed_lines: List[int] = None
    ) -> List[Dict]:
        """Run 2-pass verification on issues

        Args:
            initial_issues: Issues from Pass 1 (initial detection)
            context: Original review context
            filepath: File being reviewed
            language: Programming language (optional, will auto-detect)
            changed_lines: List of changed line numbers (for linter filtering)

        Returns:
            Verified issues (with linter evidence)
        """
        if not initial_issues:
            return []

        print(f"\n{'='*80}")
        print("DOUBLE-CHECK VERIFICATION STARTED")
        print(f"{'='*80}")

        # Separate issues by severity
        high_severity_issues = [
            issue for issue in initial_issues
            if issue.get('severity', '').lower() in self.verify_severities
        ]
        other_issues = [
            issue for issue in initial_issues
            if issue.get('severity', '').lower() not in self.verify_severities
        ]

        print(f"Pass 1 Results: {len(initial_issues)} total issues")
        print(f"  → {len(high_severity_issues)} Critical/Major (will verify)")
        print(f"  → {len(other_issues)} Minor/Suggestions (auto-pass)")

        if not high_severity_issues:
            print("No high-severity issues to verify")
            return initial_issues

        # Detect language if not provided
        if not language and self.language_detector:
            language = self.language_detector.detect_language(filepath)
            print(f"Detected language: {language}")

        # Run verification on high-severity issues
        verified_issues = []
        for idx, issue in enumerate(high_severity_issues, 1):
            print(f"\n{'-'*80}")
            print(f"Verifying Issue {idx}/{len(high_severity_issues)}")
            print(f"Severity: {issue.get('severity', 'unknown')}")
            print(f"Message: {issue.get('message', 'N/A')[:80]}...")
            print(f"{'-'*80}")

            # Pass 2: Gather evidence (linter + git + related files)
            evidence = self._gather_evidence(
                issue, filepath, language, changed_lines
            )

            # Check if linter confirms the issue
            linter_confirms = self._check_linter_confirmation(issue, evidence)

            if linter_confirms:
                # Issue confirmed by linter - definitely real
                issue['linter_confirmed'] = True
                issue['linter_evidence'] = linter_confirms
                verified_issues.append(issue)
                print(f"✓ Issue CONFIRMED by linter")
            else:
                # No linter confirmation - still might be valid
                # Keep it but mark as not linter-confirmed
                issue['linter_confirmed'] = False
                verified_issues.append(issue)
                print(f"→ Issue kept (no linter confirmation, but may still be valid)")

        # Combine verified high-severity issues with other issues
        final_issues = verified_issues + other_issues

        print(f"\n{'='*80}")
        print("VERIFICATION COMPLETE")
        print(f"Before: {len(initial_issues)} issues")
        print(f"After:  {len(final_issues)} issues")
        print(f"Linter confirmed: {sum(1 for i in verified_issues if i.get('linter_confirmed'))} issues")
        print(f"{'='*80}\n")

        return final_issues

    def _gather_evidence(
        self,
        issue: Dict,
        filepath: str,
        language: str = None,
        changed_lines: List[int] = None
    ) -> Dict[str, Any]:
        """Pass 2: Gather evidence for an issue

        Args:
            issue: Issue to gather evidence for
            filepath: File being reviewed
            language: Programming language
            changed_lines: List of changed line numbers

        Returns:
            Evidence dictionary
        """
        print("Pass 2: Gathering evidence...")
        evidence = {
            "git_history": None,
            "linter_results": None,
            "related_files": []
        }

        try:
            # 1. Run linter on changed lines only (TOKEN EFFICIENT!)
            if language:
                print(f"  → Running {language} linter on changed lines...")
                linter_result = self.tool_registry.execute_tool(
                    "run_linter",
                    filepath=filepath,
                    language=language,
                    changed_lines=changed_lines or []
                )
                if linter_result.success:
                    evidence["linter_results"] = linter_result.data
                    summary = linter_result.data.get('summary', {})
                    print(f"    Linter: {summary.get('error', 0)} errors, "
                          f"{summary.get('warning', 0)} warnings "
                          f"(filtered to {linter_result.data.get('filtered_issues', 0)} issues)")
                    print(f"    Token saved: {linter_result.data.get('token_saved', 'N/A')}")
                else:
                    print(f"    Linter not available: {linter_result.error}")

            # 2. Get git history for context
            print("  → Checking git history...")
            git_result = self.tool_registry.execute_tool(
                "git_history",
                filepath=filepath,
                max_commits=3
            )
            if git_result.success:
                evidence["git_history"] = git_result.data
                print(f"    Found {git_result.data.get('count', 0)} commits")

            # 3. Read related files (only if issue mentions them)
            issue_msg = issue.get('message', '').lower()
            issue_code = issue.get('suggestion', '').lower()
            potential_files = self._extract_file_references(issue_msg + " " + issue_code)

            if potential_files:
                print(f"  → Reading {len(potential_files)} related files...")
                for related_file in potential_files[:2]:  # Limit to 2 files for token efficiency
                    file_result = self.tool_registry.execute_tool(
                        "read_file",
                        filepath=related_file
                    )
                    if file_result.success:
                        evidence["related_files"].append(file_result.data)
                        print(f"    Read: {related_file}")

        except Exception as e:
            print(f"  ⚠ Error gathering evidence: {e}")

        return evidence

    def _check_linter_confirmation(self, issue: Dict, evidence: Dict) -> Optional[Dict]:
        """Check if linter confirms the AI-detected issue

        Args:
            issue: AI-detected issue
            evidence: Evidence with linter results

        Returns:
            Linter evidence dict if confirmed, None otherwise
        """
        linter_results = evidence.get("linter_results")
        if not linter_results or not linter_results.get("issues"):
            return None

        ai_line = issue.get('line')
        if not ai_line:
            return None

        # Check if linter found issues on the same line
        for linter_issue in linter_results.get("issues", []):
            if linter_issue.get('line') == ai_line:
                # Linter confirms issue on same line!
                return {
                    "line": linter_issue['line'],
                    "severity": linter_issue['severity'],
                    "message": linter_issue['message'],
                    "rule": linter_issue.get('rule', 'unknown'),
                    "linter_agrees": True
                }

        return None

    def _reverify_with_evidence(self, issue: Dict, evidence: Dict, original_context: str, filepath: str) -> Dict:
        """Pass 3: Re-verify issue with gathered evidence

        Args:
            issue: Original issue
            evidence: Gathered evidence
            original_context: Original review context
            filepath: File path

        Returns:
            Verified issue (potentially modified) or None if dismissed
        """
        print("Pass 3: Re-verifying with evidence...")

        # Build verification prompt
        verification_prompt = self._build_verification_prompt(
            issue, evidence, original_context, filepath
        )

        try:
            # Call AI for verification
            verification_result = self.ai_provider.verify_issue(verification_prompt)

            # Parse verification result
            if verification_result.get("confirmed", False):
                # Issue confirmed - update with verification notes
                verified_issue = issue.copy()
                verified_issue["verified"] = True
                verified_issue["verification_reasoning"] = verification_result.get("reasoning", "")

                # Update severity if AI suggests downgrade
                new_severity = verification_result.get("updated_severity")
                if new_severity and new_severity.lower() != issue.get("severity", "").lower():
                    print(f"  → Severity adjusted: {issue.get('severity')} → {new_severity}")
                    verified_issue["severity"] = new_severity

                return verified_issue
            else:
                # Issue dismissed
                print(f"  → AI dismissed: {verification_result.get('reasoning', 'No reason')}")
                return None

        except Exception as e:
            print(f"  ⚠ Verification failed: {e}")
            # On error, keep original issue (fail-safe)
            return issue

    def _build_verification_prompt(self, issue: Dict, evidence: Dict, original_context: str, filepath: str) -> str:
        """Build prompt for Pass 3 verification

        Args:
            issue: Issue to verify
            evidence: Gathered evidence
            original_context: Original context
            filepath: File path

        Returns:
            Verification prompt
        """
        prompt = f"""You are re-verifying a potential code issue. Your job is to determine if this is a REAL issue or a FALSE POSITIVE.

FILE: {filepath}

ORIGINAL ISSUE DETECTED:
- Severity: {issue.get('severity', 'unknown')}
- Message: {issue.get('message', 'N/A')}
- Line: {issue.get('line', 'N/A')}
- Suggestion: {issue.get('suggestion', 'N/A')}

GATHERED EVIDENCE:
"""

        # Add git history
        if evidence.get("git_history") and evidence["git_history"].get("commits"):
            prompt += "\n### Git History:\n"
            for commit in evidence["git_history"]["commits"][:3]:
                prompt += f"- {commit['hash']}: {commit['message']} ({commit['author']}, {commit['date']})\n"

        # Add related files
        if evidence.get("related_files"):
            prompt += f"\n### Related Files ({len(evidence['related_files'])} files):\n"
            for file_data in evidence["related_files"]:
                prompt += f"\n#### {file_data['filepath']}:\n```\n{file_data['content'][:1000]}...\n```\n"

        prompt += f"""

ORIGINAL REVIEW CONTEXT (excerpt):
{original_context[:1500]}...

YOUR TASK:
Carefully analyze the issue with the evidence provided. Answer these questions:
1. Is this a REAL issue that will cause problems?
2. Does the evidence (git history, related files) change your assessment?
3. Is the severity level appropriate?

Respond in JSON format:
{{
    "confirmed": true/false,
    "reasoning": "Detailed explanation of your decision",
    "updated_severity": "critical/major/minor/suggestion" (only if you want to change it),
    "confidence": "high/medium/low"
}}

Be strict - only confirm issues that are DEFINITELY problems. When in doubt, dismiss as false positive.
"""

        return prompt

    def _extract_file_references(self, text: str) -> List[str]:
        """Extract potential file references from text

        Simple heuristic to find file paths mentioned in issues

        Args:
            text: Text to search

        Returns:
            List of potential file paths
        """
        import re

        # Pattern for file paths (simplified)
        # Matches things like: src/utils/auth.py, components/Button.tsx, etc.
        pattern = r'\b[a-zA-Z0-9_\-/]+\.[a-zA-Z]{2,4}\b'
        matches = re.findall(pattern, text)

        # Filter out common false positives
        filtered = [
            m for m in matches
            if not m.startswith('http') and
               not m.startswith('www.') and
               m.count('/') > 0  # Likely a path with directory
        ]

        return filtered[:5]  # Limit to 5 files
