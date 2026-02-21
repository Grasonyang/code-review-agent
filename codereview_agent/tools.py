"""
Code Review Workflow — Tool Functions

These tools provide git-based code analysis capabilities for the review pipeline.
Each tool follows ADK best practices: clear docstrings, type hints, and dict returns.
"""

import subprocess
import os
import json
from typing import Optional


def get_git_diff(target_branch: str = "main", source_branch: str = "HEAD") -> dict:
    """Get the git diff between two branches for code review.

    Use this tool to retrieve the code changes that need to be reviewed.
    This is typically the first step — fetching what has changed.

    Args:
        target_branch (str): The base branch to compare against (e.g., 'main', 'develop').
        source_branch (str): The branch with changes (default: 'HEAD' for current branch).

    Returns:
        dict: Contains 'status', 'diff' text, 'files_changed' list, and 'stats' summary.
    """
    try:
        # Get the diff content
        diff_result = subprocess.run(
            ["git", "diff", f"{target_branch}...{source_branch}"],
            capture_output=True, text=True, timeout=30
        )
        if diff_result.returncode != 0:
            return {
                "status": "error",
                "error_message": f"Git diff failed: {diff_result.stderr.strip()}"
            }

        # Get list of changed files
        files_result = subprocess.run(
            ["git", "diff", "--name-status", f"{target_branch}...{source_branch}"],
            capture_output=True, text=True, timeout=15
        )

        # Get diffstat
        stat_result = subprocess.run(
            ["git", "diff", "--stat", f"{target_branch}...{source_branch}"],
            capture_output=True, text=True, timeout=15
        )

        files_changed = []
        if files_result.returncode == 0:
            for line in files_result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        files_changed.append({
                            "status": parts[0].strip(),
                            "file": parts[1].strip()
                        })

        diff_text = diff_result.stdout
        # Truncate very large diffs to avoid overwhelming the LLM
        max_chars = 80000
        truncated = False
        if len(diff_text) > max_chars:
            diff_text = diff_text[:max_chars]
            truncated = True

        return {
            "status": "success",
            "diff": diff_text,
            "truncated": truncated,
            "files_changed": files_changed,
            "file_count": len(files_changed),
            "stats": stat_result.stdout.strip() if stat_result.returncode == 0 else ""
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error_message": "Git command timed out"}
    except FileNotFoundError:
        return {"status": "error", "error_message": "Git is not installed or not in PATH"}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def get_file_content(file_path: str, branch: str = "HEAD") -> dict:
    """Read the full content of a specific file from a git branch.

    Use this tool when you need to see the complete file context
    beyond what the diff shows — helpful for understanding the
    surrounding code structure.

    Args:
        file_path (str): Path to the file relative to the repo root.
        branch (str): The branch to read from (default: 'HEAD').

    Returns:
        dict: Contains 'status', 'content' of the file, and 'line_count'.
    """
    try:
        result = subprocess.run(
            ["git", "show", f"{branch}:{file_path}"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return {
                "status": "error",
                "error_message": f"Cannot read file: {result.stderr.strip()}"
            }

        content = result.stdout
        max_chars = 50000
        truncated = False
        if len(content) > max_chars:
            content = content[:max_chars]
            truncated = True

        return {
            "status": "success",
            "content": content,
            "truncated": truncated,
            "line_count": content.count("\n") + 1
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def get_commit_messages(target_branch: str = "main", source_branch: str = "HEAD") -> dict:
    """Get commit messages between two branches.

    Use this tool to understand the intent behind the changes
    by reading the developer's commit messages.

    Args:
        target_branch (str): The base branch (e.g., 'main').
        source_branch (str): The feature branch (default: 'HEAD').

    Returns:
        dict: Contains 'status', list of 'commits' with hash, author, date, and message.
    """
    try:
        result = subprocess.run(
            [
                "git", "log",
                f"{target_branch}..{source_branch}",
                "--pretty=format:%H|%an|%ad|%s",
                "--date=short"
            ],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return {
                "status": "error",
                "error_message": f"Git log failed: {result.stderr.strip()}"
            }

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })

        return {
            "status": "success",
            "commits": commits,
            "commit_count": len(commits)
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def check_for_secrets(diff_text: str) -> dict:
    """Scan diff text for potential leaked secrets or sensitive data.

    Use this tool to check if the code changes accidentally include
    API keys, passwords, tokens, or other sensitive information.

    Args:
        diff_text (str): The diff text to scan for secrets.

    Returns:
        dict: Contains 'status', list of 'findings', and 'risk_level'.
    """
    import re

    patterns = {
        "API Key": r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{20,}',
        "AWS Key": r'AKIA[0-9A-Z]{16}',
        "Private Key": r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
        "Password Assignment": r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}',
        "Bearer Token": r'(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*',
        "Generic Token": r'(?i)(token|secret)\s*[=:]\s*["\'][A-Za-z0-9_\-]{16,}',
        "Connection String": r'(?i)(mongodb|postgres|mysql|redis)://[^\s"\']+',
        "Hardcoded IP": r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b',
    }

    findings = []
    for name, pattern in patterns.items():
        matches = re.findall(pattern, diff_text)
        if matches:
            # Don't include the actual secret in output
            findings.append({
                "type": name,
                "occurrences": len(matches) if isinstance(matches[0], str) else len(matches),
                "severity": "HIGH" if name in ["Private Key", "AWS Key", "Connection String"] else "MEDIUM"
            })

    risk_level = "CLEAN"
    if findings:
        has_high = any(f["severity"] == "HIGH" for f in findings)
        risk_level = "HIGH" if has_high else "MEDIUM"

    return {
        "status": "success",
        "findings": findings,
        "finding_count": len(findings),
        "risk_level": risk_level
    }


def list_repo_structure(max_depth: int = 3) -> dict:
    """List the repository directory structure.

    Use this tool to understand the overall project layout when reviewing
    whether new files are placed in the correct locations.

    Args:
        max_depth (int): Maximum directory depth to show (default: 3).

    Returns:
        dict: Contains 'status' and 'tree' showing the directory structure.
    """
    try:
        result = subprocess.run(
            ["find", ".", "-maxdepth", str(max_depth),
             "-not", "-path", "./.git/*",
             "-not", "-path", "./node_modules/*",
             "-not", "-path", "./__pycache__/*",
             "-not", "-path", "./.venv/*"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return {"status": "error", "error_message": result.stderr.strip()}

        return {
            "status": "success",
            "tree": result.stdout.strip()
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
