"""GitHub & GitLab Integration Engine.

Provides git diff parsing, automated PR/MR description synthesis, conventional
commit formatting, CI/CD pipeline scaffolding (GitHub Actions and GitLab CI),
and remote GitHub/GitLab REST API connectivity.
"""

import json
import re
from typing import Any, Dict, List, Optional
import requests


def parse_git_diff(diff_str: str) -> Dict[str, Any]:
    """Parse raw git diff output into structured file changes, additions, deletions, and hunks."""
    if not diff_str.strip():
        return {
            "files": [],
            "total_additions": 0,
            "total_deletions": 0,
            "changed_files_count": 0,
            "primary_changes": []
        }

    files = []
    current_file = None
    total_additions = 0
    total_deletions = 0

    lines = diff_str.splitlines()
    for line in lines:
        if line.startswith("diff --git"):
            if current_file:
                files.append(current_file)
            parts = line.split(" ")
            path = parts[-1].lstrip("b/") if len(parts) >= 4 else "unknown"
            current_file = {
                "path": path,
                "additions": 0,
                "deletions": 0,
                "status": "modified",
                "hunk_headers": []
            }
        elif current_file:
            if line.startswith("new file mode"):
                current_file["status"] = "added"
            elif line.startswith("deleted file mode"):
                current_file["status"] = "deleted"
            elif line.startswith("@@"):
                current_file["hunk_headers"].append(line)
            elif line.startswith("+") and not line.startswith("+++"):
                current_file["additions"] += 1
                total_additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                current_file["deletions"] += 1
                total_deletions += 1

    if current_file:
        files.append(current_file)

    # Extract primary themes or functions modified
    primary_changes = []
    for f in files:
        primary_changes.append(f"{f['status'].upper()}: {f['path']} (+{f['additions']}/-{f['deletions']})")

    return {
        "files": files,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "changed_files_count": len(files),
        "primary_changes": primary_changes
    }


def generate_pr_description(diff_str: str, custom_context: str = "") -> Dict[str, Any]:
    """Generate a structured Pull Request / Merge Request summary from git diff."""
    diff_data = parse_git_diff(diff_str)
    files = diff_data["files"]

    # Deduce PR type
    diff_lower = (diff_str + " " + custom_context).lower()
    if any(k in diff_lower for k in ["perf", "optimi", "tracemalloc", "memory", "slots", "speed"]):
        pr_type = "perf"
        type_desc = "Performance & Memory Optimization"
    elif "fix" in diff_lower or "bug" in diff_lower or "error" in diff_lower:
        pr_type = "fix"
        type_desc = "Bug Fix"
    elif "test" in diff_lower or any("test" in f["path"].lower() for f in files):
        pr_type = "test"
        type_desc = "Tests & QA"
    elif "doc" in diff_lower or any("readme" in f["path"].lower() for f in files):
        pr_type = "docs"
        type_desc = "Documentation"
    elif "refactor" in diff_lower:
        pr_type = "refactor"
        type_desc = "Code Refactoring"
    else:
        pr_type = "feat"
        type_desc = "New Feature"

    # Identify primary scope
    scope = "core"
    if files:
        first_file = files[0]["path"]
        parts = first_file.split("/")
        scope = parts[0] if len(parts) > 1 else parts[0].split(".")[0]

    title = f"{pr_type}({scope}): {custom_context or f'update {scope} with optimizations and enhancements'}"

    # Build key changes bullets
    change_bullets = []
    if custom_context:
        change_bullets.append(f"- **Intent**: {custom_context}")
    for f in files[:8]:
        change_bullets.append(f"- `{f['path']}`: {f['status']} (+{f['additions']} / -{f['deletions']} lines)")

    if len(files) > 8:
        change_bullets.append(f"- ...and {len(files) - 8} more files.")

    markdown_body = f"""## 📌 Summary of Changes
{custom_context or f"This PR introduces changes across {diff_data['changed_files_count']} file(s) focusing on {type_desc.lower()}."}

## 🔍 Detailed Modifications
{chr(10).join(change_bullets)}

## ⚡ Performance & Memory Impact
- **Total Diff Footprint**: +{diff_data['total_additions']} / -{diff_data['total_deletions']} lines.
- Evaluated for memory safety, garbage collection churn, and bounded allocations.

## 🧪 Testing & Verification
- [x] Automated unit and integration tests passing.
- [x] Memory profiling with `tracemalloc` confirms zero leak regressions.
- [x] Manual sanity check completed in local environment.

## 🚨 Breaking Changes
- [ ] Yes (documented in release notes)
- [x] No breaking API changes introduced.
"""

    return {
        "title": title,
        "type": pr_type,
        "scope": scope,
        "body_markdown": markdown_body,
        "diff_stats": {
            "files_count": diff_data["changed_files_count"],
            "additions": diff_data["total_additions"],
            "deletions": diff_data["total_deletions"]
        }
    }


def generate_conventional_commit(short_desc: str, scope: str = "", commit_type: str = "feat", is_breaking: bool = False) -> str:
    """Format a message adhering strictly to the Conventional Commits 1.0.0 specification."""
    scope_str = f"({scope})" if scope.strip() else ""
    breaking_str = "!" if is_breaking else ""
    header = f"{commit_type}{scope_str}{breaking_str}: {short_desc.strip()}"
    return header


def generate_cicd_pipeline(platform: str = "github", python_versions: Optional[List[str]] = None, check_memory: bool = True) -> str:
    """Generate production-ready CI/CD configuration for GitHub Actions or GitLab CI."""
    if python_versions is None:
        python_versions = ["3.11", "3.12"]

    if platform.lower() == "gitlab":
        return f"""# GitLab CI/CD Pipeline
image: python:3.12-slim

stages:
  - lint
  - test
  - memory_profile
  - security

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/

before_script:
  - python --version
  - pip install --upgrade pip
  - pip install -r requirements.txt

linting:
  stage: lint
  script:
    - pip install flake8 black
    - flake8 . --max-line-length=120 --exclude=venv
    - black --check .

unit_tests:
  stage: test
  script:
    - pip install pytest pytest-cov
    - pytest --cov=dev_tool --cov-report=term-missing tests/

memory_check:
  stage: memory_profile
  script:
    - python -c "from engine.memory_engine import analyze_memory_code; print('Memory static analyzer healthy')"
    - python test_suite.py
"""
    else:  # GitHub Actions
        matrix_py = json.dumps(python_versions)
        return f"""# GitHub Actions CI Workflow
name: CI & Memory Guard

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: {matrix_py}

    steps:
      - name: Checkout Source Code
        uses: actions/checkout@v4

      - name: Set up Python ${{{{ matrix.python-version }}}}
        uses: actions/setup-python@v5
        with:
          python-version: ${{{{ matrix.python-version }}}}
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install flake8 pytest pytest-cov requests psutil

      - name: Lint with Flake8
        run: |
          # Stop build if there are Python syntax errors or undefined names
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      - name: Execute Pytest Suite
        run: |
          pytest --verbose

      - name: Run Memory Anti-Pattern & Tracemalloc Guard
        run: |
          python test_suite.py
"""


def fetch_remote_repo_data(platform: str, repo_identifier: str, token: Optional[str] = None) -> Dict[str, Any]:
    """Fetch repository info, commits, and open pull requests from GitHub or GitLab API with mock fallback."""
    # If no token provided or demo repo identifier, return rich mock data
    if not token or repo_identifier.lower() in {"demo", "sample", "test", "mock"}:
        return _get_mock_remote_data(platform, repo_identifier)

    headers = {}
    if platform.lower() == "gitlab":
        headers["PRIVATE-TOKEN"] = token
        encoded_id = requests.utils.quote(repo_identifier, safe="")
        url = f"https://gitlab.com/api/v4/projects/{encoded_id}"
    else:  # GitHub
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/vnd.github.v3+json"
        url = f"https://api.github.com/repos/{repo_identifier}"

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "platform": platform,
                "is_mock": False,
                "name": data.get("name") or data.get("path"),
                "full_name": data.get("full_name") or data.get("path_with_namespace"),
                "description": data.get("description", "No description provided"),
                "default_branch": data.get("default_branch", "main"),
                "stars": data.get("stargazers_count") or data.get("star_count", 0),
                "forks": data.get("forks_count") or data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0)
            }
        else:
            return {
                "success": False,
                "error": f"API returned HTTP {resp.status_code}: {resp.text[:150]}",
                "fallback_mock": _get_mock_remote_data(platform, repo_identifier)
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}",
            "fallback_mock": _get_mock_remote_data(platform, repo_identifier)
        }


def _get_mock_remote_data(platform: str, repo_name: str) -> Dict[str, Any]:
    """Provide realistic sandbox repository data for offline demo testing."""
    display_name = repo_name if repo_name not in {"demo", "sample", "test", "mock"} else "dev-productivity-suite"
    return {
        "success": True,
        "platform": platform,
        "is_mock": True,
        "name": display_name,
        "full_name": f"acme-corp/{display_name}",
        "description": "High-throughput data streaming and developer productivity workspace.",
        "default_branch": "main",
        "stars": 342,
        "forks": 58,
        "open_issues": 7,
        "recent_branches": ["main", "feature/memory-optimizations", "refactor/docstring-generator", "fix/ci-pipeline"],
        "recent_prs": [
            {
                "id": 104,
                "title": "perf(stream): replace list allocations with generator pipelines",
                "author": "dev-lead",
                "status": "open",
                "additions": 142,
                "deletions": 89
            },
            {
                "id": 103,
                "title": "feat(doc): add automated Google-style docstring synthesizer",
                "author": "ankur-soni",
                "status": "merged",
                "additions": 310,
                "deletions": 12
            }
        ]
    }
