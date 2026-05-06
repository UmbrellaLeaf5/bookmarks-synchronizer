from __future__ import annotations

from src.cli import ask_user_resolve, show_sync_summary
from src.config import load_config
from src.models import FolderNode, Profile
from src.parser import parse_bookmark_file
from src.syncer import (
  apply_decisions,
  collect_conflicts,
  count_bookmarks,
  find_folder,
  now_ts,
)
from src.writer import write_bookmark_file


def main() -> None:
  print("=" * 60)
  print("  Bookmarks Manager - синхронизация закладок Chrome")
  print("=" * 60)

  # 1. Load config
  print("\n[1/5] Загрузка конфигурации...")
  try:
    config = load_config("config.json")
  except (FileNotFoundError, ValueError) as e:
    print(f"  [X] {e}")
    return
  print(f"  Профилей: {', '.join(config.profiles.keys())}")
  print(f"  Общие папки: {', '.join(config.shared_folders)}")

  # 2. Parse profiles
  print("\n[2/5] Чтение файлов закладок...")
  profiles: dict[str, Profile] = {}
  for name, path in config.profiles.items():
    root = parse_bookmark_file(path)
    total = count_bookmarks(root)
    profiles[name] = Profile(name=name, filepath=path, root=root)
    print(f"  [V] {name}: {total} закладок")
  print("  [V] Все файлы прочитаны")

  # 3. Collect conflicts
  print("\n[3/5] Поиск расхождений в общих папках...")
  all_conflicts = []
  for shared_folder in config.shared_folders:
    folder_maps: dict[str, FolderNode | None] = {}
    for name, profile in profiles.items():
      assert profile.root is not None
      folder = find_folder(profile.root, shared_folder)
      if folder is None:
        folder = FolderNode(
          name=shared_folder,
          add_date=now_ts(),
          last_modified=now_ts(),
          children=[],
        )
        profile.root.children.append(folder)
      folder_maps[name] = folder
    conflicts = collect_conflicts(folder_maps, [shared_folder])
    all_conflicts.extend(conflicts)
    print(f'  Папка "{shared_folder}": {len(conflicts)} расхождений')

  if not all_conflicts:
    print("\n  [V] Расхождений нет. Все профили синхронизированы.")
    return

  print(f"\n  Всего расхождений: {len(all_conflicts)}")

  # 4. Interactive resolution
  print("\n[4/5] Разрешение конфликтов (д/у/п/в для каждого)...")
  decisions = []
  for i, conflict in enumerate(all_conflicts, 1):
    print(f"\n  --- Конфликт {i}/{len(all_conflicts)} ---")
    decision = ask_user_resolve(conflict)
    if decision.action == "exit":
      print("  Выход по запросу пользователя.")
      break
    decisions.append(decision)

  if not decisions:
    print("  Нет принятых решений. Завершение.")
    return

  # 5. Apply and write
  print(f"\n[5/5] Применение {len(decisions)} решений...")
  changes = 0
  for shared_folder in config.shared_folders:
    root_maps: dict[str, FolderNode | None] = {}
    for name, profile in profiles.items():
      assert profile.root is not None
      folder = find_folder(profile.root, shared_folder)
      if folder is None:
        folder = FolderNode(
          name=shared_folder,
          add_date=now_ts(),
          last_modified=now_ts(),
          children=[],
        )
        profile.root.children.append(folder)
      root_maps[name] = folder

    folder_decisions = [
      d for d in decisions if d.folder_path and d.folder_path[0] == shared_folder
    ]
    if folder_decisions:
      apply_decisions(root_maps, folder_decisions)
      changes += sum(1 for d in folder_decisions if d.action in ("add", "remove"))

  # Write updated files
  for name, profile in profiles.items():
    assert profile.root is not None
    write_bookmark_file(profile.root, profile.filepath)
    bak = write_bookmark_file(profile.root, profile.filepath)
    msg = f"  [V] {name}: сохранено"
    if bak:
      msg += f" (бэкап: {bak})"
    print(msg)

  show_sync_summary(
    conflicts_found=len(all_conflicts),
    decisions_made=len(decisions),
    changes_applied=changes,
  )
  print("\n  [V] Готово!")


if __name__ == "__main__":
  main()
