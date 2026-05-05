# The Monolith CMS — Product Requirements

## Original Problem Statement
User wants a CMS that can be **installed per Emergent website** (not centralized — performance reason). Full React UI (Google Stitch: TopBar, LeftSidebar, Canvas, PropertyPanel, HistoryPanel) must be preserved. Per-website install: single command clones the CMS from GitHub into the website's `/app`, CMS runs in-process with the host FastAPI, uses the website's MongoDB with prefixed collections (`cms_*`). User language: **GERMAN**.

## Architecture (Per-Site Install)

```
Target website (/app)
├── backend/
│   ├── server.py          ← host FastAPI; install_cms(app, ...) appended
│   └── .env               ← MONGO_URL, DB_NAME, CMS_ADMIN_*, JWT_SECRET, CMS_API_PREFIX, CMS_STATIC_PATH
├── frontend/              ← host website's frontend (CMS scanner finds editable elements here)
└── cms/                   ← the CMS package (copied by install.sh)
    ├── __init__.py
    ├── core.py            ← APIRouter with all CMS routes + install_cms()
    ├── scanner.py         ← AST-based JSX scanner for Auto-Connect
    ├── VERSION            ← {commit, ref, repo} written by installer
    └── static/            ← pre-built React admin UI
```

### Mount points (all under `/api/*` to bypass K8s ingress that routes non-/api to frontend)
| What | Where |
|---|---|
| Admin UI (React) | `host.com/api/cms-admin/` |
| CMS API | `host.com/api/cms/*` |
| Public content API | `host.com/api/cms/public/{project}/content` |
| Client.js drop-in | `host.com/api/cms/client.js` |

### Database
- Shared MongoDB with host website
- Separate collections: `cms_users`, `cms_pages`, `cms_projects`, `cms_page_versions`

## Test Credentials
- Admin: `admin@monolith.cms` / `admin123` (overridable via `CMS_ADMIN_EMAIL` / `CMS_ADMIN_PASSWORD` env)

## Implementation Status

### ✅ Done (Feb–May 2026)

**Phase 1 — Editor UX**
- Static page edit flow polished (Toast notifications, Ctrl+S in inputs, HISTORY/PagesList UX)

**Phase 2 — Per-Site Installer**
- Refactored `/app/backend/server.py` (1050 → 62 lines) into thin host wrapper
- Created `/app/cms/` package with `install_cms(app, ...)` function
- All routes moved to `APIRouter` under configurable prefix (default `/api/cms`)
- React admin UI built with `PUBLIC_URL=/api/cms-admin` + `BrowserRouter basename`
- `/app/install.sh` one-line installer with `--upgrade` and `--force` flags
- Idempotent admin seeding (re-creates configured admin if .env was fixed after install)
- Newline-safe `.env` patching (fixes parse errors when host .env didn't end with `\n`)

**Phase 3 — Auto-Update**
- `install.sh --upgrade` flag preserves `.env`/MongoDB/admin user, only replaces code
- VERSION file (`/app/cms/VERSION`) tracks commit + repo + ref
- Backend endpoints: `GET /system/version`, `GET /system/check-update`, `POST /system/upgrade`
- Frontend: `UpdateChecker` component with badge + modal; auto-poll every 30 min; one-click upgrade

**Phase 4 — Auto-Connect (NEW)**
- AST-based JSX scanner using `tree-sitter` + `tree-sitter-language-pack` (no regex)
- `/app/cms/scanner.py` walks `frontend/src/pages/`, finds editable elements (`h1-6`, `p`, `button`, `a`, `span`, `img`)
- Filters out: dynamic JSX expressions, capitalized React components (Shadcn/Radix etc.), nested elements, files in `node_modules` / `components/ui` / test files
- Backend endpoints: `POST /system/scan-website`, `POST /system/apply-connection`
- Frontend: New "Connect This Website" section in Integration Guide (rocket icon)
  - Click → AST scan
  - Preview table: tag, page, content, generated ID
  - Checkboxes (select/deselect all)
  - Project name input
  - Apply → injects `data-cms-id` into source files + creates project + pages with smart-merge protection
- Manual Emergent prompt remains as Section 2 (fallback for edge cases)

### 🟡 P1 — Dynamic Collections
- Editor for repeating content types (blog posts, products, team members)
- Schema definition for Collections separate from static Pages
- Public API endpoint for collection items

### 🟡 P1 — Asset/Image Management
- Image upload UI in editor
- Media library/picker for image elements
- Required alt-text workflow

### 🟢 P2 — Backlog
- Auto-inject client.js script tag into `public/index.html` during apply-connection
- Preview iframe of the website inside the editor canvas
- Show release notes (GitHub compare API) in update modal
- Debounce undo stack to word-level (currently per-keystroke)
- reCAPTCHA on login
- Tailwind-class renderer in Canvas for arbitrary imported pages
- i18n / multi-language pages

## Key Files
- `/app/cms/__init__.py` — package entry (`install_cms`)
- `/app/cms/core.py` — all routes, seed, client.js, system endpoints, install_cms()
- `/app/cms/scanner.py` — AST scanner for Auto-Connect
- `/app/cms/static/` — pre-built React admin UI (tracked in git)
- `/app/backend/server.py` — host FastAPI (62 lines)
- `/app/install.sh` — installer with --upgrade / --force flags
- `/app/README.md` — install + usage + architecture docs
- `/app/frontend/src/pages/EditorPage.js` — editor orchestration
- `/app/frontend/src/components/editor/IntegrationDocs.js` — Auto-Connect UI + manual fallback
- `/app/frontend/src/components/editor/UpdateChecker.js` — version badge + upgrade modal
- `/app/frontend/src/lib/api.js` — uses `/api/cms` prefix

## Key API Endpoints (all under `/api/cms/*`)
- `POST /auth/login` — admin/editor login
- `GET /projects` / `POST /projects/import` — project mgmt + manual schema import
- `GET /pages?project_id=X` / `PUT /pages/{id}/content/bulk` / `PUT /pages/{id}/status`
- `GET /public/{project}/content` — public published content
- `GET /client.js` — drop-in JS for websites
- `GET /system/version` (public) — installed version
- `GET /system/check-update` (admin) — compares with GitHub
- `POST /system/upgrade` (admin) — runs install.sh --upgrade
- `POST /system/scan-website` (admin) — AST scan of host frontend
- `POST /system/apply-connection` (admin) — injects data-cms-id + creates project

## Next Action Items (priority order)
1. 🔴 **User**: Push `/app` to `github.com/zundIO/emergent-cms` via "Save to Github"
2. 🔴 **User**: Test on a fresh Emergent website end-to-end (install → login → Auto-Connect → publish)
3. 🟡 Asset/Image Management
4. 🟡 Dynamic Collections
