# Monolith CMS — Embedded Edition

**Zero-config CMS** for any website built with Emergent or Next.js. One command installs. No manual code changes. Auto-updates.

## Install

From the project root:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh)"
```

The installer auto-detects your stack:

| Stack detected | What gets installed |
|---|---|
| **Emergent** (`backend/server.py` + `frontend/package.json`) | FastAPI router under `/api/cms/*`, admin UI at `/api/cms/admin`, browser client auto-injected into `index.html` |
| **Next.js** (`package.json` with `next`) | API routes in `pages/api/cms/*`, editor at `/cms`, client auto-injected into `_document.js` |

## What it does

1. Drops ~8 files into your project (never touches existing app code beyond a single `include_router` line / script tag).
2. Adds a tiny browser script that walks the DOM, assigns stable `data-cms-id`s to every editable element (h1–h6, p, a, button, img, li, …), and reports them back.
3. First visit to the admin UI runs a setup wizard that creates your admin password.
4. Every element you see on the site is editable from the admin panel — no source changes.

## Admin access

After installation, open:

- **Emergent stack**: `https://<your-domain>/cms`  _(redirects to `/api/cms/admin`)_
- **Next.js stack**: `https://<your-domain>/cms`

## Self-updates

Whenever the upstream repo receives a new commit:

- The browser client (`cms-client.js`) is loaded directly from GitHub via CDN and auto-updates within ~5 minutes — every installation, everywhere.
- The admin panel shows an **"Update CMS"** button that pulls the latest server-side code with one click. Restart the backend (or redeploy) to activate it.

User content (`cms-data/`) and secrets (`.cms-env.json`) are never touched by updates.

## Security

- Admin password is bcrypt-hashed
- JWT session cookie, HttpOnly, 7-day expiry
- `cms-data/` is auto-added to `.gitignore`
- Auto-discovery endpoint only ADDS metadata — never overwrites saved content

## Uninstall

```bash
# Emergent stack
rm -rf backend/cms frontend/public/cms-client.js cms-data
# Revert the include_router line in backend/server.py manually

# Next.js stack
rm -rf lib/cms pages/api/cms pages/cms.js public/cms-client.js cms-data .env.local
```

## License

MIT
