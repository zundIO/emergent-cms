# 🔒 SICHERHEITS-CHECKLIST - Vor GitHub Push

## ✅ Was ist SICHER (kein Problem):

- ✅ Quellcode (lib/, pages/api/cms/)
- ✅ Client-Script (public/cms-client.js)  
- ✅ Install-Script (install.sh)
- ✅ Dokumentation (README.md, etc.)
- ✅ .gitignore Datei

## ❌ Was ist NICHT im Repo (durch .gitignore):

- ❌ `.env.local` - Environment Variables
- ❌ `.env` - Environment Variables
- ❌ `cms-data/` - User-Content & Admin-Daten
- ❌ `node_modules/` - Dependencies
- ❌ `.next/` - Build-Output

## 🔐 Neues Sicherheits-Feature:

### **First-Time Setup Flow**

**Alt (UNSICHER):**
```env
# Hardcoded in install.sh:
CMS_ADMIN_PASSWORD=admin123  ❌
```

**Neu (SICHER):**
```
1. Installation: Kein Default-Passwort!
2. Erster Besuch von /cms → Setup-Wizard
3. Admin erstellt eigenen Account:
   - Email
   - Name  
   - Passwort (min. 8 Zeichen)
4. Passwort wird gehasht (bcrypt)
5. In .env.local gespeichert (NICHT im Git!)
```

## 📋 Setup-Flow Details:

### API-Endpoint: `/api/cms/setup.js`

**Features:**
- ✅ Nur beim ersten Start verfügbar
- ✅ Erstellt `.setup-complete` Lock-File
- ✅ Generiert random CMS_SECRET
- ✅ Hasht Passwort mit bcrypt
- ✅ Speichert in .env.local (local only!)
- ✅ Automatischer Login nach Setup

**Security:**
- ✅ Setup kann nur 1x ausgeführt werden
- ✅ Lock-File verhindert erneutes Setup
- ✅ Passwort-Minimum: 8 Zeichen
- ✅ Bcrypt-Hashing (10 rounds)
- ✅ Random Secret (32 chars)

### CMS Editor UI Update:

**Neuer Flow in pages/cms.js:**
```
1. Check: Setup benötigt?
   GET /api/cms/setup → { setupRequired: true/false }

2. Wenn setupRequired = true:
   → Zeige Setup-Formular
   
3. User gibt ein:
   - Email
   - Name
   - Passwort
   
4. POST /api/cms/setup
   → Erstellt Admin
   → Automatischer Login
   
5. Setup-Complete!
   → Normaler CMS Editor
```

## 🔍 Pre-Push Checklist:

Prüfe ALLE diese Punkte bevor du pushst:

- [ ] **.gitignore** vorhanden
- [ ] **Keine .env Dateien** im Repo
- [ ] **Keine cms-data/** im Repo  
- [ ] **Keine Passwörter** im Code
- [ ] **Keine hardcoded Secrets**
- [ ] **Keine persönlichen Daten**
- [ ] **Keine API-Keys**
- [ ] **Keine Test-User** im Code

## 🧪 Test:

```bash
# Prüfe was gepusht wird:
cd /app/monolith-cms-embedded
git status

# Prüfe ob sensitive Dateien tracked sind:
git ls-files | grep -E '\.env|cms-data'
# → Sollte NICHTS zeigen!

# Suche nach Passwörtern im Code:
grep -r "admin123" --exclude-dir=.git --exclude="*.md"
# → Sollte NUR in Dokumentation sein!

grep -r "password.*=" --include="*.js" --include="*.sh"  
# → Prüfe Output manuell
```

## ✅ Was Emergent macht (nach Installation):

```
1. install.sh läuft
2. Erstellt leere .env.local (local only!)
3. npm run dev
4. User öffnet /cms
5. Setup-Wizard erscheint:
   ┌─────────────────────────────┐
   │  Monolith CMS Setup         │
   │  ───────────────────────    │
   │  Erstelle deinen Admin:     │
   │                             │
   │  Email: [____________]      │
   │  Name:  [____________]      │
   │  Pass:  [____________]      │
   │                             │
   │  [Setup Complete]           │
   └─────────────────────────────┘
6. Setup Complete → CMS Ready!
```

## 🔐 Nach Setup:

**/.env.local (local, nicht in Git):**
```env
# Monolith CMS Configuration
CMS_ADMIN_EMAIL=user@example.com
CMS_ADMIN_PASSWORD=$2b$10$... (bcrypt hash)
CMS_ADMIN_NAME=User Name
CMS_SECRET=abc123xyz789... (32 chars random)
```

**/cms-data/.setup-complete (local, nicht in Git):**
```json
{
  "completedAt": "2024-01-15T10:30:00Z",
  "adminEmail": "user@example.com",
  "adminName": "User Name"
}
```

**Beide Dateien sind durch .gitignore geschützt!** ✅

## 📊 Sicherheits-Vergleich:

| Feature | Alt | Neu |
|---------|-----|-----|
| **Default-Passwort** | ❌ admin123 | ✅ Kein Default |
| **Passwort im Code** | ❌ Ja | ✅ Nein |
| **Passwort-Hashing** | ⚠️ Optional | ✅ Immer |
| **Setup-Flow** | ❌ Manuell | ✅ Wizard |
| **Min. Passwort-Länge** | ❌ Keine | ✅ 8 Zeichen |
| **Random Secret** | ⚠️ Fixed | ✅ Generated |

## 🎯 Fazit:

**✅ SICHER ZUM PUSHEN!**

- Kein Passwort im Repo
- Kein User-Daten im Repo
- Setup-Flow für jeden User individuell
- .gitignore schützt sensitive Files

**Nächster Schritt:**
1. Pushe zu GitHub
2. Mach Repo public
3. Teste Installation auf neuer Website
4. Setup-Wizard sollte erscheinen!

---

**WICHTIG:** Nach dem Push auf GitHub, prüfe nochmal das Repo online:
https://github.com/zundIO/emergent-cms

→ Gehe durch alle Dateien
→ Stelle sicher: Keine .env, keine cms-data/
→ ✅ Alles sauber!
