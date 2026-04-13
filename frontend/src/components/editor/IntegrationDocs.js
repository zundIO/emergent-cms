import React, { useState } from 'react';
import { Copy, Check, ExternalLink, FileJson, Box, Terminal } from 'lucide-react';
import { motion } from 'framer-motion';

const IntegrationDocs = ({ cmsUrl, onClose }) => {
  const [copiedBlock, setCopiedBlock] = useState(null);

  const copyToClipboard = (text, blockId) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedBlock(blockId);
      setTimeout(() => setCopiedBlock(null), 2000);
    });
  };

  const CopyButton = ({ text, blockId }) => (
    <button
      onClick={() => copyToClipboard(text, blockId)}
      className="absolute top-3 right-3 w-8 h-8 rounded-[4px] grid place-items-center transition-colors duration-150"
      style={{
        backgroundColor: 'rgba(255,255,255,0.06)',
        color: copiedBlock === blockId ? 'var(--primary-2)' : 'var(--muted)',
      }}
    >
      {copiedBlock === blockId ? <Check size={14} /> : <Copy size={14} />}
    </button>
  );

  const schemaExample = `{
  "project_name": "Meine Website",
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
          "content": { "text": "Willkommen auf unserer Website" },
          "style": { "classes": "text-5xl font-bold" },
          "children": []
        },
        {
          "id": "hero-description",
          "type": "paragraph",
          "tag": "p",
          "label": "Hero Description",
          "content": { "text": "Wir bauen digitale Produkte." },
          "style": { "classes": "text-lg text-gray-500" },
          "children": []
        },
        {
          "id": "hero-image",
          "type": "image",
          "tag": "img",
          "label": "Hero Image",
          "content": { "src": "/images/hero.jpg", "alt": "Hero" },
          "style": { "classes": "w-full rounded-lg" },
          "children": []
        }
      ]
    }
  ]
}`;

  const htmlSnippet = `<!-- Monolith CMS Client Library -->
<script
  src="${cmsUrl}/api/client.js"
  data-project="meine-website"
  data-cms-url="${cmsUrl}">
</script>`;

  const htmlExample = `<!-- Deine Website HTML -->
<section>
  <h1 data-cms-id="hero-headline">
    Willkommen auf unserer Website
  </h1>
  <p data-cms-id="hero-description">
    Wir bauen digitale Produkte.
  </p>
  <img data-cms-id="hero-image"
       src="/images/hero.jpg"
       alt="Hero" />
</section>

${htmlSnippet}`;

  const reactHookExample = `import { useMonolithCMS } from './hooks/useMonolithCMS';

function HomePage() {
  const { getContent, loading } = useMonolithCMS(
    'meine-website',  // project ID
    '/',               // page slug
    '${cmsUrl}'        // CMS URL
  );

  if (loading) return <div>Loading...</div>;

  return (
    <section>
      <h1>{getContent('hero-headline', 'text', 'Default Headline')}</h1>
      <p>{getContent('hero-description', 'text', 'Default text')}</p>
      <img
        src={getContent('hero-image', 'src', '/default.jpg')}
        alt={getContent('hero-image', 'alt', 'Default')}
      />
    </section>
  );
}`;

  const curlImport = `curl -X POST ${cmsUrl}/api/projects/import \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d @cms-schema.json`;

  const emergentPrompt = `Wichtig fuer die CMS-Integration:

1. Jedes editierbare Element braucht ein data-cms-id Attribut:
   <h1 data-cms-id="hero-headline">Text</h1>
   <img data-cms-id="hero-image" src="..." alt="..." />
   <p data-cms-id="about-text">Text</p>

2. Erstelle eine cms-schema.json Datei im Root
   des Projekts (Format siehe Dokumentation).

3. Fuege dieses Script vor </body> ein:
   <script src="${cmsUrl}/api/client.js"
           data-project="PROJEKT-NAME"
           data-cms-url="${cmsUrl}"></script>

4. Fuer React: Verwende den useMonolithCMS Hook
   statt des Script-Tags.

Die IDs muessen einzigartig pro Seite sein und
beschreibend (z.B. hero-headline, about-image,
footer-address). Sections brauchen keine data-cms-id,
nur Elemente deren Content editierbar sein soll.`;

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
          So verbindest du jede Website mit The Monolith CMS
        </p>
      </div>

      {/* Step 1: Emergent Prompt */}
      <Section number="0" title="Emergent Anweisung" subtitle="Kopiere diesen Text und gib ihn Emergent bei jeder neuen Website">
        <CodeBlock
          code={emergentPrompt}
          language="text"
          blockId="emergent-prompt"
          copyToClipboard={copyToClipboard}
          copiedBlock={copiedBlock}
        />
      </Section>

      {/* Step 1: Schema */}
      <Section number="1" title="Schema erstellen" subtitle="Die Website generiert eine cms-schema.json Datei">
        <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
          Jede editierbare Seite und jedes editierbare Element wird als JSON-Schema beschrieben.
          Elemente haben eine <InlineCode>id</InlineCode>, <InlineCode>type</InlineCode>, <InlineCode>label</InlineCode> (Name im CMS),
          <InlineCode>content</InlineCode> (editierbare Inhalte) und <InlineCode>style</InlineCode> (nicht editierbar, nur fuer Darstellung).
        </p>
        <CodeBlock
          code={schemaExample}
          language="json"
          blockId="schema-example"
          copyToClipboard={copyToClipboard}
          copiedBlock={copiedBlock}
        />
      </Section>

      {/* Step 2: Import */}
      <Section number="2" title="Schema importieren" subtitle="Upload ins CMS per API-Call">
        <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
          Der Admin importiert das Schema ins CMS. Dies erstellt automatisch das Projekt mit allen Seiten und Elementen.
        </p>
        <CodeBlock
          code={curlImport}
          language="bash"
          blockId="curl-import"
          copyToClipboard={copyToClipboard}
          copiedBlock={copiedBlock}
        />
        <p className="text-xs mt-2" style={{ color: 'var(--muted-2)' }}>
          Bei erneutem Import werden bestehende CMS-Inhalte beibehalten (Smart Merge). Neue Elemente werden hinzugefuegt, bestehende Content-Aenderungen bleiben erhalten.
        </p>
      </Section>

      {/* Step 3a: HTML Snippet */}
      <Section number="3a" title="HTML Integration" subtitle="Fuer statische Websites oder Non-React">
        <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
          Fuege jedem editierbaren HTML-Element ein <InlineCode>data-cms-id</InlineCode> Attribut hinzu.
          Das Client-Script ueberschreibt automatisch den Inhalt mit CMS-Daten.
        </p>
        <CodeBlock
          code={htmlExample}
          language="html"
          blockId="html-example"
          copyToClipboard={copyToClipboard}
          copiedBlock={copiedBlock}
        />
      </Section>

      {/* Step 3b: React Hook */}
      <Section number="3b" title="React Integration" subtitle="Fuer React / Emergent Websites">
        <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
          Verwende den <InlineCode>useMonolithCMS</InlineCode> Hook um CMS-Inhalte als React State zu laden.
          Fallback-Werte werden angezeigt bis der CMS-Content geladen ist.
        </p>
        <CodeBlock
          code={reactHookExample}
          language="jsx"
          blockId="react-example"
          copyToClipboard={copyToClipboard}
          copiedBlock={copiedBlock}
        />
      </Section>

      {/* Element Types */}
      <Section number="4" title="Element-Typen" subtitle="Unterstuetzte Typen und ihre Content-Felder">
        <div className="space-y-2">
          <TypeRow type="heading" fields="text, highlight.word, highlight.color" example='data-cms-id="hero-headline"' />
          <TypeRow type="paragraph" fields="text" example='data-cms-id="about-text"' />
          <TypeRow type="image" fields="src, alt" example='data-cms-id="hero-image"' />
          <TypeRow type="button" fields="text, href" example='data-cms-id="cta-button"' />
          <TypeRow type="badge" fields="text" example='data-cms-id="section-badge"' />
          <TypeRow type="card" fields="title, text" example='data-cms-id="feature-card-1"' />
          <TypeRow type="quote" fields="title, text" example='data-cms-id="testimonial-1"' />
          <TypeRow type="section" fields="(Container - keine eigenen Content-Felder)" example='Kein data-cms-id noetig' />
        </div>
      </Section>

      {/* API Reference */}
      <Section number="5" title="API Referenz" subtitle="Public Endpoints fuer Websites">
        <div className="space-y-2">
          <ApiRow method="GET" path={`/api/public/{project_id}/content`} desc="Alle publizierten Inhalte als Flat-Map" />
          <ApiRow method="GET" path={`/api/public/{project_id}/pages`} desc="Liste publizierter Seiten" />
          <ApiRow method="GET" path={`/api/public/{project_id}/pages/{slug}`} desc="Einzelne Seite mit Element-Tree" />
          <ApiRow method="GET" path="/api/client.js" desc="JavaScript Client Library" />
          <ApiRow method="POST" path="/api/projects/import" desc="Schema importieren (Auth required)" />
        </div>
      </Section>
    </div>
  );
};

// Sub-components
const Section = ({ number, title, subtitle, children }) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3, delay: Number(number.replace(/[^0-9]/g, '')) * 0.05 }}
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
        className="flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-[3px] transition-colors duration-150"
        style={{
          backgroundColor: copiedBlock === blockId ? 'rgba(16, 185, 129, 0.14)' : 'rgba(255,255,255,0.04)',
          color: copiedBlock === blockId ? 'var(--primary-2)' : 'var(--muted)',
        }}
      >
        {copiedBlock === blockId ? <><Check size={10} /> Copied</> : <><Copy size={10} /> Copy</>}
      </button>
    </div>
    <pre className="p-4 overflow-x-auto text-xs leading-relaxed custom-scrollbar" style={{ color: 'var(--on-surface)' }}>
      <code>{code}</code>
    </pre>
  </div>
);

const InlineCode = ({ children }) => (
  <code
    className="text-xs px-1 py-0.5 rounded-[2px] font-mono"
    style={{ backgroundColor: 'rgba(78, 222, 163, 0.08)', color: 'var(--primary-2)' }}
  >
    {children}
  </code>
);

const TypeRow = ({ type, fields, example }) => (
  <div
    className="flex items-center gap-4 p-3 rounded-[4px]"
    style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
  >
    <span className="font-mono text-xs font-semibold w-20" style={{ color: 'var(--primary-2)' }}>{type}</span>
    <span className="text-xs flex-1" style={{ color: 'var(--muted)' }}>{fields}</span>
    <span className="text-[10px] font-mono" style={{ color: 'var(--muted-2)' }}>{example}</span>
  </div>
);

const ApiRow = ({ method, path, desc }) => (
  <div
    className="flex items-center gap-4 p-3 rounded-[4px]"
    style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
  >
    <span
      className="text-[10px] font-bold px-2 py-0.5 rounded-[3px] w-12 text-center"
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
