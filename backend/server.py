"""
The Monolith CMS - Backend Server
FastAPI + MongoDB
"""
import os
import json
import hashlib
import secrets
import copy
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
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

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_col = db["users"]
pages_col = db["pages"]
projects_col = db["projects"]
page_versions_col = db["page_versions"]


# ============================================================
# HELPERS
# ============================================================

def serialize_doc(doc):
    """Convert MongoDB document to JSON-safe dict"""
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
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
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


async def get_optional_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        user = users_col.find_one({"_id": ObjectId(payload["sub"])})
        return serialize_doc(user) if user else None
    except Exception:
        return None


def create_page_version(page_id: str, elements: list, user_email: str, action: str = "save"):
    """Create a version snapshot for a page"""
    version_count = page_versions_col.count_documents({"page_id": page_id})
    version = {
        "page_id": page_id,
        "version_number": version_count + 1,
        "elements": copy.deepcopy(elements),
        "created_at": datetime.now(timezone.utc),
        "created_by": user_email,
        "action": action,  # "save", "publish", "restore"
    }
    page_versions_col.insert_one(version)
    return version_count + 1


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

class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class ChangePasswordRequest(BaseModel):
    new_password: str

class PageContentUpdate(BaseModel):
    element_id: str
    content: Dict[str, Any]

class PageBulkContentUpdate(BaseModel):
    updates: List[PageContentUpdate]

class PageStatusUpdate(BaseModel):
    status: str  # "draft" or "published"


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
                "style": {
                    "classes": "pt-24 pb-32 px-16 bg-[#121414]"
                },
                "content": {},
                "children": [
                    {
                        "id": "hero-badge",
                        "type": "badge",
                        "tag": "span",
                        "label": "Category Badge",
                        "style": {
                            "classes": "inline-block px-3 py-1 bg-emerald-500/10 rounded-sm mb-6 text-[0.65rem] tracking-[0.2em] text-emerald-400 uppercase font-bold"
                        },
                        "content": {
                            "text": "Architecture of Clarity"
                        },
                        "children": []
                    },
                    {
                        "id": "hero-headline",
                        "type": "heading",
                        "tag": "h1",
                        "label": "Headline (H1)",
                        "style": {
                            "classes": "text-7xl font-bold leading-[1.05] tracking-tight text-white mb-8",
                            "fontSize": "64px",
                            "fontWeight": "700"
                        },
                        "content": {
                            "text": "We are skilled at making the complex plain and simple.",
                            "highlight": {
                                "word": "complex",
                                "color": "#4edea3"
                            }
                        },
                        "children": []
                    },
                    {
                        "id": "hero-description",
                        "type": "paragraph",
                        "tag": "p",
                        "label": "Body Text",
                        "style": {
                            "classes": "text-xl text-neutral-400 leading-relaxed mb-12 max-w-xl"
                        },
                        "content": {
                            "text": "We build digital systems that prioritize efficiency without sacrificing the soul of the creative vision. Editorial control meets technical precision."
                        },
                        "children": []
                    },
                    {
                        "id": "hero-cta-primary",
                        "type": "button",
                        "tag": "button",
                        "label": "Primary CTA",
                        "style": {
                            "classes": "bg-emerald-500 text-black px-8 py-3.5 rounded-lg font-bold uppercase tracking-widest text-xs"
                        },
                        "content": {
                            "text": "Start a Project",
                            "href": "#contact"
                        },
                        "children": []
                    },
                    {
                        "id": "hero-cta-secondary",
                        "type": "button",
                        "tag": "button",
                        "label": "Secondary CTA",
                        "style": {
                            "classes": "text-white font-bold uppercase tracking-widest text-xs border-b-2 border-white/20 hover:border-emerald-500"
                        },
                        "content": {
                            "text": "View Case Studies",
                            "href": "#work"
                        },
                        "children": []
                    }
                ]
            },
            {
                "id": "image-grid-section",
                "type": "section",
                "tag": "section",
                "label": "Image Grid",
                "style": {
                    "classes": "px-16 grid grid-cols-12 gap-8 items-end mb-24 bg-[#121414]"
                },
                "content": {},
                "children": [
                    {
                        "id": "grid-image-large",
                        "type": "image",
                        "tag": "img",
                        "label": "Large Image",
                        "style": {
                            "classes": "col-span-7 aspect-[4/5] rounded-sm overflow-hidden"
                        },
                        "content": {
                            "src": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
                            "alt": "Minimal Space"
                        },
                        "children": []
                    },
                    {
                        "id": "grid-image-small",
                        "type": "image",
                        "tag": "img",
                        "label": "Small Image",
                        "style": {
                            "classes": "col-span-5 aspect-square rounded-sm overflow-hidden"
                        },
                        "content": {
                            "src": "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=600&q=80",
                            "alt": "Detail"
                        },
                        "children": []
                    },
                    {
                        "id": "grid-quote-block",
                        "type": "quote",
                        "tag": "blockquote",
                        "label": "Quote Block",
                        "style": {
                            "classes": "col-span-5 p-8 border-l-2 border-emerald-500 bg-[#1a1b1b]"
                        },
                        "content": {
                            "title": "Obsessive Detail",
                            "text": "Every pixel is engineered to serve the narrative, ensuring a seamless bridge between data and design."
                        },
                        "children": []
                    }
                ]
            },
            {
                "id": "features-section",
                "type": "section",
                "tag": "section",
                "label": "Features Section",
                "style": {
                    "classes": "px-16 py-24 bg-[#0d0e0e]"
                },
                "content": {},
                "children": [
                    {
                        "id": "features-title",
                        "type": "heading",
                        "tag": "h2",
                        "label": "Section Title (H2)",
                        "style": {
                            "classes": "text-4xl font-bold tracking-tight text-white mb-4"
                        },
                        "content": {
                            "text": "Built for precision."
                        },
                        "children": []
                    },
                    {
                        "id": "features-subtitle",
                        "type": "paragraph",
                        "tag": "p",
                        "label": "Section Subtitle",
                        "style": {
                            "classes": "text-lg text-neutral-400 mb-16 max-w-2xl"
                        },
                        "content": {
                            "text": "Our approach combines meticulous engineering with an artistic sensibility that elevates every interface."
                        },
                        "children": []
                    },
                    {
                        "id": "feature-card-1",
                        "type": "card",
                        "tag": "div",
                        "label": "Feature Card 1",
                        "style": {
                            "classes": "p-8 bg-[#1a1b1b] rounded-sm"
                        },
                        "content": {
                            "title": "Visual Hierarchy",
                            "text": "Structure that guides the eye naturally through content layers, creating intuitive navigation paths."
                        },
                        "children": []
                    },
                    {
                        "id": "feature-card-2",
                        "type": "card",
                        "tag": "div",
                        "label": "Feature Card 2",
                        "style": {
                            "classes": "p-8 bg-[#1a1b1b] rounded-sm"
                        },
                        "content": {
                            "title": "Technical Precision",
                            "text": "Every component is engineered for performance, accessibility, and maintainability across all platforms."
                        },
                        "children": []
                    },
                    {
                        "id": "feature-card-3",
                        "type": "card",
                        "tag": "div",
                        "label": "Feature Card 3",
                        "style": {
                            "classes": "p-8 bg-[#1a1b1b] rounded-sm"
                        },
                        "content": {
                            "title": "Creative Control",
                            "text": "Fine-grained editorial tools that empower content teams without compromising design integrity."
                        },
                        "children": []
                    }
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
                "id": "about-hero",
                "type": "section",
                "tag": "section",
                "label": "About Hero",
                "style": {
                    "classes": "pt-24 pb-16 px-16 bg-[#121414]"
                },
                "content": {},
                "children": [
                    {
                        "id": "about-badge",
                        "type": "badge",
                        "tag": "span",
                        "label": "Page Badge",
                        "style": {
                            "classes": "inline-block px-3 py-1 bg-emerald-500/10 rounded-sm mb-6 text-[0.65rem] tracking-[0.2em] text-emerald-400 uppercase font-bold"
                        },
                        "content": {
                            "text": "Our Story"
                        },
                        "children": []
                    },
                    {
                        "id": "about-headline",
                        "type": "heading",
                        "tag": "h1",
                        "label": "Page Title (H1)",
                        "style": {
                            "classes": "text-6xl font-bold leading-[1.1] tracking-tight text-white mb-8"
                        },
                        "content": {
                            "text": "We believe in the power of clarity.",
                            "highlight": {
                                "word": "clarity",
                                "color": "#4edea3"
                            }
                        },
                        "children": []
                    },
                    {
                        "id": "about-intro",
                        "type": "paragraph",
                        "tag": "p",
                        "label": "Introduction",
                        "style": {
                            "classes": "text-xl text-neutral-400 leading-relaxed max-w-2xl"
                        },
                        "content": {
                            "text": "Founded in 2020, we have been pushing the boundaries of digital design. Our team of engineers and designers work in harmony to create systems that are both beautiful and functional."
                        },
                        "children": []
                    }
                ]
            },
            {
                "id": "about-values",
                "type": "section",
                "tag": "section",
                "label": "Values Section",
                "style": {
                    "classes": "px-16 py-24 bg-[#0d0e0e]"
                },
                "content": {},
                "children": [
                    {
                        "id": "values-title",
                        "type": "heading",
                        "tag": "h2",
                        "label": "Values Title (H2)",
                        "style": {
                            "classes": "text-3xl font-bold tracking-tight text-white mb-12"
                        },
                        "content": {
                            "text": "Our Values"
                        },
                        "children": []
                    },
                    {
                        "id": "value-1",
                        "type": "card",
                        "tag": "div",
                        "label": "Value Card 1",
                        "style": {
                            "classes": "p-6 bg-[#1a1b1b] rounded-sm"
                        },
                        "content": {
                            "title": "Precision",
                            "text": "Every detail matters. We measure twice and cut once, ensuring every component meets our exacting standards."
                        },
                        "children": []
                    },
                    {
                        "id": "value-2",
                        "type": "card",
                        "tag": "div",
                        "label": "Value Card 2",
                        "style": {
                            "classes": "p-6 bg-[#1a1b1b] rounded-sm"
                        },
                        "content": {
                            "title": "Collaboration",
                            "text": "Great work happens when diverse perspectives converge. We foster an environment where every voice shapes the outcome."
                        },
                        "children": []
                    },
                    {
                        "id": "value-3",
                        "type": "card",
                        "tag": "div",
                        "label": "Value Card 3",
                        "style": {
                            "classes": "p-6 bg-[#1a1b1b] rounded-sm"
                        },
                        "content": {
                            "title": "Innovation",
                            "text": "We stay at the frontier of technology, constantly exploring new approaches to solve complex design challenges."
                        },
                        "children": []
                    }
                ]
            }
        ]
    }


def seed_database():
    """Seed with default admin and demo pages if empty"""
    if users_col.count_documents({}) == 0:
        admin_user = {
            "email": "admin@monolith.cms",
            "password_hash": hash_password("admin123"),
            "name": "Admin",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        editor_user = {
            "email": "editor@monolith.cms",
            "password_hash": hash_password("editor123"),
            "name": "Editor",
            "role": "editor",
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        users_col.insert_many([admin_user, editor_user])
        print("Seeded users: admin@monolith.cms / admin123, editor@monolith.cms / editor123")

    if projects_col.count_documents({}) == 0:
        projects_col.insert_one({
            "name": "The Monolith",
            "slug": "the-monolith",
            "project_id": "default",
            "created_at": datetime.now(timezone.utc)
        })

    if pages_col.count_documents({}) == 0:
        pages_col.insert_one(get_demo_homepage())
        pages_col.insert_one(get_demo_about_page())
        print("Seeded demo pages: Homepage, About")


# ============================================================
# APP LIFECYCLE
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    users_col.create_index("email", unique=True)
    pages_col.create_index([("project_id", 1), ("slug", 1)])
    page_versions_col.create_index([("page_id", 1), ("version_number", DESCENDING)])
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
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user.get("name", ""),
            "role": user["role"]
        }
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
        "created_at": datetime.now(timezone.utc)
    }
    result = users_col.insert_one(new_user)
    return {"id": str(result.inserted_id), "email": req.email, "name": req.name, "role": req.role}


@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "role": current_user["role"]
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
        "created_at": u.get("created_at"),
    }) for u in users]


@app.put("/api/users/{user_id}")
async def update_user(user_id: str, body: UpdateUserRequest, current_user: dict = Depends(require_admin)):
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deactivation or role-change for the last admin
    if str(user["_id"]) == current_user["_id"]:
        if body.is_active is False:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        if body.role and body.role != "admin":
            admin_count = users_col.count_documents({"role": "admin", "is_active": {"$ne": False}})
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot change role: you are the last admin")

    update_fields = {}
    if body.name is not None:
        update_fields["name"] = body.name
    if body.role is not None and body.role in ["admin", "editor"]:
        update_fields["role"] = body.role
    if body.is_active is not None:
        update_fields["is_active"] = body.is_active

    if update_fields:
        users_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})

    updated = users_col.find_one({"_id": ObjectId(user_id)})
    return serialize_doc({
        "_id": updated["_id"],
        "email": updated["email"],
        "name": updated.get("name", ""),
        "role": updated["role"],
        "is_active": updated.get("is_active", True),
    })


@app.put("/api/users/{user_id}/password")
async def change_user_password(user_id: str, body: ChangePasswordRequest, current_user: dict = Depends(require_admin)):
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password_hash": hash_password(body.new_password)}}
    )
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
# PAGES ENDPOINTS
# ============================================================

@app.get("/api/pages")
async def list_pages(current_user: dict = Depends(get_current_user)):
    pages = list(pages_col.find({"project_id": "default"}))
    return [serialize_doc({
        "_id": p["_id"],
        "name": p["name"],
        "slug": p["slug"],
        "status": p["status"],
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
    """Update a single element's content (text, images, links only - NOT style/layout)"""
    page = pages_col.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    elements = page.get("elements", [])
    updated = update_element_content(elements, update.element_id, update.content)

    if not updated:
        raise HTTPException(status_code=404, detail=f"Element {update.element_id} not found")

    pages_col.update_one(
        {"_id": ObjectId(page_id)},
        {
            "$set": {
                "elements": elements,
                "updated_at": datetime.now(timezone.utc),
                "status": "draft"
            }
        }
    )
    return {"success": True, "element_id": update.element_id}


@app.put("/api/pages/{page_id}/content/bulk")
async def update_page_content_bulk(page_id: str, body: PageBulkContentUpdate, current_user: dict = Depends(get_current_user)):
    """Bulk update multiple elements' content and create a version snapshot"""
    page = pages_col.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Snapshot BEFORE applying changes
    create_page_version(page_id, page.get("elements", []), current_user.get("email", "unknown"), "save")

    elements = page.get("elements", [])
    for upd in body.updates:
        update_element_content(elements, upd.element_id, upd.content)

    pages_col.update_one(
        {"_id": ObjectId(page_id)},
        {
            "$set": {
                "elements": elements,
                "updated_at": datetime.now(timezone.utc),
                "status": "draft"
            }
        }
    )
    return {"success": True, "updated_count": len(body.updates)}


def update_element_content(elements, element_id, new_content):
    """Recursively find element by ID and update only its content"""
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
    """Update page status (draft/published)"""
    if body.status not in ["draft", "published"]:
        raise HTTPException(status_code=400, detail="Status must be 'draft' or 'published'")

    page = pages_col.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    update_fields = {
        "status": body.status,
        "updated_at": datetime.now(timezone.utc)
    }

    if body.status == "published":
        update_fields["published_at"] = datetime.now(timezone.utc)
        update_fields["published_elements"] = page.get("elements", [])
        create_page_version(page_id, page.get("elements", []), current_user.get("email", "unknown"), "publish")

    pages_col.update_one(
        {"_id": ObjectId(page_id)},
        {"$set": update_fields}
    )
    return {"success": True, "status": body.status}


# ============================================================
# PAGE VERSION HISTORY ENDPOINTS
# ============================================================

@app.get("/api/pages/{page_id}/versions")
async def list_page_versions(page_id: str, current_user: dict = Depends(get_current_user)):
    """List all version snapshots for a page"""
    versions = list(page_versions_col.find(
        {"page_id": page_id},
        {"elements": 0}  # Exclude full element tree for listing
    ).sort("version_number", DESCENDING).limit(50))
    return [serialize_doc(v) for v in versions]


@app.get("/api/pages/{page_id}/versions/{version_number}")
async def get_page_version(page_id: str, version_number: int, current_user: dict = Depends(get_current_user)):
    """Get a specific version snapshot (includes elements)"""
    version = page_versions_col.find_one({
        "page_id": page_id,
        "version_number": version_number
    })
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return serialize_doc(version)


@app.post("/api/pages/{page_id}/versions/{version_number}/restore")
async def restore_page_version(page_id: str, version_number: int, current_user: dict = Depends(get_current_user)):
    """Restore a page to a previous version"""
    version = page_versions_col.find_one({
        "page_id": page_id,
        "version_number": version_number
    })
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    page = pages_col.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Snapshot current state before restore
    create_page_version(page_id, page.get("elements", []), current_user.get("email", "unknown"), "restore")

    # Restore elements from version
    pages_col.update_one(
        {"_id": ObjectId(page_id)},
        {
            "$set": {
                "elements": version["elements"],
                "updated_at": datetime.now(timezone.utc),
                "status": "draft"
            }
        }
    )

    updated_page = pages_col.find_one({"_id": ObjectId(page_id)})
    return serialize_doc(updated_page)


# ============================================================
# PUBLIC API (for website consumption)
# ============================================================

@app.get("/api/public/pages")
async def public_list_pages():
    pages = list(pages_col.find({"project_id": "default", "status": "published"}))
    return [serialize_doc({
        "_id": p["_id"],
        "name": p["name"],
        "slug": p["slug"],
        "published_at": p.get("published_at"),
        "elements": p.get("published_elements", p.get("elements", []))
    }) for p in pages]


@app.get("/api/public/pages/{slug:path}")
async def public_get_page(slug: str):
    if not slug.startswith("/"):
        slug = "/" + slug
    page = pages_col.find_one({"slug": slug, "status": "published"})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found or not published")
    return serialize_doc({
        "_id": page["_id"],
        "name": page["name"],
        "slug": page["slug"],
        "published_at": page.get("published_at"),
        "elements": page.get("published_elements", page.get("elements", []))
    })


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "monolith-cms"}
