"""
Host FastAPI application.
In the real Emergent-Stack installation, this file is YOUR website's server.py.
The CMS is mounted into it via `install_cms(...)` from the cms package.
"""
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Make /app importable so we can `from cms import install_cms`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cms import install_cms  # noqa: E402

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "monolith_cms")
JWT_SECRET = os.environ.get("JWT_SECRET", "monolith-cms-secret-key-change-in-production")
CMS_ADMIN_EMAIL = os.environ.get("CMS_ADMIN_EMAIL", "admin@monolith.cms")
CMS_ADMIN_PASSWORD = os.environ.get("CMS_ADMIN_PASSWORD", "admin123")

# Path to the built React admin UI (populated by install.sh)
CMS_STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "cms", "static"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Monolith CMS Host", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the CMS at its canonical prefix /api/cms
install_cms(
    app,
    mongo_url=MONGO_URL,
    db_name=DB_NAME,
    collection_prefix="cms_",
    api_prefix="/api/cms",
    static_path="/api/cms-admin",
    static_dir=CMS_STATIC_DIR if os.path.isdir(CMS_STATIC_DIR) else None,
    jwt_secret=JWT_SECRET,
    admin_email=CMS_ADMIN_EMAIL,
    admin_password=CMS_ADMIN_PASSWORD,
    seed_demo_content=True,  # demo/dev only
    add_cors=False,          # host added CORS above
)
