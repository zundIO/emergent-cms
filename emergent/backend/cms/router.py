"""FastAPI routes for the embedded Monolith CMS.

Mount with::

    from cms.router import router as cms_router
    app.include_router(cms_router)

All endpoints are prefixed with ``/api/cms`` so they automatically match the
Emergent Kubernetes ingress (``/api/*`` routes to the backend).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from . import auth, storage
from .admin_html import ADMIN_HTML
from .scanner import scan_and_patch

router = APIRouter(prefix="/api/cms", tags=["cms"])

GITHUB_REPO = "zundIO/emergent-cms"
GITHUB_BRANCH = "main"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"

# Mapping: remote path in repo -> local target path relative to project root.
# NEVER includes cms-data/ or .cms-env.json -> secrets + content stay intact.
UPDATE_TARGETS: List[Dict[str, str]] = [
    {"remote": "emergent/backend/cms/__init__.py",    "local": "backend/cms/__init__.py"},
    {"remote": "emergent/backend/cms/router.py",      "local": "backend/cms/router.py"},
    {"remote": "emergent/backend/cms/storage.py",     "local": "backend/cms/storage.py"},
    {"remote": "emergent/backend/cms/auth.py",        "local": "backend/cms/auth.py"},
    {"remote": "emergent/backend/cms/admin_html.py",  "local": "backend/cms/admin_html.py"},
    {"remote": "emergent/backend/cms/scanner.py",     "local": "backend/cms/scanner.py"},
    {"remote": "public/cms-client.js",                "local": "frontend/public/cms-client.js"},
]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SetupBody(BaseModel):
    password: str = Field(..., min_length=8, max_length=200)


class LoginBody(BaseModel):
    password: str


class RegisterElement(BaseModel):
    id: str
    tag: str
    type: str
    label: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    page: Optional[str] = None


class RegisterBody(BaseModel):
    path: Optional[str] = "/"
    elements: List[RegisterElement] = Field(default_factory=list)


class ContentPatchBody(BaseModel):
    id: str
    content: Optional[Dict[str, Any]] = None
    published: Optional[bool] = None


def _require_auth(request: Request) -> None:
    if not auth.is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------------------
# Admin HTML (single-page app served directly by FastAPI)
# ---------------------------------------------------------------------------

@router.get("/admin", response_class=HTMLResponse)
async def admin_page() -> HTMLResponse:
    return HTMLResponse(ADMIN_HTML)


# ---------------------------------------------------------------------------
# Setup wizard
# ---------------------------------------------------------------------------

@router.get("/setup")
async def setup_status() -> Dict[str, bool]:
    return {"setupRequired": not auth.is_setup_complete()}


@router.post("/setup")
async def setup_create(body: SetupBody, response: Response) -> Dict[str, Any]:
    if auth.is_setup_complete():
        raise HTTPException(status_code=409, detail="Setup already completed")
    auth.save_admin_password(body.password)
    token = auth.create_token()
    response.set_cookie(
        key=auth.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * auth.SESSION_DAYS,
        path="/",
    )
    # Auto-run the source-code scan so the admin immediately shows all
    # editable elements without anyone visiting the site first.
    try:
        scan_result = scan_and_patch(inject=True)
    except Exception as exc:  # noqa: BLE001
        scan_result = {"success": False, "error": str(exc)}
    return {"success": True, "scan": scan_result}


# ---------------------------------------------------------------------------
# Source-code scanner
# ---------------------------------------------------------------------------

@router.post("/scan")
async def scan_source(request: Request) -> Dict[str, Any]:
    """Admin-triggered rescan of frontend/src for editable elements."""
    _require_auth(request)
    return scan_and_patch(inject=True)


@router.get("/scan")
async def scan_preview(request: Request) -> Dict[str, Any]:
    """Dry-run scan (no file modifications) — useful for previewing."""
    _require_auth(request)
    return scan_and_patch(inject=False)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@router.get("/auth")
async def auth_status(request: Request) -> Dict[str, Any]:
    return {"authenticated": auth.is_authenticated(request)}


@router.post("/auth")
async def auth_login(body: LoginBody, response: Response) -> Dict[str, Any]:
    if not auth.is_setup_complete():
        raise HTTPException(status_code=409, detail="Setup required")
    if not auth.verify_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    token = auth.create_token()
    response.set_cookie(
        key=auth.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * auth.SESSION_DAYS,
        path="/",
    )
    return {"success": True}


@router.delete("/auth")
async def auth_logout(response: Response) -> Dict[str, bool]:
    response.delete_cookie(auth.COOKIE_NAME, path="/")
    return {"success": True}


# ---------------------------------------------------------------------------
# Public content (no auth)
# ---------------------------------------------------------------------------

@router.get("/public")
async def public_content() -> JSONResponse:
    payload = {"elements": storage.get_published()}
    return JSONResponse(
        payload,
        headers={
            "Cache-Control": "public, max-age=30, stale-while-revalidate=120",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ---------------------------------------------------------------------------
# Auto-discovery registration (no auth; only ADDS metadata, never overwrites)
# ---------------------------------------------------------------------------

@router.post("/register")
async def register_elements(body: RegisterBody) -> Dict[str, Any]:
    tagged = []
    for el in body.elements:
        data = el.model_dump()
        data["page"] = data.get("page") or body.path or "/"
        tagged.append(data)
    result = storage.merge_elements(tagged)
    return {"success": True, "received": len(tagged), **result}


# ---------------------------------------------------------------------------
# Content management (auth required)
# ---------------------------------------------------------------------------

@router.get("/content")
async def get_all_content(request: Request) -> Dict[str, Any]:
    _require_auth(request)
    return storage.get_content()


@router.patch("/content")
async def patch_content(body: ContentPatchBody, request: Request) -> Dict[str, Any]:
    _require_auth(request)
    patch: Dict[str, Any] = {}
    if body.content is not None:
        patch["content"] = body.content
    if body.published is not None:
        patch["published"] = body.published
    if not patch:
        raise HTTPException(status_code=400, detail="Nothing to update")
    result = storage.update_element(body.id, patch)
    return {"success": True, "version": result["version"]}


# ---------------------------------------------------------------------------
# Self-update (pull latest CMS files from GitHub)
# ---------------------------------------------------------------------------

async def _get_remote_sha() -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                f"{GITHUB_API}/commits/{GITHUB_BRANCH}",
                headers={"User-Agent": "monolith-cms", "Accept": "application/vnd.github+json"},
            )
            if r.status_code == 200:
                return r.json().get("sha")
    except Exception:
        return None
    return None


@router.get("/update")
async def update_status(request: Request) -> Dict[str, Any]:
    _require_auth(request)
    local = storage.read_local_version()
    remote = await _get_remote_sha()
    return {
        "local_sha": local.get("sha"),
        "remote_sha": remote,
        "updated_at": local.get("updated_at"),
        "update_available": bool(remote and local.get("sha") != remote),
        "repo": f"https://github.com/{GITHUB_REPO}",
    }


@router.post("/update")
async def run_update(request: Request) -> Dict[str, Any]:
    _require_auth(request)
    root = Path.cwd().parent if (Path.cwd() / "server.py").exists() else Path.cwd()
    results = []
    succeeded = 0
    async with httpx.AsyncClient(timeout=15.0) as client:
        for t in UPDATE_TARGETS:
            try:
                r = await client.get(f"{GITHUB_RAW}/{t['remote']}", headers={"User-Agent": "monolith-cms"})
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}")
                target_path = root / t["local"]
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(r.text)
                results.append({"file": t["local"], "ok": True})
                succeeded += 1
            except Exception as exc:  # noqa: BLE001
                results.append({"file": t["local"], "ok": False, "error": str(exc)})
    remote_sha = await _get_remote_sha()
    if remote_sha:
        storage.write_local_version(remote_sha)
    return {
        "success": succeeded == len(UPDATE_TARGETS),
        "updated": succeeded,
        "total": len(UPDATE_TARGETS),
        "new_sha": remote_sha,
        "results": results,
        "note": "Restart the backend (supervisorctl restart backend) to load new server-side code.",
    }
