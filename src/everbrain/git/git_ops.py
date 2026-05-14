"""Git integration: Branch and commit tracking.

Provides safe Git operations with graceful fallbacks for non-Git directories.
"""

from typing import Optional

import git


class GitError(Exception):
    """Custom exception for Git-related errors."""

    pass


def get_current_branch() -> str:
    """Get the currently active Git branch.
    
    Returns:
        Branch name (e.g., 'main', 'feature/auth'). Returns 'main' if not in a Git repo.
    """
    try:
        repo = git.Repo(".")
        if repo.head.is_detached:
            return f"detached@{repo.head.commit.hexsha[:7]}"
        return repo.active_branch.name
    except (git.InvalidGitRepositoryError, git.GitError):
        return "main"


def get_latest_commit() -> tuple[str, str]:
    """Get the latest commit hash and message.
    
    Returns:
        Tuple of (commit_hash_short, commit_message).
        Returns ('unknown', 'No commits') if not in a Git repo or repo is empty.
    """
    try:
        repo = git.Repo(".")
        commit = repo.head.commit
        commit_hash = commit.hexsha[:7]
        commit_message = commit.message.split("\n")[0]  # First line only
        return commit_hash, commit_message
    except (git.InvalidGitRepositoryError, git.GitError, ValueError):
        return "unknown", "No commits"


def get_git_status() -> dict[str, str]:
    """Get current Git branch and latest commit.
    
    Returns:
        Dict with 'branch' and 'commit' keys. Never raises exceptions.
    """
    try:
        repo = git.Repo(".")
        branch = get_current_branch()
        commit_hash, commit_msg = get_latest_commit()
        return {
            "branch": branch,
            "commit_hash": commit_hash,
            "commit_message": commit_msg,
        }
    except Exception:
        # Graceful fallback for non-Git directories
        return {
            "branch": "main",
            "commit_hash": "unknown",
            "commit_message": "Not a Git repository",
        }
