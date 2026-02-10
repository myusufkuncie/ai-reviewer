"""Smart linter tool with filtered output for token efficiency"""

import subprocess
import json
import re
import time
from typing import Dict, Any, List, Set
from .base import Tool, ToolResult


class LinterTool(Tool):
    """Tool to run language-specific linters with filtered output"""

    # Language to linter mapping
    LINTER_COMMANDS = {
        'python': {
            'command': ['pylint', '--output-format=json'],
            'fallback': ['flake8', '--format=json'],
            'check_installed': 'pylint --version'
        },
        'javascript': {
            'command': ['eslint', '--format=json'],
            'check_installed': 'eslint --version'
        },
        'typescript': {
            'command': ['eslint', '--format=json', '--ext', '.ts,.tsx'],
            'check_installed': 'eslint --version'
        },
        'dart': {
            'command': ['dart', 'analyze', '--format=json'],
            'check_installed': 'dart --version'
        },
        'go': {
            'command': ['golangci-lint', 'run', '--out-format=json'],
            'fallback': ['go', 'vet'],
            'check_installed': 'golangci-lint --version'
        },
        'rust': {
            'command': ['cargo', 'clippy', '--message-format=json'],
            'check_installed': 'cargo --version'
        },
        'java': {
            'command': ['checkstyle', '-f', 'json'],
            'check_installed': 'checkstyle --version'
        },
        'php': {
            'command': ['phpcs', '--report=json'],
            'fallback': ['php', '-l'],  # Fallback to syntax check
            'check_installed': 'phpcs --version'
        }
    }

    def __init__(self, repo_path: str = "."):
        """Initialize linter tool

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path

    @property
    def name(self) -> str:
        return "run_linter"

    @property
    def description(self) -> str:
        return (
            "Run language-specific linter on a file and return issues "
            "ONLY for the specified line range. This is token-efficient "
            "because it filters out issues from unchanged code."
        )

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "filepath": {
                "type": "string",
                "description": "Path to file to lint (e.g., 'src/auth.py')",
                "required": True
            },
            "language": {
                "type": "string",
                "description": "Programming language (python, javascript, typescript, dart, go, rust, java)",
                "required": True
            },
            "changed_lines": {
                "type": "array",
                "description": "Array of changed line numbers [45, 46, 47, 48] to filter linter output. Only issues on these lines will be returned.",
                "required": False
            }
        }

    def execute(self, **kwargs) -> ToolResult:
        """Run linter with smart filtering

        Args:
            filepath: File to lint
            language: Programming language
            changed_lines: List of changed line numbers (optional)

        Returns:
            ToolResult with filtered linter issues
        """
        filepath = kwargs.get("filepath")
        language = kwargs.get("language", "").lower()
        changed_lines = kwargs.get("changed_lines", [])

        if not filepath:
            return ToolResult(
                success=False,
                data=None,
                error="filepath parameter is required"
            )

        if language not in self.LINTER_COMMANDS:
            return ToolResult(
                success=False,
                data=None,
                error=f"Unsupported language: {language}. Supported: {', '.join(self.LINTER_COMMANDS.keys())}"
            )

        # Check if linter is installed
        linter_config = self.LINTER_COMMANDS[language]
        if not self._is_linter_installed(linter_config):
            return ToolResult(
                success=False,
                data=None,
                error=f"Linter not installed for {language}. Install with: pip install pylint (or equivalent)"
            )

        # Run linter
        try:
            linter_output = self._run_linter(filepath, language, linter_config)

            # Parse and filter issues
            issues = self._parse_linter_output(linter_output, language)

            # Filter to changed lines only (TOKEN EFFICIENCY!)
            if changed_lines:
                changed_lines_set = set(changed_lines)
                filtered_issues = [
                    issue for issue in issues
                    if issue.get('line') in changed_lines_set
                ]
            else:
                filtered_issues = issues

            # Aggregate by severity for summary
            summary = self._aggregate_issues(filtered_issues)

            return ToolResult(
                success=True,
                data={
                    "filepath": filepath,
                    "language": language,
                    "total_issues": len(issues),
                    "filtered_issues": len(filtered_issues),
                    "changed_lines_count": len(changed_lines) if changed_lines else "all",
                    "summary": summary,
                    "issues": filtered_issues[:10],  # Limit to 10 most important
                    "token_saved": f"{len(issues) - len(filtered_issues)} issues filtered out"
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Linter execution failed: {str(e)}"
            )

    def _is_linter_installed(self, linter_config: Dict) -> bool:
        """Check if linter is installed

        Args:
            linter_config: Linter configuration

        Returns:
            True if installed
        """
        try:
            check_cmd = linter_config.get('check_installed', '').split()
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_linter(self, filepath: str, language: str, linter_config: Dict) -> str:
        """Run linter command

        Args:
            filepath: File to lint
            language: Language
            linter_config: Linter configuration

        Returns:
            Linter output as string
        """
        cmd = linter_config['command'] + [filepath]

        _t0 = time.time()
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        print(f"  → Linter subprocess: +{time.time() - _t0:.2f}s ({' '.join(cmd[:2])}...)")

        # Some linters exit with non-zero when issues found
        # This is expected, so we capture output anyway
        return result.stdout or result.stderr

    def _parse_linter_output(self, output: str, language: str) -> List[Dict]:
        """Parse linter output to standard format

        Args:
            output: Raw linter output
            language: Programming language

        Returns:
            List of standardized issue dictionaries
        """
        issues = []

        try:
            if language == 'python':
                issues = self._parse_pylint_output(output)
            elif language in ['javascript', 'typescript']:
                issues = self._parse_eslint_output(output)
            elif language == 'dart':
                issues = self._parse_dart_output(output)
            elif language == 'go':
                issues = self._parse_golangci_output(output)
            elif language == 'rust':
                issues = self._parse_clippy_output(output)
            elif language == 'php':
                issues = self._parse_phpcs_output(output)
        except Exception as e:
            print(f"Warning: Failed to parse linter output: {e}")

        return issues

    def _parse_pylint_output(self, output: str) -> List[Dict]:
        """Parse pylint JSON output"""
        issues = []
        try:
            data = json.loads(output) if output.strip() else []
            for item in data:
                issues.append({
                    'line': item.get('line', 0),
                    'column': item.get('column', 0),
                    'severity': self._map_severity(item.get('type', 'info')),
                    'message': item.get('message', ''),
                    'rule': item.get('symbol', ''),
                    'code': item.get('message-id', '')
                })
        except json.JSONDecodeError:
            pass
        return issues

    def _parse_eslint_output(self, output: str) -> List[Dict]:
        """Parse ESLint JSON output"""
        issues = []
        try:
            data = json.loads(output) if output.strip() else []
            for file_result in data:
                for msg in file_result.get('messages', []):
                    issues.append({
                        'line': msg.get('line', 0),
                        'column': msg.get('column', 0),
                        'severity': self._map_severity(str(msg.get('severity', 1))),
                        'message': msg.get('message', ''),
                        'rule': msg.get('ruleId', ''),
                        'code': msg.get('ruleId', '')
                    })
        except json.JSONDecodeError:
            pass
        return issues

    def _parse_dart_output(self, output: str) -> List[Dict]:
        """Parse Dart analyze output"""
        issues = []
        try:
            data = json.loads(output) if output.strip() else {}
            for diagnostic in data.get('diagnostics', []):
                location = diagnostic.get('location', {})
                issues.append({
                    'line': location.get('startLine', 0),
                    'column': location.get('startColumn', 0),
                    'severity': self._map_severity(diagnostic.get('severity', 'info')),
                    'message': diagnostic.get('message', ''),
                    'rule': diagnostic.get('code', ''),
                    'code': diagnostic.get('code', '')
                })
        except json.JSONDecodeError:
            pass
        return issues

    def _parse_golangci_output(self, output: str) -> List[Dict]:
        """Parse golangci-lint JSON output"""
        issues = []
        try:
            data = json.loads(output) if output.strip() else {}
            for issue in data.get('Issues', []):
                pos = issue.get('Pos', {})
                issues.append({
                    'line': pos.get('Line', 0),
                    'column': pos.get('Column', 0),
                    'severity': self._map_severity(issue.get('Severity', 'warning')),
                    'message': issue.get('Text', ''),
                    'rule': issue.get('FromLinter', ''),
                    'code': issue.get('FromLinter', '')
                })
        except json.JSONDecodeError:
            pass
        return issues

    def _parse_clippy_output(self, output: str) -> List[Dict]:
        """Parse Rust Clippy output (line-delimited JSON)"""
        issues = []
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if data.get('reason') == 'compiler-message':
                    message = data.get('message', {})
                    spans = message.get('spans', [])
                    if spans:
                        span = spans[0]
                        issues.append({
                            'line': span.get('line_start', 0),
                            'column': span.get('column_start', 0),
                            'severity': self._map_severity(message.get('level', 'warning')),
                            'message': message.get('message', ''),
                            'rule': message.get('code', {}).get('code', ''),
                            'code': message.get('code', {}).get('code', '')
                        })
            except json.JSONDecodeError:
                continue
        return issues

    def _parse_phpcs_output(self, output: str) -> List[Dict]:
        """Parse PHP CodeSniffer JSON output"""
        issues = []
        try:
            data = json.loads(output) if output.strip() else {}
            # phpcs returns {"files": {"filepath": {"messages": [...]}}}
            for filepath, file_data in data.get('files', {}).items():
                for msg in file_data.get('messages', []):
                    issues.append({
                        'line': msg.get('line', 0),
                        'column': msg.get('column', 0),
                        'severity': self._map_severity(msg.get('type', 'warning')),
                        'message': msg.get('message', ''),
                        'rule': msg.get('source', ''),
                        'code': msg.get('source', '')
                    })
        except json.JSONDecodeError:
            pass
        return issues

    def _map_severity(self, severity: str) -> str:
        """Map linter severity to standard levels

        Args:
            severity: Linter-specific severity

        Returns:
            Standard severity (error, warning, info)
        """
        severity_lower = str(severity).lower()

        if severity_lower in ['error', 'fatal', '2', 'critical']:
            return 'error'
        elif severity_lower in ['warning', 'warn', '1', 'major']:
            return 'warning'
        else:
            return 'info'

    def _aggregate_issues(self, issues: List[Dict]) -> Dict:
        """Aggregate issues by severity for summary

        Args:
            issues: List of issues

        Returns:
            Summary dictionary
        """
        summary = {
            'error': 0,
            'warning': 0,
            'info': 0,
            'total': len(issues)
        }

        for issue in issues:
            severity = issue.get('severity', 'info')
            summary[severity] = summary.get(severity, 0) + 1

        return summary
