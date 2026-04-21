#!/bin/bash
# Monolith CMS - Zero-Config One-Command Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh | bash

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MONOLITH CMS - Embedded Edition (Zero-Config)"
echo "  Installing..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration
REPO="zundIO/emergent-cms"
BRANCH="main"
BASE_URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in a Next.js project
if [ ! -f "package.json" ]; then
  echo -e "${RED}Error: package.json not found. Run this inside a Next.js project root.${NC}"
  exit 1
fi

echo -e "${BLUE}Step 1/6: Creating directories...${NC}"
mkdir -p lib/cms pages/api/cms pages/cms public cms-data

echo -e "${BLUE}Step 2/6: Downloading CMS backend files...${NC}"
curl -sf "${BASE_URL}/lib/storage.js"              -o lib/cms/storage.js
curl -sf "${BASE_URL}/lib/auth.js"                 -o lib/cms/auth.js
curl -sf "${BASE_URL}/pages/api/cms/auth.js"       -o pages/api/cms/auth.js
curl -sf "${BASE_URL}/pages/api/cms/setup.js"      -o pages/api/cms/setup.js
curl -sf "${BASE_URL}/pages/api/cms/content.js"    -o pages/api/cms/content.js
curl -sf "${BASE_URL}/pages/api/cms/discover.js"   -o pages/api/cms/discover.js
curl -sf "${BASE_URL}/pages/api/cms/register.js"   -o pages/api/cms/register.js
curl -sf "${BASE_URL}/pages/api/cms/update.js"     -o pages/api/cms/update.js
curl -sf "${BASE_URL}/pages/api/cms/public.js"     -o pages/api/cms/public.js
curl -sf "${BASE_URL}/public/cms-client.js"        -o public/cms-client.js

echo -e "${BLUE}Step 3/6: Creating CMS Editor page...${NC}"
cat > pages/cms.js << 'EOFCMS'
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

export default function CMSEditor() {
  const router = useRouter();
  const [authenticated, setAuthenticated] = useState(false);
  const [setupRequired, setSetupRequired] = useState(false);
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState({});
  const [filter, setFilter] = useState('all');
  const [updateInfo, setUpdateInfo] = useState(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    // Check setup status first, then auth
    fetch('/api/cms/setup')
      .then((r) => r.json())
      .then((s) => {
        if (s.setupRequired) { setSetupRequired(true); setLoading(false); return; }
        return fetch('/api/cms/auth')
          .then((r) => r.json())
          .then((d) => { setAuthenticated(!!d.authenticated); setLoading(false); });
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => { if (authenticated) { loadContent(); checkUpdate(); } }, [authenticated]);

  const loadContent = () => {
    fetch('/api/cms/content').then((r) => r.json()).then(setContent).catch(() => {});
  };

  const checkUpdate = () => {
    fetch('/api/cms/update').then((r) => r.json()).then(setUpdateInfo).catch(() => {});
  };

  const runUpdate = async () => {
    if (!confirm('Pull the latest CMS version from GitHub?\\nYour content (cms-data/) is untouched.')) return;
    setUpdating(true);
    try {
      const res = await fetch('/api/cms/update', { method: 'POST' });
      const data = await res.json();
      alert('Updated ' + data.updated + '/' + data.total + ' files.\\nRestart the dev server or redeploy to activate.');
      checkUpdate();
    } catch (e) {
      alert('Update failed: ' + e.message);
    } finally {
      setUpdating(false);
    }
  };

  const handleSetup = async (e) => {
    e.preventDefault();
    if (password.length < 8) return alert('Password must be at least 8 characters');
    if (password !== password2) return alert('Passwords do not match');
    const res = await fetch('/api/cms/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    if (!res.ok) return alert('Setup failed');
    // Auto-login with the new password
    const loginRes = await fetch('/api/cms/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    if (loginRes.ok) {
      setSetupRequired(false);
      setAuthenticated(true);
      setPassword(''); setPassword2('');
    } else {
      alert('Setup saved. Please reload and log in.');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const res = await fetch('/api/cms/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    if (res.ok) { setAuthenticated(true); setPassword(''); }
    else alert('Invalid password');
  };

  const handleSave = async (id, newContent) => {
    await fetch('/api/cms/content', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, content: newContent, published: true })
    });
    setEditingId(null);
    loadContent();
  };

  const togglePublish = async (el) => {
    await fetch('/api/cms/content', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: el.id, published: !el.published })
    });
    loadContent();
  };

  const startEdit = (el) => {
    setEditingId(el.id);
    setEditValue({ ...el.content });
  };

  if (loading) {
    return <div style={{ padding: '2rem', color: '#fff', background: '#0a0a0a', minHeight: '100vh' }}>Loading…</div>;
  }

  if (setupRequired) {
    return (
      <div data-cms-ignore style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0a0a0a', fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ background: '#111', padding: '2.5rem', borderRadius: 12, width: '100%', maxWidth: 420, border: '1px solid #222' }}>
          <h1 style={{ color: '#fff', fontSize: '1.5rem', margin: 0, marginBottom: 4 }}>Welcome</h1>
          <p style={{ color: '#888', fontSize: 13, marginTop: 0, marginBottom: 24 }}>Create your admin password to finish setup.</p>
          <form onSubmit={handleSetup}>
            <input autoFocus type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="New password (min 8 chars)"
              style={{ width: '100%', padding: 12, marginBottom: 10, background: '#0a0a0a', border: '1px solid #333', borderRadius: 6, color: '#fff', fontSize: 15, boxSizing: 'border-box' }} />
            <input type="password" value={password2} onChange={(e) => setPassword2(e.target.value)} placeholder="Repeat password"
              style={{ width: '100%', padding: 12, marginBottom: 14, background: '#0a0a0a', border: '1px solid #333', borderRadius: 6, color: '#fff', fontSize: 15, boxSizing: 'border-box' }} />
            <button type="submit" style={{ width: '100%', padding: 12, background: '#4edea3', color: '#000', border: 0, borderRadius: 6, fontWeight: 700, cursor: 'pointer', fontSize: 15 }}>
              Create admin & continue
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return (
      <div data-cms-ignore style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0a0a0a', fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ background: '#111', padding: '2.5rem', borderRadius: 12, width: '100%', maxWidth: 380, border: '1px solid #222' }}>
          <h1 style={{ color: '#fff', fontSize: '1.5rem', margin: 0, marginBottom: 4 }}>Monolith CMS</h1>
          <p style={{ color: '#888', fontSize: 13, marginTop: 0, marginBottom: 24 }}>Embedded Edition</p>
          <form onSubmit={handleLogin}>
            <input autoFocus type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Admin Password"
              style={{ width: '100%', padding: 12, marginBottom: 12, background: '#0a0a0a', border: '1px solid #333', borderRadius: 6, color: '#fff', fontSize: 15, boxSizing: 'border-box' }} />
            <button type="submit" style={{ width: '100%', padding: 12, background: '#4edea3', color: '#000', border: 0, borderRadius: 6, fontWeight: 700, cursor: 'pointer', fontSize: 15 }}>
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  const elements = content?.elements ? Object.values(content.elements) : [];
  const pages = Array.from(new Set(elements.map((e) => e.page || '/'))).sort();
  const filtered = filter === 'all' ? elements : elements.filter((e) => (e.page || '/') === filter);

  return (
    <div data-cms-ignore style={{ minHeight: '100vh', background: '#0a0a0a', color: '#fff', fontFamily: 'system-ui, sans-serif' }}>
      <header style={{ background: '#111', borderBottom: '1px solid #222', padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.1rem' }}>Monolith CMS</h1>
          <p style={{ margin: 0, fontSize: 12, color: '#888' }}>{elements.length} elements auto-discovered</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {updateInfo?.update_available && (
            <button onClick={runUpdate} disabled={updating} style={{ padding: '8px 14px', background: '#ffb84d', color: '#000', border: 0, borderRadius: 6, cursor: updating ? 'wait' : 'pointer', fontWeight: 700, fontSize: 13 }}>
              {updating ? 'Updating…' : 'Update CMS'}
            </button>
          )}
          <button onClick={loadContent} style={{ padding: '8px 14px', background: '#222', color: '#fff', border: 0, borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>Refresh</button>
          <button onClick={() => router.push('/')} style={{ padding: '8px 14px', background: '#4edea3', color: '#000', border: 0, borderRadius: 6, cursor: 'pointer', fontWeight: 700, fontSize: 13 }}>View site →</button>
        </div>
      </header>

      <div style={{ padding: '1.5rem', maxWidth: 900, margin: '0 auto' }}>
        {elements.length === 0 && (
          <div style={{ textAlign: 'center', padding: '3rem', background: '#111', border: '1px solid #222', borderRadius: 12 }}>
            <p style={{ fontSize: '1.1rem', margin: 0, marginBottom: 8 }}>No content yet</p>
            <p style={{ color: '#888', margin: 0, fontSize: 14 }}>Visit any page on your site — the CMS auto-discovers editable elements on load.</p>
          </div>
        )}

        {pages.length > 1 && (
          <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button onClick={() => setFilter('all')} style={{ padding: '6px 12px', background: filter === 'all' ? '#4edea3' : '#222', color: filter === 'all' ? '#000' : '#fff', border: 0, borderRadius: 6, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>
              All ({elements.length})
            </button>
            {pages.map((p) => (
              <button key={p} onClick={() => setFilter(p)} style={{ padding: '6px 12px', background: filter === p ? '#4edea3' : '#222', color: filter === p ? '#000' : '#fff', border: 0, borderRadius: 6, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>
                {p} ({elements.filter((e) => (e.page || '/') === p).length})
              </button>
            ))}
          </div>
        )}

        <div style={{ display: 'grid', gap: 12 }}>
          {filtered.map((el) => (
            <div key={el.id} style={{ background: '#111', border: '1px solid #222', borderRadius: 10, padding: '1rem 1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10, gap: 12 }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>
                    {el.tag} · {el.type} · {el.page || '/'}
                  </div>
                  <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{el.label || el.id}</div>
                </div>
                <button onClick={() => togglePublish(el)} style={{ padding: '4px 10px', background: el.published ? '#4edea3' : '#444', color: el.published ? '#000' : '#fff', border: 0, borderRadius: 4, fontSize: 11, fontWeight: 700, cursor: 'pointer', flexShrink: 0 }}>
                  {el.published ? 'PUBLISHED' : 'DRAFT'}
                </button>
              </div>

              {editingId === el.id ? (
                <div>
                  {el.type === 'image' ? (
                    <>
                      <input value={editValue.src || ''} onChange={(e) => setEditValue({ ...editValue, src: e.target.value })} placeholder="Image URL"
                        style={{ width: '100%', padding: 10, background: '#0a0a0a', border: '1px solid #333', borderRadius: 6, color: '#fff', marginBottom: 8, boxSizing: 'border-box' }} />
                      <input value={editValue.alt || ''} onChange={(e) => setEditValue({ ...editValue, alt: e.target.value })} placeholder="Alt text"
                        style={{ width: '100%', padding: 10, background: '#0a0a0a', border: '1px solid #333', borderRadius: 6, color: '#fff', marginBottom: 8, boxSizing: 'border-box' }} />
                    </>
                  ) : el.type === 'link' ? (
                    <>
                      <input value={editValue.text || ''} onChange={(e) => setEditValue({ ...editValue, text: e.target.value })} placeholder="Link text"
                        style={{ width: '100%', padding: 10, background: '#0a0a0a', border: '1px solid #333', borderRadius: 6, color: '#fff', marginBottom: 8, boxSizing: 'border-box' }} />
                      <input value={editValue.href || ''} onChange={(e) => setEditValue({ ...editValue, href: e.target.value })} placeholder="https://…"
                        style={{ width: '100%', padding: 10, background: '#0a0a0a', border: '1px solid #333', borderRadius: 6, color: '#fff', marginBottom: 8, boxSizing: 'border-box' }} />
                    </>
                  ) : (
                    <textarea value={editValue.text || ''} onChange={(e) => setEditValue({ ...editValue, text: e.target.value })}
                      style={{ width: '100%', minHeight: 90, padding: 10, background: '#0a0a0a', border: '1px solid #333', borderRadius: 6, color: '#fff', marginBottom: 8, fontFamily: 'inherit', boxSizing: 'border-box', resize: 'vertical' }} />
                  )}
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={() => handleSave(el.id, editValue)} style={{ padding: '8px 16px', background: '#4edea3', color: '#000', border: 0, borderRadius: 6, fontWeight: 700, cursor: 'pointer' }}>Save</button>
                    <button onClick={() => setEditingId(null)} style={{ padding: '8px 16px', background: '#333', color: '#fff', border: 0, borderRadius: 6, cursor: 'pointer' }}>Cancel</button>
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ color: '#bbb', fontSize: 14, marginBottom: 10, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {el.type === 'image'
                      ? (el.content?.src || '(no image)')
                      : (el.content?.text || '(empty)')}
                  </div>
                  <button onClick={() => startEdit(el)} style={{ padding: '6px 14px', background: '#222', color: '#fff', border: '1px solid #333', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>Edit</button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
EOFCMS

echo -e "${BLUE}Step 4/6: Wiring up _document.js (auto-injecting CMS client from CDN)...${NC}"
# The client script is loaded directly from GitHub (raw.githubusercontent.com, ~5 min CDN cache)
# so every installed site automatically picks up client-side improvements without reinstall.
CMS_CLIENT_SRC="https://raw.githubusercontent.com/${REPO}/${BRANCH}/public/cms-client.js"

if [ ! -f "pages/_document.js" ]; then
  cat > pages/_document.js << EOFDOC
import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html>
      <Head />
      <body>
        <Main />
        <NextScript />
        {/* Monolith CMS — auto-updating client (served from GitHub via CDN) */}
        <script src="${CMS_CLIENT_SRC}" defer />
      </body>
    </Html>
  )
}
EOFDOC
  echo "  Created pages/_document.js (auto-updating client)"
else
  if ! grep -q "cms-client.js" pages/_document.js; then
    if grep -q "</body>" pages/_document.js; then
      sed -i.bak "s|</body>|        <script src=\"${CMS_CLIENT_SRC}\" defer />\n      </body>|" pages/_document.js
      rm -f pages/_document.js.bak
      echo "  Patched pages/_document.js (added auto-updating client)"
    else
      echo -e "  ${YELLOW}Could not auto-patch _document.js. Add manually:${NC}"
      echo "    <script src=\"${CMS_CLIENT_SRC}\" defer />"
    fi
  else
    echo "  cms-client.js already referenced in _document.js"
  fi
fi

echo -e "${BLUE}Step 5/6: Installing dependencies (bcryptjs, jose)...${NC}"
if command -v yarn >/dev/null 2>&1 && [ -f "yarn.lock" ]; then
  yarn add bcryptjs jose --silent 2>/dev/null || yarn add bcryptjs jose
else
  npm install bcryptjs jose --silent
fi

echo -e "${BLUE}Step 6/6: Preparing environment...${NC}"
if [ ! -f ".env.local" ]; then
  cat > .env.local << 'EOFENV'
# Monolith CMS - admin credentials are created on first /cms visit
# DO NOT commit this file to Git
EOFENV
  echo "  Created .env.local"
fi

# Make sure cms-data is gitignored
if [ -f ".gitignore" ]; then
  grep -qxF "cms-data/" .gitignore || echo "cms-data/" >> .gitignore
  grep -qxF ".env.local" .gitignore || echo ".env.local" >> .gitignore
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  MONOLITH CMS installed successfully${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Open your site and visit /cms"
echo "  -> First visit creates your admin password (setup wizard)"
echo "  -> Then browse any page once — elements auto-appear in the CMS"
echo ""
