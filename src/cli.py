from src.models.sync import ConflictItem, SyncAction, UserDecision
from src.utils import format_timestamp, is_folder_url


class Cli:
  def ask(self, conflict: ConflictItem) -> UserDecision:
    print()
    print("=" * 60)
    print(f"  {conflict.title}")

    if not is_folder_url(conflict.url):
      print(f"  {conflict.url}")

    print(f"  Папка: {'/'.join(conflict.folder_path)}")

    if conflict.add_date:
      print(f"  Добавлена: {format_timestamp(conflict.add_date)}")

    print(f"  Есть:        {', '.join(conflict.present_in)}")
    print(f"  Отсутствует: {', '.join(conflict.missing_from)}")
    print()

    if is_folder_url(conflict.url):
      print(f"  [д] Создать папку в: {', '.join(conflict.missing_from)}")
      print(f"  [у] Удалить папку из: {', '.join(conflict.present_in)}")

    else:
      print(f"  [д] Добавить в: {', '.join(conflict.missing_from)}")
      print(f"  [у] Удалить из:  {', '.join(conflict.present_in)}")

    print("  [п] Пропустить")
    print("  [в] Выход (сохранить текущие решения)")
    print()

    source = sorted(conflict.present_in)[0] if conflict.present_in else None

    while True:
      choice = input("> ").strip().lower()

      if choice in ("д", "l", "d"):
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

      if choice in ("у", "e", "u"):
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

      if choice in ("п", "g", "p"):
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

      if choice in ("в", "d", "exit"):
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

      print("Неверный выбор. Введите д/у/п/в")

  @staticmethod
  def show_summary(
    conflicts_found: int,
    decisions_made: int,
    changes_applied: int,
  ) -> None:
    print()
    print("=" * 60)
    print("  Итоги синхронизации")
    print(f"  Всего расхождений:  {conflicts_found}")
    print(f"  Пропущено/обработано: {decisions_made}")
    print(f"  Изменений внесено:  {changes_applied}")
