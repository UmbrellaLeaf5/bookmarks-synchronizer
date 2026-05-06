import json
from pathlib import Path

from loguru import logger

from src.models.config import AppConfig


def load_config(config_path: str = "config.json") -> AppConfig:
  with open(config_path, encoding="utf-8") as f:
    data = json.load(f)

  errors = _validate_raw(data)

  if errors:
    for e in errors:
      print(f"  [X] {e}")

    raise ValueError("Invalid configuration file")

  config = AppConfig(
    profiles=data.get("profiles", {}),
    shared_folders=data.get("shared_folders", []),
  )

  for name, path in config.profiles.items():
    try:
      with open(path, encoding="utf-8") as f:
        first_line = f.readline(200).strip()
        if not first_line.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>"):
          logger.warning(f"Profile '{name}' may not be a bookmark file: {path}")

    except OSError:
      pass

  return config


def _validate_raw(data: dict) -> list[str]:
  errors: list[str] = []

  if "profiles" not in data or not isinstance(data["profiles"], dict):
    errors.append("Missing or invalid 'profiles' section")
    return errors

  if not data["profiles"]:
    errors.append("No profiles defined")

  for name, path in data["profiles"].items():
    if not isinstance(name, str) or not name.strip():
      errors.append(f"Invalid profile name: {name!r}")

    if not isinstance(path, str) or not path.strip():
      errors.append(f"Empty file path for profile '{name}'")

    elif not Path(path).exists():
      errors.append(f"File not found for profile '{name}': {path}")

  if "shared_folders" not in data or not isinstance(data["shared_folders"], list):
    errors.append("Missing or invalid 'shared_folders' section")

  elif not data["shared_folders"]:
    errors.append("No shared folders defined")

  return errors
