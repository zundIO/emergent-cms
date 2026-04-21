"""Embedded admin UI — sidebar + content layout, served by FastAPI.

Keeping this as a single HTML/vanilla-JS file (rather than touching the host
React app) means the installer never has to patch App.js or introduce a
frontend route.  The admin is always available at ``/api/cms/admin``.
"""

ADMIN_HTML = r"""<!doctype html>
<html lang="en" data-cms-ignore>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Monolith CMS</title>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
<style>
  :root {
    --bg-0:#07090a;
    --bg-1:#0c0f11;
    --bg-2:#12161a;
    --bg-3:#191e23;
    --border:#1f262c;
    --border-strong:#2a323a;
    --text:#ecf1f4;
    --muted:#7b8794;
    --muted-2:#9aa5ad;
    --accent:#4edea3;
    --accent-700:#2bb98b;
    --warn:#ffb84d;
    --danger:#ff5a5a;
    --radius:10px;
    --radius-sm:6px;
    --mono:ui-monospace, 'SFMono-Regular', Menlo, monospace;
    --shadow: 0 1px 0 rgba(255,255,255,.02) inset, 0 8px 24px rgba(0,0,0,.35);
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--bg-0);color:var(--text);font-family:'Figtree',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased}
  ::selection{background:rgba(78,222,163,.35)}
  button,input,textarea{font-family:inherit}
  a{color:inherit;text-decoration:none}

  /* Buttons */
  .btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:7px 12px;border-radius:var(--radius-sm);border:1px solid transparent;font-weight:600;font-size:12.5px;cursor:pointer;transition:background-color .15s ease,border-color .15s ease,transform .12s ease;white-space:nowrap}
  .btn:active{transform:translateY(1px)}
  .btn-primary{background:var(--accent);color:#001a10}
  .btn-primary:hover{background:var(--accent-700)}
  .btn-warn{background:var(--warn);color:#2a1800}
  .btn-ghost{background:var(--bg-3);color:var(--text);border-color:var(--border)}
  .btn-ghost:hover{background:var(--border-strong)}
  .btn-danger{background:transparent;color:var(--danger);border-color:var(--border)}
  .btn-danger:hover{background:rgba(255,90,90,.08);border-color:var(--danger)}
  .btn:disabled{opacity:.55;cursor:not-allowed;transform:none}

  .input{width:100%;padding:10px 12px;background:var(--bg-0);border:1px solid var(--border-strong);border-radius:var(--radius-sm);color:var(--text);outline:none;transition:border-color .15s ease,box-shadow .15s ease}
  .input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(78,222,163,.15)}
  textarea.input{resize:vertical;min-height:96px;font-family:inherit}

  /* Auth screens */
  .auth-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
  .auth-card{background:var(--bg-1);border:1px solid var(--border);border-radius:14px;padding:36px 32px;width:100%;max-width:400px;box-shadow:var(--shadow)}
  .auth-card h1{margin:0;font-size:22px;font-weight:800;letter-spacing:-.01em}
  .auth-card .sub{margin:4px 0 24px;color:var(--muted-2);font-size:13px}
  .auth-card .input{margin-bottom:10px}
  .auth-card .btn{width:100%;padding:12px;font-size:14px;margin-top:4px}

  /* App shell */
  .shell{display:grid;grid-template-columns:240px 1fr;grid-template-rows:56px 1fr;min-height:100vh}
  .topbar{grid-column:1 / -1;display:flex;align-items:center;justify-content:space-between;padding:0 16px;border-bottom:1px solid var(--border);background:rgba(12,15,17,.78);backdrop-filter:blur(10px);position:sticky;top:0;z-index:20}
  .brand{display:flex;align-items:center;gap:10px}
  .brand-badge{width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,var(--accent),#2bb98b);display:flex;align-items:center;justify-content:center;font-weight:800;color:#001a10;font-size:13px}
  .brand h1{margin:0;font-size:14px;font-weight:700}
  .brand .sub{color:var(--muted);font-size:11.5px;margin-top:1px}
  .topbar-actions{display:flex;align-items:center;gap:8px}

  /* Sidebar */
  .sidebar{border-right:1px solid var(--border);background:var(--bg-1);overflow-y:auto;padding:14px 10px;display:flex;flex-direction:column;gap:4px}
  .side-section{margin-top:10px;padding:6px 10px 4px;color:var(--muted);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;font-weight:700}
  .side-section:first-child{margin-top:0}
  .side-item{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px 10px;border-radius:7px;cursor:pointer;color:var(--muted-2);font-size:13px;transition:background-color .12s ease,color .12s ease;user-select:none}
  .side-item:hover{background:var(--bg-2);color:var(--text)}
  .side-item.active{background:var(--bg-3);color:var(--text);font-weight:600;box-shadow:inset 2px 0 0 var(--accent)}
  .side-item .name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .side-item .count{font-family:var(--mono);font-size:11px;color:var(--muted);background:var(--bg-0);padding:1px 7px;border-radius:999px;flex-shrink:0}
  .side-item.active .count{background:var(--bg-1);color:var(--text)}

  /* Main content */
  .main{overflow-y:auto;padding:22px 26px 40px;max-width:900px;width:100%;justify-self:start}
  .main-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin-bottom:18px}
  .main-title{margin:0;font-size:17px;font-weight:700;font-family:var(--mono);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .main-subtitle{color:var(--muted);font-size:12.5px}

  /* Element cards */
  .el-card{background:var(--bg-1);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;margin-bottom:10px;transition:border-color .15s ease}
  .el-card:hover{border-color:var(--border-strong)}
  .el-head{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:8px}
  .el-meta{color:var(--muted);font-size:10.5px;font-family:var(--mono);text-transform:uppercase;letter-spacing:.08em}
  .el-label{font-weight:600;font-size:14px;margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .badge{padding:3px 8px;border-radius:4px;font-size:10px;font-weight:800;letter-spacing:.04em;flex-shrink:0;border:0;cursor:pointer;font-family:var(--mono)}
  .badge.published{background:var(--accent);color:#001a10}
  .badge.draft{background:var(--bg-3);color:var(--muted-2)}
  .el-preview{color:#c3cbd1;font-size:13.5px;margin-bottom:10px;white-space:pre-wrap;word-break:break-word;line-height:1.55}
  .el-preview.empty{color:var(--muted);font-style:italic}
  .el-actions{display:flex;gap:8px}
  .el-edit .input{margin-bottom:8px}

  /* Empty / loading */
  .empty{display:flex;flex-direction:column;align-items:center;text-align:center;padding:56px 24px;background:var(--bg-1);border:1px dashed var(--border-strong);border-radius:12px}
  .empty h2{margin:0 0 6px;font-size:16px}
  .empty p{color:var(--muted);margin:0 0 18px;max-width:440px;font-size:13px}

  /* Toast */
  .toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--bg-2);border:1px solid var(--border-strong);padding:10px 16px;border-radius:8px;font-size:13px;box-shadow:0 8px 24px rgba(0,0,0,.4);opacity:0;transition:opacity .2s ease;pointer-events:none;z-index:100}
  .toast.show{opacity:1}
  .toast.err{border-color:var(--danger);color:#ffbcbc}
  .toast.ok{border-color:var(--accent);color:#b9f3d9}

  /* Small screens */
  @media (max-width:720px){
    .shell{grid-template-columns:1fr;grid-template-rows:56px auto 1fr}
    .sidebar{border-right:0;border-bottom:1px solid var(--border);max-height:190px;flex-direction:row;overflow-x:auto;padding:10px}
    .sidebar .side-section{display:none}
    .side-item{flex-shrink:0}
    .main{padding:16px}
  }
</style>
</head>
<body>
<div id="app"></div>
<script>
(function(){
  'use strict';
  var API='/api/cms';
  var root=document.getElementById('app');
  var state={
    loading:true,setupRequired:false,authenticated:false,
    content:null,editingId:null,editValue:{},
    filter:'all',updateInfo:null,updating:false,
    scanning:false,resetting:false
  };

  // DOM helper
  function h(tag,attrs,children){
    var el=document.createElement(tag);
    if(attrs){
      Object.keys(attrs).forEach(function(k){
        if(k==='style'&&typeof attrs[k]==='object'){Object.assign(el.style,attrs[k])}
        else if(k.indexOf('on')===0&&typeof attrs[k]==='function'){el.addEventListener(k.slice(2).toLowerCase(),attrs[k])}
        else if(k==='class'){el.className=attrs[k]}
        else if(k==='html'){el.innerHTML=attrs[k]}
        else if(attrs[k]!==undefined&&attrs[k]!==null){el.setAttribute(k,attrs[k])}
      });
    }
    (children||[]).forEach(function(c){
      if(c==null||c===false)return;
      el.appendChild(typeof c==='string'?document.createTextNode(c):c);
    });
    return el;
  }

  function toast(msg,kind){
    var t=h('div',{class:'toast '+(kind||'ok')},[msg]);
    document.body.appendChild(t);
    requestAnimationFrame(function(){t.classList.add('show')});
    setTimeout(function(){t.classList.remove('show');setTimeout(function(){t.remove()},250)},2600);
  }

  function api(path,opts){
    opts=opts||{};
    opts.headers=Object.assign({'Content-Type':'application/json'},opts.headers||{});
    opts.credentials='same-origin';
    return fetch(API+path,opts).then(function(r){
      if(!r.ok&&r.status!==409)throw new Error('HTTP '+r.status);
      return r.status===204?null:r.json();
    });
  }

  function render(){
    var view;
    if(state.loading)view=h('div',{class:'auth-wrap'},[h('div',{class:'auth-card'},['Loading…'])]);
    else if(state.setupRequired)view=renderSetup();
    else if(!state.authenticated)view=renderLogin();
    else view=renderApp();
    root.replaceChildren(view);
  }

  // ---------- Setup ----------
  function renderSetup(){
    var pw='',pw2='';
    var card=h('form',{class:'auth-card',onsubmit:function(e){
      e.preventDefault();
      if(pw.length<8)return toast('Password must be at least 8 characters','err');
      if(pw!==pw2)return toast('Passwords do not match','err');
      api('/setup',{method:'POST',body:JSON.stringify({password:pw})})
        .then(function(){state.setupRequired=false;state.authenticated=true;boot();toast('Admin created')})
        .catch(function(){toast('Setup failed','err')});
    }},[
      h('h1',{},['Welcome to Monolith CMS']),
      h('p',{class:'sub'},['Create your admin password to finish setup.']),
      (function(){var i=h('input',{class:'input',type:'password',placeholder:'New password (min 8 chars)',autofocus:''});i.addEventListener('input',function(e){pw=e.target.value});return i})(),
      (function(){var i=h('input',{class:'input',type:'password',placeholder:'Repeat password'});i.addEventListener('input',function(e){pw2=e.target.value});return i})(),
      h('button',{class:'btn btn-primary',type:'submit'},['Create admin & continue'])
    ]);
    return h('div',{class:'auth-wrap'},[card]);
  }

  // ---------- Login ----------
  function renderLogin(){
    var pw='';
    var card=h('form',{class:'auth-card',onsubmit:function(e){
      e.preventDefault();
      api('/auth',{method:'POST',body:JSON.stringify({password:pw})})
        .then(function(){state.authenticated=true;boot()})
        .catch(function(){toast('Invalid password','err')});
    }},[
      h('h1',{},['Monolith CMS']),
      h('p',{class:'sub'},['Enter admin password to continue.']),
      (function(){var i=h('input',{class:'input',type:'password',placeholder:'Admin password',autofocus:''});i.addEventListener('input',function(e){pw=e.target.value});return i})(),
      h('button',{class:'btn btn-primary',type:'submit'},['Login'])
    ]);
    return h('div',{class:'auth-wrap'},[card]);
  }

  // ---------- Main app (sidebar + main) ----------
  function renderApp(){
    var elements=state.content&&state.content.elements?Object.values(state.content.elements):[];
    var byPage={};
    elements.forEach(function(el){var p=el.page||'/';(byPage[p]=byPage[p]||[]).push(el)});

    // Group pages by section
    var pagesList=Object.keys(byPage).sort();
    var groups={Pages:[],Components:[],Other:[]};
    pagesList.forEach(function(p){
      if(p==='/'||p==='all')groups.Other.push(p);
      else if(p.indexOf('pages/')===0)groups.Pages.push(p);
      else if(p.indexOf('components/')===0)groups.Components.push(p);
      else groups.Other.push(p);
    });

    var filtered=state.filter==='all'?elements:(byPage[state.filter]||[]);

    return h('div',{class:'shell'},[renderTopbar(elements.length),renderSidebar(elements.length,groups,byPage),renderMain(filtered,elements.length)]);
  }

  function renderTopbar(total){
    var actions=[];
    if(state.updateInfo&&state.updateInfo.update_available){
      actions.push(h('button',{class:'btn btn-warn',disabled:state.updating?'':null,onclick:function(){
        if(!confirm('Pull latest CMS version from GitHub?\nYour content is untouched.'))return;
        state.updating=true;render();
        api('/update',{method:'POST'}).then(function(d){
          toast('Updated '+d.updated+'/'+d.total+' files. Restart backend.');
          state.updating=false;checkUpdate();
        }).catch(function(){state.updating=false;render();toast('Update failed','err')});
      }},[state.updating?'Updating…':'Update CMS']));
    }
    actions.push(h('button',{class:'btn btn-primary',disabled:state.scanning?'':null,onclick:function(){
      if(!confirm('Scan your frontend/src for editable elements?\nThis injects data-cms-id attributes into pages/ and components/ (skips components/ui/).'))return;
      state.scanning=true;render();
      api('/scan',{method:'POST'}).then(function(d){
        state.scanning=false;
        if(d.success)toast('Scanned '+d.discovered+' elements • '+(d.new||0)+' new');
        else toast('Scan failed: '+(d.error||'unknown'),'err');
        loadContent();
      }).catch(function(){state.scanning=false;render();toast('Scan failed','err')});
    }},[state.scanning?'Scanning…':'Scan source']));
    actions.push(h('button',{class:'btn btn-danger',disabled:state.resetting?'':null,onclick:function(){
      if(!confirm('RESET everything?\n• Delete all registered elements\n• Remove data-cms-id attributes from source files\n\nAdmin password is kept. This cannot be undone.'))return;
      state.resetting=true;render();
      api('/reset',{method:'POST'}).then(function(d){
        state.resetting=false;
        toast('Reset done • '+(d.undo?d.undo.attributes_removed:0)+' attributes cleaned');
        state.filter='all';
        loadContent();
      }).catch(function(){state.resetting=false;render();toast('Reset failed','err')});
    }},[state.resetting?'Resetting…':'Reset']));
    actions.push(h('button',{class:'btn btn-ghost',onclick:function(){loadContent()}},['Refresh']));
    actions.push(h('button',{class:'btn btn-ghost',onclick:function(){
      api('/auth',{method:'DELETE'}).then(function(){state.authenticated=false;render()});
    }},['Logout']));
    actions.push(h('a',{class:'btn btn-ghost',href:'/',target:'_blank',rel:'noopener'},['View site ↗']));

    return h('div',{class:'topbar'},[
      h('div',{class:'brand'},[
        h('div',{class:'brand-badge'},['M']),
        h('div',{},[
          h('h1',{},['Monolith CMS']),
          h('div',{class:'sub'},[total+' elements auto-discovered'])
        ])
      ]),
      h('div',{class:'topbar-actions'},actions)
    ]);
  }

  function renderSidebar(total,groups,byPage){
    var side=h('aside',{class:'sidebar'},[]);

    // "All" row
    var allItem=h('div',{class:'side-item'+(state.filter==='all'?' active':''),onclick:function(){state.filter='all';render()}},[
      h('span',{class:'name'},['All content']),
      h('span',{class:'count'},[String(total)])
    ]);
    side.appendChild(allItem);

    ['Pages','Components','Other'].forEach(function(groupName){
      var paths=groups[groupName];
      if(!paths||paths.length===0)return;
      side.appendChild(h('div',{class:'side-section'},[groupName]));
      paths.forEach(function(p){
        var nice=p.replace(/^pages\//,'').replace(/^components\//,'').replace(/\.(jsx?|tsx?)$/,'');
        var itm=h('div',{class:'side-item'+(state.filter===p?' active':''),title:p,onclick:function(){state.filter=p;render()}},[
          h('span',{class:'name'},[nice||p]),
          h('span',{class:'count'},[String((byPage[p]||[]).length)])
        ]);
        side.appendChild(itm);
      });
    });
    return side;
  }

  function renderMain(list,total){
    var main=h('main',{class:'main'},[]);
    var titleText=state.filter==='all'?'All content':state.filter;
    main.appendChild(h('div',{class:'main-head'},[
      h('h2',{class:'main-title'},[titleText]),
      h('div',{class:'main-subtitle'},[list.length+(list.length===1?' element':' elements')])
    ]));

    if(total===0){
      main.appendChild(h('div',{class:'empty'},[
        h('h2',{},['No content yet']),
        h('p',{},['Click "Scan source" in the top bar to discover editable elements in your frontend code. The scanner skips UI library internals (components/ui/) and icon names.']),
        h('button',{class:'btn btn-primary',disabled:state.scanning?'':null,onclick:function(){
          if(!confirm('Scan frontend/src now?'))return;
          state.scanning=true;render();
          api('/scan',{method:'POST'}).then(function(d){
            state.scanning=false;
            if(d.success)toast('Scanned '+d.discovered+' elements');
            loadContent();
          }).catch(function(){state.scanning=false;render();toast('Scan failed','err')});
        }},[state.scanning?'Scanning…':'Scan source now']),
      ]));
      return main;
    }

    if(list.length===0){
      main.appendChild(h('div',{class:'empty'},[
        h('h2',{},['Nothing on this page']),
        h('p',{},['Switch to another page in the sidebar.']),
      ]));
      return main;
    }

    list.forEach(function(el){main.appendChild(renderElement(el))});
    return main;
  }

  function renderElement(el){
    var card=h('div',{class:'el-card'},[]);
    var metaText=(el.tag||'').toUpperCase()+' · '+(el.type||'').toUpperCase()+' · '+(el.page||'/');
    card.appendChild(h('div',{class:'el-head'},[
      h('div',{class:'el-info'},[
        h('div',{class:'el-meta'},[metaText]),
        h('div',{class:'el-label'},[el.label||el.id])
      ]),
      h('button',{class:'badge '+(el.published?'published':'draft'),title:'Toggle publish',onclick:function(){
        api('/content',{method:'PATCH',body:JSON.stringify({id:el.id,published:!el.published})}).then(loadContent);
      }},[el.published?'PUBLISHED':'DRAFT'])
    ]));

    if(state.editingId===el.id){
      card.appendChild(renderEditor(el));
    }else{
      var prev=el.type==='image'?((el.content&&el.content.src)||'(no image)'):((el.content&&el.content.text)||'(empty)');
      var has=!!(el.content&&(el.content.text||el.content.src));
      card.appendChild(h('div',{class:'el-preview'+(has?'':' empty')},[prev]));
      card.appendChild(h('div',{class:'el-actions'},[
        h('button',{class:'btn btn-ghost',onclick:function(){
          state.editingId=el.id;
          state.editValue=Object.assign({},el.content||{});
          render();
        }},['Edit'])
      ]));
    }
    return card;
  }

  function renderEditor(el){
    var wrap=h('div',{class:'el-edit'},[]);
    function field(key,ph,multi){
      var tag=multi?'textarea':'input';
      var n=h(tag,{class:'input',placeholder:ph});
      n.value=state.editValue[key]||'';
      n.addEventListener('input',function(e){state.editValue[key]=e.target.value});
      return n;
    }
    if(el.type==='image'){wrap.appendChild(field('src','Image URL'));wrap.appendChild(field('alt','Alt text'))}
    else if(el.type==='link'){wrap.appendChild(field('text','Link text'));wrap.appendChild(field('href','https://…'))}
    else if(el.type==='button'){wrap.appendChild(field('text','Button label'))}
    else{wrap.appendChild(field('text','Content',true))}
    wrap.appendChild(h('div',{class:'el-actions'},[
      h('button',{class:'btn btn-primary',onclick:function(){
        api('/content',{method:'PATCH',body:JSON.stringify({id:el.id,content:state.editValue,published:true})})
          .then(function(){state.editingId=null;state.editValue={};loadContent();toast('Saved')})
          .catch(function(){toast('Save failed','err')});
      }},['Save & publish']),
      h('button',{class:'btn btn-ghost',onclick:function(){state.editingId=null;render()}},['Cancel'])
    ]));
    return wrap;
  }

  // ---------- Data ----------
  function loadContent(){api('/content').then(function(d){state.content=d;render()}).catch(function(){})}
  function checkUpdate(){api('/update').then(function(d){state.updateInfo=d;render()}).catch(function(){})}
  function boot(){
    api('/setup').then(function(s){
      if(s.setupRequired){state.setupRequired=true;state.loading=false;render();return}
      return api('/auth').then(function(a){
        state.authenticated=!!a.authenticated;state.loading=false;
        if(state.authenticated){loadContent();checkUpdate()}else render();
      });
    }).catch(function(){state.loading=false;render()});
  }

  render();boot();
})();
</script>
</body>
</html>
"""
