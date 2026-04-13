# plan.md — The Monolith CMS (MVP: Pages + Content Editor + Users)

## 1) Objectives
- Deliver a dark, emerald-accented CMS UI matching **“The Emerald Monolith”** spec.
- Provide a **visual page editor** where users can **select elements in the canvas** and **edit content only** (text/images/links), with **live preview updates**.
- Implement **Pages CRUD + Draft/Publish** and **JWT auth with roles (Admin/Editor)**.
- Establish a clean **integration contract**: websites fetch published content via API (collections later).

---

## 2) Implementation Steps

### Phase 1 — Core Flow POC (Editor Selection → Right Panel Edit → Persist)
**Goal:** Prove the hardest workflow works end-to-end before building the full app shell.

**User stories (Phase 1)**
1. As a user, I can open a single demo page and see it rendered in the center canvas.
2. As a user, I can click an element in the canvas and see it highlighted with an emerald outline + label.
3. As a user, I can edit the selected element’s content in the right panel.
4. As a user, I see the canvas update immediately as I type.
5. As a user, I can save changes and reload to confirm persistence.

**Steps**
- Define minimal JSON page schema (elements tree with `content` editable; `style/type` read-only).
- Backend POC endpoints (no auth):
  - `GET /api/pages/:id` (returns page JSON)
  - `PUT /api/pages/:id` (updates element content by id; validates “content-only”)
- Frontend POC route:
  - Render demo page from JSON.
  - Implement element selection overlay (emerald border + floating label).
  - Right panel shows contextual fields for selected element type (H1/paragraph/button/image).
  - Save button triggers PUT; reload fetch verifies persistence.
- Quick websearch (best practices): content-only patching + element id mapping + immutable updates (React).
- Fix until: selection is reliable, edits never mutate style/layout, persistence consistent.

**Exit criteria**
- Click-to-select never selects wrong element; edited content survives refresh.

---

### Phase 2 — V1 App Development (UI Shell + Pages + Auth)
**User stories (Phase 2)**
1. As an Admin, I can log in and reach the editor workspace.
2. As a user, I can see the left sidebar + top bar exactly like the provided screen.
3. As a user, I can navigate between pages (Homepage + at least 1 additional page).
4. As a user, I can switch Draft/Published and see status reflected in UI.
5. As a user, I can preview device sizes (desktop/tablet/mobile) in the canvas.
6. As an Editor, I can edit content but cannot access admin-only actions.

**Backend (FastAPI + MongoDB)**
- Data models:
  - `User {email, password_hash, role}`
  - `Project {name, domains[] (optional for later)}` (minimal)
  - `Page {project_id, name, slug, status(draft/published), elements[], updated_at}`
- Auth:
  - JWT login/register, role-based guards.
- Pages:
  - List pages, get page, update content-only (server-side enforcement).
  - Publish endpoint: copies draft → published snapshot (or status flip + versioned field).
- “Website consumption” API:
  - `GET /api/public/projects/:projectId/pages/:slug` returns **published** content JSON.

**Frontend (React)**
- App shell matching design:
  - Top bar: logo, page name + status badge, device icons, tabs (Structure active; SEO/History placeholders), Preview + Publish.
  - Left sidebar icon-only + “+” button (disabled/placeholder; since layout edits not allowed).
  - Right panel: Element selector header + collapsible sections; content editors only.
- Pages experience:
  - Pages list view (in main area or modal) → open page in editor.
  - Editor route: fetch page, render canvas, selection/edit/persist.
- Styling:
  - Implement tokens (surfaces, emerald gradient buttons, no hard borders, 0.25rem radii, Inter/Space Grotesk).

**Phase 2 testing (1 E2E pass)**
- Run through: login → open page → edit H1 + button text → save → publish → fetch public endpoint and verify published content.

---

### Phase 3 — Hardening + UX Polish (Still MVP)
**User stories (Phase 3)**
1. As a user, I can undo/redo my last edits (session-level).
2. As a user, I can see a clear “unsaved changes” indicator.
3. As a user, I can’t accidentally edit when clicking empty canvas space.
4. As a user, validation errors are clear (e.g., empty required text).
5. As an Admin, I can manage users (create editor, disable user).

**Steps**
- Add content patch validation (type-safe per element type).
- Add debounced autosave (optional) or explicit save + dirty state.
- Add history snapshots for page edits (minimal: store last N versions).
- Add user management endpoints + minimal UI.
- Improve accessibility/keyboard navigation for selection + right panel inputs.

**Phase 3 testing (1 E2E pass)**
- Multi-user: Admin creates Editor → Editor edits draft → Admin publishes.

---

### Phase 4 — Next Feature Track (Later, per your upcoming screens)
**Collections (Webflow-like), Assets, Settings, Publishing workflows**
- Implement after you provide Collections screens + required field types and list/detail UX.

---

## 3) Next Actions
- Confirm element types for MVP: **heading, paragraph, button, image, label/badge** (based on screen).
- Implement Phase 1 POC (single demo page) and validate selection/edit/save.
- Once Phase 1 exits cleanly, build Phase 2 full shell + auth + pages list + publish.

---

## 4) Success Criteria
- Users can visually select elements in the canvas and edit **content only** with immediate feedback.
- Backend enforces “no layout/style edits” (content-only patches).
- Draft/Publish flow works; public endpoint serves published content reliably.
- UI matches the provided screenshot + DESIGN.md (dark surfaces, emerald accents, typography).
- End-to-end tests pass for: login → edit → save → publish → consume published content.
