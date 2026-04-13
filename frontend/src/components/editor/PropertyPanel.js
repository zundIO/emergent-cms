import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  ChevronRight,
  Type,
  Image as ImageIcon,
  Link,
  MoreHorizontal,
  Square,
  Layers,
  CreditCard,
  Quote,
  Tag,
} from 'lucide-react';

const PropertyPanel = ({ selectedElement, onContentUpdate, onDeselect }) => {
  const [expandedSections, setExpandedSections] = useState({
    typography: true,
    content: true,
    image: true,
    link: true,
    highlight: false,
  });

  // Local state for editing to prevent flickering
  const [localContent, setLocalContent] = useState({});

  useEffect(() => {
    if (selectedElement) {
      setLocalContent(selectedElement.content || {});
    }
  }, [selectedElement?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleChange = (field, value) => {
    const newContent = { ...localContent, [field]: value };
    setLocalContent(newContent);
    if (selectedElement) {
      onContentUpdate(selectedElement.id, { [field]: value });
    }
  };

  const handleHighlightChange = (field, value) => {
    const newHighlight = { ...(localContent.highlight || {}), [field]: value };
    const newContent = { ...localContent, highlight: newHighlight };
    setLocalContent(newContent);
    if (selectedElement) {
      onContentUpdate(selectedElement.id, { highlight: newHighlight });
    }
  };

  const getElementIcon = (type) => {
    switch (type) {
      case 'heading':
        return <Type size={16} />;
      case 'paragraph':
        return <Type size={16} />;
      case 'image':
        return <ImageIcon size={16} />;
      case 'button':
        return <Square size={16} />;
      case 'section':
        return <Layers size={16} />;
      case 'card':
        return <CreditCard size={16} />;
      case 'quote':
        return <Quote size={16} />;
      case 'badge':
        return <Tag size={16} />;
      default:
        return <Square size={16} />;
    }
  };

  const hasTextField = ['heading', 'paragraph', 'button', 'badge', 'card', 'quote'].includes(
    selectedElement?.type
  );
  const hasTitleField = ['card', 'quote'].includes(selectedElement?.type);
  const hasImageField = selectedElement?.type === 'image';
  const hasLinkField = ['button'].includes(selectedElement?.type);
  const hasHighlightField = selectedElement?.type === 'heading' && localContent.highlight;
  const hasStyleInfo = selectedElement?.style;

  // Empty state
  if (!selectedElement) {
    return (
      <div className="right-panel custom-scrollbar" data-testid="properties-panel">
        <div className="p-6 flex flex-col items-center justify-center h-full">
          <div
            className="w-16 h-16 rounded-[4px] grid place-items-center mb-4"
            style={{ backgroundColor: 'rgba(255, 255, 255, 0.03)' }}
          >
            <Square size={24} style={{ color: 'var(--muted-2)' }} />
          </div>
          <p className="font-headline text-sm font-semibold" style={{ color: 'var(--muted)' }}>
            No Element Selected
          </p>
          <p className="text-xs mt-1 text-center" style={{ color: 'var(--muted-2)' }}>
            Click an element in the canvas to edit its content
          </p>
        </div>
      </div>
    );
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={selectedElement.id}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.15 }}
        className="right-panel custom-scrollbar"
        data-testid="properties-panel"
      >
        {/* Element selector header */}
        <div className="p-4 pb-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <div className="flex items-center justify-between mb-1">
            <span
              className="text-[10px] font-semibold tracking-[0.1em] uppercase"
              style={{ color: 'var(--muted-2)' }}
            >
              Element Selector
            </span>
            <button
              className="w-6 h-6 rounded-[4px] grid place-items-center transition-colors duration-150"
              style={{ color: 'var(--muted-2)' }}
            >
              <MoreHorizontal size={14} />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ color: 'var(--primary-2)' }}>
              {getElementIcon(selectedElement.type)}
            </span>
            <span
              className="font-headline text-base font-semibold"
              style={{ color: 'var(--on-surface)' }}
              data-testid="editor-canvas-selected-element-label"
            >
              {selectedElement.label || selectedElement.type}
            </span>
          </div>
          {selectedElement.tag && (
            <span
              className="text-[10px] mt-1 inline-block px-1.5 py-0.5 rounded-[2px]"
              style={{
                backgroundColor: 'rgba(255,255,255,0.04)',
                color: 'var(--muted-2)',
              }}
            >
              {'<'}{selectedElement.tag}{'>'}
            </span>
          )}
        </div>

        {/* Typography section - shown for text elements */}
        {hasStyleInfo && (selectedElement.style?.fontSize || selectedElement.style?.fontWeight) && (
          <Section
            title="TYPOGRAPHY"
            expanded={expandedSections.typography}
            onToggle={() => toggleSection('typography')}
            testId="properties-panel-typography-section"
          >
            <div className="grid grid-cols-2 gap-3">
              {selectedElement.style?.fontWeight && (
                <div>
                  <label
                    className="block text-[10px] font-medium uppercase tracking-wider mb-1"
                    style={{ color: 'var(--muted-2)' }}
                  >
                    Weight
                  </label>
                  <div
                    className="h-8 rounded-[4px] px-3 flex items-center text-xs"
                    style={{
                      backgroundColor: 'var(--sunken)',
                      color: 'var(--muted)',
                    }}
                  >
                    {selectedElement.style.fontWeight} (Bold)
                  </div>
                </div>
              )}
              {selectedElement.style?.fontSize && (
                <div>
                  <label
                    className="block text-[10px] font-medium uppercase tracking-wider mb-1"
                    style={{ color: 'var(--muted-2)' }}
                  >
                    Size
                  </label>
                  <div
                    className="h-8 rounded-[4px] px-3 flex items-center text-xs"
                    style={{
                      backgroundColor: 'var(--sunken)',
                      color: 'var(--muted)',
                    }}
                  >
                    {selectedElement.style.fontSize}
                  </div>
                </div>
              )}
            </div>
          </Section>
        )}

        {/* Content section - text editing */}
        {hasTextField && (
          <Section
            title="CONTENT"
            expanded={expandedSections.content}
            onToggle={() => toggleSection('content')}
            testId="properties-panel-content-section"
          >
            {hasTitleField && (
              <div className="mb-3">
                <label
                  className="block text-[10px] font-medium uppercase tracking-wider mb-1"
                  style={{ color: 'var(--muted-2)' }}
                >
                  Title
                </label>
                <input
                  data-testid="property-input-title"
                  type="text"
                  value={localContent.title || ''}
                  onChange={(e) => handleChange('title', e.target.value)}
                  className="w-full h-8 rounded-[4px] px-3 text-sm"
                  style={{
                    backgroundColor: 'var(--sunken)',
                    color: 'var(--on-surface)',
                    border: 'none',
                    outline: 'none',
                  }}
                />
              </div>
            )}
            <div>
              <label
                className="block text-[10px] font-medium uppercase tracking-wider mb-1"
                style={{ color: 'var(--muted-2)' }}
              >
                {hasTitleField ? 'Description' : selectedElement.type === 'heading' ? 'Headline Text' : 'Text'}
              </label>
              <textarea
                data-testid="property-input-text"
                value={localContent.text || ''}
                onChange={(e) => handleChange('text', e.target.value)}
                rows={selectedElement.type === 'heading' ? 3 : selectedElement.type === 'paragraph' ? 5 : 2}
                className="w-full rounded-[4px] px-3 py-2 text-sm resize-none"
                style={{
                  backgroundColor: 'var(--sunken)',
                  color: 'var(--on-surface)',
                  border: 'none',
                  outline: 'none',
                  lineHeight: '1.6',
                }}
              />
            </div>
          </Section>
        )}

        {/* Highlight section - for headings with highlights */}
        {hasHighlightField && (
          <Section
            title="TEXT HIGHLIGHT"
            expanded={expandedSections.highlight}
            onToggle={() => toggleSection('highlight')}
            testId="properties-panel-highlight-section"
          >
            <div className="mb-3">
              <label
                className="block text-[10px] font-medium uppercase tracking-wider mb-1"
                style={{ color: 'var(--muted-2)' }}
              >
                Highlighted Word
              </label>
              <input
                data-testid="property-input-highlight-word"
                type="text"
                value={localContent.highlight?.word || ''}
                onChange={(e) => handleHighlightChange('word', e.target.value)}
                className="w-full h-8 rounded-[4px] px-3 text-sm"
                style={{
                  backgroundColor: 'var(--sunken)',
                  color: 'var(--on-surface)',
                  border: 'none',
                  outline: 'none',
                }}
              />
            </div>
            <div>
              <label
                className="block text-[10px] font-medium uppercase tracking-wider mb-1"
                style={{ color: 'var(--muted-2)' }}
              >
                Highlight Color
              </label>
              <div className="flex items-center gap-2">
                <div
                  className="w-8 h-8 rounded-[4px]"
                  style={{ backgroundColor: localContent.highlight?.color || '#4edea3' }}
                />
                <input
                  data-testid="property-input-highlight-color"
                  type="text"
                  value={localContent.highlight?.color || '#4edea3'}
                  onChange={(e) => handleHighlightChange('color', e.target.value)}
                  className="flex-1 h-8 rounded-[4px] px-3 text-sm font-mono"
                  style={{
                    backgroundColor: 'var(--sunken)',
                    color: 'var(--on-surface)',
                    border: 'none',
                    outline: 'none',
                  }}
                />
              </div>
            </div>
          </Section>
        )}

        {/* Image section */}
        {hasImageField && (
          <Section
            title="IMAGE"
            expanded={expandedSections.image}
            onToggle={() => toggleSection('image')}
            testId="properties-panel-image-section"
          >
            <div className="mb-3">
              <label
                className="block text-[10px] font-medium uppercase tracking-wider mb-1"
                style={{ color: 'var(--muted-2)' }}
              >
                Image URL
              </label>
              <input
                data-testid="property-input-src"
                type="text"
                value={localContent.src || ''}
                onChange={(e) => handleChange('src', e.target.value)}
                className="w-full h-8 rounded-[4px] px-3 text-sm"
                style={{
                  backgroundColor: 'var(--sunken)',
                  color: 'var(--on-surface)',
                  border: 'none',
                  outline: 'none',
                }}
              />
            </div>
            <div>
              <label
                className="block text-[10px] font-medium uppercase tracking-wider mb-1"
                style={{ color: 'var(--muted-2)' }}
              >
                Alt Text
              </label>
              <input
                data-testid="property-input-alt"
                type="text"
                value={localContent.alt || ''}
                onChange={(e) => handleChange('alt', e.target.value)}
                className="w-full h-8 rounded-[4px] px-3 text-sm"
                style={{
                  backgroundColor: 'var(--sunken)',
                  color: 'var(--on-surface)',
                  border: 'none',
                  outline: 'none',
                }}
              />
            </div>
            {localContent.src && (
              <div className="mt-3">
                <div
                  className="rounded-[4px] overflow-hidden"
                  style={{ backgroundColor: 'var(--sunken)' }}
                >
                  <img
                    src={localContent.src}
                    alt={localContent.alt || ''}
                    className="w-full h-32 object-cover"
                  />
                </div>
              </div>
            )}
          </Section>
        )}

        {/* Link section */}
        {hasLinkField && (
          <Section
            title="LINK"
            expanded={expandedSections.link}
            onToggle={() => toggleSection('link')}
            testId="properties-panel-link-section"
          >
            <div>
              <label
                className="block text-[10px] font-medium uppercase tracking-wider mb-1"
                style={{ color: 'var(--muted-2)' }}
              >
                URL
              </label>
              <input
                data-testid="property-input-href"
                type="text"
                value={localContent.href || ''}
                onChange={(e) => handleChange('href', e.target.value)}
                className="w-full h-8 rounded-[4px] px-3 text-sm"
                style={{
                  backgroundColor: 'var(--sunken)',
                  color: 'var(--on-surface)',
                  border: 'none',
                  outline: 'none',
                }}
              />
            </div>
          </Section>
        )}

        {/* Element info */}
        <div className="p-4 mt-auto">
          <div
            className="text-[10px] uppercase tracking-wider font-medium mb-2"
            style={{ color: 'var(--muted-2)' }}
          >
            Element Info
          </div>
          <div className="space-y-1">
            <InfoRow label="Type" value={selectedElement.type} />
            <InfoRow label="Tag" value={`<${selectedElement.tag || 'div'}>`} />
            <InfoRow label="ID" value={selectedElement.id} />
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

// Collapsible section component
const Section = ({ title, expanded, onToggle, testId, children }) => (
  <div
    data-testid={testId}
    style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
  >
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between px-4 py-3 transition-colors duration-150"
      style={{ color: 'var(--primary-2)' }}
    >
      <span className="text-[10px] font-semibold tracking-[0.1em] uppercase">
        {title}
      </span>
      {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
    </button>
    <AnimatePresence initial={false}>
      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2, ease: [0.2, 0.8, 0.2, 1] }}
          className="overflow-hidden"
        >
          <div className="px-4 pb-4">{children}</div>
        </motion.div>
      )}
    </AnimatePresence>
  </div>
);

// Info row
const InfoRow = ({ label, value }) => (
  <div className="flex items-center justify-between">
    <span className="text-[10px]" style={{ color: 'var(--muted-2)' }}>
      {label}
    </span>
    <span
      className="text-[10px] font-mono px-1.5 py-0.5 rounded-[2px]"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        color: 'var(--muted)',
      }}
    >
      {value}
    </span>
  </div>
);

export default PropertyPanel;
