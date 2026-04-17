# plan.md — The Monolith CMS (MVP: Pages + Content Editor + Users + Integration Package)

## 1) Objectives
- ✅ Deliver a dark, emerald-accented CMS UI matching **“The Emerald Monolith”** spec.
- ✅ Provide a **visual page editor** where users can **select elements in the canvas** and **edit content only** (text/images/links), with **live preview updates**.
- ✅ Implement **Pages** (list + open) and **Draft/Publish workflow**.
- ✅ Implement **JWT auth** with roles (**Admin / Editor**) and gated endpoints.
- ✅ Establish a working **integration contract** for websites to fetch **published** page content via a public API.
- ✅ Add Phase 3 hardening features:
  - ✅ **Undo/Redo** (session-level) with toolbar buttons + keyboard shortcuts
  - ✅ **History snapshots** (server-side versioning) with restore UI
  - ✅ **Admin user management UI** (create/disable/role/password/delete)
- ✅ Deliver Phase 4 integration package (for “plug into any website”):
  - ✅ **Schema Import API** (website → CMS) with smart-merge
  - ✅ **Multi-project support** (projects + per-project page listing)
  - ✅ **Public content delivery endpoint** per project (CMS → website)
  - ✅ **Client Library** (vanilla JS snippet served by CMS)
  - ✅ **React Hook** (`useMonolithCMS`) for React/Emergent sites
  - ✅ **In-app Integration Guide** with copy/paste instructions for Emergent

**Current status:** Phases 1–4 COMPLETED and fully verified.
- Backend: ✅ 100% tests passed (Phase 4: 42/42)
- Frontend: ✅ Fully functional, manually verified
- Integration Guide: ✅ Working perfectly (admin-only access, complete Emergent instruction, schema import UI)
- Smart Merge Fix: ✅ VERIFIED - CMS edits are properly preserved when timestamps are newer than schema imports

---

## 2) Implementation Steps

### Phase 1 — Core Flow POC (Editor Selection → Right Panel Edit → Persist)
**Status:** ✅ Completed (implemented directly as part of the full app build).

**Delivered (Phase 1 acceptance):**
1. ✅ Open demo page rendered in center canvas.
2. ✅ Click element → emerald highlight + label.
3. ✅ Edit selected element content in right panel.
4. ✅ Canvas updates in real-time.
5. ✅ Save persists changes; refresh confirms persistence.

**Notes / Decisions captured:**
- Instead of relying on dynamic Tailwind classes from JSON (not safelisted at build time), the canvas preview was implemented with **inline style mappings** for reliable rendering.
- Element deselection implemented by detecting background clicks and setting selection to `null`.

---

### Phase 2 — V1 App Development (UI Shell + Pages + Auth)
**Status:** ✅ Completed.

**User stories (Phase 2) — Delivered**
1. ✅ Admin can log in and reach the editor workspace.
2. ✅ Workspace matches provided screen: top bar, left icon rail, center canvas, right properties panel.
3. ✅ Users can navigate between pages (Homepage + About).
4. ✅ Draft/Published state shown via status badge.
5. ✅ Device preview switching (desktop/tablet/mobile) resizes the canvas frame.
6. ✅ Editor role can log in and edit content.

**Backend (FastAPI + MongoDB) — Delivered**
- Data models implemented:
  - ✅ `User {email, password_hash, role, name, is_active}`
  - ✅ `Project {project_id, name, slug}` (minimal; default project seeded)
  - ✅ `Page {project_id, name, slug, status, elements[], published_elements?, updated_at, published_at}`
- Auth:
  - ✅ JWT login
  - ✅ `/api/auth/me`
  - ✅ Admin-only `/api/auth/register`
- Pages:
  - ✅ List pages
  - ✅ Get page
  - ✅ Content-only updates (single + bulk) with server-side enforcement (`content` only)
  - ✅ Publish endpoint (stores `published_elements` snapshot + `published_at`)
- Public “website consumption” API:
  - ✅ `GET /api/public/pages` returns published pages only (legacy default-project endpoint)
  - ✅ `GET /api/public/pages/{slug}` returns published page by slug (legacy default-project endpoint)

**Frontend (React) — Delivered**
- ✅ Login page (dark theme + emerald CTA)
- ✅ Editor shell:
  - ✅ Top bar: page name, status badge, device icons, tabs (Structure/SEO/History), Preview + Publish, avatar/logout
  - ✅ Left sidebar: + button + icons (Pages enabled; other items placeholder/disabled; Support icon)
  - ✅ Center canvas: rendered preview; selectable elements; deselect on background click
  - ✅ Right property panel: Element selector header + collapsible sections (Typography read-only, Content, Image, Link, Highlight)
- ✅ Editing experience:
  - ✅ Real-time updates
  - ✅ Dirty state indicator + Save button
  - ✅ Save (bulk) persists to backend
  - ✅ Publish updates status

**Phase 2 testing — Completed**
- ✅ E2E run-through: login → open page → edit content → save → publish → verify public API
- ✅ Backend endpoints validated (100% pass)
- ✅ Frontend flows validated; deselection bug fixed and manually re-verified.

---

### Phase 3 — Hardening + UX Polish (Still MVP)
**Status:** ✅ Completed.

**Delivered user stories (Phase 3)**
1. ✅ **Undo/Redo** (session-level)
   - Toolbar buttons in the top bar
   - Keyboard shortcuts: **Ctrl/Cmd+Z**, **Ctrl/Cmd+Y** (and Shift+Cmd/Ctrl+Z), and **Ctrl/Cmd+S** to save
2. ✅ **History snapshots**
   - Server-side versioning created on **Save** and **Publish**
   - History tab lists versions with version number, action type, timestamp, and author
   - Restore capability from any version (restores into Draft)
3. ✅ **Admin user management UI**
   - Admin-only panel accessible via sidebar (settings/users)
   - Create user (email/name/password/role)
   - Change role (admin/editor)
   - Toggle active/disabled (disabled users cannot log in)
   - Change password
   - Delete user (guardrails: cannot delete self; cannot deactivate self; cannot demote last active admin)

**Backend (Phase 3) — Delivered**
- ✅ `page_versions` collection storing snapshots with `version_number`, `created_at`, `created_by`, `action`
- ✅ Page history endpoints:
  - `GET /api/pages/{page_id}/versions`
  - `GET /api/pages/{page_id}/versions/{version_number}`
  - `POST /api/pages/{page_id}/versions/{version_number}/restore`
- ✅ User management endpoints (admin only):
  - `GET /api/users`
  - `PUT /api/users/{user_id}` (name/role/is_active)
  - `PUT /api/users/{user_id}/password`
  - `DELETE /api/users/{user_id}`

**Frontend (Phase 3) — Delivered**
- ✅ Undo/Redo UI integrated into top bar
- ✅ History tab renders server-side versions with restore action
- ✅ User Management screen for admin role

**Phase 3 testing — Completed**
- Backend: ✅ 100% (24/24)
- Frontend: ✅ 95% (22/23)
  - Only noted limitation: automated verification of canvas-driven undo/redo is harder for test runners; functionality manually verified.

---

### Phase 4 — Website Integration Package (Schema Import + Client Library + Docs)
**Status:** ✅ Completed.

**Goal:** Make “connect any new website to Monolith CMS” a repeatable workflow where you can hand Emergent a single instruction and receive:
- a `cms-schema.json`
- `data-cms-id` instrumentation in the markup
- either a script-tag integration (vanilla) or React hook integration

**Delivered (Phase 4)**

#### A) Multi-project support
- ✅ Projects collection indexed by `project_id`
- ✅ `GET /api/projects` list projects with page counts
- ✅ Pages listing supports `GET /api/pages?project_id=...` (defaults to `default`)

#### B) Schema Import API (Website → CMS)
- ✅ `POST /api/projects/import`
  - Accepts `{ project_name, pages[] }` (the `cms-schema.json` payload)
  - Creates project if missing
  - Creates or updates pages by slug
  - **Smart merge with timestamp-based conflict resolution:**
    - Compares `element_timestamps[element_id]` (CMS edit time) vs `source_updated_at` (website rebuild time)
    - If CMS edit is NEWER → **preserves CMS content**, updates structure/style only
    - If website rebuild is NEWER → takes new content
    - New elements are always added
    - ✅ **VERIFIED (iteration 5):** Timestamp comparison bug fixed, CMS edits now properly protected from older schema imports

#### C) Public content delivery (CMS → Website)
- ✅ `GET /api/public/{project_id}/content`
  - Returns published content as a **flat map** grouped by page slug: `{ "/": { "hero-headline": {content...}, ... } }`
  - Returns `{}` until content is published (expected)
- ✅ `GET /api/public/{project_id}/pages` (published pages)
- ✅ `GET /api/public/{project_id}/pages/{slug}` (published page tree)
- ✅ Legacy endpoints kept for backward compatibility:
  - `GET /api/public/pages` (default project)

#### D) Client Library
- ✅ `GET /api/client.js` served by backend
- ✅ Script-tag integration:
  - Reads `data-project` and `data-cms-url`
  - Fetches `/api/public/{project_id}/content`
  - Applies content to elements marked with `data-cms-id`
  - Supports:
    - text (`text`)
    - images (`src`, `alt`)
    - links (`href`)
    - heading highlight (`highlight.word`, `highlight.color`)

#### E) React Integration
- ✅ `useMonolithCMS(projectId, pageSlug, cmsUrl)` hook
  - Fetches published content
  - Provides helpers (`getContent`, `getHighlight`, `renderHighlightedText`)

#### F) Integration Documentation (in-app)
- ✅ “Integration Guide” screen (rocket icon) with:
  - Step 0: **Emergent prompt** (copy/paste instruction)
  - Step 1: Schema format example
  - Step 2: cURL import example
  - Step 3a: HTML `data-cms-id` + script tag example
  - Step 3b: React hook example
  - Element type reference + API reference

**Phase 4 testing — COMPLETED**
- ✅ Backend: 100% (42/42 tests passed)
- ✅ Frontend: Fully functional (login, editor, Integration Guide verified via manual testing)
- ✅ **CRITICAL FIX VERIFIED:** Smart merge timestamp comparison correctly preserves CMS edits when they are newer than schema re-imports (iteration 5)
- Test reports: `/app/test_reports/iteration_1-5.json`

---

### Phase 5 — Next Feature Track (Later, per your upcoming screens)
**Status:** ⏭️ Blocked on screens/spec.

**Collections (Webflow-like), Assets, Settings, Publishing workflows**
- Implement once you provide the Collections screens and requirements:
  - Collection schema definition
  - Entry editor
  - List/detail views
  - Relationships/references
  - Public collection API

---

## 3) Next Actions
- ✅ Phase 4 integration package is complete.
- ⏭️ Provide the next screens/spec for **Collections** when ready (Phase 5).
- ⏭️ Decide how Emergent should output the `cms-schema.json` automatically:
  - Where it lives in the repo
  - Whether it is generated at build time
  - Whether you want a “CMS export” button in Emergent
- ⏭️ Optional production-hardening items (when desired):
  - Restrict CORS origins
  - Add API keys / signed requests for public endpoints
  - Add project-level auth/ACLs (which editors can edit which projects)
  - Add import validation + schema versioning

---

## 4) Success Criteria
- ✅ Users can visually select elements in the canvas and edit **content only** with immediate feedback.
- ✅ Backend enforces “no layout/style edits” (content-only patches).
- ✅ Draft/Publish flow works; public endpoint serves published content reliably.
- ✅ UI matches the provided screenshot + DESIGN.md (dark surfaces, emerald accents, typography).
- ✅ End-to-end tests pass for: login → edit → save → publish → consume published content.
- ✅ Phase 3 capabilities proven:
  - Undo/Redo works and is accessible via UI + shortcuts
  - Version history exists, is visible, and supports restoring safely
  - Admin can manage users entirely from the UI
- ✅ Phase 4 integration capabilities proven:
  - New sites can be connected via schema import
  - Websites can consume published content via per-project public API
  - Vanilla JS snippet updates DOM via `data-cms-id`
  - React hook supports Emergent/React builds
  - Integration guide provides a single copy/paste instruction for Emergent
