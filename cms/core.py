"""
The Monolith CMS - Pluggable Core
Exposes install_cms(app, ...) for mounting into any FastAPI application.
"""
import os
import copy
import json
import re
import subprocess
import threading
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient, DESCENDING
from bson import ObjectId
import jwt
import bcrypt

# ============================================================
# CONFIGURATION - Set at install time via install_cms()
# ============================================================

_config = {
    "mongo_client": None,
    "db": None,
    "users_col": None,
    "pages_col": None,
    "projects_col": None,
    "page_versions_col": None,
    "jwt_secret": "monolith-cms-default-secret-change-me",
    "jwt_algorithm": "HS256",
    "jwt_expiry_hours": 24,
    "admin_email": "admin@monolith.cms",
    "admin_password": "admin123",
}


def _db():
    return _config["db"]


def users_col():
    return _config["users_col"]


def pages_col():
    return _config["pages_col"]


def projects_col():
    return _config["projects_col"]


def page_versions_col():
    return _config["page_versions_col"]


router = APIRouter()


# ============================================================
# HELPERS
# ============================================================

def serialize_doc(doc):
    if doc is None:
        return None
    result = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, list):
            result[k] = [serialize_doc(i) if isinstance(i, dict) else str(i) if isinstance(i, ObjectId) else i for i in v]
        elif isinstance(v, dict):
            result[k] = serialize_doc(v)
        else:
            result[k] = v
    return result


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=_config["jwt_expiry_hours"])
    }
    return jwt.encode(payload, _config["jwt_secret"], algorithm=_config["jwt_algorithm"])


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _config["jwt_secret"], algorithms=[_config["jwt_algorithm"]])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    user = users_col().find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return serialize_doc(user)


async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def create_page_version(page_id: str, elements: list, user_email: str, action: str = "save"):
    version_count = page_versions_col().count_documents({"page_id": page_id})
    version = {
        "page_id": page_id,
        "version_number": version_count + 1,
        "elements": copy.deepcopy(elements),
        "created_at": datetime.now(timezone.utc),
        "created_by": user_email,
        "action": action,
    }
    page_versions_col().insert_one(version)
    return version_count + 1


def flatten_content(elements, prefix=""):
    """Flatten element tree into a dict of {element_id: content}"""
    result = {}
    for el in elements:
        eid = el.get("id", "")
        if eid and el.get("content") and len(el["content"]) > 0:
            result[eid] = {
                "content": el["content"],
                "type": el.get("type", ""),
                "label": el.get("label", ""),
                "tag": el.get("tag", ""),
            }
        if el.get("children"):
            result.update(flatten_content(el["children"]))
    return result


# ============================================================
# PYDANTIC MODELS
# ============================================================

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str = "editor"
    project_access: Optional[List[str]] = None

class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    project_access: Optional[List[str]] = None

class ChangePasswordRequest(BaseModel):
    new_password: str

class PageContentUpdate(BaseModel):
    element_id: str
    content: Dict[str, Any]

class PageBulkContentUpdate(BaseModel):
    updates: List[PageContentUpdate]

class PageStatusUpdate(BaseModel):
    status: str

class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""

class SchemaImportRequest(BaseModel):
    project_name: str
    pages: List[Dict[str, Any]]
    source_updated_at: Optional[str] = None  # ISO timestamp of when the website was last built/changed


# ============================================================
# SEED DATA
# ============================================================

def get_demo_homepage():
    return {
        "name": "Homepage",
        "slug": "/",
        "status": "draft",
        "project_id": "default",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "elements": [
            {
                "id": "hero-section",
                "type": "section",
                "tag": "section",
                "label": "Hero Section",
                "style": {"classes": "pt-24 pb-32 px-16 bg-[#121414]"},
                "content": {},
                "children": [
                    {
                        "id": "hero-badge",
                        "type": "badge",
                        "tag": "span",
                        "label": "Category Badge",
                        "style": {"classes": "inline-block px-3 py-1 bg-emerald-500/10 rounded-sm mb-6 text-[0.65rem] tracking-[0.2em] text-emerald-400 uppercase font-bold"},
                        "content": {"text": "Architecture of Clarity"},
                        "children": []
                    },
                    {
                        "id": "hero-headline",
                        "type": "heading",
                        "tag": "h1",
                        "label": "Headline (H1)",
                        "style": {"classes": "text-7xl font-bold leading-[1.05] tracking-tight text-white mb-8", "fontSize": "64px", "fontWeight": "700"},
                        "content": {"text": "We are skilled at making the complex plain and simple.", "highlight": {"word": "complex", "color": "#4edea3"}},
                        "children": []
                    },
                    {
                        "id": "hero-description",
                        "type": "paragraph",
                        "tag": "p",
                        "label": "Body Text",
                        "style": {"classes": "text-xl text-neutral-400 leading-relaxed mb-12 max-w-xl"},
                        "content": {"text": "We build digital systems that prioritize efficiency without sacrificing the soul of the creative vision. Editorial control meets technical precision."},
                        "children": []
                    },
                    {
                        "id": "hero-cta-primary",
                        "type": "button",
                        "tag": "button",
                        "label": "Primary CTA",
                        "style": {"classes": "bg-emerald-500 text-black px-8 py-3.5 rounded-lg font-bold uppercase tracking-widest text-xs"},
                        "content": {"text": "Start a Project", "href": "#contact"},
                        "children": []
                    },
                    {
                        "id": "hero-cta-secondary",
                        "type": "button",
                        "tag": "button",
                        "label": "Secondary CTA",
                        "style": {"classes": "text-white font-bold uppercase tracking-widest text-xs border-b-2 border-white/20 hover:border-emerald-500"},
                        "content": {"text": "View Case Studies", "href": "#work"},
                        "children": []
                    }
                ]
            },
            {
                "id": "image-grid-section",
                "type": "section",
                "tag": "section",
                "label": "Image Grid",
                "style": {"classes": "px-16 grid grid-cols-12 gap-8 items-end mb-24 bg-[#121414]"},
                "content": {},
                "children": [
                    {
                        "id": "grid-image-large",
                        "type": "image",
                        "tag": "img",
                        "label": "Large Image",
                        "style": {"classes": "col-span-7 aspect-[4/5] rounded-sm overflow-hidden"},
                        "content": {"src": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80", "alt": "Minimal Space"},
                        "children": []
                    },
                    {
                        "id": "grid-image-small",
                        "type": "image",
                        "tag": "img",
                        "label": "Small Image",
                        "style": {"classes": "col-span-5 aspect-square rounded-sm overflow-hidden"},
                        "content": {"src": "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=600&q=80", "alt": "Detail"},
                        "children": []
                    },
                    {
                        "id": "grid-quote-block",
                        "type": "quote",
                        "tag": "blockquote",
                        "label": "Quote Block",
                        "style": {"classes": "col-span-5 p-8 border-l-2 border-emerald-500 bg-[#1a1b1b]"},
                        "content": {"title": "Obsessive Detail", "text": "Every pixel is engineered to serve the narrative, ensuring a seamless bridge between data and design."},
                        "children": []
                    }
                ]
            },
            {
                "id": "features-section",
                "type": "section",
                "tag": "section",
                "label": "Features Section",
                "style": {"classes": "px-16 py-24 bg-[#0d0e0e]"},
                "content": {},
                "children": [
                    {
                        "id": "features-title",
                        "type": "heading",
                        "tag": "h2",
                        "label": "Section Title (H2)",
                        "style": {"classes": "text-4xl font-bold tracking-tight text-white mb-4"},
                        "content": {"text": "Built for precision."},
                        "children": []
                    },
                    {
                        "id": "features-subtitle",
                        "type": "paragraph",
                        "tag": "p",
                        "label": "Section Subtitle",
                        "style": {"classes": "text-lg text-neutral-400 mb-16 max-w-2xl"},
                        "content": {"text": "Our approach combines meticulous engineering with an artistic sensibility that elevates every interface."},
                        "children": []
                    },
                    {"id": "feature-card-1", "type": "card", "tag": "div", "label": "Feature Card 1", "style": {"classes": "p-8 bg-[#1a1b1b] rounded-sm"}, "content": {"title": "Visual Hierarchy", "text": "Structure that guides the eye naturally through content layers, creating intuitive navigation paths."}, "children": []},
                    {"id": "feature-card-2", "type": "card", "tag": "div", "label": "Feature Card 2", "style": {"classes": "p-8 bg-[#1a1b1b] rounded-sm"}, "content": {"title": "Technical Precision", "text": "Every component is engineered for performance, accessibility, and maintainability across all platforms."}, "children": []},
                    {"id": "feature-card-3", "type": "card", "tag": "div", "label": "Feature Card 3", "style": {"classes": "p-8 bg-[#1a1b1b] rounded-sm"}, "content": {"title": "Creative Control", "text": "Fine-grained editorial tools that empower content teams without compromising design integrity."}, "children": []}
                ]
            }
        ]
    }


def get_demo_about_page():
    return {
        "name": "About",
        "slug": "/about",
        "status": "draft",
        "project_id": "default",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "elements": [
            {
                "id": "about-hero", "type": "section", "tag": "section", "label": "About Hero",
                "style": {"classes": "pt-24 pb-16 px-16 bg-[#121414]"}, "content": {},
                "children": [
                    {"id": "about-badge", "type": "badge", "tag": "span", "label": "Page Badge", "style": {"classes": "inline-block px-3 py-1 bg-emerald-500/10 rounded-sm mb-6 text-[0.65rem] tracking-[0.2em] text-emerald-400 uppercase font-bold"}, "content": {"text": "Our Story"}, "children": []},
                    {"id": "about-headline", "type": "heading", "tag": "h1", "label": "Page Title (H1)", "style": {"classes": "text-6xl font-bold leading-[1.1] tracking-tight text-white mb-8"}, "content": {"text": "We believe in the power of clarity.", "highlight": {"word": "clarity", "color": "#4edea3"}}, "children": []},
                    {"id": "about-intro", "type": "paragraph", "tag": "p", "label": "Introduction", "style": {"classes": "text-xl text-neutral-400 leading-relaxed max-w-2xl"}, "content": {"text": "Founded in 2020, we have been pushing the boundaries of digital design. Our team of engineers and designers work in harmony to create systems that are both beautiful and functional."}, "children": []}
                ]
            },
            {
                "id": "about-values", "type": "section", "tag": "section", "label": "Values Section",
                "style": {"classes": "px-16 py-24 bg-[#0d0e0e]"}, "content": {},
                "children": [
                    {"id": "values-title", "type": "heading", "tag": "h2", "label": "Values Title (H2)", "style": {"classes": "text-3xl font-bold tracking-tight text-white mb-12"}, "content": {"text": "Our Values"}, "children": []},
                    {"id": "value-1", "type": "card", "tag": "div", "label": "Value Card 1", "style": {"classes": "p-6 bg-[#1a1b1b] rounded-sm"}, "content": {"title": "Precision", "text": "Every detail matters. We measure twice and cut once, ensuring every component meets our exacting standards."}, "children": []},
                    {"id": "value-2", "type": "card", "tag": "div", "label": "Value Card 2", "style": {"classes": "p-6 bg-[#1a1b1b] rounded-sm"}, "content": {"title": "Collaboration", "text": "Great work happens when diverse perspectives converge. We foster an environment where every voice shapes the outcome."}, "children": []},
                    {"id": "value-3", "type": "card", "tag": "div", "label": "Value Card 3", "style": {"classes": "p-6 bg-[#1a1b1b] rounded-sm"}, "content": {"title": "Innovation", "text": "We stay at the frontier of technology, constantly exploring new approaches to solve complex design challenges."}, "children": []}
                ]
            }
        ]
    }


def seed_database(seed_demo_content: bool = True):
    """Seed initial admin user. Demo content only if seed_demo_content=True."""
    admin_email = _config["admin_email"]
    admin_password = _config["admin_password"]

    # Idempotent admin creation: if the configured admin doesn't exist yet,
    # create it. This handles the case where a previous broken install seeded
    # the wrong admin (e.g. due to a malformed .env) and the operator has
    # since fixed the env vars and restarted.
    if not users_col().find_one({"email": admin_email}):
        users_col().insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "role": "admin",
            "is_active": True,
            "project_access": [],
            "created_at": datetime.now(timezone.utc),
        })
        print(f"[CMS] Seeded admin user: {admin_email}")
    else:
        print(f"[CMS] Admin user {admin_email} already exists — skipping seed.")

    if seed_demo_content:
        if projects_col().count_documents({}) == 0:
            projects_col().insert_one({
                "name": "The Monolith",
                "slug": "the-monolith",
                "project_id": "default",
                "description": "Demo project",
                "created_at": datetime.now(timezone.utc)
            })

        if pages_col().count_documents({}) == 0:
            pages_col().insert_one(get_demo_homepage())
            pages_col().insert_one(get_demo_about_page())
            print("[CMS] Seeded demo pages")


# ============================================================
# LIFECYCLE HOOKS (called by install_cms)
# ============================================================

def _init_indexes():
    users_col().create_index("email", unique=True)
    pages_col().create_index([("project_id", 1), ("slug", 1)])
    page_versions_col().create_index([("page_id", 1), ("version_number", DESCENDING)])
    projects_col().create_index("project_id", unique=True)


# ============================================================
# AUTH ENDPOINTS
# ============================================================

@router.post("/auth/login")
async def login(req: LoginRequest):
    user = users_col().find_one({"email": req.email})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Account is disabled")
    token = create_token(str(user["_id"]), user["email"], user["role"])
    return {
        "token": token,
        "user": {"id": str(user["_id"]), "email": user["email"], "name": user.get("name", ""), "role": user["role"]}
    }

@router.post("/auth/register")
async def register(req: RegisterRequest, current_user: dict = Depends(require_admin)):
    if users_col().find_one({"email": req.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = {
        "email": req.email,
        "password_hash": hash_password(req.password),
        "name": req.name,
        "role": req.role,
        "is_active": True,
        "project_access": req.project_access if req.project_access else [],
        "created_at": datetime.now(timezone.utc)
    }
    result = users_col().insert_one(new_user)
    return {"id": str(result.inserted_id), "email": req.email, "name": req.name, "role": req.role, "project_access": new_user["project_access"]}

@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "role": current_user["role"],
        "project_access": current_user.get("project_access", [])
    }


# ============================================================
# USER MANAGEMENT ENDPOINTS (Admin only)
# ============================================================

@router.get("/users")
async def list_users(current_user: dict = Depends(require_admin)):
    users = list(users_col().find({}))
    return [serialize_doc({
        "_id": u["_id"],
        "email": u["email"],
        "name": u.get("name", ""),
        "role": u["role"],
        "is_active": u.get("is_active", True),
        "project_access": u.get("project_access", []),
        "created_at": u.get("created_at")
    }) for u in users]

@router.put("/users/{user_id}")
async def update_user(user_id: str, body: UpdateUserRequest, current_user: dict = Depends(require_admin)):
    user = users_col().find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if str(user["_id"]) == current_user["_id"]:
        if body.is_active is False:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        if body.role and body.role != "admin":
            admin_count = users_col().count_documents({"role": "admin", "is_active": {"$ne": False}})
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot change role: you are the last admin")
    update_fields = {}
    if body.name is not None: update_fields["name"] = body.name
    if body.role is not None and body.role in ["admin", "editor"]: update_fields["role"] = body.role
    if body.is_active is not None: update_fields["is_active"] = body.is_active
    if body.project_access is not None: update_fields["project_access"] = body.project_access
    if update_fields:
        users_col().update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    updated = users_col().find_one({"_id": ObjectId(user_id)})
    return serialize_doc({
        "_id": updated["_id"],
        "email": updated["email"],
        "name": updated.get("name", ""),
        "role": updated["role"],
        "is_active": updated.get("is_active", True),
        "project_access": updated.get("project_access", [])
    })

@router.put("/users/{user_id}/password")
async def change_user_password(user_id: str, body: ChangePasswordRequest, current_user: dict = Depends(require_admin)):
    user = users_col().find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    users_col().update_one({"_id": ObjectId(user_id)}, {"$set": {"password_hash": hash_password(body.new_password)}})
    return {"success": True}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    if user_id == current_user["_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = users_col().delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True}


# ============================================================
# PROJECTS ENDPOINTS
# ============================================================

@router.get("/projects")
async def list_projects(current_user: dict = Depends(get_current_user)):
    # Admins see all projects, editors only their assigned ones
    if current_user.get("role") == "admin":
        projects = list(projects_col().find({}))
    else:
        # Filter by project_access
        project_access = current_user.get("project_access", [])
        if not project_access:
            return []  # No access to any project
        projects = list(projects_col().find({"project_id": {"$in": project_access}}))
    
    result = []
    for p in projects:
        page_count = pages_col().count_documents({"project_id": p["project_id"]})
        result.append(serialize_doc({
            "_id": p["_id"],
            "project_id": p["project_id"],
            "name": p["name"],
            "description": p.get("description", ""),
            "page_count": page_count,
            "created_at": p.get("created_at"),
        }))
    return result

@router.post("/projects")
async def create_project(body: ProjectCreateRequest, current_user: dict = Depends(require_admin)):
    project_id = body.name.lower().replace(" ", "-").replace("_", "-")
    # Ensure unique
    if projects_col().find_one({"project_id": project_id}):
        project_id = f"{project_id}-{uuid.uuid4().hex[:6]}"
    project = {
        "name": body.name,
        "project_id": project_id,
        "description": body.description or "",
        "slug": project_id,
        "created_at": datetime.now(timezone.utc),
    }
    projects_col().insert_one(project)
    return serialize_doc(project)


# ============================================================
# SCHEMA IMPORT ENDPOINT
# ============================================================

@router.post("/projects/import")
async def import_schema(body: SchemaImportRequest, current_user: dict = Depends(require_admin)):
    """
    Import a cms-schema.json to create/update a project with all pages and elements.
    Uses timestamp comparison to decide which content wins:
    - If CMS editor changed content AFTER last import → keep CMS version
    - If Emergent changed content AFTER last CMS edit → take Emergent version
    - New elements always get added
    """
    project_id = body.project_name.lower().replace(" ", "-").replace("_", "-")
    existing_project = projects_col().find_one({"project_id": project_id})

    now = datetime.now(timezone.utc)
    source_ts = now
    if body.source_updated_at:
        try:
            source_ts = datetime.fromisoformat(body.source_updated_at.replace("Z", "+00:00"))
        except Exception:
            source_ts = now

    if not existing_project:
        projects_col().insert_one({
            "name": body.project_name,
            "project_id": project_id,
            "slug": project_id,
            "description": f"Imported project: {body.project_name}",
            "created_at": now,
            "last_imported_at": now,
        })
    else:
        projects_col().update_one(
            {"project_id": project_id},
            {"$set": {"last_imported_at": now}}
        )

    imported_pages = []
    for page_data in body.pages:
        slug = page_data.get("slug", "/")
        name = page_data.get("name", "Untitled")
        elements = page_data.get("elements", [])

        existing_page = pages_col().find_one({"project_id": project_id, "slug": slug})

        if existing_page:
            # Smart merge with timestamp comparison
            last_import = existing_project.get("last_imported_at") if existing_project else None
            merged_elements = merge_elements_with_timestamps(
                existing_page.get("elements", []),
                elements,
                existing_page.get("element_timestamps", {}),
                source_ts,
            )
            pages_col().update_one(
                {"_id": existing_page["_id"]},
                {"$set": {
                    "elements": merged_elements,
                    "name": name,
                    "updated_at": now,
                    "last_imported_at": now,
                }}
            )
            imported_pages.append({"name": name, "slug": slug, "action": "updated"})
        else:
            pages_col().insert_one({
                "name": name,
                "slug": slug,
                "status": "draft",
                "project_id": project_id,
                "created_at": now,
                "updated_at": now,
                "last_imported_at": now,
                "elements": elements,
                "element_timestamps": {},
            })
            imported_pages.append({"name": name, "slug": slug, "action": "created"})

    return {
        "success": True,
        "project_id": project_id,
        "project_name": body.project_name,
        "pages_imported": len(imported_pages),
        "details": imported_pages,
    }


def merge_elements_with_timestamps(existing_elements, new_elements, element_timestamps, source_ts):
    """
    Smart merge with timestamp comparison.
    Keeps CMS editor changes if they are newer than source_updated_at.
    """
    existing_map = {}
    def build_map(elements):
        for el in elements:
            existing_map[el.get("id")] = el
            if el.get("children"):
                build_map(el["children"])
    build_map(existing_elements)

    # Ensure source_ts is timezone-aware for proper comparison
    if source_ts.tzinfo is None:
        source_ts = source_ts.replace(tzinfo=timezone.utc)

    def merge_tree(new_els):
        result = []
        for new_el in new_els:
            eid = new_el.get("id")
            if eid in existing_map:
                cms_edit_ts = None
                cms_edit_ts_str = element_timestamps.get(eid)
                if cms_edit_ts_str:
                    try:
                        parsed = datetime.fromisoformat(str(cms_edit_ts_str).replace("Z", "+00:00"))
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=timezone.utc)
                        cms_edit_ts = parsed
                    except Exception:
                        cms_edit_ts = None

                if cms_edit_ts is not None and cms_edit_ts > source_ts:
                    # CMS editor changed AFTER website build: keep CMS content
                    merged = {**new_el, "content": existing_map[eid].get("content", new_el.get("content", {}))}
                else:
                    # No CMS edit or Emergent is newer: take new content
                    merged = {**new_el}

                if new_el.get("children"):
                    merged["children"] = merge_tree(new_el["children"])
                result.append(merged)
            else:
                result.append(new_el)
        return result

    return merge_tree(new_elements)


# ============================================================
# PAGES ENDPOINTS
# ============================================================

@router.get("/pages")
async def list_pages(project_id: str = "default", current_user: dict = Depends(get_current_user)):
    # Check if user has access to this project
    if current_user.get("role") != "admin":
        project_access = current_user.get("project_access", [])
        if project_id not in project_access:
            raise HTTPException(status_code=403, detail="No access to this project")
    
    pages = list(pages_col().find({"project_id": project_id}))
    return [serialize_doc({
        "_id": p["_id"],
        "name": p["name"],
        "slug": p["slug"],
        "status": p["status"],
        "project_id": p["project_id"],
        "updated_at": p.get("updated_at"),
        "element_count": count_elements(p.get("elements", []))
    }) for p in pages]


def count_elements(elements):
    count = 0
    for el in elements:
        count += 1
        if el.get("children"):
            count += count_elements(el["children"])
    return count


@router.get("/pages/{page_id}")
async def get_page(page_id: str, current_user: dict = Depends(get_current_user)):
    page = pages_col().find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return serialize_doc(page)


@router.put("/pages/{page_id}/content")
async def update_page_content(page_id: str, update: PageContentUpdate, current_user: dict = Depends(get_current_user)):
    page = pages_col().find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    elements = page.get("elements", [])
    updated = update_element_content(elements, update.element_id, update.content)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Element {update.element_id} not found")
    # Track per-element edit timestamp
    element_timestamps = page.get("element_timestamps", {})
    element_timestamps[update.element_id] = datetime.now(timezone.utc).isoformat()
    pages_col().update_one(
        {"_id": ObjectId(page_id)},
        {"$set": {"elements": elements, "updated_at": datetime.now(timezone.utc), "status": "draft", "element_timestamps": element_timestamps}}
    )
    return {"success": True, "element_id": update.element_id}


@router.put("/pages/{page_id}/content/bulk")
async def update_page_content_bulk(page_id: str, body: PageBulkContentUpdate, current_user: dict = Depends(get_current_user)):
    page = pages_col().find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    create_page_version(page_id, page.get("elements", []), current_user.get("email", "unknown"), "save")
    elements = page.get("elements", [])
    element_timestamps = page.get("element_timestamps", {})
    now_iso = datetime.now(timezone.utc).isoformat()
    for upd in body.updates:
        update_element_content(elements, upd.element_id, upd.content)
        element_timestamps[upd.element_id] = now_iso
    pages_col().update_one(
        {"_id": ObjectId(page_id)},
        {"$set": {"elements": elements, "updated_at": datetime.now(timezone.utc), "status": "draft", "element_timestamps": element_timestamps}}
    )
    return {"success": True, "updated_count": len(body.updates)}


def update_element_content(elements, element_id, new_content):
    for el in elements:
        if el.get("id") == element_id:
            el["content"] = {**el.get("content", {}), **new_content}
            return True
        if el.get("children"):
            if update_element_content(el["children"], element_id, new_content):
                return True
    return False


@router.put("/pages/{page_id}/status")
async def update_page_status(page_id: str, body: PageStatusUpdate, current_user: dict = Depends(get_current_user)):
    if body.status not in ["draft", "published"]:
        raise HTTPException(status_code=400, detail="Status must be 'draft' or 'published'")
    page = pages_col().find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    update_fields = {"status": body.status, "updated_at": datetime.now(timezone.utc)}
    if body.status == "published":
        update_fields["published_at"] = datetime.now(timezone.utc)
        update_fields["published_elements"] = page.get("elements", [])
        create_page_version(page_id, page.get("elements", []), current_user.get("email", "unknown"), "publish")
    pages_col().update_one({"_id": ObjectId(page_id)}, {"$set": update_fields})
    return {"success": True, "status": body.status}


# ============================================================
# PAGE VERSION HISTORY
# ============================================================

@router.get("/pages/{page_id}/versions")
async def list_page_versions(page_id: str, current_user: dict = Depends(get_current_user)):
    versions = list(page_versions_col().find(
        {"page_id": page_id}, {"elements": 0}
    ).sort("version_number", DESCENDING).limit(50))
    return [serialize_doc(v) for v in versions]

@router.get("/pages/{page_id}/versions/{version_number}")
async def get_page_version(page_id: str, version_number: int, current_user: dict = Depends(get_current_user)):
    version = page_versions_col().find_one({"page_id": page_id, "version_number": version_number})
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return serialize_doc(version)

@router.post("/pages/{page_id}/versions/{version_number}/restore")
async def restore_page_version(page_id: str, version_number: int, current_user: dict = Depends(get_current_user)):
    version = page_versions_col().find_one({"page_id": page_id, "version_number": version_number})
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    page = pages_col().find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    create_page_version(page_id, page.get("elements", []), current_user.get("email", "unknown"), "restore")
    pages_col().update_one(
        {"_id": ObjectId(page_id)},
        {"$set": {"elements": version["elements"], "updated_at": datetime.now(timezone.utc), "status": "draft"}}
    )
    updated_page = pages_col().find_one({"_id": ObjectId(page_id)})
    return serialize_doc(updated_page)


# ============================================================
# PUBLIC API (for website consumption)
# ============================================================

@router.get("/public/{project_id}/content")
async def public_project_content(project_id: str):
    """
    Returns ALL published content for a project as a flat map:
    { "page_slug": { "element_id": { content, type, label, tag }, ... }, ... }
    
    This is the main endpoint websites use to fetch CMS content.
    """
    pages = list(pages_col().find({"project_id": project_id, "status": "published"}))
    result = {}
    for p in pages:
        elements = p.get("published_elements", p.get("elements", []))
        result[p["slug"]] = flatten_content(elements)
    return result


@router.get("/public/{project_id}/pages")
async def public_list_pages(project_id: str):
    pages = list(pages_col().find({"project_id": project_id, "status": "published"}))
    return [serialize_doc({
        "_id": p["_id"],
        "name": p["name"],
        "slug": p["slug"],
        "published_at": p.get("published_at"),
        "elements": p.get("published_elements", p.get("elements", []))
    }) for p in pages]


@router.get("/public/{project_id}/pages/{slug:path}")
async def public_get_page(project_id: str, slug: str):
    if not slug.startswith("/"):
        slug = "/" + slug
    page = pages_col().find_one({"slug": slug, "project_id": project_id, "status": "published"})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found or not published")
    return serialize_doc({
        "_id": page["_id"],
        "name": page["name"],
        "slug": page["slug"],
        "published_at": page.get("published_at"),
        "elements": page.get("published_elements", page.get("elements", []))
    })


# Keep legacy public endpoints for backward compatibility
@router.get("/public/pages")
async def public_list_pages_legacy():
    pages = list(pages_col().find({"project_id": "default", "status": "published"}))
    return [serialize_doc({
        "_id": p["_id"], "name": p["name"], "slug": p["slug"],
        "published_at": p.get("published_at"),
        "elements": p.get("published_elements", p.get("elements", []))
    }) for p in pages]


# ============================================================
# CLIENT LIBRARY (served as JS)
# ============================================================

CLIENT_JS = """
/**
 * Monolith CMS - Client Library v1.0
 * Drop this script into any website to connect it to The Monolith CMS.
 *
 * Usage:
 *   <script src="YOUR_CMS_URL/api/client.js"
 *           data-project="your-project-id"
 *           data-cms-url="YOUR_CMS_URL"></script>
 *
 * HTML elements use data-cms-id to map to CMS content:
 *   <h1 data-cms-id="hero-headline">Default text</h1>
 *   <img data-cms-id="hero-image" src="default.jpg" alt="default" />
 */
(function() {
  'use strict';

  var script = document.currentScript;
  var projectId = script && script.getAttribute('data-project');
  var cmsUrl = script && script.getAttribute('data-cms-url');

  if (!projectId) {
    console.warn('[Monolith CMS] Missing data-project attribute on script tag.');
    return;
  }
  if (!cmsUrl) {
    // Try to infer from script src
    if (script && script.src) {
      var url = new URL(script.src);
      cmsUrl = url.origin;
    } else {
      console.warn('[Monolith CMS] Missing data-cms-url attribute on script tag.');
      return;
    }
  }

  // Remove trailing slash
  cmsUrl = cmsUrl.replace(/\\/$/, '');

  // Detect current page slug
  var pageSlug = window.location.pathname || '/';

  function applyContent(contentMap) {
    if (!contentMap) return;

    // Get content for current page
    var pageContent = contentMap[pageSlug];
    if (!pageContent) {
      // Try without trailing slash or with trailing slash
      pageContent = contentMap[pageSlug.replace(/\\/$/, '')] || contentMap[pageSlug + '/'];
    }
    if (!pageContent) {
      console.log('[Monolith CMS] No published content found for page:', pageSlug);
      return;
    }

    // Find all elements with data-cms-id
    var elements = document.querySelectorAll('[data-cms-id]');
    var applied = 0;

    elements.forEach(function(el) {
      var cmsId = el.getAttribute('data-cms-id');
      var entry = pageContent[cmsId];
      if (!entry || !entry.content) return;

      var content = entry.content;
      var tag = el.tagName.toLowerCase();

      // Apply content based on element type
      if (tag === 'img') {
        if (content.src) el.src = content.src;
        if (content.alt) el.alt = content.alt;
      } else if (tag === 'a') {
        if (content.text) el.textContent = content.text;
        if (content.href) el.href = content.href;
      } else if (content.text !== undefined) {
        // Handle text with highlight
        if (content.highlight && content.highlight.word) {
          var regex = new RegExp('(' + content.highlight.word.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + ')', 'gi');
          var parts = content.text.split(regex);
          el.innerHTML = '';
          parts.forEach(function(part) {
            if (part.toLowerCase() === content.highlight.word.toLowerCase()) {
              var span = document.createElement('span');
              span.style.color = content.highlight.color || '#4edea3';
              span.textContent = part;
              el.appendChild(span);
            } else {
              el.appendChild(document.createTextNode(part));
            }
          });
        } else {
          el.textContent = content.text;
        }
      }

      applied++;
    });

    console.log('[Monolith CMS] Applied', applied, 'content updates for', pageSlug);
  }

  // Fetch and apply content
  function init() {
    var apiUrl = cmsUrl + '__API_PREFIX__/public/' + projectId + '/content';

    fetch(apiUrl)
      .then(function(res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function(data) {
        applyContent(data);
        // Dispatch event for frameworks that need to know
        window.dispatchEvent(new CustomEvent('monolith-cms-loaded', { detail: data }));
      })
      .catch(function(err) {
        console.warn('[Monolith CMS] Failed to load content:', err.message);
      });
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose global API
  window.MonolithCMS = {
    projectId: projectId,
    cmsUrl: cmsUrl,
    refresh: init,
  };
})();
"""

@router.get("/client.js")
async def serve_client_js():
    # Replace __API_PREFIX__ placeholder with the actual mounted prefix
    api_prefix = _config.get("api_prefix", "/api/cms")
    js = CLIENT_JS.replace("__API_PREFIX__", api_prefix)
    return Response(content=js, media_type="application/javascript")


# ============================================================
# HEALTH + SYSTEM (auto-update)
# ============================================================


def _read_version() -> Dict[str, Any]:
    """Read /app/cms/VERSION (created by install.sh)."""
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")
    if not os.path.isfile(version_file):
        return {"commit": "unknown", "ref": "main", "repo": None, "installed_at": None}
    try:
        with open(version_file, "r") as f:
            return json.loads(f.read())
    except Exception:
        return {"commit": "unknown", "ref": "main", "repo": None, "installed_at": None}


def _fetch_latest_commit(repo_url: Optional[str], ref: str = "main") -> Optional[str]:
    """Query the GitHub API for the latest commit SHA on the given ref."""
    if not repo_url:
        return None
    # Convert https://github.com/user/repo.git → user/repo
    try:
        slug = repo_url.rstrip("/").replace(".git", "").split("github.com/")[-1]
        api_url = f"https://api.github.com/repos/{slug}/commits/{ref}"
        req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("sha")
    except Exception as e:
        print(f"[CMS] check-update failed: {e}")
        return None


@router.get("/system/version")
async def get_version():
    """Public — returns the currently installed CMS version."""
    v = _read_version()
    return {
        "commit": v.get("commit", "unknown"),
        "short": (v.get("commit") or "")[:8],
        "ref": v.get("ref", "main"),
        "installed_at": v.get("installed_at"),
    }


@router.get("/system/check-update")
async def check_update(current_user: dict = Depends(require_admin)):
    """Admin — compares local commit with the latest on GitHub."""
    v = _read_version()
    current_sha = v.get("commit", "unknown")
    repo_url = v.get("repo")
    ref = v.get("ref", "main")

    if not repo_url:
        return {
            "current": current_sha,
            "latest": None,
            "update_available": False,
            "reason": "VERSION file missing or repo URL unknown.",
        }

    latest_sha = _fetch_latest_commit(repo_url, ref)
    if not latest_sha:
        return {
            "current": current_sha,
            "latest": None,
            "update_available": False,
            "reason": "Could not reach GitHub API.",
        }

    return {
        "current": current_sha,
        "current_short": current_sha[:8],
        "latest": latest_sha,
        "latest_short": latest_sha[:8],
        "update_available": (current_sha != latest_sha and current_sha != "unknown"),
        "ref": ref,
        "repo": repo_url,
    }


@router.post("/system/upgrade")
async def upgrade_cms(current_user: dict = Depends(require_admin)):
    """Admin — runs install.sh --upgrade in the background."""
    v = _read_version()
    repo_url = v.get("repo")
    ref = v.get("ref", "main")

    if not repo_url:
        raise HTTPException(status_code=400, detail="VERSION file missing — cannot determine source repo.")

    # Convert https://github.com/user/repo.git → raw URL for install.sh
    try:
        slug = repo_url.rstrip("/").replace(".git", "").split("github.com/")[-1]
        install_url = f"https://raw.githubusercontent.com/{slug}/{ref}/install.sh"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not derive install.sh URL: {e}")

    # Run the upgrade in a background thread so we can return immediately.
    # The backend will be restarted by supervisor at the end of install.sh.
    def _run():
        try:
            print(f"[CMS] Self-upgrade starting from {install_url} (ref: {ref})…")
            cmd = f'cd /app && bash -c "$(curl -fsSL {install_url})" -- --upgrade'
            subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, timeout=180)
            print("[CMS] Self-upgrade finished successfully.")
        except subprocess.CalledProcessError as e:
            print(f"[CMS] Self-upgrade FAILED: {e.stderr or e.stdout}")
        except Exception as e:
            print(f"[CMS] Self-upgrade error: {e}")

    threading.Thread(target=_run, daemon=True).start()

    return {
        "started": True,
        "message": "Upgrade started. The backend will restart in ~30 seconds. Reload the admin UI afterwards.",
        "from": v.get("commit", "unknown"),
        "ref": ref,
    }


# ============================================================
# AUTO-CONNECT — scan host frontend, inject data-cms-id, import schema
# ============================================================


class ScanRequest(BaseModel):
    scan_path: Optional[str] = None  # default: /app/frontend/src/pages


class ApplyConnectionRequest(BaseModel):
    suggestion_ids: List[str]                  # which suggested_ids to apply
    project_name: str = "Auto-detected Site"


@router.post("/system/scan-website")
async def scan_website(req: ScanRequest, current_user: dict = Depends(require_admin)):
    """Admin — scan the host website's frontend source for editable elements."""
    try:
        from . import scanner
    except ImportError as e:
        # tree-sitter not installed on host
        raise HTTPException(
            status_code=503,
            detail=(
                "Auto-Connect scanner unavailable: tree-sitter packages are missing. "
                "Run on the host: pip install tree-sitter tree-sitter-language-pack — "
                f"or re-run install.sh --upgrade. (ImportError: {e})"
            ),
        )

    scan_root = req.scan_path or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "src", "pages"
    )
    if not os.path.isdir(scan_root):
        # Fall back to /app/frontend/src
        scan_root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "frontend", "src"
        )
    if not os.path.isdir(scan_root):
        raise HTTPException(
            status_code=400,
            detail=f"Could not find frontend source. Tried {scan_root}. Set scan_path explicitly."
        )

    try:
        suggestions = scanner.scan_directory(scan_root)
    except Exception as e:
        import traceback as _tb
        _tb.print_exc()
        raise HTTPException(status_code=500, detail=f"Scan failed: {type(e).__name__}: {e}")

    return {
        "scan_root": scan_root,
        "count": len(suggestions),
        "suggestions": scanner.suggestions_to_dicts(suggestions),
    }


@router.post("/system/apply-connection")
async def apply_connection(req: ApplyConnectionRequest, current_user: dict = Depends(require_admin)):
    """Admin — inject data-cms-id into source files, build schema, import as project."""
    from . import scanner

    # Re-scan to get fresh offsets (file may have changed)
    scan_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "src", "pages"
    )
    if not os.path.isdir(scan_root):
        scan_root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "frontend", "src"
        )

    fresh_suggestions = scanner.scan_directory(scan_root)
    selected = [s for s in fresh_suggestions if s.suggested_id in req.suggestion_ids or s.existing_id in req.suggestion_ids]

    if not selected:
        raise HTTPException(status_code=400, detail="No matching elements found.")

    # 1. Inject data-cms-id into source files
    apply_result = scanner.apply_suggestions(selected)

    # 2. Re-scan once more so the schema has the freshly-injected ids
    final_suggestions = scanner.scan_directory(scan_root)
    schema = scanner.build_schema_from_suggestions(final_suggestions, project_name=req.project_name)

    # 3. Import the schema (re-uses existing import logic)
    project_id = re.sub(r"[^a-z0-9-]+", "-", req.project_name.lower()).strip("-") or "auto-site"

    # Idempotent project create
    if not projects_col().find_one({"project_id": project_id}):
        projects_col().insert_one({
            "project_id": project_id,
            "name": req.project_name,
            "slug": project_id,
            "description": f"Auto-detected from {scan_root}",
            "created_at": datetime.now(timezone.utc),
            "source_updated_at": schema["source_updated_at"],
        })
    else:
        projects_col().update_one(
            {"project_id": project_id},
            {"$set": {"source_updated_at": schema["source_updated_at"]}}
        )

    pages_added = 0
    pages_updated = 0
    for page in schema["pages"]:
        existing = pages_col().find_one({"project_id": project_id, "slug": page["slug"]})
        if existing:
            # Smart merge: keep CMS edits made after source_updated_at
            pages_col().update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "elements": _merge_elements(existing.get("elements", []), page["elements"], existing.get("source_updated_at")),
                    "source_updated_at": schema["source_updated_at"],
                    "updated_at": datetime.now(timezone.utc),
                }}
            )
            pages_updated += 1
        else:
            pages_col().insert_one({
                "_id": str(ObjectId()),
                "project_id": project_id,
                "name": page["name"],
                "slug": page["slug"],
                "elements": page["elements"],
                "status": "draft",
                "source_updated_at": schema["source_updated_at"],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            pages_added += 1

    return {
        "success": True,
        "project_id": project_id,
        "files_modified": apply_result["files_modified"],
        "elements_added": apply_result["elements_added"],
        "pages_added": pages_added,
        "pages_updated": pages_updated,
        "total_elements": sum(len(p["elements"]) for p in schema["pages"]),
    }


def _merge_elements(existing: list, fresh: list, last_source_updated: Optional[datetime]) -> list:
    """Keep existing element content if it was edited after the source was last scanned."""
    existing_by_id = {e["id"]: e for e in existing}
    merged = []
    for fresh_el in fresh:
        eid = fresh_el["id"]
        if eid in existing_by_id:
            old = existing_by_id[eid]
            old_updated = old.get("updated_at")
            if old_updated and last_source_updated and old_updated > last_source_updated:
                # CMS edit is newer -> keep it
                fresh_el = {**fresh_el, "content": old.get("content", fresh_el["content"])}
        merged.append(fresh_el)
    return merged


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
async def health():
    return {"status": "ok", "service": "monolith-cms"}


# ============================================================
# INSTALLER — mount this CMS into any FastAPI app
# ============================================================

def install_cms(
    app: FastAPI,
    mongo_url: str,
    db_name: str,
    collection_prefix: str = "cms_",
    api_prefix: str = "/api/cms",
    static_path: str = "/api/cms-admin",
    static_dir: Optional[str] = None,
    jwt_secret: str = "monolith-cms-default-secret-change-me",
    admin_email: str = "admin@monolith.cms",
    admin_password: str = "admin123",
    seed_demo_content: bool = False,
    add_cors: bool = False,
    cors_origins: Optional[List[str]] = None,
):
    """
    Mount The Monolith CMS into a FastAPI application.

    Args:
        app: The FastAPI instance to mount onto.
        mongo_url: MongoDB connection string.
        db_name: MongoDB database name (shared with host app or dedicated).
        collection_prefix: Prefix for CMS collections (e.g. "cms_" -> cms_pages, cms_users).
        api_prefix: URL prefix for CMS API routes. Default "/api/cms".
        static_path: URL path where the CMS admin UI is served. Default "/cms".
        static_dir: Absolute path to the built React admin UI. If None, UI is not mounted.
        jwt_secret: Secret key for JWT tokens. CHANGE THIS IN PRODUCTION.
        admin_email: Seeded admin user email (only used on first install).
        admin_password: Seeded admin user password.
        seed_demo_content: If True, creates demo project + pages.
        add_cors: If True, adds CORS middleware (only enable if host app doesn't already).
        cors_origins: List of allowed CORS origins (default: ["*"]).
    """
    # Store config
    _config["jwt_secret"] = jwt_secret
    _config["admin_email"] = admin_email
    _config["admin_password"] = admin_password
    _config["api_prefix"] = api_prefix

    # Initialize Mongo
    mongo_client = MongoClient(mongo_url)
    db = mongo_client[db_name]
    _config["mongo_client"] = mongo_client
    _config["db"] = db
    _config["users_col"] = db[f"{collection_prefix}users"]
    _config["pages_col"] = db[f"{collection_prefix}pages"]
    _config["projects_col"] = db[f"{collection_prefix}projects"]
    _config["page_versions_col"] = db[f"{collection_prefix}page_versions"]

    # Create indexes + seed
    _init_indexes()
    seed_database(seed_demo_content=seed_demo_content)

    # Optionally add CORS (only for standalone CMS, not when mounted inside host app)
    if add_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Mount the API router with the chosen prefix
    app.include_router(router, prefix=api_prefix)

    # Mount the admin UI as static files if provided
    if static_dir and os.path.isdir(static_dir):
        app.mount(static_path, StaticFiles(directory=static_dir, html=True), name="cms-admin")
        print(f"[CMS] Admin UI mounted at {static_path} (serving from {static_dir})")
    else:
        print(f"[CMS] No static_dir provided — admin UI not mounted. API available at {api_prefix}/*")

    print(f"[CMS] Installed. API: {api_prefix}/*, collections: {collection_prefix}*")
