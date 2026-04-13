# plan.md — The Monolith CMS (MVP: Pages + Content Editor + Users)

## 1) Objectives
- ✅ Deliver a dark, emerald-accented CMS UI matching **“The Emerald Monolith”** spec.
- ✅ Provide a **visual page editor** where users can **select elements in the canvas** and **edit content only** (text/images/links), with **live preview updates**.
- ✅ Implement **Pages** (list + open) and **Draft/Publish workflow**.
- ✅ Implement **JWT auth** with roles (**Admin / Editor**) and gated endpoints.
- ✅ Establish a working **integration contract** for websites to fetch **published** page content via a public API (Collections later).

**Current status:** Phase 1+2 completed and end-to-end verified. Backend tests 100%; frontend 95%+ and the only reported issue (deselection) is fixed.

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
- Instead of relying on dynamic Tailwind classes from JSON (which are not safelisted at build time), the canvas preview was implemented with **inline style mappings** for reliable rendering.
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
  - ✅ `User {email, password_hash, role, name}`
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
  - ✅ `GET /api/public/pages` returns published pages only
  - ✅ `GET /api/public/pages/{slug}` returns published page by slug

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
**Status:** ⏭️ Optional / Next (not started)

**Proposed user stories (Phase 3)**
1. Undo/redo (session-level or persisted).
2. Stronger “unsaved changes” UX (e.g., autosave toggle, last saved timestamp).
3. More robust selection UX:
   - element breadcrumb/path
   - keyboard navigation
   - lock selection while typing
4. Validation rules per element type (e.g., required fields, URL format).
5. Admin user management UI (create/disable users) beyond API-only.
6. Optional: history snapshots UI (History tab) to restore prior versions.

**Implementation steps (Phase 3)**
- Add client-side edit history stack (undo/redo) and optionally persist snapshots server-side.
- Add structured validation layer for `content` updates (type-safe schemas per element type).
- Expand History tab from placeholder to functional version list.
- Improve disabled sidebar items with clearer “Coming soon” treatment.
- Accessibility: focus management in property panel; consistent keyboard shortcuts.

**Phase 3 testing**
- E2E: Admin creates Editor → Editor edits draft → Admin publishes.
- Regression: selection/deselection, save/publish, device switching.

---

### Phase 4 — Next Feature Track (Later, per your upcoming screens)
**Status:** ⏭️ Blocked on screens/spec.

**Collections (Webflow-like), Assets, Settings, Publishing workflows**
- Implement once you provide the Collections screens and requirements:
  - Collection schema definition
  - entry editor
  - list/detail views
  - relationships/references
  - public collection API

---

## 3) Next Actions
- Decide whether to proceed with Phase 3 hardening items now (undo/redo + history + validation recommended).
- Provide next screens/spec for **Collections** when ready (Phase 4).
- Define integration details for real Emergent projects (project registration, mapping of pages/collections, environment-specific base URLs).

---

## 4) Success Criteria
- ✅ Users can visually select elements in the canvas and edit **content only** with immediate feedback.
- ✅ Backend enforces “no layout/style edits” (content-only patches).
- ✅ Draft/Publish flow works; public endpoint serves published content reliably.
- ✅ UI matches the provided screenshot + DESIGN.md (dark surfaces, emerald accents, typography).
- ✅ End-to-end tests pass for: login → edit → save → publish → consume published content.
