#!/usr/bin/env bash
# ============================================================
# The Monolith CMS - One-Line Installer
#
# Usage (from inside your Emergent website's /app directory):
#   curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh | bash
#
# Or specify a version / branch:
#   curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh | CMS_REF=v1.0.0 bash
#
# This script:
#   1. Downloads the CMS package into /app/cms/
#   2. Appends required env vars to /app/backend/.env
#   3. Patches /app/backend/server.py to mount the CMS
#   4. Prints the admin credentials
# ============================================================
set -euo pipefail

# ---------- Configuration (override via env vars) ----------
TARGET_DIR="${TARGET_DIR:-/app}"
CMS_REPO="${CMS_REPO:-https://github.com/zundIO/emergent-cms.git}"
CMS_REF="${CMS_REF:-main}"
CMS_ADMIN_EMAIL="${CMS_ADMIN_EMAIL:-admin@$(hostname -s 2>/dev/null || echo cms).local}"
CMS_ADMIN_PASSWORD="${CMS_ADMIN_PASSWORD:-}"
CMS_API_PREFIX="${CMS_API_PREFIX:-/api/cms}"
CMS_STATIC_PATH="${CMS_STATIC_PATH:-/api/cms-admin}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${GREEN}[CMS]${NC} $*"; }
warn() { echo -e "${YELLOW}[CMS]${NC} $*"; }
fail() { echo -e "${RED}[CMS]${NC} $*" >&2; exit 1; }

# ---------- Pre-flight checks ----------
log "The Monolith CMS installer starting…"

[[ -d "$TARGET_DIR/backend" ]] || fail "No /app/backend directory found. Run this inside an Emergent website."
[[ -f "$TARGET_DIR/backend/server.py" ]] || fail "/app/backend/server.py not found."
[[ -f "$TARGET_DIR/backend/.env" ]] || fail "/app/backend/.env not found."

# ---------- Mode detection (--upgrade vs --force vs fresh) ----------
MODE="fresh"
for arg in "$@"; do
  case "$arg" in
    --upgrade) MODE="upgrade" ;;
    --force)   MODE="force"   ;;
  esac
done

if [[ -d "$TARGET_DIR/cms" ]]; then
  case "$MODE" in
    upgrade)
      log "Upgrade mode — keeping .env, MongoDB data and admin user. Replacing CMS code…"
      rm -rf "$TARGET_DIR/cms"
      ;;
    force)
      warn "Force mode — overwriting $TARGET_DIR/cms (data in MongoDB is preserved)."
      rm -rf "$TARGET_DIR/cms"
      ;;
    *)
      warn "$TARGET_DIR/cms already exists."
      warn "  Run with --upgrade to update the CMS to the latest version (recommended)"
      warn "  Run with --force   to fully overwrite the CMS code"
      fail "Aborting. Nothing changed."
      ;;
  esac
fi

# ---------- Generate admin password if not provided ----------
if [[ -z "$CMS_ADMIN_PASSWORD" ]]; then
  CMS_ADMIN_PASSWORD="$(openssl rand -base64 12 | tr -d '/+=' | head -c 16)"
fi

# ---------- Download CMS package ----------
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

log "Downloading CMS package from $CMS_REPO (ref: $CMS_REF)…"
git clone --depth 1 --branch "$CMS_REF" "$CMS_REPO" "$TMP/repo" >/dev/null 2>&1 \
  || fail "git clone failed. Is the repo public?"

[[ -d "$TMP/repo/cms" ]] || fail "Repo structure is unexpected: cms/ directory missing."

log "Copying CMS package to $TARGET_DIR/cms…"
cp -r "$TMP/repo/cms" "$TARGET_DIR/cms"

# Write VERSION file with the installed commit SHA so the CMS can later
# detect when a newer version is available on GitHub.
INSTALLED_SHA=$(cd "$TMP/repo" && git rev-parse HEAD 2>/dev/null || echo "unknown")
INSTALLED_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat > "$TARGET_DIR/cms/VERSION" <<EOF
{
  "commit": "$INSTALLED_SHA",
  "ref": "$CMS_REF",
  "repo": "$CMS_REPO",
  "installed_at": "$INSTALLED_DATE"
}
EOF
log "Installed version: ${INSTALLED_SHA:0:8} (ref: $CMS_REF)"

# ---------- Python dependencies ----------
log "Installing Python dependencies…"
REQ_FILE="$TARGET_DIR/backend/requirements.txt"
PYTHON_BIN=$(command -v python3 || command -v python)
[[ -n "$PYTHON_BIN" ]] || fail "python3 not found."

# These should already exist in an Emergent stack but install defensively
$PYTHON_BIN -m pip install --quiet --no-warn-script-location \
  pymongo bcrypt pyjwt python-dotenv fastapi pydantic 2>&1 | tail -5 || true

# ---------- Patch /app/backend/.env ----------
log "Writing CMS env vars to /app/backend/.env…"
ENV_FILE="$TARGET_DIR/backend/.env"

# Ensure the file ends with a newline before appending (otherwise the
# new variable gets glued to the end of the previous line and breaks
# python-dotenv parsing — issue reported by Emergent agent).
if [[ -s "$ENV_FILE" ]] && [[ -n "$(tail -c 1 "$ENV_FILE")" ]]; then
  printf '\n' >> "$ENV_FILE"
fi

# Append vars only if not already set (idempotent)
grep -q "^CMS_ADMIN_EMAIL=" "$ENV_FILE"   || printf 'CMS_ADMIN_EMAIL="%s"\n' "$CMS_ADMIN_EMAIL"             >> "$ENV_FILE"
grep -q "^CMS_ADMIN_PASSWORD=" "$ENV_FILE"|| printf 'CMS_ADMIN_PASSWORD="%s"\n' "$CMS_ADMIN_PASSWORD"       >> "$ENV_FILE"
grep -q "^JWT_SECRET=" "$ENV_FILE"        || printf 'JWT_SECRET="%s"\n' "$(openssl rand -hex 32)"          >> "$ENV_FILE"
grep -q "^CMS_API_PREFIX=" "$ENV_FILE"    || printf 'CMS_API_PREFIX="%s"\n' "$CMS_API_PREFIX"              >> "$ENV_FILE"
grep -q "^CMS_STATIC_PATH=" "$ENV_FILE"   || printf 'CMS_STATIC_PATH="%s"\n' "$CMS_STATIC_PATH"            >> "$ENV_FILE"

# ---------- Patch server.py (idempotent) ----------
SERVER="$TARGET_DIR/backend/server.py"
if grep -q "from cms import install_cms" "$SERVER"; then
  log "server.py already patched — skipping."
else
  log "Patching $SERVER with CMS mount…"
  # Backup
  cp "$SERVER" "$SERVER.pre-cms.bak"

  # Append the CMS installation at the end of server.py
  cat >> "$SERVER" <<'PYEOF'


# ============================================================
# Monolith CMS — auto-added by installer
# ============================================================
import os as _cms_os
import sys as _cms_sys
_cms_sys.path.insert(0, _cms_os.path.dirname(_cms_os.path.dirname(_cms_os.path.abspath(__file__))))
try:
    from cms import install_cms as _cms_install
    _cms_static_dir = _cms_os.path.join(
        _cms_os.path.dirname(_cms_os.path.dirname(_cms_os.path.abspath(__file__))),
        "cms", "static"
    )
    _cms_install(
        app,
        mongo_url=_cms_os.environ.get("MONGO_URL"),
        db_name=_cms_os.environ.get("DB_NAME", "monolith_cms"),
        collection_prefix="cms_",
        api_prefix=_cms_os.environ.get("CMS_API_PREFIX", "/api/cms"),
        static_path=_cms_os.environ.get("CMS_STATIC_PATH", "/api/cms-admin"),
        static_dir=_cms_static_dir if _cms_os.path.isdir(_cms_static_dir) else None,
        jwt_secret=_cms_os.environ.get("JWT_SECRET", "change-me"),
        admin_email=_cms_os.environ.get("CMS_ADMIN_EMAIL", "admin@monolith.cms"),
        admin_password=_cms_os.environ.get("CMS_ADMIN_PASSWORD", "admin123"),
        seed_demo_content=False,
        add_cors=False,
    )
except Exception as _cms_e:
    import traceback as _cms_tb
    print("[CMS] Failed to mount:", _cms_e)
    _cms_tb.print_exc()
PYEOF
fi

# ---------- Restart backend ----------
if command -v supervisorctl >/dev/null 2>&1; then
  log "Restarting backend via supervisor…"
  sudo supervisorctl restart backend >/dev/null 2>&1 || supervisorctl restart backend >/dev/null 2>&1 || warn "Could not restart backend — please restart manually."
else
  warn "supervisorctl not found — please restart your backend manually."
fi

# ---------- Final output ----------
echo
echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║        The Monolith CMS installed successfully            ║${NC}"
echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "  Admin UI:    ${BOLD}<your-site>${CMS_STATIC_PATH}/${NC}"
echo -e "  API base:    ${BOLD}<your-site>${CMS_API_PREFIX}${NC}"
echo
echo -e "  ${BOLD}Admin login:${NC}"
echo -e "    email:     ${BOLD}$CMS_ADMIN_EMAIL${NC}"
echo -e "    password:  ${BOLD}$CMS_ADMIN_PASSWORD${NC}"
echo
echo -e "  Credentials stored in ${BOLD}/app/backend/.env${NC}"
echo -e "  ${YELLOW}→ Write the password down or change it after first login.${NC}"
echo
echo -e "  Next: after logging in, click the rocket icon in the sidebar"
echo -e "  to see the ${BOLD}Integration Guide${NC} for connecting this website to the CMS."
echo
