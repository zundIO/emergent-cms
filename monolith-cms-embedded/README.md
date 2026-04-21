# Monolith CMS - Embedded Edition

Ein **Plug & Play Content Management System** das direkt in deine Emergent-Website eingebettet wird.

## 🎯 Konzept

- **Kein separates Hosting nötig** - CMS läuft auf deiner Website-Domain
- **File-based Storage** - Content wird als JSON gespeichert (kein extra DB)
- **Auto-Discovery** - CMS scannt deine Website automatisch
- **Bi-direktional** - Emergent ↔ CMS ↔ Website

## 🏗️ Architektur

```
https://deine-website.com/
  ├── /                    → Deine Website
  ├── /cms                 → CMS Editor (passwortgeschützt)
  └── /api/cms/*           → CMS Backend API
```

## 📋 Installation für Emergent-Websites

### Voraussetzung
- Next.js Website (Emergent Standard)
- Node.js 18+

### Dateien kopieren

```bash
# 1. CMS Dateien in dein Projekt kopieren
cp -r monolith-cms-embedded/pages/cms pages/
cp -r monolith-cms-embedded/pages/api/cms pages/api/
cp -r monolith-cms-embedded/components/cms components/
cp -r monolith-cms-embedded/lib/cms lib/
cp -r monolith-cms-embedded/cms-data cms-data/

# 2. Dependencies installieren
npm install bcryptjs jose
```

### Struktur nach Installation

```
deine-website/
├── pages/
│   ├── index.js               (Deine Website)
│   ├── cms/
│   │   └── index.js           (CMS Editor UI)
│   └── api/
│       └── cms/
│           ├── auth.js        (Login/Session)
│           ├── content.js     (Content CRUD)
│           ├── discover.js    (Auto-Discovery)
│           └── public.js      (Public Content API)
├── components/
│   └── cms/
│       └── Editor.js          (Editor Komponenten)
├── lib/
│   └── cms/
│       ├── storage.js         (File Storage)
│       └── auth.js            (Auth Helpers)
├── cms-data/
│   ├── content.json           (Dein Content)
│   └── .cms-config.json       (CMS Config)
└── public/
    └── cms-client.js          (Client Script für Website)
```

## 🔐 Erstes Setup

### 1. Admin-Passwort setzen

Erstelle `.env.local`:
```env
CMS_ADMIN_PASSWORD=dein-sicheres-passwort
CMS_SECRET=generiere-einen-random-string
```

### 2. Content initialisieren

```bash
npm run cms:init
```

### 3. CMS öffnen

```
https://deine-website.com/cms
→ Login mit Passwort
→ CMS scannt Website automatisch
```

## 🌐 Website mit CMS verbinden

### Schritt 1: data-cms-id zu Elementen hinzufügen

```jsx
// pages/index.js
export default function Home() {
  return (
    <div>
      <h1 data-cms-id="hero-headline">
        Willkommen auf meiner Website
      </h1>
      
      <p data-cms-id="hero-description">
        Das ist der Standard-Text
      </p>
      
      <img 
        data-cms-id="hero-image"
        src="/default.jpg" 
        alt="Hero"
      />
    </div>
  )
}
```

### Schritt 2: Client Script einbinden

```jsx
// pages/_document.js
import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html>
      <Head />
      <body>
        <Main />
        <NextScript />
        <script src="/cms-client.js" />
      </body>
    </Html>
  )
}
```

**Das war's!** 🎉 Content wird automatisch geladen und angewendet.

## 🔄 Workflow

### 1. Content bearbeiten

```
1. Öffne https://deine-website.com/cms
2. CMS zeigt automatisch alle data-cms-id Elemente
3. Bearbeite Content im Editor
4. Klicke "Save"
→ Content wird in cms-data/content.json gespeichert
```

### 2. Content erscheint auf Website

```
1. Besucher lädt Website
2. cms-client.js lädt Content von /api/cms/public
3. Content wird auf Elemente mit data-cms-id angewendet
4. Fertig!
```

### 3. Emergent ändert Website

```
1. Emergent fügt neue Elemente hinzu (mit data-cms-id)
2. Beim nächsten CMS-Login: Klicke "Sync"
3. CMS scannt Website und findet neue Elemente
4. Neue Elemente sind jetzt im CMS editierbar
```

## 📝 Emergent-Anweisung (Komplett)

**Kopiere diese Anweisung für jede neue Website:**

```
MONOLITH CMS - EMBEDDED INSTALLATION

1. Installiere folgende npm packages:
   - bcryptjs
   - jose

2. Erstelle folgende Dateien:

   pages/cms/index.js:
   [Inhalt aus monolith-cms-embedded/pages/cms/index.js kopieren]

   pages/api/cms/auth.js:
   [Inhalt aus monolith-cms-embedded/pages/api/cms/auth.js kopieren]

   pages/api/cms/content.js:
   [Inhalt aus monolith-cms-embedded/pages/api/cms/content.js kopieren]

   pages/api/cms/discover.js:
   [Inhalt aus monolith-cms-embedded/pages/api/cms/discover.js kopieren]

   pages/api/cms/public.js:
   [Inhalt aus monolith-cms-embedded/pages/api/cms/public.js kopieren]

   lib/cms/storage.js:
   [Inhalt aus monolith-cms-embedded/lib/cms/storage.js kopieren]

   lib/cms/auth.js:
   [Inhalt aus monolith-cms-embedded/lib/cms/auth.js kopieren]

   public/cms-client.js:
   [Inhalt aus monolith-cms-embedded/public/cms-client.js kopieren]

3. Erstelle .env.local:
   CMS_ADMIN_PASSWORD=admin123
   CMS_SECRET=your-random-secret-min-32-chars

4. Erstelle Ordner: cms-data/

5. Füge zu ALLEN editierbaren Elementen data-cms-id hinzu:
   <h1 data-cms-id="unique-id">Text</h1>

6. Füge in pages/_document.js (oder _app.js) ein:
   <script src="/cms-client.js" />

FERTIG! CMS ist unter /cms erreichbar.
```

## 🚀 Deployment

### Vercel / Netlify
```bash
# Funktioniert out-of-the-box!
# cms-data/ wird automatisch mit deployed
# Bei Änderungen: git commit + push
```

### Environment Variables setzen
```
CMS_ADMIN_PASSWORD=dein-passwort
CMS_SECRET=dein-secret
```

## 🔧 API Endpoints

### Public (kein Auth)
```
GET /api/cms/public
→ Gibt published content zurück
```

### Admin (mit Auth)
```
POST /api/cms/auth/login
→ Login

GET /api/cms/content
→ Alle Content-Einträge

PUT /api/cms/content
→ Content speichern

POST /api/cms/discover
→ Website scannen nach neuen data-cms-id Elementen
```

## 📊 Content Format

```json
{
  "elements": {
    "hero-headline": {
      "id": "hero-headline",
      "type": "heading",
      "content": {
        "text": "Willkommen!"
      },
      "published": true,
      "updated_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

## 🎨 Editor Features

- ✅ Auto-Discovery (scannt Website)
- ✅ Visual Content-Liste
- ✅ Text-Editing
- ✅ Image-Upload (base64 oder URL)
- ✅ Link-Editing
- ✅ Publish/Draft Status
- ✅ Einfaches Auth-System
- ✅ File-based Storage

## 🔒 Sicherheit

- Passwort-geschützt (bcrypt)
- JWT-basierte Sessions
- Nur Admin-User
- CORS-safe (gleiche Domain)

## 💾 Storage

**Development/Preview:**
- File-based (cms-data/content.json)
- Git-tracked (versioniert!)

**Production (Optional):**
- Kann auf Vercel KV umgestellt werden
- Oder PostgreSQL/Redis

## 🐛 Troubleshooting

**CMS zeigt keine Elemente:**
- Prüfe: Haben Elemente data-cms-id?
- Klicke "Sync" im CMS

**Content erscheint nicht auf Website:**
- Prüfe: Ist cms-client.js eingebunden?
- Prüfe Browser Console für Fehler
- Prüfe: Ist Content "published"?

**Login funktioniert nicht:**
- Prüfe: Ist CMS_ADMIN_PASSWORD in .env.local?
- Prüfe: Ist CMS_SECRET gesetzt? (min. 32 Zeichen)

## 📚 Weiterführend

### Custom Storage Backend
```javascript
// lib/cms/storage.js anpassen
// Statt File: Vercel KV, Redis, etc.
```

### Multi-User Support
```javascript
// Erweitere auth.js für mehrere User
// Füge Rollen hinzu (admin/editor)
```

### Webhook bei Publish
```javascript
// POST /api/cms/content
// Triggere Rebuild/Deployment
```

---

**Version:** 1.0.0 (Embedded Edition)  
**Lizenz:** MIT  
**Support:** github.com/your-repo/issues
