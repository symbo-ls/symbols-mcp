# symbols-mcp review server

Temporary review dashboard for the 25 md files inside `symbols-mcp/symbols_mcp/skills/`.

## Run

```bash
cd <symbols-mcp-checkout>/review-server
node server.js
# or pick a port
PORT=4747 node server.js
```

Then open `http://localhost:4747`.

## What it does

- Serves all 25 md files at `GET /api/files/:name` and lists at `GET /api/files`
- Renders each one with `marked` + syntax highlighting (`highlight.js`) + `DOMPurify`
- Lets you **select any text** in any file → a popover appears → write a comment for Claude
- Comments persist to `./comments.json` (a flat JSON list — easy for Claude to read + apply)
- Comments are anchored to the selected quote so highlights re-render across reloads
- Polls the API every 5s so Claude's edits to the md files show up live

## How comments flow

```
1. Select text in any file  →  popover  →  type comment  →  Save
2. POST /api/comments → appended to comments.json with { id, file, quote, comment, status, createdAt }
3. Claude reads comments.json, applies edits, then either:
   - PUT /api/comments/:id  with { status: 'resolved' }  to mark done
   - or you click "Resolve" in the UI when satisfied
```

## Keyboard

- `j` / `k` — next / prev file
- `/` — focus filter
- `s` — toggle source view
- `⌘ + Enter` — save comment (when popover open)
- `Esc` — close popover

## Endpoints

| Method | Path | Body | Returns |
| -- | -- | -- | -- |
| GET | `/api/files` | — | `[{ name, bytes, lines, mtime }, …]` |
| GET | `/api/files/:name` | — | `{ name, content }` |
| GET | `/api/comments` | — | `[{ id, file, quote, comment, status, createdAt, … }, …]` |
| POST | `/api/comments` | `{ file, quote, comment, line? }` | created comment |
| PUT | `/api/comments/:id` | partial | updated comment |
| DELETE | `/api/comments/:id` | — | 204 |

## Stop

```bash
# find pid
lsof -ti:4747 | xargs kill
```
