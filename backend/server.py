"""
The Monolith CMS - Backend Server
FastAPI + MongoDB
"""
import os
import json
import hashlib
import secrets
import copy
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, Body, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from pymongo import MongoClient, DESCENDING
from bson import ObjectId
import jwt
import bcrypt
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "monolith_cms")
JWT_SECRET = os.environ.get("JWT_SECRET", "monolith-cms-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

users_col = db["users"]
pages_col = db["pages"]
projects_col = db["projects"]
page_versions_col = db["page_versions"]


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
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    user = users_col.find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return serialize_doc(user)


async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def create_page_version(page_id: str, elements: list, user_email: str, action: str = "save"):
    version_count = page_versions_col.count_documents({"page_id": page_id})
    version = {
        "page_id": page_id,
        "version_number": version_count + 1,
        "elements": copy.deepcopy(elements),
        "created_at": datetime.now(timezone.utc),
        "created_by": user_email,
        "action": action,
    }
    page_versions_col.insert_one(version)
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


def seed_database():
    if users_col.count_documents({}) == 0:
        users_col.insert_many([
            {"email": "roman@zund.io", "password_hash": hash_password("admin123"), "name": "Roman Zund", "role": "admin", "is_active": True, "project_access": [], "created_at": datetime.now(timezone.utc)},
            {"email": "admin@monolith.cms", "password_hash": hash_password("admin123"), "name": "Admin", "role": "admin", "is_active": True, "project_access": [], "created_at": datetime.now(timezone.utc)},
            {"email": "editor@monolith.cms", "password_hash": hash_password("editor123"), "name": "Editor", "role": "editor", "is_active": True, "project_access": ["default"], "created_at": datetime.now(timezone.utc)},
        ])
        print("Seeded users")

    if projects_col.count_documents({}) == 0:
        projects_col.insert_one({
            "name": "The Monolith",
            "slug": "the-monolith",
            "project_id": "default",
            "description": "Demo project",
            "created_at": datetime.now(timezone.utc)
        })

    if pages_col.count_documents({}) == 0:
        pages_col.insert_one(get_demo_homepage())
        pages_col.insert_one(get_demo_about_page())
        print("Seeded demo pages")


# ============================================================
# APP LIFECYCLE
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    users_col.create_index("email", unique=True)
    pages_col.create_index([("project_id", 1), ("slug", 1)])
    page_versions_col.create_index([("page_id", 1), ("version_number", DESCENDING)])
    projects_col.create_index("project_id", unique=True)
    seed_database()
    yield
    client.close()

app = FastAPI(title="The Monolith CMS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# AUTH ENDPOINTS
# ============================================================

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = users_col.find_one({"email": req.email})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Account is disabled")
    token = create_token(str(user["_id"]), user["email"], user["role"])
    return {
        "token": token,
        "user": {"id": str(user["_id"]), "email": user["email"], "name": user.get("name", ""), "role": user["role"]}
    }

@app.post("/api/auth/register")
async def register(req: RegisterRequest, current_user: dict = Depends(require_admin)):
    if users_col.find_one({"email": req.email}):
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
    result = users_col.insert_one(new_user)
    return {"id": str(result.inserted_id), "email": req.email, "name": req.name, "role": req.role, "project_access": new_user["project_access"]}

@app.get("/api/auth/me")
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

@app.get("/api/users")
async def list_users(current_user: dict = Depends(require_admin)):
    users = list(users_col.find({}))
    return [serialize_doc({
        "_id": u["_id"],
        "email": u["email"],
        "name": u.get("name", ""),
        "role": u["role"],
        "is_active": u.get("is_active", True),
        "project_access": u.get("project_access", []),
        "created_at": u.get("created_at")
    }) for u in users]

@app.put("/api/users/{user_id}")
async def update_user(user_id: str, body: UpdateUserRequest, current_user: dict = Depends(require_admin)):
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if str(user["_id"]) == current_user["_id"]:
        if body.is_active is False:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        if body.role and body.role != "admin":
            admin_count = users_col.count_documents({"role": "admin", "is_active": {"$ne": False}})
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot change role: you are the last admin")
    update_fields = {}
    if body.name is not None: update_fields["name"] = body.name
    if body.role is not None and body.role in ["admin", "editor"]: update_fields["role"] = body.role
    if body.is_active is not None: update_fields["is_active"] = body.is_active
    if body.project_access is not None: update_fields["project_access"] = body.project_access
    if update_fields:
        users_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    updated = users_col.find_one({"_id": ObjectId(user_id)})
    return serialize_doc({
        "_id": updated["_id"],
        "email": updated["email"],
        "name": updated.get("name", ""),
        "role": updated["role"],
        "is_active": updated.get("is_active", True),
        "project_access": updated.get("project_access", [])
    })

@app.put("/api/users/{user_id}/password")
async def change_user_password(user_id: str, body: ChangePasswordRequest, current_user: dict = Depends(require_admin)):
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"password_hash": hash_password(body.new_password)}})
    return {"success": True}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    if user_id == current_user["_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = users_col.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True}


# ============================================================
# PROJECTS ENDPOINTS
# ============================================================

@app.get("/api/projects")
async def list_projects(current_user: dict = Depends(get_current_user)):
    # Admins see all projects, editors only their assigned ones
    if current_user.get("role") == "admin":
        projects = list(projects_col.find({}))
    else:
        # Filter by project_access
        project_access = current_user.get("project_access", [])
        if not project_access:
            return []  # No access to any project
        projects = list(projects_col.find({"project_id": {"$in": project_access}}))
    
    result = []
    for p in projects:
        page_count = pages_col.count_documents({"project_id": p["project_id"]})
        result.append(serialize_doc({
            "_id": p["_id"],
            "project_id": p["project_id"],
            "name": p["name"],
            "description": p.get("description", ""),
            "page_count": page_count,
            "created_at": p.get("created_at"),
        }))
    return result

@app.post("/api/projects")
async def create_project(body: ProjectCreateRequest, current_user: dict = Depends(require_admin)):
    project_id = body.name.lower().replace(" ", "-").replace("_", "-")
    # Ensure unique
    if projects_col.find_one({"project_id": project_id}):
        project_id = f"{project_id}-{uuid.uuid4().hex[:6]}"
    project = {
        "name": body.name,
        "project_id": project_id,
        "description": body.description or "",
        "slug": project_id,
        "created_at": datetime.now(timezone.utc),
    }
    projects_col.insert_one(project)
    return serialize_doc(project)


# ============================================================
# SCHEMA IMPORT ENDPOINT
# ============================================================

@app.post("/api/projects/import")
async def import_schema(body: SchemaImportRequest, current_user: dict = Depends(require_admin)):
    """
    Import a cms-schema.json to create/update a project with all pages and elements.
    Uses timestamp comparison to decide which content wins:
    - If CMS editor changed content AFTER last import → keep CMS version
    - If Emergent changed content AFTER last CMS edit → take Emergent version
    - New elements always get added
    """
    project_id = body.project_name.lower().replace(" ", "-").replace("_", "-")
    existing_project = projects_col.find_one({"project_id": project_id})

    now = datetime.now(timezone.utc)
    source_ts = now
    if body.source_updated_at:
        try:
            source_ts = datetime.fromisoformat(body.source_updated_at.replace("Z", "+00:00"))
        except Exception:
            source_ts = now

    if not existing_project:
        projects_col.insert_one({
            "name": body.project_name,
            "project_id": project_id,
            "slug": project_id,
            "description": f"Imported project: {body.project_name}",
            "created_at": now,
            "last_imported_at": now,
        })
    else:
        projects_col.update_one(
            {"project_id": project_id},
            {"$set": {"last_imported_at": now}}
        )

    imported_pages = []
    for page_data in body.pages:
        slug = page_data.get("slug", "/")
        name = page_data.get("name", "Untitled")
        elements = page_data.get("elements", [])

        existing_page = pages_col.find_one({"project_id": project_id, "slug": slug})

        if existing_page:
            # Smart merge with timestamp comparison
            last_import = existing_project.get("last_imported_at") if existing_project else None
            merged_elements = merge_elements_with_timestamps(
                existing_page.get("elements", []),
                elements,
                existing_page.get("element_timestamps", {}),
                source_ts,
            )
            pages_col.update_one(
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
            pages_col.insert_one({
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

@app.get("/api/pages")
async def list_pages(project_id: str = "default", current_user: dict = Depends(get_current_user)):
    # Check if user has access to this project
    if current_user.get("role") != "admin":
        project_access = current_user.get("project_access", [])
        if project_id not in project_access:
            raise HTTPException(status_code=403, detail="No access to this project")
    
    pages = list(pages_col.find({"project_id": project_id}))
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


@app.get("/api/pages/{page_id}")
async def get_page(page_id: str, current_user: dict = Depends(get_current_user)):
    page = pages_col.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return serialize_doc(page)


@app.put("/api/pages/{page_id}/content")
async def update_page_content(page_id: str, update: PageContentUpdate, current_user: dict = Depends(get_current_user)):
    page = pages_col.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    elements = page.get("elements", [])
    updated = update_element_content(elements, update.element_id, update.content)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Element {update.element_id} not found")
    # Track per-element edit timestamp
    element_timestamps = page.get("element_timestamps", {})
    element_timestamps[update.element_id] = datetime.now(timezone.utc).isoformat()
    pages_col.update_one(
        {"_id": ObjectId(page_id)},
        {"$set": {"elements": elements, "updated_at": datetime.now(timezone.utc), "status": "draft", "element_timestamps": element_timestamps}}
    )
    return {"success": True, "element_id": update.element_id}


@app.put("/api/pages/{page_id}/content/bulk")
async def update_page_content_bulk(page_id: str, body: PageBulkContentUpdate, current_user: dict = Depends(get_current_user)):
    page = pages_col.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    create_page_version(page_id, page.get("elements", []), current_user.get("email", "unknown"), "save")
    elements = page.get("elements", [])
    element_timestamps = page.get("element_timestamps", {})
    now_iso = datetime.now(timezone.utc).isoformat()
    for upd in body.updates:
        update_element_content(elements, upd.element_id, upd.content)
        element_timestamps[upd.element_id] = now_iso
    pages_col.update_one(
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


@app.put("/api/pages/{page_id}/status")
async def update_page_status(page_id: str, body: PageStatusUpdate, current_user: dict = Depends(get_current_user)):
    if body.status not in ["draft", "published"]:
        raise HTTPException(status_code=400, detail="Status must be 'draft' or 'published'")
    page = pages_col.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    update_fields = {"status": body.status, "updated_at": datetime.now(timezone.utc)}
    if body.status == "published":
        update_fields["published_at"] = datetime.now(timezone.utc)
        update_fields["published_elements"] = page.get("elements", [])
        create_page_version(page_id, page.get("elements", []), current_user.get("email", "unknown"), "publish")
    pages_col.update_one({"_id": ObjectId(page_id)}, {"$set": update_fields})
    return {"success": True, "status": body.status}


# ============================================================
# PAGE VERSION HISTORY
# ============================================================

@app.get("/api/pages/{page_id}/versions")
async def list_page_versions(page_id: str, current_user: dict = Depends(get_current_user)):
    versions = list(page_versions_col.find(
        {"page_id": page_id}, {"elements": 0}
    ).sort("version_number", DESCENDING).limit(50))
    return [serialize_doc(v) for v in versions]

@app.get("/api/pages/{page_id}/versions/{version_number}")
async def get_page_version(page_id: str, version_number: int, current_user: dict = Depends(get_current_user)):
    version = page_versions_col.find_one({"page_id": page_id, "version_number": version_number})
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return serialize_doc(version)

@app.post("/api/pages/{page_id}/versions/{version_number}/restore")
async def restore_page_version(page_id: str, version_number: int, current_user: dict = Depends(get_current_user)):
    version = page_versions_col.find_one({"page_id": page_id, "version_number": version_number})
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    page = pages_col.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    create_page_version(page_id, page.get("elements", []), current_user.get("email", "unknown"), "restore")
    pages_col.update_one(
        {"_id": ObjectId(page_id)},
        {"$set": {"elements": version["elements"], "updated_at": datetime.now(timezone.utc), "status": "draft"}}
    )
    updated_page = pages_col.find_one({"_id": ObjectId(page_id)})
    return serialize_doc(updated_page)


# ============================================================
# PUBLIC API (for website consumption)
# ============================================================

@app.get("/api/public/{project_id}/content")
async def public_project_content(project_id: str):
    """
    Returns ALL published content for a project as a flat map:
    { "page_slug": { "element_id": { content, type, label, tag }, ... }, ... }
    
    This is the main endpoint websites use to fetch CMS content.
    """
    pages = list(pages_col.find({"project_id": project_id, "status": "published"}))
    result = {}
    for p in pages:
        elements = p.get("published_elements", p.get("elements", []))
        result[p["slug"]] = flatten_content(elements)
    return result


@app.get("/api/public/{project_id}/pages")
async def public_list_pages(project_id: str):
    pages = list(pages_col.find({"project_id": project_id, "status": "published"}))
    return [serialize_doc({
        "_id": p["_id"],
        "name": p["name"],
        "slug": p["slug"],
        "published_at": p.get("published_at"),
        "elements": p.get("published_elements", p.get("elements", []))
    }) for p in pages]


@app.get("/api/public/{project_id}/pages/{slug:path}")
async def public_get_page(project_id: str, slug: str):
    if not slug.startswith("/"):
        slug = "/" + slug
    page = pages_col.find_one({"slug": slug, "project_id": project_id, "status": "published"})
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
@app.get("/api/public/pages")
async def public_list_pages_legacy():
    pages = list(pages_col.find({"project_id": "default", "status": "published"}))
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
    var apiUrl = cmsUrl + '/api/public/' + projectId + '/content';

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

@app.get("/api/client.js")
async def serve_client_js():
    return Response(content=CLIENT_JS, media_type="application/javascript")


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "monolith-cms"}
