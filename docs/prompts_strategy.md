# Prompt & Regeneration Strategy (Crash-only)

## Core Philosophy
- **Crash-only**: No error handling, no retries, no complex recovery. If something goes wrong (API error, validation failure, DB issue), the process crashes immediately (500 Internal Server Error).
- **Synchronous**: No background tasks, no `task_id`. The client waits for the response.
- **KISS**: Minimal logic. Keep it simple.

## API Specification
- **Endpoint**: `PATCH /api/games/{slug}`
- **Query Params**:
  - `regenerate=true` (Required for regeneration)
  - `fill_missing_only=true|false` (Default: false)
- **Response**:
  - Success: 200 OK with updated game data.
  - Failure: 500 Internal Server Error (stack trace in server logs).

## Implementation Rules

### 1. Flow (Synchronous)
1.  **Validate**: Check inputs. If invalid -> Crash.
2.  **Generate**: Call Gemini. If 429/5xx or timeout -> Crash.
3.  **Parse**: Parse JSON. If invalid JSON or missing schema -> Crash.
4.  **Merge**:
    - `fill_missing_only=true`: Only update fields that are currently `null` or empty.
    - `fill_missing_only=false`: Overwrite all fields (except ID/Slug).
5.  **Save**: Update DB. If DB error -> Crash.

### 2. Validation
- Use `pydantic` or `jsonschema` to validate Gemini response.
- Any violation (missing field, wrong type) raises an unhandled exception.

### 3. Logging
- Standard output only (stdout/stderr).
- No custom file handlers or complex logging logic.

### 4. Slug & ID Preservation
- `slug` and `id` must never be changed during regeneration.
- `title` changes do not update the `slug`.

## Anti-Patterns (Forbidden)
- **No try-catch**: Do not catch exceptions to suppress them.
- **No Retries**: Do not implement retry logic or backoff.
- **No Background Tasks**: Everything must be synchronous.
- **No "Partial Success"**: Either it works completely, or it crashes.
