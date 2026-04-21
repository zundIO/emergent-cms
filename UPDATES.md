# 🔄 CMS Updates - So funktioniert's

## ✅ Auto-Updates (Empfohlen)

### Was wird automatisch geupdated?

**Client-Script (cms-client.js):**
- ✅ **Automatisch!** Lädt immer neueste Version von GitHub
- ✅ Kein manueller Update nötig
- ✅ Alle Websites bekommen Updates sofort

**Wie?**
```html
<!-- In _document.js: -->
<script src="https://cdn.jsdelivr.net/gh/zundIO/emergent-cms@main/public/cms-client.js" />
```

→ CDN (jsDelivr) cached nur für kurze Zeit  
→ Neue Version auf GitHub = Auto-Update auf allen Websites!

---

## 📦 Manuelle Updates (Backend-Files)

### Was muss manuell geupdatet werden?

**Backend-Dateien:**
- lib/cms/storage.js
- lib/cms/auth.js  
- pages/api/cms/*.js
- pages/cms.js (Editor UI)

### Update-Prozess:

**Option A: Re-Install (Einfachst)**
```bash
# In Website-Ordner ausführen:
bash -c "$(curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh)"
```

→ Überschreibt alle CMS-Dateien  
→ Content (cms-data/) bleibt erhalten!  
→ .env.local bleibt erhalten!

**Option B: Selective Update**
```bash
# Nur einzelne Dateien updaten:
curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/lib/storage.js -o lib/cms/storage.js
curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/pages/cms.js -o pages/cms.js
```

---

## 🚀 Workflow: CMS verbessern & verteilen

### 1. Du machst Änderungen am CMS

```bash
cd /app/monolith-cms-embedded

# Datei bearbeiten (z.B. neue Feature in pages/cms.js)
# ...

git add .
git commit -m "Feature: XYZ hinzugefügt"
git push
```

### 2. Was passiert automatisch?

**Client-Script (cms-client.js):**
- ✅ Nach ~1-5 Minuten: CDN Cache läuft ab
- ✅ Alle Websites laden neue Version automatisch
- ✅ **Nichts tun nötig!**

**Backend-Files:**
- ⚠️ Müssen manuell geupdated werden (siehe oben)
- ODER: Du informierst User über Update

### 3. Breaking Changes vermeiden

**Best Practice:**
- Client-Script: Abwärtskompatibel halten
- Backend: Versionierung nutzen

**Beispiel:**
```javascript
// In cms-client.js:
var API_VERSION = '1.0';

// Neues Feature nur wenn API unterstützt:
if (API_VERSION >= '1.0') {
  // Neue Funktion
}
```

---

## 📊 Update-Strategie

### Für NEUE Websites:
```
Immer neueste Version via install.sh
→ Bekommen automatisch alle Features
```

### Für BESTEHENDE Websites:

**Client-Script:**
```
✅ Auto-Update via CDN
→ Keine Aktion nötig
```

**Backend (bei Breaking Changes):**
```
1. Release Notes erstellen
2. User informieren  
3. User führt Re-Install aus
```

**Backend (bei kleinen Fixes):**
```
Optional - User entscheidet selbst
```

---

## 🔔 Update-Benachrichtigung (Optional)

**Im CMS Editor anzeigen:**

```javascript
// In pages/cms.js:
useEffect(() => {
  fetch('https://api.github.com/repos/zundIO/emergent-cms/commits/main')
    .then(r => r.json())
    .then(data => {
      const latestCommit = data.sha.substring(0, 7);
      const currentVersion = 'abc1234'; // Lokal gespeichert
      
      if (latestCommit !== currentVersion) {
        setUpdateAvailable(true);
      }
    });
}, []);

// UI:
{updateAvailable && (
  <div className="update-banner">
    🎉 CMS Update verfügbar! 
    <button onClick={handleUpdate}>Jetzt updaten</button>
  </div>
)}
```

---

## 💡 Credits sparen

### Kurze Emergent-Anweisung (nach GitHub public):

```
Installiere Monolith CMS:

bash -c "$(curl -fsSL https://raw.githubusercontent.com/zundIO/emergent-cms/main/install.sh)"

Füge data-cms-id zu editierbaren Elementen hinzu:
<h1 data-cms-id="hero">Text</h1>
```

**Das spart ~90% Tokens!**

Statt 5000+ Tokens (Self-contained)  
→ Nur ~200 Tokens (GitHub-Link)

---

## ✅ Checklist: Repo Public machen

- [ ] Gehe zu: https://github.com/zundIO/emergent-cms/settings
- [ ] Scrolle zu "Danger Zone"
- [ ] "Change visibility" → "Make public"
- [ ] Pushe aktualisierte install.sh (mit CDN-Link)
- [ ] Teste Installation auf neuer Website
- [ ] Fertig! 🎉

---

## 📚 Zusammenfassung

| Was | Update-Methode | Häufigkeit |
|-----|----------------|------------|
| **Client-Script** | ✅ Automatisch (CDN) | Sofort |
| **Backend-Files** | 🔄 Manuell (Re-Install) | Bei Bedarf |
| **Content** | - Bleibt lokal | - |
| **Config** | - Bleibt lokal | - |

**Fazit:** 
- Client-Updates = Automatisch! 🎉
- Backend-Updates = Selten nötig, dann Re-Install
- Content = Immer sicher (lokal)

---

**Nächster Schritt:** Mach dein Repo public, dann funktioniert alles! 🚀
