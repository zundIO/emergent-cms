# 🚀 CMS in eine Emergent-Website einbinden — Quick Start

## TL;DR (Aktueller "Zentraler" Ansatz)

Dein CMS läuft hier:
**`https://react-cms-editor.preview.emergentagent.com`**
(Login: `admin@monolith.cms` / `admin123`)

Jede neue Emergent-Website verbindet sich in **3 Schritten** mit dem CMS:

---

## Schritt 1 — Emergent-Anweisung kopieren

1. Öffne dein CMS und logge dich ein
2. Klick im **linken Sidebar** auf das **Rocket-Icon** (5. Icon, "Integration Guide")
3. **Section 1 → "Emergent Anweisung"** → klick `Kopieren`

Du hast jetzt einen ~2 KB langen Text in der Zwischenablage. Das ist die komplette Anleitung für Emergent — er enthält:
- Wie `data-cms-id` Attribute gesetzt werden
- Wie die `cms-schema.json` aufgebaut sein muss
- Wie der Client-Script eingebunden wird
- Welche Element-Typen unterstützt werden

---

## Schritt 2 — Neue Emergent-Website erstellen

1. Geh zu **emergent.sh**, starte einen neuen Chat
2. Beschreibe deine Website wie gewohnt
3. **Füge die kopierte Anweisung als Kontext** mit ein (z.B. am Ende der Beschreibung)
4. Emergent baut die Website UND
   - fügt automatisch `data-cms-id="..."` zu allen editierbaren Elementen hinzu
   - generiert eine `cms-schema.json` im Projekt-Root
   - bindet das Client-Script vor `</body>` ein:
     ```html
     <script
       src="https://react-cms-editor.preview.emergentagent.com/api/client.js"
       data-project="DEIN-PROJEKT-NAME"
       data-cms-url="https://react-cms-editor.preview.emergentagent.com">
     </script>
     ```

---

## Schritt 3 — Schema ins CMS importieren

1. Im Emergent-Workspace lädst du die generierte `cms-schema.json` aus dem Projekt-Root herunter
2. Im CMS → **Integration Guide → Section 2 "Website importieren"**
3. Klick `cms-schema.json hochladen` ODER fügst den JSON-Inhalt in die Textarea ein
4. Klick **`Schema importieren`**
5. Du siehst eine grüne Bestätigung: *"Projekt: DEIN-NAME — X Pages created"*

✅ Dein neues Projekt erscheint im CMS-Sidebar (Pages-Icon → Project Switcher oben links).

---

## Schritt 4 — Inhalte editieren & publishen

1. Wähle dein neues Projekt im **Project Switcher** (oben links)
2. Wähle eine Page über das **Pages-Icon** (1. Icon im Sidebar)
3. Klick auf ein Element im Canvas → editiere im rechten PropertyPanel
4. **Ctrl+S** zum Speichern (Toast bestätigt)
5. **PUBLISH-Button** oben rechts → die Website fetcht automatisch den neuen Content

---

## Was passiert wenn du die Website mit Emergent erneut änderst?

**Das CMS macht einen Smart Merge:**

| Szenario | Ergebnis |
|---|---|
| Editor ändert Text im CMS, dann wird die Website mit Emergent neu gebaut | ✅ CMS-Text bleibt (Editor-Änderung ist neuer) |
| Website wird mit Emergent geändert, Editor hat nichts im CMS geändert | ✅ Neuer Emergent-Text wird übernommen |
| Neues Element wird mit Emergent hinzugefügt | ✅ Erscheint automatisch im CMS-Editor |
| Element wird mit Emergent entfernt | ✅ Verschwindet aus dem CMS-Editor |

**Bei jeder Re-Build:**
- Emergent muss die `cms-schema.json` mit aktualisiertem `source_updated_at`-Zeitstempel neu erzeugen
- Du importierst die neue `cms-schema.json` einfach erneut in Section 2 — fertig

---

## ⚠️ Hinweis zum "Per-Site Installer" (geplante Erweiterung)

Aktuell läuft das CMS **zentral** — alle Websites zeigen via `/api/client.js` auf diesen einen Server.

Du hast bereits den Wunsch geäußert, dass das CMS **per Website** installiert werden soll (für bessere Performance & Isolation). Das ist die nächste P0-Aufgabe und wird so funktionieren:

```bash
# Auf jeder neuen Website ausführen:
bash -c "$(curl -fsSL https://raw.githubusercontent.com/zundIO/cms/main/install.sh)"
```

Das Script wird:
1. Backend (FastAPI + MongoDB/SQLite) installieren
2. Den **kompilierten React-Build** (mit Google Stitch UI) als Static Files servieren
3. Standard-Admin anlegen
4. Auf einem konfigurierbaren Port starten

→ **Status: noch nicht gebaut.** Sag Bescheid wenn ich damit anfangen soll.

---

## Quick Reference — API Endpoints (für eigene Integrationen)

| Methode | Endpoint | Zweck |
|---|---|---|
| `POST` | `/api/projects/import` | Schema importieren (Admin, mit Bearer-Token) |
| `GET` | `/api/public/{project}/content` | Publizierten Content abrufen (öffentlich) |
| `GET` | `/api/public/{project}/pages` | Publizierte Seiten (öffentlich) |
| `GET` | `/api/client.js` | JavaScript Client Library |

---

## Beispiel — Minimales Test-Schema

```json
{
  "project_name": "Mein Test",
  "source_updated_at": "2026-02-15T10:00:00Z",
  "pages": [
    {
      "name": "Homepage",
      "slug": "/",
      "elements": [
        {
          "id": "hero-headline",
          "type": "heading",
          "tag": "h1",
          "label": "Hero Headline",
          "content": { "text": "Willkommen" },
          "style": {},
          "children": []
        },
        {
          "id": "hero-cta",
          "type": "button",
          "tag": "a",
          "label": "CTA",
          "content": { "text": "Kontakt", "href": "/kontakt" },
          "style": {},
          "children": []
        }
      ]
    }
  ]
}
```

Das CMS kennt diese **Element-Typen**: `heading`, `paragraph`, `image`, `button`, `badge`, `card`, `quote`, `section` (Container).

---

**Weitere Fragen?** Sag einfach Bescheid, dann passe ich die Anleitung an oder bauen den Per-Site Installer.
