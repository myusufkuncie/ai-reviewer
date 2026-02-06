"""Build comprehensive context for AI review"""

import re
import json
from typing import Dict, List, Optional
from pathlib import Path
from .language_detector import LanguageDetector


class ContextBuilder:
    """Builds comprehensive context for code review"""

    def __init__(self, platform_adapter, config):
        """Initialize context builder

        Args:
            platform_adapter: Platform adapter for fetching files
            config: Configuration loader
        """
        self.platform = platform_adapter
        self.config = config
        self.language_detector = LanguageDetector()

    def get_readme_content(self, ref: str) -> Optional[Dict]:
        """Find and read README file."""
        readme_files = [
            'README.md',
            'README.MD',
            'readme.md',
            'README',
            'README.txt',
            'README.rst',
            'Readme.md'
        ]

        for readme_file in readme_files:
            content = self.platform.get_file_content(readme_file, ref)
            if content:
                print(f"✓ Found README: {readme_file}")
                return {
                    'file': readme_file,
                    'content': content[:3000]  # First 3000 chars
                }

        print("⚠ No README found")
        return None

    def get_dockerfile_content(self, ref: str) -> Optional[Dict]:
        """Find and read Dockerfile and docker-compose files."""
        docker_files = [
            'Dockerfile',
            'dockerfile',
            'Dockerfile.prod',
            'Dockerfile.dev',
            'docker-compose.yml',
            'docker-compose.yaml',
            'docker-compose.prod.yml',
            'docker-compose.dev.yml'
        ]

        docker_info = {
            'dockerfiles': [],
            'compose_files': []
        }

        for docker_file in docker_files:
            content = self.platform.get_file_content(docker_file, ref)
            if content:
                file_info = {
                    'file': docker_file,
                    'content': content[:2000]
                }

                if 'compose' in docker_file.lower():
                    docker_info['compose_files'].append(file_info)
                    print(f"✓ Found docker-compose: {docker_file}")
                else:
                    docker_info['dockerfiles'].append(file_info)
                    print(f"✓ Found Dockerfile: {docker_file}")

        if not docker_info['dockerfiles'] and not docker_info['compose_files']:
            print("⚠ No Docker files found")
            return None

        return docker_info

    def extract_imports_and_functions(self, content: str, filepath: str) -> Dict:
        """Extract imports, function definitions, and class definitions."""
        result = {
            'imports': [],
            'functions': [],
            'classes': [],
            'constants': []
        }

        if filepath.endswith('.py'):
            # Extract imports
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    result['imports'].append(line)

            # Extract function and class definitions
            for match in re.finditer(r'^def\s+(\w+)\s*\(([^)]*)\)', content, re.MULTILINE):
                result['functions'].append({
                    'name': match.group(1),
                    'params': match.group(2)
                })

            for match in re.finditer(r'^class\s+(\w+)(\([^)]*\))?:', content, re.MULTILINE):
                result['classes'].append(match.group(1))

            # Extract constants (UPPER_CASE variables)
            for match in re.finditer(r'^([A-Z_]+)\s*=', content, re.MULTILINE):
                result['constants'].append(match.group(1))

        elif filepath.endswith(('.js', '.ts', '.jsx', '.tsx')):
            # Extract imports
            for match in re.finditer(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content):
                result['imports'].append(match.group(0))

            # Extract function definitions
            for match in re.finditer(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()', content):
                func_name = match.group(1) or match.group(2)
                if func_name:
                    result['functions'].append({'name': func_name})

            # Extract class definitions
            for match in re.finditer(r'class\s+(\w+)', content):
                result['classes'].append(match.group(1))

        return result

    def get_related_files_smart(self, filepath: str, base_sha: str, head_sha: str) -> List[Dict]:
        """Intelligently find related files based on imports and usage."""
        related_files = []

        # Get the changed file content
        file_content = self.platform.get_file_content(filepath, head_sha)
        if not file_content:
            return []

        # Extract imports to find directly related files
        file_info = self.extract_imports_and_functions(file_content, filepath)

        # Get exclusions from config
        exclusions = self.config.get_exclusions()

        # Parse imports to find local file references
        for import_stmt in file_info['imports']:
            # Extract relative imports (Python)
            if filepath.endswith('.py'):
                match = re.search(r'from\s+\.+([^\s]+)\s+import', import_stmt)
                if match:
                    relative_path = match.group(1).replace('.', '/') + '.py'
                    content = self.platform.get_file_content(relative_path, head_sha)
                    if content:
                        excluded, _ = self._should_exclude_file(relative_path, exclusions)
                        if not excluded:
                            related_files.append({
                                'path': relative_path,
                                'content': content[:2000],
                                'reason': 'imported_by_changed_file',
                                'relevance': 'high'
                            })

            # Extract relative imports (JavaScript/TypeScript)
            elif filepath.endswith(('.js', '.ts', '.jsx', '.tsx')):
                match = re.search(r'from\s+[\'"]\.([^\'"]+)[\'"]', import_stmt)
                if match:
                    relative_path = match.group(1)
                    if not any(relative_path.endswith(ext) for ext in ['.js', '.ts', '.jsx', '.tsx']):
                        # Try common extensions
                        for ext in ['.js', '.ts', '.jsx', '.tsx']:
                            test_path = relative_path + ext
                            excluded, _ = self._should_exclude_file(test_path, exclusions)
                            if not excluded:
                                content = self.platform.get_file_content(test_path, head_sha)
                                if content:
                                    related_files.append({
                                        'path': test_path,
                                        'content': content[:2000],
                                        'reason': 'imported_by_changed_file',
                                        'relevance': 'high'
                                    })
                                    break

        # Get files in the same directory
        file_dir = str(Path(filepath).parent)
        try:
            tree = self.platform.get_directory_tree(file_dir, head_sha)

            for item in tree[:10]:  # Check up to 10 files
                if item.get('type') == 'blob' and item.get('path') != filepath:
                    excluded, _ = self._should_exclude_file(item['path'], exclusions)
                    if not excluded:
                        if any(item['name'].endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.go']):
                            content = self.platform.get_file_content(item['path'], head_sha)
                            if content:
                                related_files.append({
                                    'path': item['path'],
                                    'content': content[:1500],
                                    'reason': 'same_directory',
                                    'relevance': 'medium'
                                })
                                if len(related_files) >= 5:
                                    break
        except Exception as e:
            print(f"Error fetching directory tree: {e}")

        # Find test files
        test_paths = self.find_test_files(filepath, head_sha)
        for test_path in test_paths[:2]:
            excluded, _ = self._should_exclude_file(test_path, exclusions)
            if not excluded:
                content = self.platform.get_file_content(test_path, head_sha)
                if content:
                    related_files.append({
                        'path': test_path,
                        'content': content[:1500],
                        'reason': 'test_file',
                        'relevance': 'high'
                    })

        return related_files[:5]

    def find_test_files(self, filepath: str, ref: str) -> List[str]:
        """Find test files related to the given file."""
        test_files = []
        base_name = Path(filepath).stem
        dir_name = str(Path(filepath).parent)

        # Common test file patterns
        patterns = [
            f"test_{base_name}.py",
            f"{base_name}_test.py",
            f"test{base_name}.py",
            f"{base_name}.test.js",
            f"{base_name}.spec.js",
            f"{base_name}.test.ts",
            f"{base_name}.spec.ts",
        ]

        # Check in same directory
        for pattern in patterns:
            test_path = f"{dir_name}/{pattern}" if dir_name != '.' else pattern
            content = self.platform.get_file_content(test_path, ref)
            if content:
                test_files.append(test_path)

        # Check in tests directory
        test_dirs = ['tests', 'test', '__tests__', 'spec']
        for test_dir in test_dirs:
            for pattern in patterns:
                test_path = f"{test_dir}/{pattern}"
                content = self.platform.get_file_content(test_path, ref)
                if content:
                    test_files.append(test_path)

        return test_files

    def get_project_architecture(self, ref: str) -> Dict:
        """Understand project architecture from config files."""
        architecture = {
            'language': None,
            'framework': None,
            'dependencies': [],
            'structure': None
        }

        # Check for common config files
        config_files = {
            'requirements.txt': 'python',
            'setup.py': 'python',
            'pyproject.toml': 'python',
            'package.json': 'javascript',
            'go.mod': 'go',
            'Cargo.toml': 'rust',
            'pom.xml': 'java',
            'build.gradle': 'java',
        }

        for config_file, lang in config_files.items():
            content = self.platform.get_file_content(config_file, ref)
            if content:
                architecture['language'] = lang
                architecture['structure'] = {
                    'file': config_file,
                    'content': content[:1000]
                }

                # Extract dependencies
                if config_file == 'package.json':
                    try:
                        pkg = json.loads(content)
                        if 'dependencies' in pkg:
                            architecture['dependencies'] = list(pkg['dependencies'].keys())[:10]
                        # Detect framework
                        deps = str(pkg.get('dependencies', {}))
                        if 'react' in deps:
                            architecture['framework'] = 'React'
                        elif 'vue' in deps:
                            architecture['framework'] = 'Vue'
                        elif 'angular' in deps:
                            architecture['framework'] = 'Angular'
                        elif 'next' in deps:
                            architecture['framework'] = 'Next.js'
                    except:
                        pass

                elif config_file == 'requirements.txt':
                    architecture['dependencies'] = [
                        line.split('==')[0].strip()
                        for line in content.split('\n')[:10]
                        if line.strip() and not line.startswith('#')
                    ]
                    # Detect framework
                    deps_lower = content.lower()
                    if 'django' in deps_lower:
                        architecture['framework'] = 'Django'
                    elif 'flask' in deps_lower:
                        architecture['framework'] = 'Flask'
                    elif 'fastapi' in deps_lower:
                        architecture['framework'] = 'FastAPI'

                break

        return architecture

    def analyze_change_impact(self, filepath: str, diff: str, file_info: Dict) -> Dict:
        """Analyze the impact of changes."""
        impact = {
            'scope': 'minor',
            'areas': [],
            'risks': []
        }

        # Check if public API is changed
        if any(func.get('name', '').startswith('_') for func in file_info.get('functions', [])):
            if 'def ' in diff and not any(line.strip().startswith('def _') for line in diff.split('\n')):
                impact['areas'].append('public_api')
                impact['scope'] = 'major'

        # Check for breaking changes
        breaking_keywords = ['breaking', 'removed', 'deprecated', 'renamed']
        if any(keyword in diff.lower() for keyword in breaking_keywords):
            impact['areas'].append('breaking_change')
            impact['scope'] = 'major'
            impact['risks'].append('Potential breaking change detected')

        # Check for security-related changes
        security_keywords = ['password', 'token', 'secret', 'auth', 'permission', 'security']
        if any(keyword in diff.lower() for keyword in security_keywords):
            impact['areas'].append('security')
            impact['risks'].append('Security-related code modified')

        # Check for database changes
        db_keywords = ['migration', 'schema', 'table', 'column', 'database', 'query']
        if any(keyword in diff.lower() for keyword in db_keywords):
            impact['areas'].append('database')
            impact['risks'].append('Database-related changes')

        # Check for Docker/infrastructure changes
        if 'Dockerfile' in filepath or 'docker-compose' in filepath:
            impact['areas'].append('infrastructure')
            impact['scope'] = 'major' if impact['scope'] == 'minor' else impact['scope']
            impact['risks'].append('Infrastructure/Docker configuration changed')

        # Check size of change
        lines_changed = len([l for l in diff.split('\n') if l.startswith('+') or l.startswith('-')])
        if lines_changed > 100:
            impact['scope'] = 'major' if impact['scope'] != 'major' else impact['scope']
        elif lines_changed > 50:
            impact['scope'] = 'moderate' if impact['scope'] == 'minor' else impact['scope']

        return impact

    def _should_exclude_file(self, filepath: str, exclusions: Dict) -> tuple:
        """Check if file should be excluded."""
        path = Path(filepath)

        # Check directories
        for excluded_dir in exclusions.get('directories', []):
            if excluded_dir in path.parts:
                return True, f"in excluded directory: {excluded_dir}"

        # Check file prefixes
        filename = path.name
        for prefix in exclusions.get('file_prefixes', []):
            if filename.startswith(prefix):
                return True, f"matches excluded prefix: {prefix}"

        # Check file patterns
        for pattern in exclusions.get('file_patterns', []):
            if path.match(pattern):
                return True, f"matches excluded pattern: {pattern}"

        return False, None

    def build_context(self, filepath: str, diff: str, change: Dict) -> str:
        """Build comprehensive review context for a file

        Args:
            filepath: Path to file
            diff: File diff
            change: Change metadata with base_sha and head_sha

        Returns:
            Formatted context string for AI
        """
        base_sha = change.get('base_sha')
        head_sha = change.get('head_sha')

        # Get file content before and after
        file_before = self.platform.get_file_content(filepath, base_sha)
        file_after = self.platform.get_file_content(filepath, head_sha)

        # Detect language
        lang_info = self.language_detector.get_language_info(
            filepath,
            file_after or ""
        )

        # Extract structure information
        file_info_after = {}
        if file_after:
            file_info_after = self.extract_imports_and_functions(file_after, filepath)

        # Get README
        readme = self.get_readme_content(head_sha)

        # Get Docker files
        docker_info = self.get_dockerfile_content(head_sha)

        # Get related files
        related_files = self.get_related_files_smart(filepath, base_sha, head_sha)

        # Get project architecture
        architecture = self.get_project_architecture(head_sha)

        # Analyze impact
        impact = self.analyze_change_impact(filepath, diff, file_info_after)

        # Build context string
        context = f"""# CODE REVIEW CONTEXT

## File: {filepath}

## Language: {lang_info['language'] or 'Unknown'}
## Framework: {lang_info['framework'] or 'None detected'}

## Change Impact Analysis
- Scope: {impact['scope'].upper()}
- Areas affected: {', '.join(impact['areas']) if impact['areas'] else 'None'}
- Potential risks: {', '.join(impact['risks']) if impact['risks'] else 'None'}

"""

        # Add README context
        if readme:
            context += f"""## Project Overview (from {readme['file']})
```
{readme['content']}
```

"""

        # Add Docker context
        if docker_info:
            if docker_info.get('dockerfiles'):
                context += """## Docker Configuration
"""
                for dockerfile in docker_info['dockerfiles']:
                    context += f"""### {dockerfile['file']}
```dockerfile
{dockerfile['content']}
```

"""

            if docker_info.get('compose_files'):
                context += """## Docker Compose Configuration
"""
                for compose in docker_info['compose_files']:
                    context += f"""### {compose['file']}
```yaml
{compose['content']}
```

"""

        if architecture['language']:
            context += f"""## Project Architecture
- Language: {architecture['language']}
- Framework: {architecture['framework'] or 'None detected'}
- Key dependencies: {', '.join(architecture['dependencies'][:5]) if architecture['dependencies'] else 'None'}

"""

        if file_info_after.get('imports'):
            context += f"""## Imports in Changed File
```
{chr(10).join(file_info_after['imports'][:10])}
```

"""

        if file_info_after.get('functions'):
            context += f"""## Functions Defined
{', '.join([f.get('name', '') for f in file_info_after['functions'][:10]])}

"""

        if file_info_after.get('classes'):
            context += f"""## Classes Defined
{', '.join(file_info_after['classes'][:5])}

"""

        if file_before:
            context += f"""## Full File BEFORE Changes (truncated)
```
{file_before[:2000]}
{'...[truncated]...' if len(file_before) > 2000 else ''}
```

"""

        if file_after:
            context += f"""## Full File AFTER Changes (truncated)
```
{file_after[:2000]}
{'...[truncated]...' if len(file_after) > 2000 else ''}
```

"""

        if related_files:
            context += f"""## Related Files ({len(related_files)} found)

"""
            for rel_file in related_files:
                context += f"""### {rel_file['path']} ({rel_file['relevance']} relevance - {rel_file['reason']})
```
{rel_file['content']}
{'...[truncated]...' if len(rel_file.get('content', '')) >= 1500 else ''}
```

"""

        context += f"""## DIFF (Actual Changes)
```diff
{diff}
```

---
## Review Instructions

Review the changes considering:
1. **Project Context**: Does this align with the project's purpose (from README)?
2. **Infrastructure**: If Docker files changed, are they consistent and correct?
3. **Integration**: How do changes integrate with existing code and related files?
4. **Breaking Changes**: Could this break existing functionality or APIs?
5. **Impact**: Given the scope ({impact['scope']}), are proper safeguards in place?
6. **Patterns**: Does this follow project patterns and conventions?
7. **Dependencies**: Are import changes and dependencies handled correctly?
8. **Testing**: Should this change have corresponding tests?
9. **Security**: Any security implications from the changes?
10. **Performance**: Any performance concerns?
11. **Code Quality**: Clean, maintainable, and well-structured?
12. **{lang_info['language']} Best Practices**: Does this follow {lang_info['language']} conventions?
"""

        if lang_info['framework']:
            context += f"13. **{lang_info['framework']} Patterns**: Does this follow {lang_info['framework']} best practices?\n"

        context += """
Provide your review as a JSON array with format:
[
  {
    "filepath": "<filepath>",
    "line": <line_number>,
    "comment": "<your detailed comment>",
    "severity": "critical|major|minor|suggestion"
  }
]

Return empty array [] if code looks good. Be specific and constructive."""

        return context
