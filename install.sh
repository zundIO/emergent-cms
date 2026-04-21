#!/bin/bash
# Monolith CMS - One-Command Installation
# Usage: curl -sSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh | bash

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MONOLITH CMS - Embedded Edition"
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
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in a Next.js project
if [ ! -f "package.json" ]; then
  echo -e "${RED}❌ Error: package.json not found. Are you in a Next.js project?${NC}"
  exit 1
fi

echo -e "${BLUE}📦 Step 1/6: Creating directories...${NC}"
mkdir -p lib/cms
mkdir -p pages/api/cms
mkdir -p pages/cms
mkdir -p public
mkdir -p cms-data

echo -e "${BLUE}📥 Step 2/6: Downloading CMS files...${NC}"

# Download lib files
curl -sf "${BASE_URL}/lib/storage.js" -o lib/cms/storage.js || { echo "Failed to download storage.js"; exit 1; }
curl -sf "${BASE_URL}/lib/auth.js" -o lib/cms/auth.js || { echo "Failed to download auth.js"; exit 1; }

# Download API files
curl -sf "${BASE_URL}/pages/api/cms/auth.js" -o pages/api/cms/auth.js || { echo "Failed to download api/auth.js"; exit 1; }
curl -sf "${BASE_URL}/pages/api/cms/content.js" -o pages/api/cms/content.js || { echo "Failed to download api/content.js"; exit 1; }
curl -sf "${BASE_URL}/pages/api/cms/discover.js" -o pages/api/cms/discover.js || { echo "Failed to download api/discover.js"; exit 1; }
curl -sf "${BASE_URL}/pages/api/cms/public.js" -o pages/api/cms/public.js || { echo "Failed to download api/public.js"; exit 1; }

# Download client script (local copy for fallback)
curl -sf "${BASE_URL}/public/cms-client.js" -o public/cms-client.js || { echo "Failed to download cms-client.js"; exit 1; }

# Also create CDN version that auto-updates
echo "Creating auto-updating client loader..."
cat > public/cms-client-cdn.js << 'EOFCDN'
// Auto-updating CMS client - always loads latest from GitHub
(function() {
  var script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/gh/zundIO/emergent-cms@main/public/cms-client.js';
  script.async = false;
  document.head.appendChild(script);
})();
EOFCDN

echo -e "${BLUE}📝 Step 3/6: Creating CMS Editor page...${NC}"

# Create CMS Editor page
cat > pages/cms.js << 'EOFCMS'
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

export default function CMSEditor() {
  const router = useRouter();
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');

  useEffect(() => {
    fetch('/api/cms/auth')
      .then(r => r.json())
      .then(data => { setAuthenticated(data.authenticated); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => { if (authenticated) loadContent(); }, [authenticated]);

  const loadContent = () => {
    fetch('/api/cms/content').then(r => r.json()).then(setContent).catch(err => alert('Failed to load'));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const res = await fetch('/api/cms/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    if (res.ok) { setAuthenticated(true); setPassword(''); } else alert('Invalid password');
  };

  const handleDiscover = async () => {
    const res = await fetch('/api/cms/discover', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: window.location.origin })
    });
    const data = await res.json();
    alert(`Discovered ${data.discovered} elements (${data.new} new)`);
    loadContent();
  };

  const handleSave = async (elementId, newContent) => {
    await fetch('/api/cms/content', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: elementId, content: newContent, published: true })
    });
    loadContent();
    setEditingId(null);
    alert('Saved!');
  };

  const startEdit = (el) => { setEditingId(el.id); setEditValue(el.content?.text || ''); };

  if (loading) return <div style={{ padding: '2rem' }}>Loading...</div>;

  if (!authenticated) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a0a0a' }}>
        <div style={{ backgroundColor: '#1a1a1a', padding: '3rem', borderRadius: '12px', width: '100%', maxWidth: '400px', border: '1px solid #333' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#fff' }}>Monolith CMS</h1>
          <p style={{ color: '#888', marginBottom: '2rem', fontSize: '0.875rem' }}>Embedded Edition</p>
          <form onSubmit={handleLogin}>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Admin Password"
              style={{ width: '100%', padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#0a0a0a', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '1rem' }} required />
            <button type="submit" style={{ width: '100%', padding: '0.75rem', backgroundColor: '#4edea3', color: '#000', border: 'none', borderRadius: '6px', fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer' }}>Login</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0a', color: '#fff' }}>
      <div style={{ backgroundColor: '#1a1a1a', borderBottom: '1px solid #333', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Monolith CMS</h1>
          <p style={{ color: '#888', fontSize: '0.875rem' }}>{content?.elements ? Object.keys(content.elements).length : 0} Elements</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button onClick={handleDiscover} style={{ padding: '0.5rem 1rem', backgroundColor: '#333', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.875rem' }}>🔍 Sync</button>
          <button onClick={() => router.push('/')} style={{ padding: '0.5rem 1rem', backgroundColor: '#4edea3', color: '#000', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.875rem' }}>View →</button>
        </div>
      </div>
      <div style={{ padding: '2rem' }}>
        {!content?.elements && (
          <div style={{ textAlign: 'center', padding: '3rem', backgroundColor: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
            <p style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>No content</p>
            <p style={{ color: '#888', marginBottom: '2rem' }}>Click "Sync" to discover elements</p>
            <button onClick={handleDiscover} style={{ padding: '0.75rem 1.5rem', backgroundColor: '#4edea3', color: '#000', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Sync Now</button>
          </div>
        )}
        {content?.elements && (
          <div style={{ display: 'grid', gap: '1rem', maxWidth: '800px' }}>
            {Object.values(content.elements).map(el => (
              <div key={el.id} style={{ backgroundColor: '#1a1a1a', padding: '1.5rem', borderRadius: '8px', border: '1px solid #333' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <div>
                    <h3 style={{ fontWeight: 'bold' }}>{el.label || el.id}</h3>
                    <p style={{ color: '#888', fontSize: '0.75rem' }}>{el.type} • {el.tag}</p>
                  </div>
                  <span style={{ padding: '0.25rem 0.5rem', backgroundColor: el.published ? '#4edea3' : '#666', color: el.published ? '#000' : '#fff', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                    {el.published ? 'PUBLISHED' : 'DRAFT'}
                  </span>
                </div>
                {editingId === el.id ? (
                  <div>
                    <textarea value={editValue} onChange={(e) => setEditValue(e.target.value)} style={{ width: '100%', padding: '0.75rem', backgroundColor: '#0a0a0a', border: '1px solid #333', borderRadius: '6px', color: '#fff', minHeight: '100px', marginBottom: '0.5rem' }} />
                    <button onClick={() => handleSave(el.id, { text: editValue })} style={{ padding: '0.5rem 1rem', backgroundColor: '#4edea3', color: '#000', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', marginRight: '0.5rem' }}>Save</button>
                    <button onClick={() => setEditingId(null)} style={{ padding: '0.5rem 1rem', backgroundColor: '#333', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
                  </div>
                ) : (
                  <div>
                    <p style={{ color: '#ccc', marginBottom: '0.75rem', fontStyle: !el.content?.text ? 'italic' : 'normal' }}>{el.content?.text || '(empty)'}</p>
                    <button onClick={() => startEdit(el)} style={{ padding: '0.5rem 1rem', backgroundColor: '#333', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>✏️ Edit</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
EOFCMS

echo -e "${BLUE}📝 Step 4/6: Creating/updating _document.js...${NC}"

# Create or update _document.js
if [ ! -f "pages/_document.js" ]; then
  cat > pages/_document.js << 'EOFDOC'
import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="de">
      <Head />
      <body>
        <Main />
        <NextScript />
        {/* CMS Client - Auto-updating from CDN */}
        <script src="https://cdn.jsdelivr.net/gh/zundIO/emergent-cms@main/public/cms-client.js" />
      </body>
    </Html>
  )
}
EOFDOC
  echo "  ✓ Created pages/_document.js with auto-updating CMS client"
else
  # Check if cms-client.js is already included
  if ! grep -q "cms-client.js" pages/_document.js; then
    echo "  ⚠️  Please add <script src=\"https://cdn.jsdelivr.net/gh/zundIO/emergent-cms@main/public/cms-client.js\" /> to your pages/_document.js"
  else
    echo "  ✓ cms-client.js already included in _document.js"
  fi
fi

echo -e "${BLUE}📦 Step 5/6: Installing dependencies...${NC}"
npm install bcryptjs jose jsdom

echo -e "${BLUE}🔐 Step 6/6: Setting up environment...${NC}"

if [ ! -f ".env.local" ]; then
  cat > .env.local << 'EOFENV'
# Monolith CMS Configuration
# First admin will be created on first /cms visit
# DO NOT commit this file to Git!
EOFENV
  echo "  ✓ Created .env.local (admin setup required on first visit)"
else
  echo "  ✓ .env.local already exists"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ MONOLITH CMS INSTALLED SUCCESSFULLY!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "  1. Add data-cms-id to editable elements:"
echo "     <h1 data-cms-id=\"hero\">Your text</h1>"
echo ""
echo "  2. Start dev server:"
echo "     npm run dev"
echo ""
echo "  3. Open CMS for FIRST-TIME SETUP:"
echo "     http://localhost:3000/cms"
echo ""
echo "  4. Create your first admin user"
echo "     (Email, Name, Password - min 8 characters)"
echo ""
echo "  5. Click 'Sync' to discover all data-cms-id elements"
echo ""
echo -e "${BLUE}🔒 Security:${NC}"
echo "  - Never commit .env.local to Git!"
echo "  - Use a strong password (min 8 characters)"
echo "  - Change password in production"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "  https://github.com/${REPO}"
echo ""
