"""
Helper utilities for the persona simulation framework.
"""

import json
import yaml
from pathlib import Path
from typing import Union, Dict, Any


def load_yaml_or_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load data from a YAML or JSON file.

    Args:
        file_path: Path to the file

    Returns:
        Loaded data as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r") as f:
        if path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        elif path.suffix == ".json":
            return json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")


def save_yaml_or_json(data: Dict[str, Any], file_path: Union[str, Path]):
    """
    Save data to a YAML or JSON file.

    Args:
        data: Data to save
        file_path: Path to save to
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        if path.suffix in [".yaml", ".yml"]:
            yaml.dump(data, f, indent=2, sort_keys=False)
        elif path.suffix == ".json":
            json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")


def format_score(score: float) -> str:
    """
    Format a score for display.

    Args:
        score: Score value (0-100)

    Returns:
        Formatted score string with color indicator
    """
    if score >= 80:
        return f"🟢 {score:.1f}/100"
    elif score >= 60:
        return f"🟡 {score:.1f}/100"
    else:
        return f"🔴 {score:.1f}/100"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def calculate_improvement(initial: float, final: float) -> float:
    """
    Calculate percentage improvement.

    Args:
        initial: Initial value
        final: Final value

    Returns:
        Improvement percentage
    """
    if initial == 0:
        return 0.0

    return ((final - initial) / initial) * 100
