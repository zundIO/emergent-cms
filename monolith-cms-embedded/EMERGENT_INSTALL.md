# 🚀 Monolith CMS - Emergent Installation Guide

## Komplette Anweisung für Emergent Agent

Kopiere diese **KOMPLETTE Anweisung** an Emergent beim Erstellen einer neuen Website:

---

## MONOLITH CMS - EMBEDDED INSTALLATION

Installiere das Monolith CMS als eingebettetes Content-Management-System in diese Website.

### SCHRITT 1: Dependencies installieren

```bash
npm install bcryptjs jose jsdom
# oder
yarn add bcryptjs jose jsdom
```

### SCHRITT 2: Ordner-Struktur erstellen

Erstelle folgende Ordner:
- `lib/cms/`
- `pages/api/cms/`
- `cms-data/`

### SCHRITT 3: Core-Dateien erstellen

**Datei: `lib/cms/storage.js`**
```javascript
[KOMPLETTER INHALT VON /app/monolith-cms-embedded/lib/storage.js]
```

**Datei: `lib/cms/auth.js`**
```javascript
[KOMPLETTER INHALT VON /app/monolith-cms-embedded/lib/auth.js]
```

### SCHRITT 4: API Routes erstellen

**Datei: `pages/api/cms/auth.js`**
```javascript
[KOMPLETTER INHALT VON /app/monolith-cms-embedded/pages/api/cms/auth.js]
```

**Datei: `pages/api/cms/content.js`**
```javascript
[KOMPLETTER INHALT VON /app/monolith-cms-embedded/pages/api/cms/content.js]
```

**Datei: `pages/api/cms/discover.js`**
```javascript
[KOMPLETTER INHALT VON /app/monolith-cms-embedded/pages/api/cms/discover.js]
```

**Datei: `pages/api/cms/public.js`**
```javascript
[KOMPLETTER INHALT VON /app/monolith-cms-embedded/pages/api/cms/public.js]
```

### SCHRITT 5: Client Script erstellen

**Datei: `public/cms-client.js`**
```javascript
[KOMPLETTER INHALT VON /app/monolith-cms-embedded/public/cms-client.js]
```

### SCHRITT 6: Environment Variables

Erstelle oder erweitere `.env.local`:
```env
CMS_ADMIN_PASSWORD=admin123
CMS_SECRET=monolith-cms-secret-min-32-chars-change-this
```

### SCHRITT 7: CMS Editor UI Page erstellen

**Datei: `pages/cms.js` (oder `pages/cms/index.js`)**
```javascript
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

  // Check authentication
  useEffect(() => {
    fetch('/api/cms/auth')
      .then(r => r.json())
      .then(data => {
        setAuthenticated(data.authenticated);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Load content if authenticated
  useEffect(() => {
    if (authenticated) {
      loadContent();
    }
  }, [authenticated]);

  const loadContent = () => {
    fetch('/api/cms/content')
      .then(r => r.json())
      .then(data => setContent(data))
      .catch(err => alert('Failed to load content'));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/cms/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      
      if (res.ok) {
        setAuthenticated(true);
        setPassword('');
      } else {
        alert('Invalid password');
      }
    } catch (err) {
      alert('Login failed');
    }
  };

  const handleDiscover = async () => {
    const siteUrl = window.location.origin;
    try {
      const res = await fetch('/api/cms/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: siteUrl })
      });
      
      const data = await res.json();
      alert(`Discovered ${data.discovered} elements (${data.new} new)`);
      loadContent();
    } catch (err) {
      alert('Discovery failed');
    }
  };

  const handleSave = async (elementId, newContent) => {
    try {
      await fetch('/api/cms/content', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: elementId,
          content: newContent,
          published: true
        })
      });
      
      loadContent();
      setEditingId(null);
      alert('Saved!');
    } catch (err) {
      alert('Save failed');
    }
  };

  const startEdit = (element) => {
    setEditingId(element.id);
    setEditValue(element.content?.text || '');
  };

  if (loading) {
    return <div style={{ padding: '2rem' }}>Loading...</div>;
  }

  // Login screen
  if (!authenticated) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        backgroundColor: '#0a0a0a'
      }}>
        <div style={{
          backgroundColor: '#1a1a1a',
          padding: '3rem',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '400px',
          border: '1px solid #333'
        }}>
          <h1 style={{ 
            fontSize: '2rem', 
            fontWeight: 'bold', 
            marginBottom: '0.5rem',
            color: '#fff'
          }}>
            Monolith CMS
          </h1>
          <p style={{ 
            color: '#888', 
            marginBottom: '2rem',
            fontSize: '0.875rem'
          }}>
            Embedded Edition
          </p>
          
          <form onSubmit={handleLogin}>
            <input
              type=\"password\"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder=\"Admin Password\"
              style={{
                width: '100%',
                padding: '0.75rem',
                marginBottom: '1rem',
                backgroundColor: '#0a0a0a',
                border: '1px solid #333',
                borderRadius: '6px',
                color: '#fff',
                fontSize: '1rem'
              }}
              required
            />
            
            <button
              type=\"submit\"
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: '#4edea3',
                color: '#000',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 'bold',
                fontSize: '1rem',
                cursor: 'pointer'
              }}
            >
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Editor screen
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#0a0a0a',
      color: '#fff'
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#1a1a1a',
        borderBottom: '1px solid #333',
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            Monolith CMS
          </h1>
          <p style={{ color: '#888', fontSize: '0.875rem' }}>
            {content?.elements ? Object.keys(content.elements).length : 0} Elements
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={handleDiscover}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#333',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            🔍 Sync Website
          </button>
          
          <button
            onClick={() => router.push('/')}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#4edea3',
              color: '#000',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '0.875rem'
            }}
          >
            View Website →
          </button>
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: '2rem' }}>
        {!content?.elements && (
          <div style={{
            textAlign: 'center',
            padding: '3rem',
            backgroundColor: '#1a1a1a',
            borderRadius: '12px',
            border: '1px solid #333'
          }}>
            <p style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>
              No content found
            </p>
            <p style={{ color: '#888', marginBottom: '2rem' }}>
              Click \"Sync Website\" to discover editable elements
            </p>
            <button
              onClick={handleDiscover}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#4edea3',
                color: '#000',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Sync Now
            </button>
          </div>
        )}

        {content?.elements && (
          <div style={{
            display: 'grid',
            gap: '1rem',
            maxWidth: '800px'
          }}>
            {Object.values(content.elements).map(element => (
              <div
                key={element.id}
                style={{
                  backgroundColor: '#1a1a1a',
                  padding: '1.5rem',
                  borderRadius: '8px',
                  border: '1px solid #333'
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'start',
                  marginBottom: '1rem'
                }}>
                  <div>
                    <h3 style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
                      {element.label || element.id}
                    </h3>
                    <p style={{ color: '#888', fontSize: '0.75rem' }}>
                      {element.type} • {element.tag}
                    </p>
                  </div>
                  
                  <span style={{
                    padding: '0.25rem 0.5rem',
                    backgroundColor: element.published ? '#4edea3' : '#666',
                    color: element.published ? '#000' : '#fff',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                  }}>
                    {element.published ? 'PUBLISHED' : 'DRAFT'}
                  </span>
                </div>

                {editingId === element.id ? (
                  <div>
                    <textarea
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        backgroundColor: '#0a0a0a',
                        border: '1px solid #333',
                        borderRadius: '6px',
                        color: '#fff',
                        fontSize: '1rem',
                        minHeight: '100px',
                        fontFamily: 'inherit',
                        marginBottom: '0.5rem'
                      }}
                    />
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => handleSave(element.id, { text: editValue })}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: '#4edea3',
                          color: '#000',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontWeight: 'bold',
                          fontSize: '0.875rem'
                        }}
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: '#333',
                          color: '#fff',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '0.875rem'
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <p style={{ 
                      color: '#ccc', 
                      marginBottom: '0.75rem',
                      fontStyle: !element.content?.text ? 'italic' : 'normal'
                    }}>
                      {element.content?.text || '(empty)'}
                    </p>
                    <button
                      onClick={() => startEdit(element)}
                      style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: '#333',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.875rem'
                      }}
                    >
                      ✏️ Edit
                    </button>
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
```

### SCHRITT 8: Website mit CMS verbinden

**In `pages/_document.js` (oder erstelle diese Datei):**
```javascript
import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang=\"de\">
      <Head />
      <body>
        <Main />
        <NextScript />
        {/* CMS Client Script */}
        <script src=\"/cms-client.js\" />
      </body>
    </Html>
  )
}
```

### SCHRITT 9: data-cms-id zu allen editierbaren Elementen hinzufügen

Füge zu JEDEM Element, das im CMS editierbar sein soll, ein `data-cms-id` Attribut hinzu:

**Beispiel:**
```jsx
<h1 data-cms-id=\"hero-headline\">
  Willkommen auf meiner Website
</h1>

<p data-cms-id=\"hero-description\">
  Das ist die Beschreibung
</p>

<img 
  data-cms-id=\"hero-image\"
  src=\"/hero.jpg\" 
  alt=\"Hero Bild\"
/>

<a 
  data-cms-id=\"cta-button\"
  href=\"/kontakt\"
>
  Kontakt aufnehmen
</a>
```

**Wichtig:** Jede `data-cms-id` muss unique sein!

### SCHRITT 10: .gitignore anpassen

Füge zu `.gitignore` hinzu (optional):
```
# CMS Data (optional - kann auch committed werden)
cms-data/
```

---

## ✅ FERTIG!

Das CMS ist jetzt installiert:

- **CMS Editor:** `https://deine-website.com/cms`
- **Login Passwort:** `admin123` (aus .env.local)
- **Content wird automatisch auf der Website geladen**

### Erste Schritte nach Installation:

1. Öffne `https://deine-website.com/cms`
2. Login mit Passwort aus `.env.local`
3. Klicke \"Sync Website\" - CMS findet alle `data-cms-id` Elemente
4. Bearbeite Content
5. Klicke \"Save\"
6. Besuche deine Website - Content ist aktualisiert!

---

## 🔧 Wichtige Hinweise für Emergent:

- Alle Dateipfade sind relativ zum Projekt-Root
- `pages/` ist Next.js Standard
- Falls kein Next.js: Passe API-Routes entsprechend an
- CMS funktioniert auch in Emergent Preview-URLs
- Nach Deployment auf Vercel/Netlify: Setze Environment Variables

---

**Version:** 1.0.0 (Embedded)  
**Lizenz:** MIT
