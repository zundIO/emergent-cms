# 🚀 QUICK START GUIDE - Monolith CMS Embedded

## Für DICH (Setup einmalig)

### 1. Push zu GitHub
```bash
cd /app/monolith-cms-embedded
git init
git add .
git commit -m "Monolith CMS v1.0"

# Ersetze 'zundIO' mit deinem GitHub Username:
git remote add origin https://github.com/zundIO/monolith-cms-embedded.git
git push -u origin main
```

### 2. Emergent-Anweisung vorbereiten

Öffne und bearbeite: `EMERGENT_PROMPT_GITHUB.txt`

**Ersetze überall:**
- `[DEIN-USERNAME]` → Dein GitHub Username

**Speichere als:** `EMERGENT_PROMPT_READY.txt`

---

## Für JEDE neue Website

### Option A: Kopiere & Einfügen (Einfachst)

```
1. Öffne: EMERGENT_PROMPT_READY.txt
2. Kopiere KOMPLETTEN Inhalt (Strg+A, Strg+C)
3. Füge in Emergent ein
4. Emergent erstellt Website + CMS automatisch!
```

### Option B: GitHub Link (Kürzer)

```
Gib Emergent:

"Installiere Monolith CMS von GitHub:
https://github.com/zundIO/monolith-cms-embedded

Befolge die Anleitung in EMERGENT_PROMPT_GITHUB.txt"
```

---

## Nach Installation (auf jeder Website)

### 1. CMS öffnen
```
https://deine-website.preview.emergentagent.com/cms
```

### 2. Login
```
Passwort: admin123
(Aus .env.local: CMS_ADMIN_PASSWORD)
```

### 3. Website synchen
```
Klick: "Sync Website"
→ CMS findet alle data-cms-id Elemente automatisch
```

### 4. Content bearbeiten
```
1. Wähle Element
2. Klick "Edit"
3. Ändere Text
4. Klick "Save"
5. Refresh Website → Änderung sichtbar!
```

---

## Typischer Workflow

```
Emergent baut Website
  ↓
Emergent installiert CMS (via Anweisung)
  ↓
Du öffnest /cms
  ↓
"Sync Website" → Elemente gefunden
  ↓
Content bearbeiten
  ↓
Save → Veröffentlicht!
```

---

## Wichtige Links

### Deine GitHub URLs (Template)
```
Repository: 
https://github.com/zundIO/monolith-cms-embedded

Raw Files:
https://raw.githubusercontent.com/zundIO/monolith-cms-embedded/main/lib/storage.js
https://raw.githubusercontent.com/zundIO/monolith-cms-embedded/main/lib/auth.js
... (usw.)
```

### Dokumentation
```
README.md              → Technische Übersicht
USER_MANUAL.md         → Dein Benutzerhandbuch
GITHUB_SETUP.md        → GitHub Setup Anleitung
EMERGENT_PROMPT_GITHUB.txt → Fertige Emergent-Anweisung
```

---

## Troubleshooting

### CMS zeigt keine Elemente
```
→ Haben Elemente data-cms-id?
→ Klick "Sync Website"
```

### Content erscheint nicht auf Website
```
→ Ist <script src="/cms-client.js" /> eingebunden?
→ Prüfe Browser Console
→ Ist Content "published"?
```

### Login funktioniert nicht
```
→ Prüfe .env.local: CMS_ADMIN_PASSWORD gesetzt?
→ Prüfe .env.local: CMS_SECRET gesetzt?
→ Restart: npm run dev
```

---

## Updates verteilen

Wenn du CMS updatest:

```bash
# Änderungen pushen
git add .
git commit -m "Update: ..."
git push

# User bekommen automatisch Updates beim nächsten Install
```

---

## Cheat Sheet

### Element Types
```html
<h1 data-cms-id="hero">Heading</h1>
<p data-cms-id="desc">Paragraph</p>
<img data-cms-id="img" src="..." />
<a data-cms-id="btn" href="#">Link</a>
```

### API Endpoints
```
GET  /api/cms/public        → Published content (kein Auth)
POST /api/cms/auth          → Login
GET  /api/cms/content       → Alle content (Auth)
PUT  /api/cms/content       → Save content (Auth)
POST /api/cms/discover      → Scan website (Auth)
```

### File Structure
```
Website/
├── lib/cms/              → Storage & Auth
├── pages/
│   ├── cms.js            → Editor UI
│   └── api/cms/          → Backend
├── public/
│   └── cms-client.js     → Client Script
├── cms-data/
│   └── content.json      → Content Storage
└── .env.local            → Passwort
```

---

## Deployment

### Vercel
```
1. Push zu GitHub
2. Import in Vercel
3. Setze Environment Variables:
   - CMS_ADMIN_PASSWORD
   - CMS_SECRET
4. Deploy!
```

### Nach Deploy
```
Website: https://deine-domain.com/
CMS:     https://deine-domain.com/cms
```

---

**Du bist ready! 🚀**

Für jede neue Website:
→ Emergent-Anweisung kopieren
→ Einfügen
→ Fertig!
