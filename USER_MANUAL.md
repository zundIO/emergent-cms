# 📘 Monolith CMS - Embedded Edition - Benutzer-Manual

## 🎯 Was ist das?

Ein **Plug & Play CMS** das direkt in deine Emergent-Website eingebettet wird:
- ✅ Kein separates Hosting nötig
- ✅ Läuft auf der gleichen Domain wie deine Website
- ✅ Content wird automatisch geladen
- ✅ File-based (kein extra DB-Server)

---

## 🚀 Quick Start für neue Websites

### Schritt 1: Gib Emergent diese Anweisung

```
Installiere das Monolith CMS (Embedded Edition) in diese Website.

Folge der kompletten Anleitung in:
https://github.com/dein-repo/monolith-cms-embedded/EMERGENT_INSTALL.md

Wichtig:
- Alle editierbaren Elemente brauchen data-cms-id=\"unique-id\"
- Client-Script in _document.js einbinden
- Environment Variables in .env.local setzen
```

### Schritt 2: Nach der Installation

1. **Öffne das CMS:**
   ```
   https://deine-website.preview.emergentagent.com/cms
   ```

2. **Login:**
   - Passwort: `admin123` (standardmäßig)
   - Aus `.env.local`: `CMS_ADMIN_PASSWORD`

3. **Website scannen:**
   - Klicke "Sync Website"
   - CMS findet automatisch alle `data-cms-id` Elemente

4. **Content bearbeiten:**
   - Wähle Element aus Liste
   - Klicke "Edit"
   - Ändere Text
   - Klicke "Save"

5. **Website ansehen:**
   - Besuche `https://deine-website.com/`
   - Content ist automatisch aktualisiert!

---

## 🔄 Workflow

### Content ändern (Normale Nutzung)

```
1. Öffne /cms
2. Login
3. Bearbeite Element
4. Save
5. Refresh deine Website → Änderung ist sichtbar!
```

### Website mit Emergent ändern

```
1. Emergent fügt neues Element hinzu (mit data-cms-id)
2. Öffne /cms
3. Klicke "Sync Website"
4. Neues Element erscheint in CMS
5. Bearbeite Content
6. Save
```

**Bi-direktional funktioniert automatisch!**

---

## 📁 Wo ist der Content gespeichert?

```
/cms-data/
  └── content.json    ← Hier liegt ALLER Content
```

**Format:**
```json
{
  "elements": {
    "hero-headline": {
      "id": "hero-headline",
      "type": "heading",
      "tag": "h1",
      "content": {
        "text": "Dein geänderter Text"
      },
      "published": true,
      "updated_at": "2024-01-15T10:30:00Z"
    }
  },
  "version": 42,
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

## 🌐 Wie funktioniert die Website-Integration?

### 1. Element wird markiert:
```html
<h1 data-cms-id="hero">Fallback Text</h1>
```

### 2. Client-Script lädt Content:
```javascript
// cms-client.js (automatisch eingebunden)
fetch('/api/cms/public')
  .then(content => {
    // Findet Element mit data-cms-id="hero"
    // Setzt Text aus CMS
  })
```

### 3. Content wird angewendet:
```html
<h1 data-cms-id="hero">Text aus CMS</h1>
```

---

## 🔐 Sicherheit

### Passwort ändern:

**.env.local:**
```env
CMS_ADMIN_PASSWORD=dein-neues-passwort
```

### Produktion:

Für Produktion **unbedingt** sichere Werte setzen:
```env
CMS_ADMIN_PASSWORD=EinSehrSicheresPasswort123!
CMS_SECRET=generiere-einen-random-string-min-32-zeichen
```

---

## 🚢 Deployment

### Vercel / Netlify

**Funktioniert automatisch!**

1. Push zu Git
2. Vercel/Netlify buildet automatisch
3. Setze Environment Variables in Vercel-Dashboard:
   - `CMS_ADMIN_PASSWORD`
   - `CMS_SECRET`

### Nach Deployment:

```
Website: https://deine-domain.com/
CMS:     https://deine-domain.com/cms
```

**Gleiche Domain = Keine CORS-Probleme!**

---

## 📊 Content-Flow Diagram

```
┌─────────────────┐
│  Deine Website  │
│  (Next.js)      │
└────────┬────────┘
         │
         │ <script src="/cms-client.js">
         │
         ▼
┌─────────────────┐
│ GET /api/cms/   │
│ public          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  cms-data/      │
│  content.json   │
└─────────────────┘
         ▲
         │
         │ Save Content
         │
┌─────────────────┐
│  CMS Editor     │
│  /cms           │
└─────────────────┘
```

---

## 🐛 Troubleshooting

### Problem: CMS zeigt keine Elemente

**Lösung:**
1. Prüfe: Haben Elemente `data-cms-id`?
2. Klicke "Sync Website" im CMS
3. Prüfe Browser Console für Fehler

### Problem: Content erscheint nicht auf Website

**Lösung:**
1. Prüfe: Ist `<script src="/cms-client.js">` eingebunden?
2. Öffne Browser Console → Siehst du "[Monolith CMS] ..." Messages?
3. Prüfe: Ist Content "published" im CMS?
4. Teste API direkt: `https://deine-website.com/api/cms/public`

### Problem: Login funktioniert nicht

**Lösung:**
1. Prüfe `.env.local`: Ist `CMS_ADMIN_PASSWORD` gesetzt?
2. Prüfe `.env.local`: Ist `CMS_SECRET` gesetzt? (min. 32 Zeichen)
3. Restart dev server: `npm run dev`

### Problem: 500 Error bei /api/cms/*

**Lösung:**
1. Prüfe: Sind Dependencies installiert? (`npm install bcryptjs jose jsdom`)
2. Prüfe: Existiert `cms-data/` Ordner?
3. Prüfe Server Logs für Details

---

## 🎨 Erweiterte Nutzung

### Custom Element Types

Aktuell unterstützt:
- `heading` (h1-h6)
- `paragraph` (p)
- `image` (img)
- `link` (a)
- `button` (button, a[role=button])

**Neue Types hinzufügen:**
Bearbeite `pages/api/cms/discover.js` und `public/cms-client.js`

### Mehrere Admins

Aktuell: Ein globales Passwort

**Für Multi-User:**
Erweitere `lib/cms/auth.js` und `lib/cms/storage.js`

### Webhook bei Publish

```javascript
// In pages/api/cms/content.js nach Save:
if (element.published) {
  await fetch('https://your-webhook.com', {
    method: 'POST',
    body: JSON.stringify({ event: 'content_published', element })
  })
}
```

---

## 📦 Dateien-Übersicht

```
Projekt-Root/
├── lib/cms/
│   ├── storage.js          ← Content lesen/schreiben
│   └── auth.js             ← Login/Session
├── pages/
│   ├── cms.js              ← CMS Editor UI
│   ├── _document.js        ← Script einbinden
│   └── api/cms/
│       ├── auth.js         ← Login API
│       ├── content.js      ← Content CRUD API
│       ├── discover.js     ← Auto-Discovery API
│       └── public.js       ← Public Content API
├── public/
│   └── cms-client.js       ← Client-Script für Website
├── cms-data/
│   └── content.json        ← Content Storage
└── .env.local              ← Passwort & Secret
```

---

## 💡 Best Practices

### 1. Aussagekräftige IDs
```html
❌ <h1 data-cms-id="h1">Text</h1>
✅ <h1 data-cms-id="hero-headline">Text</h1>
```

### 2. Fallback-Content
```html
<!-- Immer Fallback-Content hinzufügen: -->
<h1 data-cms-id="hero">Fallback Text wenn CMS nicht lädt</h1>
```

### 3. Content committen (Optional)
```bash
# Content versionieren:
git add cms-data/content.json
git commit -m "Update content"

# Vorteil: Content-History in Git
```

### 4. Cache leeren
```javascript
// Im Browser Console:
MonolithCMS.clearCache()
MonolithCMS.refresh()
```

---

## 🔗 Links

- **GitHub Repository:** (Dein Repo-Link)
- **Issues/Support:** (Dein Issues-Link)
- **Dokumentation:** `/monolith-cms-embedded/README.md`
- **Emergent-Anleitung:** `/monolith-cms-embedded/EMERGENT_INSTALL.md`

---

## ✅ Zusammenfassung

**Was du brauchst:**
1. Emergent-Anweisung aus `EMERGENT_INSTALL.md`
2. Alle Elemente mit `data-cms-id` markieren
3. Login-Passwort in `.env.local`

**Was automatisch funktioniert:**
- ✅ Content wird auf Website geladen
- ✅ Cache für Performance
- ✅ Bi-direktionale Synchronisation
- ✅ Kein separates Hosting

**Zugriff:**
- Editor: `https://deine-website.com/cms`
- API: `https://deine-website.com/api/cms/public`

---

**Version:** 1.0.0 (Embedded Edition)  
**Erstellt:** 2024  
**Lizenz:** MIT
