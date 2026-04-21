# Monolith CMS — Embedded Edition

**Zero-config** content management for any Next.js site. No manual attribution. No separate server. One command to install.

## Install

In the root of any Next.js project:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh)"
```

That's it.

## How it works

1. The installer drops a tiny CMS (~10 files) into your project:
   - `pages/cms.js` — admin editor page
   - `pages/api/cms/*` — backend routes (auth, content, register, setup, public)
   - `lib/cms/*` — storage + auth helpers
   - `public/cms-client.js` — runtime auto-discovery script
   - `cms-data/content.json` — file-based content store (gitignored)

2. The client script is auto-injected into `pages/_document.js`.

3. On every page load the client walks the DOM, assigns stable `data-cms-id`
   attributes to all editable elements (h1–h6, p, a, button, img, li, …), and
   reports them to `/api/cms/register`. No source changes. No manual tagging.

4. Open `/cms` → on first visit the setup wizard creates your admin password,
   then every auto-discovered element is ready to edit.

## Requirements

- Next.js project (pages router)
- Node 18+
- `bcryptjs` and `jose` will be installed automatically

## Security

- `.env.local` and `cms-data/` are automatically added to `.gitignore`
- Admin password is bcrypt-hashed
- JWT secret is auto-generated per installation
- Never commit `.env.local`

## Uninstall

```bash
rm -rf pages/cms.js pages/api/cms lib/cms public/cms-client.js cms-data
```

## License

MIT
