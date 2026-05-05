import React, { useState, useRef, useEffect } from 'react';
import { Copy, Check, Upload, FileJson, Box, Loader2, AlertCircle, CheckCircle2, Sparkles, Wand2, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import api, { projectsAPI } from '../../lib/api';

const API_BASE = process.env.REACT_APP_CMS_API_BASE || '/api/cms';

const IntegrationDocs = ({ cmsUrl, onClose }) => {
  const [copiedBlock, setCopiedBlock] = useState(null);
  const [importJson, setImportJson] = useState('');
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [importError, setImportError] = useState('');
  const fileInputRef = useRef(null);

  // Auto-Connect state
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null); // {scan_root, count, suggestions}
  const [scanError, setScanError] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [projectName, setProjectName] = useState('Auto-detected Site');
  const [applying, setApplying] = useState(false);
  const [applyResult, setApplyResult] = useState(null);

  const handleScan = async () => {
    setScanning(true);
    setScanError('');
    setScanResult(null);
    try {
      const res = await api.post(`${API_BASE}/system/scan-website`, {});
      setScanResult(res.data);
      // Pre-select all by default
      setSelectedIds(new Set(res.data.suggestions.map(s => s.has_existing_id ? s.existing_id : s.suggested_id)));
    } catch (err) {
      setScanError(err.response?.data?.detail || err.message);
    } finally {
      setScanning(false);
    }
  };

  const toggleSelection = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleApplyConnection = async () => {
    if (selectedIds.size === 0) {
      toast.error('Select at least one element to connect.');
      return;
    }
    setApplying(true);
    setApplyResult(null);
    try {
      const res = await api.post(`${API_BASE}/system/apply-connection`, {
        suggestion_ids: Array.from(selectedIds),
        project_name: projectName,
      });
      setApplyResult(res.data);
      toast.success('Website connected!', {
        description: `${res.data.elements_added} elements tagged across ${res.data.files_modified} files. Project "${res.data.project_id}" ready.`,
      });
    } catch (err) {
      toast.error('Connection failed', { description: err.response?.data?.detail || err.message });
    } finally {
      setApplying(false);
    }
  };

  const copyToClipboard = (text, blockId) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedBlock(blockId);
      setTimeout(() => setCopiedBlock(null), 2000);
    });
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      setImportJson(evt.target.result);
      setImportError('');
      setImportResult(null);
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    setImportError('');
    setImportResult(null);
    let parsed;
    try {
      parsed = JSON.parse(importJson);
    } catch {
      setImportError('Ungültiges JSON. Bitte überprüfe das Format.');
      return;
    }
    if (!parsed.project_name || !parsed.pages) {
      setImportError('Schema benötigt "project_name" und "pages" Felder.');
      return;
    }
    setImporting(true);
    try {
      const res = await projectsAPI.importSchema(parsed);
      setImportResult(res.data);
      setImportJson('');
    } catch (err) {
      setImportError(err.response?.data?.detail || 'Import fehlgeschlagen');
    } finally {
      setImporting(false);
    }
  };

  // ============================================================
  // THE COMPLETE EMERGENT INSTRUCTION
  // ============================================================
  const emergentInstruction = `=== CMS-INTEGRATION ANWEISUNG FÜR EMERGENT ===

Diese Website wird mit The Monolith CMS verbunden.
Das CMS erlaubt Editoren, Texte und Bilder zu ändern,
ohne das Design oder Layout zu berühren.

REGELN FÜR DIE WEBSITE-ENTWICKLUNG:

1. EDITIERBARE ELEMENTE MARKIEREN
   Jedes Element dessen Inhalt im CMS editierbar sein
   soll, bekommt ein data-cms-id Attribut:

   <h1 data-cms-id="hero-headline">Headline Text</h1>
   <p data-cms-id="hero-description">Beschreibung</p>
   <img data-cms-id="hero-image" src="bild.jpg" alt="Alt Text" />
   <a data-cms-id="cta-button" href="/kontakt">Kontakt</a>
   <span data-cms-id="section-badge">Kategorie</span>

   Die IDs müssen einzigartig pro Seite sein und
   beschreibend benannt werden (z.B. hero-headline,
   about-team-image, footer-address).

   KEINE data-cms-id auf Layout-Container/Sections
   setzen – nur auf Elemente mit editierbarem Inhalt.

2. CMS-SCHEMA DATEI ERSTELLEN
   Erstelle eine Datei "cms-schema.json" im Projekt-Root.
   Format:

   {
     "project_name": "PROJEKTNAME",
     "source_updated_at": "2026-01-15T10:00:00Z",
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
             "content": { "text": "Der aktuelle Headline-Text" },
             "style": { "classes": "text-5xl font-bold" },
             "children": []
           },
           {
             "id": "hero-image",
             "type": "image",
             "tag": "img",
             "label": "Hero Bild",
             "content": { "src": "/images/hero.jpg", "alt": "Hero" },
             "style": { "classes": "w-full rounded-lg" },
             "children": []
           },
           {
             "id": "cta-button",
             "type": "button",
             "tag": "a",
             "label": "CTA Button",
             "content": { "text": "Kontakt", "href": "/kontakt" },
             "style": { "classes": "btn-primary" },
             "children": []
           }
         ]
       }
     ]
   }

   WICHTIG: "source_updated_at" muss den aktuellen
   Zeitstempel enthalten. Das CMS vergleicht diesen
   mit dem Zeitpunkt der letzten Editor-Änderung.
   Wenn der Editor im CMS etwas nach dem letzten
   Website-Build geändert hat, wird die CMS-Version
   beibehalten. Sonst wird der neue Text übernommen.

   Element-Typen und ihre Content-Felder:
   - heading:   { text, highlight: { word, color } }
   - paragraph:  { text }
   - image:      { src, alt }
   - button:     { text, href }
   - badge:      { text }
   - card:       { title, text }
   - quote:      { title, text }
   - section:    (Container, keine eigenen Content-Felder,
                  hat "children" Array mit Kind-Elementen)

3. CLIENT-SCRIPT EINBINDEN
   Vor dem schließenden </body> Tag einfügen:

   Für HTML/statische Websites:
   <script
     src="${cmsUrl}/api/client.js"
     data-project="PROJEKTNAME"
     data-cms-url="${cmsUrl}">
   </script>

   Für React/Emergent Websites stattdessen den
   useMonolithCMS Hook verwenden:

   import { useMonolithCMS } from './hooks/useMonolithCMS';

   function MeinePage() {
     const { getContent, loading } = useMonolithCMS(
       'PROJEKTNAME', '/', '${cmsUrl}'
     );
     if (loading) return <div>Laden...</div>;
     return (
       <h1>{getContent('hero-headline', 'text', 'Fallback')}</h1>
     );
   }

4. BEI JEDER ÄNDERUNG MIT EMERGENT
   Wenn die Website mit Emergent geändert wird:
   - cms-schema.json aktualisieren (neue/geänderte Elemente)
   - source_updated_at auf den aktuellen Zeitstempel setzen
   - Die Schema-Datei wird dann erneut ins CMS importiert
   - Das CMS merged automatisch: Editor-Änderungen bleiben
     erhalten, neue Emergent-Änderungen werden übernommen

=== ENDE CMS-INTEGRATION ANWEISUNG ===`;

  const schemaExample = `{
  "project_name": "Meine Website",
  "source_updated_at": "${new Date().toISOString()}",
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
          "style": { "classes": "text-5xl font-bold" },
          "children": []
        },
        {
          "id": "hero-image",
          "type": "image",
          "tag": "img",
          "label": "Hero Bild",
          "content": {
            "src": "https://example.com/hero.jpg",
            "alt": "Hero Bild"
          },
          "style": {},
          "children": []
        }
      ]
    }
  ]
}`;

  return (
    <div className="p-6 md:p-10 max-w-[1000px] mx-auto" data-testid="integration-docs">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-2">
          <Box size={24} style={{ color: 'var(--primary-2)' }} />
          <h1 className="font-headline text-2xl font-bold" style={{ color: 'var(--on-surface)' }}>
            Integration Guide
          </h1>
        </div>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          Verbinde jede Website mit The Monolith CMS
        </p>
      </div>

      {/* ============================================================ */}
      {/* SECTION: Auto-Connect (NEW) */}
      {/* ============================================================ */}
      <Section
        number="1"
        title="Connect This Website"
        subtitle="Automatisch alle editierbaren Elemente erkennen und verbinden – kein manuelles Prompt-Kopieren mehr"
      >
        {!scanResult && !applyResult && (
          <div>
            <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
              Der Scanner durchsucht <span className="font-mono text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>frontend/src/pages/</span> mit AST-basierter Analyse, findet statische Texte, Buttons und Bilder, und schlägt sie als editierbare Elemente vor. Du wählst aus, was übernommen wird.
            </p>
            <button
              data-testid="auto-connect-scan-btn"
              onClick={handleScan}
              disabled={scanning}
              className="gradient-btn px-5 py-2.5 rounded-[4px] font-headline font-bold text-xs tracking-wider uppercase flex items-center gap-2"
            >
              {scanning ? <><Loader2 size={14} className="animate-spin" /> Scanning…</> : <><Wand2 size={14} /> Scan Website</>}
            </button>
            {scanError && (
              <div className="mt-3 flex items-start gap-2 p-3 rounded-[4px]" style={{ backgroundColor: 'rgba(239,68,68,0.08)', color: '#fca5a5' }}>
                <AlertCircle size={14} style={{ flexShrink: 0, marginTop: 2 }} />
                <span className="text-xs">{scanError}</span>
              </div>
            )}
          </div>
        )}

        {scanResult && !applyResult && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-xs uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>
                  Found {scanResult.count} editable elements
                </p>
                <p className="text-xs font-mono" style={{ color: 'var(--muted)' }}>
                  {scanResult.scan_root}
                </p>
              </div>
              <button
                onClick={handleScan}
                className="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-[4px]"
                style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--muted)' }}
                data-testid="auto-connect-rescan-btn"
              >
                <RefreshCw size={12} /> Re-scan
              </button>
            </div>

            <div className="mb-3 flex items-center gap-2 text-xs">
              <button
                onClick={() => setSelectedIds(new Set(scanResult.suggestions.map(s => s.has_existing_id ? s.existing_id : s.suggested_id)))}
                className="px-2 py-1 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--muted)' }}
              >Select all</button>
              <button
                onClick={() => setSelectedIds(new Set())}
                className="px-2 py-1 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--muted)' }}
              >Deselect all</button>
              <span style={{ color: 'var(--muted)' }}>
                {selectedIds.size} of {scanResult.count} selected
              </span>
            </div>

            <div
              className="rounded-[4px] max-h-96 overflow-y-auto mb-4"
              style={{ backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}
            >
              <table className="w-full text-xs">
                <thead style={{ backgroundColor: 'rgba(255,255,255,0.04)', position: 'sticky', top: 0 }}>
                  <tr>
                    <th className="text-left p-2 w-8"></th>
                    <th className="text-left p-2">Tag</th>
                    <th className="text-left p-2">Page</th>
                    <th className="text-left p-2">Content</th>
                    <th className="text-left p-2">ID</th>
                  </tr>
                </thead>
                <tbody>
                  {scanResult.suggestions.map((s, idx) => {
                    const id = s.has_existing_id ? s.existing_id : s.suggested_id;
                    const checked = selectedIds.has(id);
                    return (
                      <tr
                        key={idx}
                        onClick={() => toggleSelection(id)}
                        className="cursor-pointer"
                        style={{ borderTop: '1px solid rgba(255,255,255,0.04)', opacity: checked ? 1 : 0.5 }}
                        data-testid={`auto-connect-row-${idx}`}
                      >
                        <td className="p-2">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleSelection(id)}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </td>
                        <td className="p-2 font-mono" style={{ color: 'var(--primary-2)' }}>{s.tag}</td>
                        <td className="p-2 font-mono text-xs opacity-60">
                          {s.rel_file}:{s.line}
                        </td>
                        <td className="p-2" style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {s.text}
                        </td>
                        <td className="p-2 font-mono text-xs opacity-50">
                          {s.has_existing_id ? <span style={{ color: '#10b981' }}>✓ {s.existing_id}</span> : s.suggested_id}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="flex items-center gap-3">
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="Project name"
                className="flex-1 px-3 py-2 text-sm rounded-[4px]"
                style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text)', border: '1px solid rgba(255,255,255,0.08)' }}
                data-testid="auto-connect-project-name"
              />
              <button
                onClick={handleApplyConnection}
                disabled={applying || selectedIds.size === 0}
                className="gradient-btn px-5 py-2.5 rounded-[4px] font-headline font-bold text-xs tracking-wider uppercase flex items-center gap-2"
                data-testid="auto-connect-apply-btn"
              >
                {applying ? <><Loader2 size={14} className="animate-spin" /> Applying…</> : <><Sparkles size={14} /> Apply & Connect</>}
              </button>
            </div>
          </div>
        )}

        {applyResult && (
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-4 rounded-[4px]" style={{ backgroundColor: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)' }}>
              <CheckCircle2 size={18} style={{ color: '#10b981', flexShrink: 0, marginTop: 2 }} />
              <div className="flex-1 text-sm">
                <p className="font-bold mb-1" style={{ color: '#10b981' }}>Website connected successfully</p>
                <ul className="text-xs space-y-1 opacity-80">
                  <li>• Project: <span className="font-mono">{applyResult.project_id}</span></li>
                  <li>• {applyResult.elements_added} new elements tagged across {applyResult.files_modified} files</li>
                  <li>• {applyResult.pages_added} pages added, {applyResult.pages_updated} updated</li>
                  <li>• {applyResult.total_elements} total editable elements available in CMS</li>
                </ul>
                <p className="text-xs mt-2 opacity-70">
                  Switch to project <span className="font-mono">{applyResult.project_id}</span> in the top bar to start editing.
                </p>
              </div>
            </div>
            <button
              onClick={() => { setScanResult(null); setApplyResult(null); setSelectedIds(new Set()); }}
              className="text-xs px-3 py-1.5 rounded-[4px]"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--muted)' }}
            >
              Scan again
            </button>
          </div>
        )}
      </Section>

      {/* ============================================================ */}
      {/* SECTION: Emergent Anweisung (manual fallback) */}
      {/* ============================================================ */}
      <Section number="2" title="Emergent Anweisung (manuell)" subtitle="Falls Auto-Connect nicht alles erfasst hat — kopieren und Emergent geben">
        <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
          Diese Anweisung enthält alles was Emergent braucht – Element-Markierung, Schema-Format, Client-Script, und Update-Regeln. Einfach kopieren und als Kontext mitgeben.
        </p>
        <CodeBlock
          code={emergentInstruction}
          language="text"
          blockId="emergent-complete"
          copyToClipboard={copyToClipboard}
          copiedBlock={copiedBlock}
        />
      </Section>

      {/* ============================================================ */}
      {/* SECTION: Schema Import */}
      {/* ============================================================ */}
      <Section number="3" title="Website importieren (manuell)" subtitle="Lade die cms-schema.json hier hoch oder füge das JSON ein">
        <div
          className="rounded-[4px] p-6"
          style={{ backgroundColor: 'var(--elevated)' }}
          data-testid="schema-import-panel"
        >
          {/* File upload */}
          <div className="flex items-center gap-3 mb-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
              data-testid="schema-file-input"
            />
            <button
              data-testid="schema-upload-button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-2 px-4 py-2 rounded-[4px] text-xs font-semibold transition-colors duration-150"
              style={{
                backgroundColor: 'rgba(255,255,255,0.06)',
                color: 'var(--on-surface)',
              }}
            >
              <FileJson size={14} />
              cms-schema.json hochladen
            </button>
            <span className="text-xs" style={{ color: 'var(--muted-2)' }}>oder JSON unten einfügen</span>
          </div>

          {/* JSON textarea */}
          <textarea
            data-testid="schema-json-textarea"
            value={importJson}
            onChange={(e) => { setImportJson(e.target.value); setImportError(''); setImportResult(null); }}
            placeholder={`{\n  "project_name": "Meine Website",\n  "source_updated_at": "${new Date().toISOString()}",\n  "pages": [ ... ]\n}`}
            rows={10}
            className="w-full rounded-[4px] px-4 py-3 text-xs font-mono resize-none custom-scrollbar mb-4"
            style={{
              backgroundColor: 'var(--sunken)',
              color: 'var(--on-surface)',
              border: 'none',
              outline: 'none',
              lineHeight: '1.7',
            }}
          />

          {/* Error */}
          <AnimatePresence>
            {importError && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-2 mb-4 px-3 py-2 rounded-[4px] text-xs"
                style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}
              >
                <AlertCircle size={14} />
                {importError}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Success */}
          <AnimatePresence>
            {importResult && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mb-4 px-4 py-3 rounded-[4px]"
                style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}
                data-testid="schema-import-success"
              >
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 size={16} style={{ color: 'var(--primary-2)' }} />
                  <span className="text-sm font-semibold" style={{ color: 'var(--primary-2)' }}>
                    Import erfolgreich
                  </span>
                </div>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>
                  Projekt: <strong>{importResult.project_name}</strong> ({importResult.project_id})
                </p>
                <div className="mt-2 space-y-1">
                  {importResult.details?.map((d, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <span
                        className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded-[2px]"
                        style={{
                          backgroundColor: d.action === 'created' ? 'rgba(16, 185, 129, 0.14)' : 'rgba(56, 189, 248, 0.14)',
                          color: d.action === 'created' ? 'var(--primary-2)' : 'var(--info)',
                        }}
                      >
                        {d.action}
                      </span>
                      <span style={{ color: 'var(--on-surface)' }}>{d.name}</span>
                      <span style={{ color: 'var(--muted-2)' }}>{d.slug}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Import button */}
          <button
            data-testid="schema-import-button"
            onClick={handleImport}
            disabled={!importJson.trim() || importing}
            className="gradient-btn flex items-center gap-2 px-5 py-2 rounded-[4px] font-headline font-bold text-xs tracking-wider uppercase disabled:opacity-40"
          >
            {importing ? (
              <><Loader2 size={14} className="animate-spin" /> Importiere...</>
            ) : (
              <><Upload size={14} /> Schema importieren</>
            )}
          </button>
        </div>
      </Section>

      {/* ============================================================ */}
      {/* SECTION: Schema Beispiel */}
      {/* ============================================================ */}
      <Section number="4" title="Schema Beispiel" subtitle="Vorlage für die cms-schema.json">
        <CodeBlock
          code={schemaExample}
          language="json"
          blockId="schema-example"
          copyToClipboard={copyToClipboard}
          copiedBlock={copiedBlock}
        />
      </Section>

      {/* ============================================================ */}
      {/* SECTION: Element-Typen Referenz */}
      {/* ============================================================ */}
      <Section number="5" title="Element-Typen" subtitle="Unterstützte Typen und ihre Content-Felder">
        <div className="space-y-2">
          <TypeRow type="heading" fields="text, highlight.word, highlight.color" tag="h1-h6" />
          <TypeRow type="paragraph" fields="text" tag="p" />
          <TypeRow type="image" fields="src, alt" tag="img" />
          <TypeRow type="button" fields="text, href" tag="a, button" />
          <TypeRow type="badge" fields="text" tag="span" />
          <TypeRow type="card" fields="title, text" tag="div" />
          <TypeRow type="quote" fields="title, text" tag="blockquote" />
          <TypeRow type="section" fields="(Container mit children)" tag="section, div" />
        </div>
      </Section>

      {/* ============================================================ */}
      {/* SECTION: Timestamp-Merge Erklärung */}
      {/* ============================================================ */}
      <Section number="6" title="Smart Merge" subtitle="Wie das CMS entscheidet welcher Content gilt">
        <div className="space-y-3">
          <MergeRow
            scenario="Editor ändert Text im CMS, dann wird Website mit Emergent neu gebaut"
            result="CMS-Text bleibt (Editor-Änderung ist neuer)"
            color="var(--primary-2)"
          />
          <MergeRow
            scenario="Website wird mit Emergent geändert, Editor hat nichts im CMS geändert"
            result="Neuer Emergent-Text wird übernommen"
            color="var(--info)"
          />
          <MergeRow
            scenario="Neues Element wird mit Emergent hinzugefügt"
            result="Element erscheint automatisch im CMS-Editor"
            color="var(--primary-2)"
          />
          <MergeRow
            scenario="Element wird mit Emergent entfernt"
            result="Element verschwindet aus dem CMS-Editor"
            color="var(--warning)"
          />
        </div>
      </Section>

      {/* ============================================================ */}
      {/* SECTION: API Referenz */}
      {/* ============================================================ */}
      <Section number="7" title="API Referenz" subtitle="Endpoints für Integration">
        <div className="space-y-2">
          <ApiRow method="POST" path="/api/projects/import" desc="Schema importieren (Admin)" />
          <ApiRow method="GET" path="/api/public/{project}/content" desc="Publizierte Inhalte (öffentlich)" />
          <ApiRow method="GET" path="/api/public/{project}/pages" desc="Publizierte Seiten (öffentlich)" />
          <ApiRow method="GET" path="/api/client.js" desc="JavaScript Client Library" />
        </div>
      </Section>
    </div>
  );
};

// ============================================================
// SUB-COMPONENTS
// ============================================================

const Section = ({ number, title, subtitle, children }) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3, delay: Number(String(number).replace(/[^0-9]/g, '')) * 0.04 }}
    className="mb-10"
  >
    <div className="flex items-start gap-3 mb-4">
      <span
        className="w-7 h-7 rounded-[4px] grid place-items-center text-xs font-bold flex-shrink-0 mt-0.5"
        style={{ backgroundColor: 'rgba(16, 185, 129, 0.14)', color: 'var(--primary-2)' }}
      >
        {number}
      </span>
      <div>
        <h2 className="font-headline text-lg font-bold" style={{ color: 'var(--on-surface)' }}>{title}</h2>
        <p className="text-xs" style={{ color: 'var(--muted-2)' }}>{subtitle}</p>
      </div>
    </div>
    <div className="ml-10">{children}</div>
  </motion.div>
);

const CodeBlock = ({ code, language, blockId, copyToClipboard, copiedBlock }) => (
  <div className="relative rounded-[4px] overflow-hidden" style={{ backgroundColor: 'var(--sunken)' }}>
    <div className="flex items-center justify-between px-4 py-2" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
      <span className="text-[10px] font-mono font-medium" style={{ color: 'var(--muted-2)' }}>{language}</span>
      <button
        onClick={() => copyToClipboard(code, blockId)}
        data-testid={`copy-${blockId}`}
        className="flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-[3px] transition-colors duration-150"
        style={{
          backgroundColor: copiedBlock === blockId ? 'rgba(16, 185, 129, 0.14)' : 'rgba(255,255,255,0.04)',
          color: copiedBlock === blockId ? 'var(--primary-2)' : 'var(--muted)',
        }}
      >
        {copiedBlock === blockId ? <><Check size={10} /> Kopiert</> : <><Copy size={10} /> Kopieren</>}
      </button>
    </div>
    <pre className="p-4 overflow-x-auto text-xs leading-relaxed custom-scrollbar" style={{ color: 'var(--on-surface)', maxHeight: '500px' }}>
      <code>{code}</code>
    </pre>
  </div>
);

const TypeRow = ({ type, fields, tag }) => (
  <div
    className="flex items-center gap-4 p-3 rounded-[4px]"
    style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
  >
    <span className="font-mono text-xs font-semibold w-24" style={{ color: 'var(--primary-2)' }}>{type}</span>
    <span className="text-xs flex-1" style={{ color: 'var(--muted)' }}>{fields}</span>
    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-[2px]" style={{ backgroundColor: 'rgba(255,255,255,0.04)', color: 'var(--muted-2)' }}>
      {'<'}{tag}{'>'}
    </span>
  </div>
);

const MergeRow = ({ scenario, result, color }) => (
  <div
    className="p-3 rounded-[4px]"
    style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
  >
    <p className="text-xs mb-1" style={{ color: 'var(--muted)' }}>{scenario}</p>
    <p className="text-xs font-semibold" style={{ color }}>{result}</p>
  </div>
);

const ApiRow = ({ method, path, desc }) => (
  <div
    className="flex items-center gap-4 p-3 rounded-[4px]"
    style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
  >
    <span
      className="text-[10px] font-bold px-2 py-0.5 rounded-[3px] w-14 text-center"
      style={{
        backgroundColor: method === 'GET' ? 'rgba(56, 189, 248, 0.14)' : 'rgba(16, 185, 129, 0.14)',
        color: method === 'GET' ? 'var(--info)' : 'var(--primary-2)',
      }}
    >
      {method}
    </span>
    <span className="font-mono text-xs flex-1" style={{ color: 'var(--on-surface)' }}>{path}</span>
    <span className="text-xs" style={{ color: 'var(--muted-2)' }}>{desc}</span>
  </div>
);

export default IntegrationDocs;
