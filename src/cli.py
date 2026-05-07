from src.models.sync import ConflictItem, SyncAction, UserDecision
from src.utils import format_timestamp, is_folder_url


class Cli:
  def ask(self, conflict: ConflictItem) -> UserDecision:
    print()
    print("=" * 60)
    print(f"  {conflict.title}")

    if not is_folder_url(conflict.url):
      print(f"  {conflict.url}")

    print(f"  Folder: {'/'.join(conflict.folder_path)}")

    if conflict.add_date:
      print(f"  Added: {format_timestamp(conflict.add_date)}")

    print(f"  Present in:  {', '.join(conflict.present_in)}")
    print(f"  Missing from: {', '.join(conflict.missing_from)}")
    print()

    if is_folder_url(conflict.url):
      print(f"  [a] Add folder to: {', '.join(conflict.missing_from)}")
      print(f"  [r] Remove folder from: {', '.join(conflict.present_in)}")

    else:
      print(f"  [a] Add to: {', '.join(conflict.missing_from)}")
      print(f"  [r] Remove from:  {', '.join(conflict.present_in)}")

    print("  [s] Skip")
    print("  [e] Exit (save current decisions)")
    print()

    source = sorted(conflict.present_in)[0] if conflict.present_in else None

    while True:
      choice = input("> ").strip().lower()

      if choice in ("a", "l", "d"):
        return UserDecision(
          url=conflict.url,
          title=conflict.title,
          add_date=conflict.add_date,
          folder_path=conflict.folder_path,
          action=SyncAction.ADD,
          target_profiles=conflict.missing_from,
          icon=conflict.icon,
          source_profile=source,
        )

      if choice in ("r", "e", "u"):
        return UserDecision(
          url=conflict.url,
          title=conflict.title,
          add_date=conflict.add_date,
          folder_path=conflict.folder_path,
          action=SyncAction.REMOVE,
          target_profiles=conflict.present_in,
          icon=conflict.icon,
          source_profile=source,
        )

      if choice in ("s", "g", "p"):
        return UserDecision(
          url=conflict.url,
          title=conflict.title,
          add_date=conflict.add_date,
          folder_path=conflict.folder_path,
          action=SyncAction.SKIP,
          target_profiles=[],
          icon=conflict.icon,
          source_profile=source,
        )

      if choice in ("e", "d", "exit"):
        return UserDecision(
          url=conflict.url,
          title=conflict.title,
          add_date=conflict.add_date,
          folder_path=conflict.folder_path,
          action=SyncAction.EXIT,
          target_profiles=[],
          icon=conflict.icon,
          source_profile=source,
        )

      print("Invalid choice. Enter a/r/s/e")

  @staticmethod
  def show_summary(
    conflicts_found: int,
    decisions_made: int,
    changes_applied: int,
  ) -> None:
    print()
    print("=" * 60)
    print("  Sync Summary")
    print(f"  Total conflicts:     {conflicts_found}")
    print(f"  Decisions made:      {decisions_made}")
    print(f"  Changes applied:     {changes_applied}")
