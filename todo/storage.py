from __future__ import annotations

import csv
import os
import uuid
from dataclasses import dataclass
from typing import List


TASKS_CSV_HEADER = ["id", "title", "completed"]


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    completed: bool = False


def _parse_bool(value: str) -> bool:
    v = (value or "").strip().lower()
    if v in {"true", "1", "yes", "y", "t"}:
        return True
    if v in {"false", "0", "no", "n", "f", ""}:
        return False
    # Defensive default
    return False


def is_legacy_tasks_csv(path: str) -> bool:
    if not os.path.exists(path):
        return False

    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            first_row = next(reader, None)
    except OSError:
        # If we can't read it, treat as non-legacy to avoid destructive overwrite.
        return False

    if first_row is None:
        return False

    normalized = [c.strip().lower() for c in first_row]
    return normalized != TASKS_CSV_HEADER


def migrate_legacy_tasks_csv(path: str) -> None:
    if not os.path.exists(path):
        return
    if not is_legacy_tasks_csv(path):
        return

    legacy_titles: List[str] = []

    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                title = (row[0] or "").strip()
                if title:
                    legacy_titles.append(title)
    except OSError:
        # Can't read; leave as-is.
        return

    tasks = [Task(id=str(uuid.uuid4()), title=title, completed=False) for title in legacy_titles]
    save_tasks(path, tasks)


def load_tasks(path: str) -> List[Task]:
    """Load tasks from CSV.

    If file is legacy (single column, no header), it is migrated to v2.
    If file is missing/corrupt, returns an empty list.
    """

    if not os.path.exists(path):
        return []

    if is_legacy_tasks_csv(path):
        migrate_legacy_tasks_csv(path)

    tasks: List[Task] = []
    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return []
            for row in reader:
                task_id = (row.get("id") or "").strip()
                title = (row.get("title") or "").strip()
                completed_str = row.get("completed")
                if not task_id or not title:
                    continue
                tasks.append(Task(id=task_id, title=title, completed=_parse_bool(completed_str or "")))
    except (OSError, csv.Error):
        return []

    return tasks


def save_tasks(path: str, tasks: List[Task]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(TASKS_CSV_HEADER)
        for task in tasks:
            writer.writerow([task.id, task.title, "true" if task.completed else "false"])


def add_task(path: str, title: str) -> Task:
    cleaned = (title or "").strip()
    if not cleaned:
        raise ValueError("Task title cannot be empty")

    tasks = load_tasks(path)
    new_task = Task(id=str(uuid.uuid4()), title=cleaned, completed=False)
    tasks.append(new_task)
    save_tasks(path, tasks)
    return new_task


def set_task_completed(path: str, task_id: str, completed: bool) -> bool:
    tasks = load_tasks(path)
    updated = False
    new_tasks: List[Task] = []

    for t in tasks:
        if t.id == task_id:
            new_tasks.append(Task(id=t.id, title=t.title, completed=completed))
            updated = True
        else:
            new_tasks.append(t)

    if updated:
        save_tasks(path, new_tasks)

    return updated
