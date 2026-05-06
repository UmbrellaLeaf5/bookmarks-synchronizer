from dataclasses import dataclass


@dataclass
class AppConfig:
  profiles: dict[str, str]
  shared_folders: list[str]
