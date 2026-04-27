# The Monolith CMS — Product Requirements

## Original Problem Statement
User wants a CMS that can be plugged into any future Emergent website. The CMS must keep its full React UI (Google Stitch design: TopBar, LeftSidebar, Canvas, PropertyPanel, HistoryPanel) and run **per website** (not centralized) to avoid performance bottlenecks. User language: **GERMAN**.

## Architecture
- **Backend**: FastAPI + MongoDB (`/app/backend`)
- **Frontend**: React with custom Google Stitch dark theme (`/app/frontend`)
- **Auth**: JWT-based with bcrypt, admin/editor roles
- **Storage**: MongoDB (test_database)
- **Deployment Target**: per-website install (each site self-hosts the CMS)

## Core Features
1. **Editor**: Click-to-edit canvas, PropertyPanel for content updates, undo/redo, device modes, structure/SEO/history tabs
2. **Pages**: Static pages with element tree (heading, paragraph, image, button, badge, card, quote, section)
3. **Auth**: Admin + editor roles, project-level access control
4. **Versions**: Page version history with restore
5. **Public API**: `/api/public/{project}/content` delivers published content
6. **Integration**: Schema import (`POST /api/projects/import`) + client.js script for any website
7. **Smart Merge**: Timestamp-based merge so editor changes survive Emergent re-builds

## Test Credentials
- Admin: `admin@monolith.cms` / `admin123`
- Admin: `roman@zund.io` / `admin123`
- Editor: `editor@monolith.cms` / `editor123`

## Implementation Status

### ✅ Done (Feb 2026 fork)
- Static page edit flow polished (100% tests passing, 25/25 critical scenarios)
- Toast notifications added (sonner) for save/publish success + errors
- Ctrl+S works inside PropertyPanel inputs (was previously blocked)
- HISTORY/SEO tab now closes PagesList/UserManagement/IntegrationDocs panel automatically
- Demo data reset; 9 stale test projects cleaned from MongoDB
- End-to-end verified: login → click element → edit in PropertyPanel → live canvas update → Ctrl+S save → publish → public API delivers updated content

### 🔴 P0 — Per-Site React-UI Installer
- Compile React frontend (`/app/frontend/build`) and serve as static files from FastAPI
- Single install script (e.g. `install.sh` from GitHub) that sets up the full CMS on any website's server
- Replace MongoDB dependency option with embedded SQLite/JSON for zero-dependency installs (or document MongoDB requirement)
- Clean up `/app/monolith-cms-embedded/` and rejected vanilla-JS GitHub repo (`zundIO/emergent-cms`)

### 🟡 P1 — Dynamic Collections
- Editor for repeating content types (blog posts, products, team members, etc.)
- Schema definition for Collections separate from static Pages
- Public API endpoint for collection items

### 🟡 P1 — Asset/Image Management
- Image upload UI inside the editor
- Media library/picker for image elements
- Thumbnails + alt-text required workflow

### 🟢 P2 — reCAPTCHA on deployment safety
### 🟢 P2 — Toast on undo/redo notifications
### 🟢 P2 — Debounce undo stack to word-level (currently per-keystroke)

## Known Limitations
- `Canvas.js` has hardcoded `sectionStyles` map for the Monolith demo sections — non-default sections fall back to generic padding. Acceptable for now; will need a Tailwind class renderer for arbitrary imported pages.

## Key Files
- `/app/frontend/src/pages/EditorPage.js` — main editor orchestration
- `/app/frontend/src/components/editor/Canvas.js` — element rendering + selection
- `/app/frontend/src/components/editor/PropertyPanel.js` — right-side content editor
- `/app/frontend/src/components/editor/IntegrationDocs.js` — Emergent prompt + schema import UI
- `/app/backend/server.py` — all routes (auth, pages, projects, public, client.js)

## Key API Endpoints
- `POST /api/auth/login` — login
- `GET /api/projects` — list projects
- `POST /api/projects/import` — import cms-schema.json (admin)
- `GET /api/pages?project_id=X` — list pages
- `PUT /api/pages/{id}/content/bulk` — bulk save edits
- `PUT /api/pages/{id}/status` — publish/unpublish
- `GET /api/public/{project}/content` — public published content (no auth)
- `GET /api/client.js` — JavaScript client library for websites

## Next Action Items (priority order)
1. P0: Plan per-site installer architecture (decide: static React build served by FastAPI vs separate frontend deployment)
2. P0: Build install.sh + clean GitHub repo
3. P1: Dynamic Collections
4. P1: Asset Management
