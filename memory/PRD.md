# The Monolith CMS — Product Requirements

## Original Problem Statement
User wants a CMS that can be **installed per Emergent website** (not centralized — performance reason). Full React UI (Google Stitch: TopBar, LeftSidebar, Canvas, PropertyPanel, HistoryPanel) must be preserved. Per-website install: single command clones the CMS from GitHub into the website's `/app`, CMS runs in-process with the host FastAPI, uses the website's MongoDB with prefixed collections (`cms_*`). User language: **GERMAN**.

## Architecture (Per-Site Install)

```
Target website (/app)
├── backend/
│   ├── server.py          ← host FastAPI; install_cms(app, ...) appended
│   └── .env               ← MONGO_URL, DB_NAME, CMS_ADMIN_EMAIL, CMS_ADMIN_PASSWORD, JWT_SECRET
├── frontend/              ← host website's frontend (untouched)
└── cms/                   ← the CMS package (copied by install.sh)
    ├── __init__.py
    ├── core.py            ← APIRouter with all CMS routes + install_cms()
    └── static/            ← pre-built React admin UI (Google Stitch)
```

### Mount points on the host FastAPI
| What | Where |
|---|---|
| Admin UI (React static) | `host.com/cms/` |
| CMS API | `host.com/api/cms/*` |
| Public content API | `host.com/api/cms/public/{project}/content` |
| Client.js drop-in | `host.com/api/cms/client.js` |

### Database
- Shared MongoDB with host website
- Separate collections: `cms_users`, `cms_pages`, `cms_projects`, `cms_page_versions`

## Test Credentials (seeded on install)
- Admin: `admin@monolith.cms` / `admin123` (overridable via `CMS_ADMIN_EMAIL` / `CMS_ADMIN_PASSWORD` env)

## Implementation Status

### ✅ Done (Feb 2026)
- Static page edit flow polished (Toast notifications, Ctrl+S in inputs, HISTORY/PagesList UX)
- **Per-Site Installer complete**:
  - Refactored `/app/backend/server.py` (1050 → 62 lines) into thin host wrapper
  - Created `/app/cms/` package with `install_cms(app, ...)` function
  - All routes moved to `APIRouter` under configurable prefix (default `/api/cms`)
  - `CLIENT_JS` updated with dynamic prefix placeholder
  - React admin UI built with `PUBLIC_URL=/cms` → `/app/cms/static/`
  - `/app/install.sh` one-line installer (161 lines, idempotent, validates target, backs up server.py)
  - `/app/README.md` with install + usage + architecture docs
  - Legacy code cleaned up: removed `/app/monolith-cms-embedded/`, `/app/cms-data/`, old prompts, `backend_test.py`
- End-to-end verified: Login, Edit, Save, Publish, Public Content, Schema Import — all via `/api/cms/*`

### 🔴 P0 — User Action Required
- **Push `/app` contents to `github.com/zundIO/cms`** (or preferred repo). The `install.sh` expects the repo at this location. Use "Save to Github" in Emergent chat.
- **Test installation** on a fresh Emergent website via: `bash -c "$(curl -fsSL https://raw.githubusercontent.com/zundIO/cms/main/install.sh)"`

### 🟡 P1 — Dynamic Collections
- Editor for repeating content types (blog posts, products, team members)
- Schema definition for Collections separate from static Pages
- Public API endpoint for collection items

### 🟡 P1 — Asset/Image Management
- Image upload UI in editor
- Media library/picker for image elements
- Required alt-text workflow

### 🟢 P2 — Backlog
- Debounce undo stack to word-level (currently per-keystroke)
- reCAPTCHA on login
- Tailwind-class renderer in Canvas for arbitrary imported pages
- Live-Preview iframe inside the editor
- i18n / multi-language pages

## Key Files
- `/app/cms/__init__.py` — package entry (`install_cms`)
- `/app/cms/core.py` — all CMS logic, routes, seed, client.js, `install_cms()`
- `/app/cms/static/` — pre-built React admin UI (tracked in git)
- `/app/backend/server.py` — host FastAPI (62 lines)
- `/app/install.sh` — one-line installer
- `/app/README.md` — install + usage docs
- `/app/frontend/src/pages/EditorPage.js` — main editor orchestration
- `/app/frontend/src/components/editor/Canvas.js` — element rendering + selection
- `/app/frontend/src/components/editor/PropertyPanel.js` — content editor panel
- `/app/frontend/src/components/editor/IntegrationDocs.js` — schema import UI (rocket-icon)
- `/app/frontend/src/lib/api.js` — uses `/api/cms` prefix

## Key API Endpoints (all under `/api/cms/*`)
- `POST /auth/login` — admin/editor login
- `GET /projects` — list projects
- `POST /projects/import` — import `cms-schema.json` (admin)
- `GET /pages?project_id=X` — list pages
- `PUT /pages/{id}/content/bulk` — bulk save edits
- `PUT /pages/{id}/status` — publish/unpublish
- `GET /public/{project}/content` — publicly accessible published content
- `GET /client.js` — drop-in JavaScript client library

## Verification Checklist
- [x] `/api/cms/auth/login` returns token
- [x] `/api/cms/pages` list works
- [x] `/api/cms/pages/{id}/content/bulk` saves edits
- [x] `/api/cms/pages/{id}/status` publishes
- [x] `/api/cms/public/default/content` returns published content
- [x] `/api/cms/projects/import` creates project from schema
- [x] `/api/cms/client.js` serves JS with correct `/api/cms/public/` URL
- [x] `/cms/` serves React admin UI (locally on port 8001)
- [x] MongoDB uses `cms_*` collections only
- [x] `/app/backend/server.py` is 62 lines (thin host wrapper)
- [x] Legacy `/api/*` routes removed (no collisions with host app)

## Next Action Items (priority order)
1. 🔴 **User**: Push `/app` to `github.com/zundIO/cms` via "Save to Github"
2. 🔴 **User**: Test `install.sh` on a fresh Emergent website
3. 🟡 Build Dynamic Collections feature
4. 🟡 Build Asset/Image Management
