#!/bin/bash
# Monolith CMS - Universal One-Command Installer
# Detects the stack automatically (Emergent React+FastAPI OR Next.js) and
# installs the appropriate CMS edition. Zero manual steps required.
#
# Usage: bash -c "$(curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh)"

set -e

REPO="zundIO/emergent-cms"
BRANCH="main"
BASE_URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; NC='\033[0m'

banner() {
  echo ""
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN}  $1${NC}"
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

log()  { echo -e "${BLUE}$1${NC}"; }
warn() { echo -e "${YELLOW}$1${NC}"; }
die()  { echo -e "${RED}$1${NC}"; exit 1; }

# ---------------------------------------------------------------------------
# Stack detection
# ---------------------------------------------------------------------------

detect_stack() {
  # Emergent stack: /app root with backend/server.py (FastAPI) + frontend/package.json
  if [ -f "backend/server.py" ] && [ -f "frontend/package.json" ]; then
    echo "emergent"; return
  fi
  # Next.js stack: package.json with "next" dependency
  if [ -f "package.json" ] && grep -q '"next"' package.json; then
    echo "nextjs"; return
  fi
  echo "unknown"
}

ROOT="$(pwd)"

# If run from /app or any parent of backend/, normalize to project root
if [ -d "/app/backend" ] && [ -d "/app/frontend" ] && [ ! -f "backend/server.py" ]; then
  cd /app
  ROOT="$(pwd)"
fi

STACK="$(detect_stack)"

banner "Monolith CMS — Universal Installer"
echo "Detected stack: ${STACK}"
echo "Project root:   ${ROOT}"
echo ""

# ===========================================================================
# EMERGENT STACK (FastAPI + React)
# ===========================================================================
install_emergent() {
  log "Step 1/6 · Creating directories…"
  mkdir -p backend/cms frontend/public cms-data

  log "Step 2/6 · Downloading FastAPI backend files…"
  curl -fsSL "${BASE_URL}/emergent/backend/cms/__init__.py"   -o backend/cms/__init__.py
  curl -fsSL "${BASE_URL}/emergent/backend/cms/router.py"     -o backend/cms/router.py
  curl -fsSL "${BASE_URL}/emergent/backend/cms/storage.py"    -o backend/cms/storage.py
  curl -fsSL "${BASE_URL}/emergent/backend/cms/auth.py"       -o backend/cms/auth.py
  curl -fsSL "${BASE_URL}/emergent/backend/cms/admin_html.py" -o backend/cms/admin_html.py

  log "Step 3/6 · Downloading browser client script…"
  curl -fsSL "${BASE_URL}/public/cms-client.js" -o frontend/public/cms-client.js

  log "Step 4/6 · Installing Python dependencies (bcrypt, PyJWT, httpx)…"
  if [ -d "/root/.venv" ]; then
    PIP="/root/.venv/bin/pip"
  elif command -v pip >/dev/null 2>&1; then
    PIP="pip"
  else
    PIP="pip3"
  fi
  $PIP install -q bcrypt PyJWT httpx >/dev/null 2>&1 || $PIP install bcrypt PyJWT httpx

  # Freeze updated deps (preserves existing requirements.txt conventions)
  if [ -f "backend/requirements.txt" ]; then
    for dep in bcrypt PyJWT httpx; do
      if ! grep -qi "^${dep}" backend/requirements.txt; then
        echo "${dep}" >> backend/requirements.txt
      fi
    done
  fi

  log "Step 5/6 · Patching backend/server.py (mounting CMS router)…"
  SERVER="backend/server.py"
  if [ ! -f "$SERVER" ]; then die "backend/server.py not found"; fi

  if grep -q "from cms.router import router as cms_router" "$SERVER"; then
    echo "  server.py already patched"
  else
    python3 - <<'PYFIX'
import re, sys, pathlib
p = pathlib.Path("backend/server.py")
src = p.read_text()
import_line = "from cms.router import router as cms_router\n"
mount_line  = "app.include_router(cms_router)\n"

# Insert import after the last existing top-level import block
lines = src.splitlines(keepends=True)
out = []
inserted_import = False
for i, ln in enumerate(lines):
    out.append(ln)
    if not inserted_import and (ln.startswith("from ") or ln.startswith("import ")):
        # peek next non-import line to place import before it
        j = i + 1
        while j < len(lines) and (lines[j].startswith("from ") or lines[j].startswith("import ") or lines[j].strip() == ""):
            j += 1
        # We'll insert right before the first non-import line after this block
        if j > i + 1 and not (lines[j].startswith("from ") or lines[j].startswith("import ")):
            # Only inject once, after this block
            inserted_import = True
            # Append blank line if needed, then import
            if out[-1].strip() != "":
                out.append("\n")
            out.append(import_line)
if not inserted_import:
    out.insert(0, import_line)

src2 = "".join(out)
if "app.include_router(cms_router)" not in src2:
    # Find the FastAPI app instance and append include_router after it
    m = re.search(r"^(app\s*=\s*FastAPI\([^)]*\))", src2, re.MULTILINE)
    if m:
        end = m.end()
        src2 = src2[:end] + "\n\n# Monolith CMS (auto-injected)\n" + mount_line + src2[end:]
    else:
        src2 += "\n\n# Monolith CMS (auto-injected)\n" + mount_line

p.write_text(src2)
print("  server.py patched")
PYFIX
  fi

  log "Step 6/6 · Injecting browser client + /cms shortcut…"
  INDEX="frontend/public/index.html"
  APP_JS=""
  for cand in frontend/src/App.js frontend/src/App.jsx frontend/src/App.tsx; do
    [ -f "$cand" ] && APP_JS="$cand" && break
  done

  # (A) Patch index.html  -> cms-client.js + /cms redirect in <head>
  #     We always run the patcher so re-runs don't skip when client already injected.
  if [ -f "$INDEX" ]; then
    python3 - <<PYHTML
import pathlib
p = pathlib.Path("$INDEX")
s = p.read_text()
changed = False

head_snippet = '''  <script>
    // Monolith CMS — /cms shortcut
    (function(){ var p=location.pathname; if(p==='/cms'||p==='/cms/') location.replace('/api/cms/admin'+location.search); })();
  </script>
</head>'''
if "Monolith CMS — /cms shortcut" not in s and "</head>" in s:
    s = s.replace("</head>", head_snippet, 1); changed = True

body_snippet = '    <script src="${BASE_URL}/public/cms-client.js" defer></script>\n  </body>'
if "cms-client.js" not in s and "</body>" in s:
    s = s.replace("</body>", body_snippet, 1); changed = True

if changed:
    p.write_text(s)
    print("  index.html patched")
else:
    print("  index.html already up to date")
PYHTML
  else
    warn "  frontend/public/index.html not found — skipped"
  fi

  # (B) Patch App.js  -> add <Route path=\"/cms\" element={<CmsRedirect />} />
  #     This is the RELIABLE shortcut: works even if Emergent overwrites index.html.
  if [ -n "$APP_JS" ]; then
    python3 - <<PYAPP
import re, pathlib
p = pathlib.Path("$APP_JS")
s = p.read_text()
if "CmsRedirect" in s:
    print("  App.js already has CmsRedirect")
else:
    component = '''
// Monolith CMS shortcut: /cms -> /api/cms/admin
function CmsRedirect() {
  if (typeof window !== "undefined") window.location.replace("/api/cms/admin");
  return null;
}
'''
    # Insert component after the last import line
    lines = s.splitlines(keepends=True)
    last_import = -1
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith(("import ", "require(")):
            last_import = i
    if last_import >= 0:
        lines.insert(last_import + 1, component)
        s = "".join(lines)
    else:
        s = component + s

    # Add <Route path="/cms" ...> before the first </Routes>
    if "</Routes>" in s and "path=\"/cms\"" not in s and "path='/cms'" not in s:
        s = s.replace("</Routes>",
                      '        <Route path="/cms" element={<CmsRedirect />} />\n      </Routes>', 1)
        p.write_text(s)
        print("  App.js patched with /cms route")
    else:
        print("  App.js: no </Routes> found (or /cms route already present)")
PYAPP
  else
    echo "  No App.js/.jsx/.tsx found under frontend/src — skipping React route patch"
  fi

  # Gitignore
  if [ -f ".gitignore" ]; then
    grep -qxF "cms-data/" .gitignore || echo "cms-data/" >> .gitignore
  fi

  # Restart backend (supervisor) so the new router is live
  if command -v supervisorctl >/dev/null 2>&1; then
    supervisorctl restart backend >/dev/null 2>&1 || true
    echo "  (backend restarted via supervisorctl)"
  fi

  banner "Monolith CMS installed successfully"
  echo "  Admin UI:  https://<your-domain>/cms      (short URL — redirects to /api/cms/admin)"
  echo "  Or local:  http://localhost:3000/cms"
  echo ""
  echo "  On first visit you'll create your admin password (setup wizard)."
  echo "  Then open any page on the site once — elements auto-appear in the CMS."
  echo ""
}

# ===========================================================================
# NEXT.JS STACK
# ===========================================================================
install_nextjs() {
  log "Step 1/6 · Creating directories…"
  mkdir -p lib/cms pages/api/cms pages/cms public cms-data

  log "Step 2/6 · Downloading CMS backend files…"
  curl -fsSL "${BASE_URL}/lib/storage.js"            -o lib/cms/storage.js
  curl -fsSL "${BASE_URL}/lib/auth.js"               -o lib/cms/auth.js
  curl -fsSL "${BASE_URL}/pages/api/cms/auth.js"     -o pages/api/cms/auth.js
  curl -fsSL "${BASE_URL}/pages/api/cms/setup.js"    -o pages/api/cms/setup.js
  curl -fsSL "${BASE_URL}/pages/api/cms/content.js"  -o pages/api/cms/content.js
  curl -fsSL "${BASE_URL}/pages/api/cms/discover.js" -o pages/api/cms/discover.js
  curl -fsSL "${BASE_URL}/pages/api/cms/register.js" -o pages/api/cms/register.js
  curl -fsSL "${BASE_URL}/pages/api/cms/update.js"   -o pages/api/cms/update.js
  curl -fsSL "${BASE_URL}/pages/api/cms/public.js"   -o pages/api/cms/public.js
  curl -fsSL "${BASE_URL}/public/cms-client.js"      -o public/cms-client.js

  log "Step 3/6 · Downloading CMS editor page…"
  curl -fsSL "${BASE_URL}/pages/cms.js"              -o pages/cms.js

  log "Step 4/6 · Wiring up _document.js…"
  if [ ! -f "pages/_document.js" ]; then
    cat > pages/_document.js <<EOFDOC
import { Html, Head, Main, NextScript } from 'next/document'
export default function Document() {
  return (
    <Html>
      <Head />
      <body>
        <Main />
        <NextScript />
        <script src="${BASE_URL}/public/cms-client.js" defer />
      </body>
    </Html>
  )
}
EOFDOC
  elif ! grep -q "cms-client.js" pages/_document.js; then
    sed -i.bak "s|</body>|        <script src=\"${BASE_URL}/public/cms-client.js\" defer />\n      </body>|" pages/_document.js
    rm -f pages/_document.js.bak
  fi

  log "Step 5/6 · Installing dependencies (bcryptjs, jose)…"
  if [ -f "yarn.lock" ] && command -v yarn >/dev/null 2>&1; then
    yarn add bcryptjs jose --silent 2>/dev/null || yarn add bcryptjs jose
  else
    npm install bcryptjs jose --silent
  fi

  log "Step 6/6 · Preparing environment…"
  [ -f ".env.local" ] || printf "# Monolith CMS — credentials created on first /cms visit\n" > .env.local
  if [ -f ".gitignore" ]; then
    grep -qxF "cms-data/" .gitignore || echo "cms-data/" >> .gitignore
    grep -qxF ".env.local" .gitignore || echo ".env.local" >> .gitignore
  fi

  banner "Monolith CMS installed successfully"
  echo "  Admin UI:  http://localhost:3000/cms"
  echo "  First visit creates your admin password (setup wizard)."
  echo ""
}

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

case "$STACK" in
  emergent) install_emergent ;;
  nextjs)   install_nextjs ;;
  *)
    die "Could not auto-detect stack.
  Expected one of:
    - Emergent: backend/server.py + frontend/package.json
    - Next.js : package.json with \"next\" dependency
  Run this script from your project root and try again."
    ;;
esac
