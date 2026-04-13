/**
 * useMonolithCMS - React Hook for The Monolith CMS
 *
 * Usage:
 *   import { useMonolithCMS } from './hooks/useMonolithCMS';
 *
 *   function MyPage() {
 *     const { content, loading, error, getContent } = useMonolithCMS('my-project-id', '/');
 *
 *     if (loading) return <div>Loading...</div>;
 *
 *     return (
 *       <h1>{getContent('hero-headline', 'text', 'Default Headline')}</h1>
 *     );
 *   }
 */
import { useState, useEffect, useCallback } from 'react';

const CMS_CACHE = {};

export function useMonolithCMS(projectId, pageSlug = '/', cmsUrl = '') {
  const [content, setContent] = useState(null);
  const [allContent, setAllContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Determine CMS URL
  const baseUrl = cmsUrl || process.env.REACT_APP_CMS_URL || process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    let cancelled = false;

    async function fetchContent() {
      const cacheKey = `${baseUrl}:${projectId}`;

      // Check cache first
      if (CMS_CACHE[cacheKey]) {
        if (!cancelled) {
          setAllContent(CMS_CACHE[cacheKey]);
          setContent(CMS_CACHE[cacheKey][pageSlug] || null);
          setLoading(false);
        }
        return;
      }

      try {
        const res = await fetch(`${baseUrl}/api/public/${projectId}/content`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        CMS_CACHE[cacheKey] = data;

        if (!cancelled) {
          setAllContent(data);
          setContent(data[pageSlug] || null);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      }
    }

    fetchContent();
    return () => { cancelled = true; };
  }, [baseUrl, projectId, pageSlug]);

  /**
   * Get content value for a specific element.
   * @param {string} elementId - The CMS element ID (e.g., 'hero-headline')
   * @param {string} field - Content field (e.g., 'text', 'src', 'alt', 'href', 'title')
   * @param {string} fallback - Fallback value if CMS content not found
   */
  const getContent = useCallback(
    (elementId, field = 'text', fallback = '') => {
      if (!content || !content[elementId]) return fallback;
      return content[elementId].content?.[field] ?? fallback;
    },
    [content]
  );

  /**
   * Get highlight info for a heading.
   * @param {string} elementId
   * @returns {{ word: string, color: string } | null}
   */
  const getHighlight = useCallback(
    (elementId) => {
      if (!content || !content[elementId]) return null;
      return content[elementId].content?.highlight || null;
    },
    [content]
  );

  /**
   * Render text with highlight applied.
   * @param {string} elementId
   * @param {string} fallback
   */
  const renderHighlightedText = useCallback(
    (elementId, fallback = '') => {
      const text = getContent(elementId, 'text', fallback);
      const highlight = getHighlight(elementId);

      if (!highlight || !highlight.word) return text;

      const parts = text.split(new RegExp(`(${highlight.word})`, 'gi'));
      return parts.map((part, i) => {
        if (part.toLowerCase() === highlight.word.toLowerCase()) {
          return { text: part, highlighted: true, color: highlight.color || '#4edea3' };
        }
        return { text: part, highlighted: false };
      });
    },
    [getContent, getHighlight]
  );

  return {
    content,
    allContent,
    loading,
    error,
    getContent,
    getHighlight,
    renderHighlightedText,
  };
}

export default useMonolithCMS;
