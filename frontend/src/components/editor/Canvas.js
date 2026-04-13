import React, { useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Type, Image as ImageIcon, MousePointer2, Square, Layers, Tag, CreditCard, Quote as QuoteIcon } from 'lucide-react';

const Canvas = ({ page, selectedElement, onSelectElement, deviceMode }) => {
  const getFrameWidth = () => {
    switch (deviceMode) {
      case 'tablet':
        return '768px';
      case 'mobile':
        return '375px';
      default:
        return '1100px';
    }
  };

  const handleElementClick = useCallback(
    (e, element) => {
      e.stopPropagation();
      onSelectElement(element);
    },
    [onSelectElement]
  );

  const getElementIcon = (type) => {
    switch (type) {
      case 'heading':
        return <Type size={11} />;
      case 'paragraph':
        return <Type size={11} />;
      case 'image':
        return <ImageIcon size={11} />;
      case 'button':
        return <Square size={11} />;
      case 'section':
        return <Layers size={11} />;
      case 'badge':
        return <Tag size={11} />;
      case 'card':
        return <CreditCard size={11} />;
      case 'quote':
        return <QuoteIcon size={11} />;
      default:
        return <MousePointer2 size={11} />;
    }
  };

  // Inline style mappings for element types (instead of Tailwind classes)
  const sectionStyles = {
    'hero-section': {
      padding: '96px 64px 128px',
      backgroundColor: '#121414',
    },
    'image-grid-section': {
      padding: '0 64px',
      display: 'grid',
      gridTemplateColumns: 'repeat(12, 1fr)',
      gap: '32px',
      alignItems: 'end',
      marginBottom: '96px',
      backgroundColor: '#121414',
    },
    'features-section': {
      padding: '96px 64px',
      backgroundColor: '#0d0e0e',
    },
    'about-hero': {
      padding: '96px 64px 64px',
      backgroundColor: '#121414',
    },
    'about-values': {
      padding: '96px 64px',
      backgroundColor: '#0d0e0e',
    },
  };

  const renderElement = (element) => {
    const isSelected = selectedElement?.id === element.id;
    const isSection = element.type === 'section';

    if (isSection) {
      const sStyle = sectionStyles[element.id] || { padding: '64px', backgroundColor: '#121414' };

      // Special layout for image-grid-section
      const isGrid = element.id === 'image-grid-section';
      const isFeatures = element.id === 'features-section' || element.id === 'about-values';

      return (
        <div
          key={element.id}
          data-testid={`canvas-element-${element.id}`}
          className="element-selectable relative"
          onClick={(e) => handleElementClick(e, element)}
          style={{
            ...sStyle,
            position: 'relative',
            ...(isSelected
              ? {
                  boxShadow:
                    '0 0 0 2px rgba(78, 222, 163, 0.85), 0 0 0 6px rgba(16, 185, 129, 0.10)',
                }
              : {}),
          }}
        >
          {isSelected && (
            <AnimatePresence>
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="element-label"
              >
                {getElementIcon('section')}
                {element.label || 'Section'}
              </motion.div>
            </AnimatePresence>
          )}
          {isGrid ? (
            // Grid layout
            element.children?.map((child) => renderElement(child))
          ) : isFeatures ? (
            // Features with card grid
            <div>
              {element.children?.filter(c => c.type !== 'card').map((child) => renderElement(child))}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                {element.children?.filter(c => c.type === 'card').map((child) => renderElement(child))}
              </div>
            </div>
          ) : (
            <div style={{ maxWidth: '768px' }}>
              {element.children?.map((child) => renderElement(child))}
              {/* Render buttons inline */}
              {element.children?.some(c => c.type === 'button') && null}
            </div>
          )}
        </div>
      );
    }

    // Leaf elements
    return (
      <div
        key={element.id}
        data-testid={`canvas-element-${element.id}`}
        className="element-selectable relative"
        onClick={(e) => handleElementClick(e, element)}
        style={{
          position: 'relative',
          ...(isSelected
            ? {
                boxShadow:
                  '0 0 0 2px rgba(78, 222, 163, 0.85), 0 0 0 6px rgba(16, 185, 129, 0.10)',
                borderRadius: '2px',
              }
            : {}),
          // Grid children positioning
          ...(element.id === 'grid-image-large' ? { gridColumn: 'span 7' } : {}),
          ...(element.id === 'grid-image-small' ? { gridColumn: 'span 5' } : {}),
          ...(element.id === 'grid-quote-block' ? { gridColumn: '8 / span 5' } : {}),
        }}
      >
        {isSelected && (
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="element-label"
            >
              {getElementIcon(element.type)}
              {element.label || element.type}
            </motion.div>
          </AnimatePresence>
        )}
        {renderElementContent(element)}
      </div>
    );
  };

  const renderElementContent = (element) => {
    const { type, content } = element;

    switch (type) {
      case 'heading': {
        const tag = element.tag || 'h1';
        const isH1 = tag === 'h1';
        const isH2 = tag === 'h2';
        let text = content?.text || '';

        const style = {
          fontFamily: "'Space Grotesk', sans-serif",
          fontWeight: 700,
          letterSpacing: '-0.02em',
          lineHeight: 1.05,
          color: '#e3e2e2',
          marginBottom: '32px',
          ...(isH1
            ? { fontSize: deviceMode === 'mobile' ? '36px' : '64px' }
            : isH2
            ? { fontSize: deviceMode === 'mobile' ? '28px' : '36px', marginBottom: '16px' }
            : { fontSize: '28px' }),
        };

        if (content?.highlight?.word) {
          const parts = text.split(new RegExp(`(${content.highlight.word})`, 'gi'));
          return (
            <div style={style}>
              {parts.map((part, i) =>
                part.toLowerCase() === content.highlight.word.toLowerCase() ? (
                  <span key={i} style={{ color: content.highlight.color || '#4edea3' }}>
                    {part}
                  </span>
                ) : (
                  <React.Fragment key={i}>{part}</React.Fragment>
                )
              )}
            </div>
          );
        }
        return <div style={style}>{text}</div>;
      }

      case 'paragraph':
        return (
          <p
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: deviceMode === 'mobile' ? '16px' : '20px',
              color: '#a3a3a3',
              lineHeight: 1.7,
              marginBottom: '48px',
              maxWidth: '560px',
            }}
          >
            {content?.text || ''}
          </p>
        );

      case 'badge':
        return (
          <span
            style={{
              display: 'inline-block',
              padding: '4px 12px',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              borderRadius: '2px',
              fontSize: '10px',
              fontWeight: 700,
              letterSpacing: '0.2em',
              color: '#4edea3',
              textTransform: 'uppercase',
              marginBottom: '24px',
              fontFamily: "'Space Grotesk', sans-serif",
            }}
          >
            {content?.text || ''}
          </span>
        );

      case 'button': {
        const isPrimary = element.id?.includes('primary');
        if (isPrimary) {
          return (
            <span
              style={{
                display: 'inline-block',
                background: 'linear-gradient(135deg, #4edea3, #10b981)',
                color: '#0b0c0c',
                padding: '14px 32px',
                borderRadius: '8px',
                fontFamily: "'Space Grotesk', sans-serif",
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.15em',
                fontSize: '12px',
                cursor: 'default',
                marginRight: '24px',
                marginBottom: '8px',
              }}
            >
              {content?.text || ''}
            </span>
          );
        }
        return (
          <span
            style={{
              display: 'inline-block',
              color: '#e3e2e2',
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.15em',
              fontSize: '12px',
              cursor: 'default',
              borderBottom: '2px solid rgba(255,255,255,0.2)',
              paddingBottom: '4px',
              marginBottom: '8px',
            }}
          >
            {content?.text || ''}
          </span>
        );
      }

      case 'image':
        return (
          <div
            style={{
              borderRadius: '2px',
              overflow: 'hidden',
              aspectRatio: element.id?.includes('large') ? '4/5' : '1/1',
              position: 'relative',
            }}
          >
            <img
              src={content?.src || ''}
              alt={content?.alt || ''}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
              loading="lazy"
            />
            {element.id?.includes('large') && (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  background: 'linear-gradient(to top, rgba(0,0,0,0.4), transparent)',
                }}
              />
            )}
          </div>
        );

      case 'card':
        return (
          <div
            style={{
              padding: '32px',
              backgroundColor: '#1a1b1b',
              borderRadius: '2px',
            }}
          >
            {content?.title && (
              <h3
                style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontSize: '20px',
                  fontWeight: 700,
                  color: '#e3e2e2',
                  marginBottom: '8px',
                }}
              >
                {content.title}
              </h3>
            )}
            {content?.text && (
              <p
                style={{
                  fontSize: '14px',
                  color: '#a3a3a3',
                  lineHeight: 1.6,
                }}
              >
                {content.text}
              </p>
            )}
          </div>
        );

      case 'quote':
        return (
          <div
            style={{
              padding: '32px',
              borderLeft: '2px solid #10b981',
              backgroundColor: '#1a1b1b',
            }}
          >
            {content?.title && (
              <h3
                style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontSize: '24px',
                  fontWeight: 700,
                  color: '#e3e2e2',
                  marginBottom: '8px',
                }}
              >
                {content.title}
              </h3>
            )}
            {content?.text && (
              <p
                style={{
                  fontSize: '14px',
                  color: '#a3a3a3',
                  lineHeight: 1.6,
                }}
              >
                {content.text}
              </p>
            )}
          </div>
        );

      default:
        return (
          <div style={{ padding: '8px', color: '#7b7b7b' }}>
            {content?.text || `[${type}]`}
          </div>
        );
    }
  };

  if (!page) return null;

  const handleCanvasBgClick = (e) => {
    // Only deselect if clicked on the canvas background itself, not on an element
    if (e.target === e.currentTarget) {
      onSelectElement(null);
    }
  };

  return (
    <div
      style={{ padding: '24px 40px' }}
      data-testid="editor-canvas"
      onClick={handleCanvasBgClick}
    >
      <div
        className="canvas-frame mx-auto"
        style={{
          maxWidth: getFrameWidth(),
          boxShadow: '0 0 100px rgba(0, 0, 0, 0.8)',
          backgroundColor: '#121414',
          minHeight: '80vh',
          transition: 'max-width 0.3s cubic-bezier(0.2, 0.8, 0.2, 1)',
        }}
        onClick={handleCanvasBgClick}
      >
        <div className="canvas-preview" onClick={handleCanvasBgClick}>
          {page.elements?.map((element) => renderElement(element))}
        </div>
      </div>
    </div>
  );
};

export default Canvas;
