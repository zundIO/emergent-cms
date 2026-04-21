/**
 * Monolith CMS - Client Script (Embedded Edition)
 * Lädt Content vom lokalen CMS und wendet ihn an
 */
(function() {
  'use strict';

  // Configuration
  var API_URL = '/api/cms/public';
  var CACHE_KEY = 'monolith-cms-content';
  var CACHE_VERSION_KEY = 'monolith-cms-version';
  var CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  /**
   * Get cached content
   */
  function getCachedContent() {
    try {
      var cached = localStorage.getItem(CACHE_KEY);
      var cachedAt = localStorage.getItem(CACHE_VERSION_KEY);
      
      if (cached && cachedAt) {
        var age = Date.now() - parseInt(cachedAt, 10);
        if (age < CACHE_DURATION) {
          return JSON.parse(cached);
        }
      }
    } catch (err) {
      console.warn('[Monolith CMS] Cache read error:', err);
    }
    return null;
  }

  /**
   * Cache content
   */
  function cacheContent(content) {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(content));
      localStorage.setItem(CACHE_VERSION_KEY, Date.now().toString());
    } catch (err) {
      console.warn('[Monolith CMS] Cache write error:', err);
    }
  }

  /**
   * Apply content to elements
   */
  function applyContent(content) {
    if (!content) return;

    var elements = document.querySelectorAll('[data-cms-id]');
    var applied = 0;

    elements.forEach(function(el) {
      var cmsId = el.getAttribute('data-cms-id');
      var entry = content[cmsId];
      
      if (!entry || !entry.content) return;

      var contentData = entry.content;
      var tag = el.tagName.toLowerCase();

      // Apply content based on element type
      if (tag === 'img') {
        if (contentData.src) el.src = contentData.src;
        if (contentData.alt) el.alt = contentData.alt;
      } else if (tag === 'a' || tag === 'button') {
        if (contentData.text) el.textContent = contentData.text;
        if (contentData.href && tag === 'a') el.href = contentData.href;
      } else if (contentData.text !== undefined) {
        el.textContent = contentData.text;
      }

      applied++;
    });

    console.log('[Monolith CMS] Applied', applied, 'content updates');
    
    // Dispatch event
    window.dispatchEvent(new CustomEvent('monolith-cms-loaded', { 
      detail: { content, applied } 
    }));
  }

  /**
   * Load content from CMS
   */
  function loadContent() {
    // Try cache first
    var cached = getCachedContent();
    if (cached) {
      console.log('[Monolith CMS] Loaded from cache');
      applyContent(cached);
      return;
    }

    // Fetch from API
    fetch(API_URL)
      .then(function(res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function(content) {
        console.log('[Monolith CMS] Loaded from API');
        cacheContent(content);
        applyContent(content);
      })
      .catch(function(err) {
        console.warn('[Monolith CMS] Failed to load content:', err.message);
      });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadContent);
  } else {
    loadContent();
  }

  // Expose API for manual refresh
  window.MonolithCMS = {
    refresh: function() {
      localStorage.removeItem(CACHE_KEY);
      localStorage.removeItem(CACHE_VERSION_KEY);
      loadContent();
    },
    clearCache: function() {
      localStorage.removeItem(CACHE_KEY);
      localStorage.removeItem(CACHE_VERSION_KEY);
    }
  };

})();
