# 🚀 Monolith CMS - GitHub Setup Guide

## Schritt 1: GitHub Repository erstellen

### 1.1 Neues Repository auf GitHub

```bash
# Auf GitHub.com:
1. Gehe zu: https://github.com/new
2. Repository Name: monolith-cms-embedded
3. Beschreibung: "Plug & Play CMS for Next.js websites"
4. Public ✅
5. Create Repository
```

### 1.2 Lokale Dateien pushen

```bash
# Im Terminal:
cd /app/monolith-cms-embedded

git init
git add .
git commit -m "Initial commit: Monolith CMS Embedded v1.0"

# Ersetze 'zundIO' mit deinem GitHub Username:
git remote add origin https://github.com/zundIO/monolith-cms-embedded.git
git branch -M main
git push -u origin main
```

### 1.3 Verifizierung

Öffne: `https://github.com/zundIO/monolith-cms-embedded`

Du solltest sehen:
```
monolith-cms-embedded/
├── README.md
├── USER_MANUAL.md
├── EMERGENT_PROMPT.txt       ← Wichtig!
├── package.json
├── lib/
├── pages/
└── public/
```

---

## Schritt 2: Raw File URLs generieren

GitHub stellt jede Datei als "Raw" zur Verfügung:

**Format:**
```
https://raw.githubusercontent.com/USERNAME/REPO/main/PFAD/DATEI
```

**Deine URLs:**
```
https://raw.githubusercontent.com/zundIO/monolith-cms-embedded/main/lib/storage.js
https://raw.githubusercontent.com/zundIO/monolith-cms-embedded/main/lib/auth.js
https://raw.githubusercontent.com/zundIO/monolith-cms-embedded/main/pages/api/cms/auth.js
...
```

---

## Schritt 3: Emergent-Anweisung vorbereiten

### Option A: Self-Contained Prompt (Empfohlen für Start)

**Datei:** `EMERGENT_PROMPT.txt` (siehe nächste Sektion)

**Verwendung:**
1. Öffne `EMERGENT_PROMPT.txt`
2. Kopiere KOMPLETTEN Inhalt
3. Füge in Emergent ein
4. Fertig!

### Option B: GitHub Installation (Für fortgeschrittene Nutzung)

**Emergent-Anweisung:**
```
Installiere Monolith CMS von GitHub:

1. Lade Installation-Script:
   curl -o install-cms.sh https://raw.githubusercontent.com/zundIO/monolith-cms-embedded/main/install.sh
   chmod +x install-cms.sh
   ./install-cms.sh

2. Oder manuell:
   - Erstelle Ordner: lib/cms/, pages/api/cms/, public/
   - Lade Dateien von:
     https://github.com/zundIO/monolith-cms-embedded/tree/main
   
3. Installiere Dependencies:
   npm install bcryptjs jose jsdom

4. Erstelle .env.local:
   CMS_ADMIN_PASSWORD=admin123
   CMS_SECRET=dein-random-secret-min-32-chars

5. Füge zu allen editierbaren Elementen hinzu:
   data-cms-id="unique-id"

6. Binde Client-Script ein in pages/_document.js:
   <script src="/cms-client.js" />

Details: https://github.com/zundIO/monolith-cms-embedded
```

---

## Schritt 4: Installation Script erstellen (Optional)

Erstelle `install.sh` in deinem Repository:

```bash
#!/bin/bash
# Monolith CMS - Installation Script

echo "📦 Installing Monolith CMS..."

REPO="zundIO/monolith-cms-embedded"
BASE_URL="https://raw.githubusercontent.com/${REPO}/main"

# Create directories
mkdir -p lib/cms
mkdir -p pages/api/cms
mkdir -p pages/cms
mkdir -p public
mkdir -p cms-data

# Download files
echo "⬇️  Downloading files..."

curl -s "${BASE_URL}/lib/storage.js" -o lib/cms/storage.js
curl -s "${BASE_URL}/lib/auth.js" -o lib/cms/auth.js

curl -s "${BASE_URL}/pages/api/cms/auth.js" -o pages/api/cms/auth.js
curl -s "${BASE_URL}/pages/api/cms/content.js" -o pages/api/cms/content.js
curl -s "${BASE_URL}/pages/api/cms/discover.js" -o pages/api/cms/discover.js
curl -s "${BASE_URL}/pages/api/cms/public.js" -o pages/api/cms/public.js

curl -s "${BASE_URL}/public/cms-client.js" -o public/cms-client.js

# Download CMS Editor UI from GitHub Gist or include inline
echo "Creating CMS Editor page..."
cat > pages/cms.js << 'EOF'
[KOMPLETTER CODE VON pages/cms.js - siehe EMERGENT_PROMPT.txt]
EOF

# Install dependencies
echo "📦 Installing dependencies..."
npm install bcryptjs jose jsdom

# Create .env.local if not exists
if [ ! -f .env.local ]; then
  echo "🔐 Creating .env.local..."
  cat > .env.local << 'EOF'
CMS_ADMIN_PASSWORD=admin123
CMS_SECRET=change-this-to-random-string-min-32-chars
EOF
fi

echo ""
echo "✅ Monolith CMS installed successfully!"
echo ""
echo "Next steps:"
echo "1. Add data-cms-id to editable elements"
echo "2. Include <script src=\"/cms-client.js\"> in pages/_document.js"
echo "3. Access CMS: http://localhost:3000/cms"
echo "4. Login with password from .env.local"
echo ""
echo "Documentation: https://github.com/${REPO}"
```

Push dieses Script auch zu GitHub:
```bash
git add install.sh
git commit -m "Add installation script"
git push
```

---

## Schritt 5: README.md für GitHub optimieren

Stelle sicher, dass dein Repository-README folgendes enthält:

1. **Installation Instructions**
2. **Quick Start**
3. **Emergent Integration** (wie man es mit Emergent nutzt)
4. **Live Demo** (optional)
5. **Screenshots**

---

## Schritt 6: NPM Package veröffentlichen (Optional)

Für professionelle Nutzung:

```bash
# 1. In package.json: Name anpassen
{
  "name": "@zundIO/monolith-cms-embedded",
  "version": "1.0.0",
  ...
}

# 2. NPM Login
npm login

# 3. Publish
npm publish --access public

# 4. Installation für User:
npm install @zundIO/monolith-cms-embedded
```

---

## ✅ Checklist

Vor dem Pushen zu GitHub:

- [ ] Alle sensiblen Daten entfernt (keine Passwörter im Code)
- [ ] README.md ist vollständig
- [ ] EMERGENT_PROMPT.txt ist self-contained
- [ ] LICENSE file hinzugefügt (MIT empfohlen)
- [ ] .gitignore vorhanden
- [ ] Alle Beispiel-URLs enthalten deinen GitHub Username

---

## 📝 Deine URLs (Template)

Ersetze `zundIO` mit deinem GitHub Username:

```
Repository: https://github.com/zundIO/monolith-cms-embedded
Clone: git clone https://github.com/zundIO/monolith-cms-embedded.git
Install: curl -sSL https://raw.githubusercontent.com/zundIO/monolith-cms-embedded/main/install.sh | bash
```

---

## 🔄 Updates verteilen

Wenn du das CMS updatest:

```bash
# 1. Änderungen machen
# 2. Commit + Push
git add .
git commit -m "Update: ..."
git push

# 3. User können updaten:
cd monolith-cms-embedded
git pull origin main
# Oder: install.sh erneut ausführen
```

---

**Nächster Schritt:** Erstelle die Self-Contained Emergent-Anweisung → Siehe `EMERGENT_PROMPT.txt`
