"""Embedded admin UI — a single-page vanilla-JS application served by FastAPI.

Keeping this as an HTML string (rather than touching the React app) means the
installer never has to patch App.js or add a frontend route. The admin is
always available at ``/api/cms/admin`` on any Emergent website.
"""

ADMIN_HTML = r"""<!doctype html>
<html lang="en" data-cms-ignore>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Monolith CMS</title>
<style>
  :root {
    --bg: #0a0a0a; --panel: #111; --border: #222; --border-2: #2a2a2a;
    --text: #f5f5f5; --muted: #9a9a9a; --accent: #4edea3; --warn: #ffb84d;
    --radius: 10px; --mono: ui-monospace, 'SFMono-Regular', Menlo, monospace;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text);
    font-family: 'Figtree', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px; line-height: 1.5; -webkit-font-smoothing: antialiased; }
  a { color: var(--accent); }
  button { font-family: inherit; font-size: 13px; cursor: pointer; }
  input, textarea { font-family: inherit; font-size: 14px; }
  .btn { padding: 8px 14px; border-radius: 6px; border: 0; font-weight: 600; transition: transform 120ms ease, opacity 120ms ease; }
  .btn:hover { transform: translateY(-1px); }
  .btn:active { transform: translateY(0); }
  .btn:disabled { opacity: .6; cursor: not-allowed; }
  .btn-primary { background: var(--accent); color: #001a10; }
  .btn-warn { background: var(--warn); color: #2a1800; }
  .btn-ghost { background: var(--border); color: var(--text); }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); }
  .input { width: 100%; padding: 10px 12px; background: #050505; border: 1px solid var(--border-2); border-radius: 6px; color: var(--text); outline: none; }
  .input:focus { border-color: var(--accent); }
  .shell { min-height: 100vh; display: flex; flex-direction: column; }
  .auth-wrap { flex: 1; display: flex; align-items: center; justify-content: center; padding: 24px; }
  .auth-card { padding: 32px; width: 100%; max-width: 400px; }
  .auth-card h1 { margin: 0; font-size: 22px; }
  .auth-card p { margin: 4px 0 24px; color: var(--muted); font-size: 13px; }
  .auth-card .input { margin-bottom: 10px; }
  .auth-card .btn { width: 100%; padding: 12px; font-size: 14px; }
  header { display: flex; align-items: center; justify-content: space-between;
    padding: 14px 20px; border-bottom: 1px solid var(--border); background: #0c0c0c; position: sticky; top: 0; z-index: 10; backdrop-filter: blur(8px); }
  header h1 { margin: 0; font-size: 15px; font-weight: 700; letter-spacing: -.01em; }
  header .sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
  header .actions { display: flex; gap: 8px; align-items: center; }
  main { padding: 20px; max-width: 880px; width: 100%; margin: 0 auto; flex: 1; }
  .filters { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }
  .pill { padding: 5px 11px; border-radius: 999px; background: var(--border); color: var(--text); border: 0; font-size: 12px; font-weight: 600; }
  .pill.active { background: var(--accent); color: #001a10; }
  .el { padding: 14px 16px; margin-bottom: 10px; }
  .el-meta { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
  .el-info { min-width: 0; flex: 1; }
  .el-tag { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; font-family: var(--mono); }
  .el-label { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 2px; }
  .el-pub { padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; letter-spacing: .04em; border: 0; flex-shrink: 0; }
  .el-pub.published { background: var(--accent); color: #001a10; }
  .el-pub.draft { background: var(--border-2); color: var(--text); }
  .el-preview { color: #bdbdbd; font-size: 13.5px; margin-bottom: 10px; white-space: pre-wrap; word-break: break-word; }
  .el-preview.empty { color: var(--muted); font-style: italic; }
  .el-edit .input { margin-bottom: 8px; }
  .el-edit textarea { min-height: 90px; resize: vertical; }
  .el-actions { display: flex; gap: 8px; }
  .empty-state { text-align: center; padding: 48px 20px; }
  .empty-state p { color: var(--muted); max-width: 420px; margin: 8px auto; }
  .toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #0c0c0c; border: 1px solid var(--border); padding: 10px 18px; border-radius: 8px; font-size: 13px; box-shadow: 0 8px 24px rgba(0,0,0,.4); opacity: 0; transition: opacity 200ms ease; pointer-events: none; z-index: 100; }
  .toast.show { opacity: 1; }
  .toast.err { border-color: #ff5e5e; color: #ffb4b4; }
  @media (max-width: 640px) { main { padding: 14px; } header { padding: 12px 14px; } }
</style>
</head>
<body>
<div id="app" class="shell"></div>

<script>
(function () {
  'use strict';
  var API = '/api/cms';
  var root = document.getElementById('app');
  var state = {
    loading: true,
    setupRequired: false,
    authenticated: false,
    content: null,
    editingId: null,
    editValue: {},
    filter: 'all',
    updateInfo: null,
    updating: false,
  };

  function h(tag, attrs, children) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === 'style' && typeof attrs[k] === 'object') { Object.assign(el.style, attrs[k]); }
      else if (k.indexOf('on') === 0 && typeof attrs[k] === 'function') { el.addEventListener(k.slice(2).toLowerCase(), attrs[k]); }
      else if (k === 'class') { el.className = attrs[k]; }
      else if (k === 'html') { el.innerHTML = attrs[k]; }
      else if (attrs[k] !== undefined && attrs[k] !== null) { el.setAttribute(k, attrs[k]); }
    });
    (children || []).forEach(function (c) {
      if (c == null || c === false) return;
      el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return el;
  }

  function toast(msg, isError) {
    var t = h('div', { class: 'toast' + (isError ? ' err' : '') }, [msg]);
    document.body.appendChild(t);
    requestAnimationFrame(function () { t.classList.add('show'); });
    setTimeout(function () { t.classList.remove('show'); setTimeout(function () { t.remove(); }, 250); }, 2400);
  }

  function api(path, opts) {
    opts = opts || {};
    opts.headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
    opts.credentials = 'same-origin';
    return fetch(API + path, opts).then(function (r) {
      if (!r.ok && r.status !== 409) throw new Error('HTTP ' + r.status);
      return r.status === 204 ? null : r.json();
    });
  }

  function render() {
    var view;
    if (state.loading) view = h('div', { class: 'auth-wrap' }, [h('div', { class: 'card auth-card' }, ['Loading…'])]);
    else if (state.setupRequired) view = renderSetup();
    else if (!state.authenticated) view = renderLogin();
    else view = renderAdmin();
    root.replaceChildren(view);
  }

  // -------- Setup wizard --------
  function renderSetup() {
    var pw = '', pw2 = '';
    var card = h('form', { class: 'card auth-card', onsubmit: function (e) {
      e.preventDefault();
      if (pw.length < 8) return toast('Password must be at least 8 characters', true);
      if (pw !== pw2) return toast('Passwords do not match', true);
      api('/setup', { method: 'POST', body: JSON.stringify({ password: pw }) })
        .then(function () {
          state.setupRequired = false; state.authenticated = true; boot();
          toast('Admin created');
        })
        .catch(function () { toast('Setup failed', true); });
    }}, [
      h('h1', {}, ['Welcome']),
      h('p', {}, ['Create your admin password to finish setup.']),
      (function(){ var i = h('input', { class: 'input', type: 'password', placeholder: 'New password (min 8 chars)', autofocus: '' }); i.addEventListener('input', function(e){ pw = e.target.value; }); return i; })(),
      (function(){ var i = h('input', { class: 'input', type: 'password', placeholder: 'Repeat password' }); i.addEventListener('input', function(e){ pw2 = e.target.value; }); return i; })(),
      h('button', { class: 'btn btn-primary', type: 'submit' }, ['Create admin & continue']),
    ]);
    return h('div', { class: 'auth-wrap' }, [card]);
  }

  // -------- Login --------
  function renderLogin() {
    var pw = '';
    var card = h('form', { class: 'card auth-card', onsubmit: function (e) {
      e.preventDefault();
      api('/auth', { method: 'POST', body: JSON.stringify({ password: pw }) })
        .then(function () { state.authenticated = true; boot(); })
        .catch(function () { toast('Invalid password', true); });
    }}, [
      h('h1', {}, ['Monolith CMS']),
      h('p', {}, ['Embedded Edition']),
      (function(){ var i = h('input', { class: 'input', type: 'password', placeholder: 'Admin password', autofocus: '' }); i.addEventListener('input', function(e){ pw = e.target.value; }); return i; })(),
      h('button', { class: 'btn btn-primary', type: 'submit' }, ['Login']),
    ]);
    return h('div', { class: 'auth-wrap' }, [card]);
  }

  // -------- Admin --------
  function renderAdmin() {
    var elements = state.content && state.content.elements ? Object.values(state.content.elements) : [];
    var pages = Array.from(new Set(elements.map(function (e) { return e.page || '/'; }))).sort();
    var filtered = state.filter === 'all' ? elements : elements.filter(function (e) { return (e.page || '/') === state.filter; });

    var headerActions = [];
    if (state.updateInfo && state.updateInfo.update_available) {
      headerActions.push(h('button', { class: 'btn btn-warn', disabled: state.updating ? '' : null,
        onclick: function () {
          if (!confirm('Pull latest CMS version from GitHub?\nYour content is untouched.')) return;
          state.updating = true; render();
          api('/update', { method: 'POST' }).then(function (d) {
            toast('Updated ' + d.updated + '/' + d.total + ' files. Restart backend.');
            state.updating = false; checkUpdate();
          }).catch(function () { state.updating = false; render(); toast('Update failed', true); });
        }
      }, [state.updating ? 'Updating…' : 'Update CMS']));
    }
    headerActions.push(h('button', { class: 'btn btn-ghost', onclick: function(){ loadContent(); }}, ['Refresh']));
    headerActions.push(h('button', { class: 'btn btn-ghost', onclick: function(){
      api('/auth', { method: 'DELETE' }).then(function(){ state.authenticated = false; render(); });
    }}, ['Logout']));
    headerActions.push(h('a', { class: 'btn btn-primary', href: '/', style: 'text-decoration:none;display:inline-flex;align-items:center;' }, ['View site →']));

    var header = h('header', {}, [
      h('div', {}, [
        h('h1', {}, ['Monolith CMS']),
        h('div', { class: 'sub' }, [elements.length + ' elements auto-discovered']),
      ]),
      h('div', { class: 'actions' }, headerActions),
    ]);

    var main = h('main', {}, []);

    if (pages.length > 1) {
      var filters = h('div', { class: 'filters' }, []);
      filters.appendChild(h('button', { class: 'pill' + (state.filter === 'all' ? ' active' : ''), onclick: function(){ state.filter = 'all'; render(); } }, ['All (' + elements.length + ')']));
      pages.forEach(function (p) {
        var count = elements.filter(function (e) { return (e.page || '/') === p; }).length;
        filters.appendChild(h('button', { class: 'pill' + (state.filter === p ? ' active' : ''), onclick: function(){ state.filter = p; render(); } }, [p + ' (' + count + ')']));
      });
      main.appendChild(filters);
    }

    if (elements.length === 0) {
      main.appendChild(h('div', { class: 'card empty-state' }, [
        h('h2', {}, ['No content yet']),
        h('p', {}, ['Visit any page on your site — the CMS auto-discovers editable elements on load.']),
      ]));
    } else {
      filtered.forEach(function (el) { main.appendChild(renderElement(el)); });
    }

    return h('div', { class: 'shell' }, [header, main]);
  }

  function renderElement(el) {
    var card = h('div', { class: 'card el' }, []);
    var meta = h('div', { class: 'el-meta' }, [
      h('div', { class: 'el-info' }, [
        h('div', { class: 'el-tag' }, [(el.tag || '') + ' · ' + (el.type || '') + ' · ' + (el.page || '/')]),
        h('div', { class: 'el-label' }, [el.label || el.id]),
      ]),
      h('button', { class: 'el-pub ' + (el.published ? 'published' : 'draft'), onclick: function () {
        api('/content', { method: 'PATCH', body: JSON.stringify({ id: el.id, published: !el.published }) }).then(loadContent);
      }}, [el.published ? 'PUBLISHED' : 'DRAFT']),
    ]);
    card.appendChild(meta);

    if (state.editingId === el.id) {
      card.appendChild(renderEditor(el));
    } else {
      var previewText;
      if (el.type === 'image') previewText = (el.content && el.content.src) || '(no image)';
      else previewText = (el.content && el.content.text) || '(empty)';
      var hasText = !!(el.content && (el.content.text || el.content.src));
      card.appendChild(h('div', { class: 'el-preview' + (hasText ? '' : ' empty') }, [previewText]));
      card.appendChild(h('div', { class: 'el-actions' }, [
        h('button', { class: 'btn btn-ghost', onclick: function () {
          state.editingId = el.id;
          state.editValue = Object.assign({}, el.content || {});
          render();
        }}, ['Edit']),
      ]));
    }
    return card;
  }

  function renderEditor(el) {
    var wrap = h('div', { class: 'el-edit' }, []);
    function field(key, placeholder, multiline) {
      var tag = multiline ? 'textarea' : 'input';
      var node = h(tag, { class: 'input', placeholder: placeholder });
      node.value = state.editValue[key] || '';
      node.addEventListener('input', function (e) { state.editValue[key] = e.target.value; });
      return node;
    }
    if (el.type === 'image') {
      wrap.appendChild(field('src', 'Image URL'));
      wrap.appendChild(field('alt', 'Alt text'));
    } else if (el.type === 'link') {
      wrap.appendChild(field('text', 'Link text'));
      wrap.appendChild(field('href', 'https://…'));
    } else if (el.type === 'button') {
      wrap.appendChild(field('text', 'Button label'));
    } else {
      wrap.appendChild(field('text', 'Content', true));
    }
    wrap.appendChild(h('div', { class: 'el-actions' }, [
      h('button', { class: 'btn btn-primary', onclick: function () {
        api('/content', { method: 'PATCH', body: JSON.stringify({ id: el.id, content: state.editValue, published: true }) })
          .then(function () { state.editingId = null; state.editValue = {}; loadContent(); toast('Saved'); })
          .catch(function () { toast('Save failed', true); });
      }}, ['Save']),
      h('button', { class: 'btn btn-ghost', onclick: function () { state.editingId = null; render(); }}, ['Cancel']),
    ]));
    return wrap;
  }

  // -------- Data loading --------
  function loadContent() {
    api('/content').then(function (d) { state.content = d; render(); }).catch(function () {});
  }
  function checkUpdate() {
    api('/update').then(function (d) { state.updateInfo = d; render(); }).catch(function () {});
  }

  function boot() {
    api('/setup').then(function (s) {
      if (s.setupRequired) { state.setupRequired = true; state.loading = false; render(); return; }
      return api('/auth').then(function (a) {
        state.authenticated = !!a.authenticated;
        state.loading = false;
        if (state.authenticated) { loadContent(); checkUpdate(); }
        else render();
      });
    }).catch(function () { state.loading = false; render(); });
  }

  render();
  boot();
})();
</script>
</body>
</html>
"""
