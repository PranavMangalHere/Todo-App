# Implementation Plan

## Requirement

LOGQA-321 — Render tasks with checkboxes and support toggling completion

Supporting stories/enabling work: LOGQA-320 (Task data model + structured persistence), LOGQA-322 (Migrate legacy tasks.csv flat list file).

## Objective

Implement a real “completed” state per task, render tasks with Streamlit checkboxes, persist toggles to disk, and automatically migrate existing legacy `tasks.csv` (single column list of titles) to a structured CSV schema, without data loss or duplication.

## Current Implementation

Files: `app.py`, `requirements.txt`.

- The app loads a list of tasks via `load_tasks()`, which reads `tasks.csv` as a plain CSV with one value per row and returns `List[str]`: `task_list = [row[0] for row in reader]`.
  - If the file doesn’t exist, it returns an empty list.
- The UI shows a text input and an “Add” button that appends the text to the list, then overwrites the CSV via `save_tasks()` which writes `[[task]]` rows.
- The app also provides a “Clear all tasks” button that clears the in-memory list and overwrites the CSV empty.

Note: README mentions checkbox completion and `main.py`, but the code currently lives in `app.py` and does not support completion.

## Proposed Changes

### Frontend

- Update task display to render each task with a checkbox that reflects the persisted `completed` state.
  - Each checkbox must have a stable, unique Streamlit key based on task id (e.g. `task-<task_id>`) to avoid collisions for duplicate titles.
- Wire checkbox toggle events to update the stored task by id and rerender from storage on rerun.
- Use `st.session_state` for the new-task input (e.g. `key="new_task"`) so clearing input and reruns behave predictably.

### Backend

(There is no separate server backend; “backend” here is the Python domain/storage logic.)

- Introduce a Task data model: `id` (string), `title` (string), `completed` (bool).
  - IDs must be stable and unique. Use `uuid.uuid4()`.
- Replace `load_tasks()` and `save_tasks()` with schema-aware read/write helpers that handle:
  1) Structured CSV (expected header, parse rows into Task objects)
  2) Legacy CSV (no header, single column titles) — detect and migrate.
- Add an update operation, e.g. `set_task_completed(task_id: str, completed: bool)` that loads tasks, updates the matching task by id, and persists.
- Ensure migration is idempotent: if `tasks.csv` is already structured, do not duplicate tasks or reassign IDs.

### Database

- Continue using `tasks.csv` as persistence, but change format to structured CSV with header.
- Proposed columns: `id,title,completed`
  - Store `completed` consistently (e.g. `true/false`).

### API

- None (Streamlit UI + local file persistence).

## Files to Modify

- `app.py` (adjust UI rendering, add/toggle wiring, replace load/save usage)

## New Files

- `tasks.py` (Task model + CSV storage helpers + migration routine)

## Components Affected

- Streamlit UI
- CSV persistence layer (load/save/migrate)

## Dependencies

- No new runtime dependencies beyond standard library (`csv`, `uuid`, `dataclasses`/`typing`) and existing Streamlit.
- If automated tests are added later: add `pytest` (repo currently has no test tooling; confirm desired direction).

## Testing Strategy

- Unit tests (for `tasks.py`)—recommended if test framework is acceptable:
  - Loading structured CSV returns Task objects with correct fields.
  - Saving tasks writes header and all rows; reload matches.
  - Migration: legacy file migrates once; second run is a no-op.
  - Malformed/empty legacy file does not crash; yields empty list.
  - Toggle updates only the targeted task by id.
- Manual verification (minimum, if tests are not introduced):
  1) Start with no `tasks.csv` → add a task → reload app → checkbox state persists.
  2) Create legacy `tasks.csv` with one title per row → run app → verify titles preserved and all unchecked.
  3) With duplicate titles, toggle one → verify the correct one persists (id-based).

## Deployment Considerations

- File persistence on hosted Streamlit environments may be ephemeral or shared between users/sessions.
  - Confirm the deployment target; if multi-user/durable storage is required, consider SQLite or external storage as follow-up.
- Migration runs on startup; ensure it does not break existing deployments with legacy `tasks.csv`.

## Risks

- Streamlit rerun/state: if checkbox keys are not stable per task id, toggles may appear to “move” between tasks.
- CSV migration edge cases: malformed CSV, empty rows, commas/newlines in titles.
  - Mitigation: use `csv` module consistently, skip empty rows, always write header for structured file.
- Concurrent writes to `tasks.csv` can lose updates in multi-user environments.
  - Mitigation is out of scope for this story; document as limitation.

## Rollback Strategy

- Code rollback: revert commits that change UI logic and storage helpers.
- Data rollback: before migration, create a one-time backup `tasks.csv.bak` if it does not already exist.
  - If rollback is needed, restore `tasks.csv.bak` → `tasks.csv` to return to legacy behavior.
