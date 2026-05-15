import sys
from pathlib import Path
from typing import Optional
import re

def get_project_python_version(project_root: Path) -> str:
    """Detect the intended Python version for the project.
    
    Priority:
    1. pyproject.toml (project.requires-python or tool.poetry.dependencies.python)
    2. .python-version (pyenv)
    3. Current system version (fallback)
    
    Returns:
        A string representing the major.minor version (e.g., "3.11").
    """
    # 1. Check pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            content = pyproject_path.read_text(encoding="utf-8")
            # Look for requires-python = ">=3.11"
            match = re.search(r'requires-python\s*=\s*"(?:>=|~=|>)?([\d\.]+)"', content)
            if match:
                return _sanitize_version(match.group(1))
            
            # Look for [tool.poetry.dependencies] python = "^3.11"
            match = re.search(r'python\s*=\s*"(?:[\^~>=|>])?([\d\.]+)"', content)
            if match:
                return _sanitize_version(match.group(1))
        except Exception:
            pass

    # 2. Check .python-version
    python_version_path = project_root / ".python-version"
    if python_version_path.exists():
        try:
            version = python_version_path.read_text(encoding="utf-8").strip()
            if version:
                return _sanitize_version(version)
        except Exception:
            pass

    # 3. Fallback to current system version
    return f"{sys.version_info.major}.{sys.version_info.minor}"

def _sanitize_version(version: str) -> str:
    """Extract major.minor from a version string."""
    match = re.match(r'(\d+\.\d+)', version)
    if match:
        return match.group(1)
    return version

def get_python_executable() -> str:
    """Return the path to the current python executable."""
    return sys.executable
