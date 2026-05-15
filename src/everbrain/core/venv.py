import subprocess
import venv
from pathlib import Path
import sys
from everbrain.utils.console import print_step, print_success, print_error

# Mapping of libraries to versions/alternatives based on Python version
OPTIMIZATION_MAP = {
    "default": {
        "pydantic": ">=2.10.0",
        "gitpython": ">=3.1.43",
        "pyyaml": ">=6.0.2",
        "rich": ">=13.9.0",
        "typer": ">=0.12.0",
        "tomli": ">=2.0.1",
    },
    "3.8": {
        "pydantic": ">=2.0.0",
        "typing-extensions": ">=4.0.0",
        "importlib-metadata": ">=4.0.0",
    },
    "3.11": {
        "tomli": None,  # Use built-in tomllib
    }
}

def create_internal_venv(project_root: Path) -> Path:
    """Create the internal virtual environment for EverBrain.
    
    Args:
        project_root: Root directory of the project.
        
    Returns:
        Path to the created venv directory.
    """
    venv_dir = project_root / ".everbrain" / "internal_venv"
    
    if not venv_dir.exists():
        print_step(f"Creating internal venv at {venv_dir.relative_to(project_root)}...")
        venv.create(venv_dir, with_pip=True)
        print_success("Internal venv created")
    
    return venv_dir

def install_optimized_dependencies(venv_dir: Path, python_version: str):
    """Install dependencies into the internal venv based on Python version."""
    print_step("Installing optimized dependencies...")
    
    # Determine which pip to use
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"
        
    dependencies = OPTIMIZATION_MAP.get("default", {}).copy()
    
    # Convert string version to float for comparison
    try:
        ver_float = float(python_version)
    except ValueError:
        ver_float = 0.0

    # Apply 3.11+ optimizations
    if ver_float >= 3.11:
        overrides = OPTIMIZATION_MAP.get("3.11", {})
        for lib, version in overrides.items():
            if version is None and lib in dependencies:
                del dependencies[lib]
            elif version is not None:
                dependencies[lib] = version

    # Apply 3.8-specific optimizations if exactly 3.8 (or older)
    if ver_float <= 3.8:
        overrides = OPTIMIZATION_MAP.get("3.8", {})
        for lib, version in overrides.items():
            dependencies[lib] = version
            
    # Convert to list for pip
    install_list = [f"{lib}{ver}" if ver and ver.startswith(">") else lib for lib, ver in dependencies.items()]
    
    try:
        subprocess.run(
            [str(pip_path), "install"] + install_list,
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e.stderr}")
        raise
