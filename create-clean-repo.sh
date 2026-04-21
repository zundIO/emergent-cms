#!/bin/bash
# Script: Sauberes CMS-Repo erstellen

echo "🧹 Erstelle sauberes Monolith CMS Repo..."

# 1. Erstelle temp Ordner
cd /tmp
rm -rf monolith-cms-clean
mkdir monolith-cms-clean
cd monolith-cms-clean

# 2. Kopiere NUR CMS-Dateien
echo "📦 Kopiere CMS-Dateien..."
cp -r /app/monolith-cms-embedded/* .

# 3. Prüfe dass keine sensitive Daten vorhanden
echo "🔍 Prüfe auf sensitive Daten..."
if [ -f ".env" ] || [ -f ".env.local" ]; then
  echo "❌ FEHLER: .env Dateien gefunden!"
  exit 1
fi

if [ -d "cms-data" ]; then
  echo "❌ FEHLER: cms-data/ gefunden!"
  exit 1
fi

# 4. Git initialisieren
echo "📝 Git initialisieren..."
git init
git add .
git commit -m "Monolith CMS - Clean v1.0"

echo ""
echo "✅ Sauberes Repo erstellt in: /tmp/monolith-cms-clean"
echo ""
echo "🚀 Nächste Schritte:"
echo ""
echo "1. Erstelle NEUES Repo auf GitHub:"
echo "   https://github.com/new"
echo "   Name: monolith-cms"
echo "   Public ✅"
echo ""
echo "2. Pushe:"
echo "   cd /tmp/monolith-cms-clean"
echo "   git remote add origin https://github.com/zundIO/monolith-cms.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Emergent-Anweisung wird dann:"
echo "   bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/zundIO/monolith-cms/main/install.sh)\""
echo ""
echo "4. ALTES Repo (zundIO/cms):"
echo "   → Auf PRIVATE stellen!"
echo "   → Oder komplett löschen"
echo ""
