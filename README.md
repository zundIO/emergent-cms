# The Monolith CMS

**A plug-and-play CMS for Emergent websites.**
Full Google-Stitch React editor + FastAPI backend, installed into each website with a single command.

---

## ⚡️ Install (on any Emergent website)

```bash
cd /app
bash -c "$(curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh)"
```

What the installer does:
1. Downloads the `cms/` package into `/app/cms/`
2. Appends `CMS_ADMIN_EMAIL`, `CMS_ADMIN_PASSWORD`, `JWT_SECRET` to `/app/backend/.env`
3. Patches `/app/backend/server.py` to mount the CMS
4. Restarts the backend via supervisor
5. Prints your admin credentials

**No extra services. No Docker. Uses the website's existing MongoDB** (separate `cms_*` collections).

---

## 🔌 What gets mounted on your website

| What | Where |
|---|---|
| Admin UI (React) | `https://your-site.com/api/cms-admin/` |
| CMS API | `https://your-site.com/api/cms/*` |
| Public content API (for the website itself) | `https://your-site.com/api/cms/public/{project}/content` |
| Client JS (drop-in script) | `https://your-site.com/api/cms/client.js` |

The host website keeps running on its own routes. The CMS lives in its own API namespace + its own Mongo collections (`cms_pages`, `cms_projects`, `cms_users`, `cms_page_versions`).

---

## 🧱 Connecting a website to its CMS

After install, open the admin UI, log in, and click the **rocket icon** in the left sidebar. The **Integration Guide** has a copy-paste prompt for Emergent that teaches it how to:

1. Add `data-cms-id="…"` to editable elements
2. Generate a `cms-schema.json` with the page structure
3. Embed the client.js script before `</body>`

Then in the admin UI, upload the `cms-schema.json` once. After that, editors can click-to-edit on the Canvas and publish — the website picks up changes automatically.

---

## 🏗 Architecture

```
Your website (/app)
├── backend/
│   ├── server.py           ← has `from cms import install_cms; install_cms(app, …)`
│   └── .env                ← MONGO_URL, DB_NAME, CMS_ADMIN_*, JWT_SECRET
├── frontend/               ← your website's frontend (unchanged)
└── cms/                    ← the CMS package (added by installer)
    ├── __init__.py
    ├── core.py             ← APIRouter with all CMS routes + install_cms()
    └── static/             ← pre-built React admin UI (Google Stitch)
```

FastAPI mounts the CMS router at `/api/cms/*` and the React admin UI as static files at `/api/cms-admin/*`. The path prefix `/api/*` is critical on Emergent stacks because the Kubernetes ingress routes only `/api/*` requests to the backend; everything else goes to the host frontend (which would otherwise hijack the admin UI). MongoDB collections are prefixed with `cms_` so they never collide with the host website's data.

---

## ⚙️ Configuration (env vars in `/app/backend/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `MONGO_URL` | (required) | The MongoDB connection URL — shared with host app |
| `DB_NAME` | `monolith_cms` | MongoDB database name |
| `CMS_ADMIN_EMAIL` | `admin@…` | First admin account, seeded on install |
| `CMS_ADMIN_PASSWORD` | (generated) | First admin password |
| `JWT_SECRET` | (generated) | Signs JWT tokens |
| `CMS_API_PREFIX` | `/api/cms` | Change only if you need a different prefix |
| `CMS_STATIC_PATH` | `/api/cms-admin` | Change to mount admin UI at a different path |

---

## 🗂 Using the CMS in Python (programmatic install)

If you prefer not to use `install.sh`, do it manually:

```python
from fastapi import FastAPI
from cms import install_cms

app = FastAPI()

install_cms(
    app,
    mongo_url="mongodb://localhost:27017",
    db_name="my_site",
    collection_prefix="cms_",
    api_prefix="/api/cms",
    static_path="/api/cms-admin",
    static_dir="/app/cms/static",
    jwt_secret="change-me-in-production",
    admin_email="admin@example.com",
    admin_password="changeme",
    seed_demo_content=False,
)
```

---

## 🔁 Updating the CMS

```bash
cd /app
bash -c "$(curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh)" -- --force
```

Your content in MongoDB is preserved — only the `cms/` code is replaced.

---

## 🔨 Features

- **Click-to-edit** Canvas with element selection + live preview
- **PropertyPanel** for editing text, images, buttons, badges, cards, quotes, headings with highlight
- **Version History** — every save creates a restorable snapshot
- **Device modes** — Desktop / Tablet / Mobile preview frames
- **Undo/Redo** with keyboard shortcuts (`Ctrl+Z` / `Ctrl+Y` / `Ctrl+S`)
- **Smart Merge** — when Emergent rebuilds the website, editor changes survive based on timestamps
- **Multi-project** — manage several websites from one CMS installation
- **Role-based access** — admins and editors; editors can be scoped to specific projects
- **Public content API** — websites fetch published content via a single endpoint
- **Zero-config client.js** — drop one `<script>` tag on any website

---

## 🛠 Development

For contributors:

```bash
git clone https://github.com/zundIO/emergent-cms.git
cd cms

# Backend dev server (in-place)
cd backend && python -m uvicorn server:app --reload --port 8001

# Frontend dev server
cd frontend && yarn install && yarn start

# Rebuild admin UI into cms/static/
cd frontend && REACT_APP_BACKEND_URL="" PUBLIC_URL="/api/cms-admin" yarn build
rm -rf ../cms/static && cp -r build ../cms/static
```

---

## 📝 License

MIT — use freely.

---

*Built with The Monolith design system. Maintained by zundIO.*
