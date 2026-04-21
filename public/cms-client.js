/**
 * Monolith CMS - Client Script (Zero-Config Edition)
 *
 * Auto-discovers editable elements (h1-h6, p, img, a, button) and assigns
 * stable data-cms-id attributes automatically. No manual attribution needed.
 *
 * - Generates deterministic IDs from DOM path + tag + initial content hash
 * - Registers discovered elements with the backend (fire-and-forget)
 * - Applies published content overrides transparently
 */
(function () {
  'use strict';

  var API_PUBLIC = '/api/cms/public';
  var API_REGISTER = '/api/cms/register';
  var CACHE_KEY = 'monolith-cms-content';
  var CACHE_TS_KEY = 'monolith-cms-content-ts';
  var CACHE_TTL = 60 * 1000; // 1 minute

  var EDITABLE_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'img', 'a', 'button', 'li', 'span', 'blockquote'];
  var SELECTOR = EDITABLE_TAGS.join(',');

  /**
   * Fast FNV-1a hash -> base36 string
   */
  function hash(str) {
    var h = 2166136261;
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = (h * 16777619) >>> 0;
    }
    return h.toString(36);
  }

  /**
   * Build a stable identifier for an element based on its DOM path.
   * Deterministic: same element across reloads produces the same ID.
   */
  function stableId(el) {
    var parts = [];
    var cur = el;
    var depth = 0;
    while (cur && cur.nodeType === 1 && cur !== document.body && depth < 10) {
      var parent = cur.parentElement;
      if (!parent) break;
      var siblings = parent.children;
      var idx = 0;
      for (var i = 0; i < siblings.length; i++) {
        if (siblings[i] === cur) { idx = i; break; }
      }
      parts.unshift(cur.tagName.toLowerCase() + idx);
      cur = parent;
      depth++;
    }
    var path = parts.join('-');
    return el.tagName.toLowerCase() + '-' + hash(path);
  }

  /**
   * Does this element carry editable content we care about?
   */
  function isEditable(el) {
    var tag = el.tagName.toLowerCase();

    // Skip elements inside the CMS editor, scripts, styles, nav internals
    if (el.closest('[data-cms-ignore]')) return false;
    if (el.closest('script,style,noscript,template')) return false;

    if (tag === 'img') {
      return !!el.getAttribute('src');
    }

    if (tag === 'a' || tag === 'button') {
      var txt = (el.textContent || '').trim();
      return txt.length > 0 && txt.length < 200;
    }

    // Text elements: must have direct text content (not just child elements)
    var hasDirectText = false;
    for (var i = 0; i < el.childNodes.length; i++) {
      var n = el.childNodes[i];
      if (n.nodeType === 3 && n.textContent.trim().length > 0) {
        hasDirectText = true;
        break;
      }
    }
    if (!hasDirectText) return false;

    var text = (el.textContent || '').trim();
    return text.length > 0 && text.length < 2000;
  }

  /**
   * Extract the current content payload from an element
   */
  function extractContent(el) {
    var tag = el.tagName.toLowerCase();
    if (tag === 'img') {
      return { src: el.getAttribute('src') || '', alt: el.getAttribute('alt') || '' };
    }
    if (tag === 'a') {
      return { text: (el.textContent || '').trim(), href: el.getAttribute('href') || '#' };
    }
    if (tag === 'button') {
      return { text: (el.textContent || '').trim() };
    }
    return { text: (el.textContent || '').trim() };
  }

  /**
   * Classify element for the editor UI
   */
  function classifyType(tag) {
    if (tag === 'img') return 'image';
    if (tag === 'a') return 'link';
    if (tag === 'button') return 'button';
    if (/^h[1-6]$/.test(tag)) return 'heading';
    if (tag === 'p' || tag === 'blockquote') return 'paragraph';
    return 'text';
  }

  /**
   * Walk the DOM, auto-assign IDs, return discovered elements
   */
  function discoverAll() {
    var nodes = document.body.querySelectorAll(SELECTOR);
    var discovered = [];
    var usedIds = Object.create(null);

    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (!isEditable(el)) continue;

      var id = el.getAttribute('data-cms-id');
      if (!id) {
        id = stableId(el);
        // Handle rare collisions
        var base = id, n = 1;
        while (usedIds[id]) { id = base + '-' + (n++); }
        el.setAttribute('data-cms-id', id);
      }
      usedIds[id] = true;

      var tag = el.tagName.toLowerCase();
      var content = extractContent(el);
      var label = content.text || content.alt || content.src || id;
      if (label.length > 50) label = label.substring(0, 50) + '…';

      discovered.push({
        id: id,
        tag: tag,
        type: classifyType(tag),
        label: label,
        content: content,
        path: window.location.pathname
      });
    }

    return discovered;
  }

  /**
   * Apply published content overrides
   */
  function applyOverrides(content) {
    if (!content) return;
    var map = content.elements ? content.elements : content;
    var applied = 0;

    var nodes = document.querySelectorAll('[data-cms-id]');
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var id = el.getAttribute('data-cms-id');
      var entry = map[id];
      if (!entry) continue;
      // For the public API, entries are pre-filtered by published=true
      var c = entry.content || entry;
      var tag = el.tagName.toLowerCase();

      if (tag === 'img') {
        if (c.src) el.src = c.src;
        if (c.alt !== undefined) el.alt = c.alt;
      } else if (tag === 'a') {
        if (c.text !== undefined && c.text !== null) el.textContent = c.text;
        if (c.href) el.setAttribute('href', c.href);
      } else if (tag === 'button') {
        if (c.text !== undefined && c.text !== null) el.textContent = c.text;
      } else if (c.text !== undefined && c.text !== null) {
        el.textContent = c.text;
      }
      applied++;
    }

    if (applied > 0) {
      console.log('[Monolith CMS] Applied ' + applied + ' content overrides');
    }
  }

  /**
   * Fetch published content with short-lived cache
   */
  function fetchContent() {
    try {
      var ts = parseInt(localStorage.getItem(CACHE_TS_KEY) || '0', 10);
      if (Date.now() - ts < CACHE_TTL) {
        var cached = localStorage.getItem(CACHE_KEY);
        if (cached) return Promise.resolve(JSON.parse(cached));
      }
    } catch (e) { /* ignore */ }

    return fetch(API_PUBLIC, { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        try {
          localStorage.setItem(CACHE_KEY, JSON.stringify(data));
          localStorage.setItem(CACHE_TS_KEY, String(Date.now()));
        } catch (e) { /* ignore */ }
        return data;
      })
      .catch(function () { return null; });
  }

  /**
   * Register discovered elements with the backend (fire-and-forget)
   */
  function registerDiscovered(elements) {
    if (!elements || elements.length === 0) return;
    try {
      fetch(API_REGISTER, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ path: window.location.pathname, elements: elements })
      }).catch(function () { /* silent */ });
    } catch (e) { /* silent */ }
  }

  /**
   * Boot sequence
   */
  function boot() {
    // 1. Auto-assign IDs and snapshot initial content
    var discovered = discoverAll();
    if (discovered.length > 0) {
      console.log('[Monolith CMS] Discovered ' + discovered.length + ' editable elements');
    }

    // 2. Fetch + apply overrides (and register new elements in parallel)
    fetchContent().then(function (content) { applyOverrides(content); });
    registerDiscovered(discovered);

    // Expose a tiny API for debugging / manual refresh
    window.MonolithCMS = {
      rediscover: function () {
        var d = discoverAll();
        registerDiscovered(d);
        return d;
      },
      refresh: function () {
        try {
          localStorage.removeItem(CACHE_KEY);
          localStorage.removeItem(CACHE_TS_KEY);
        } catch (e) {}
        return fetchContent().then(applyOverrides);
      }
    };

    window.dispatchEvent(new CustomEvent('monolith-cms-ready', { detail: { discovered: discovered.length } }));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
