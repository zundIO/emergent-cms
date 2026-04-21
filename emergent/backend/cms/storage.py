"""File-based content storage for the embedded CMS.

All content lives in a single JSON file under ``<cwd>/cms-data/content.json``.
The directory is created on first use and is intended to be gitignored.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional

_LOCK = RLock()


def _data_dir() -> Path:
    base = Path(os.environ.get("CMS_DATA_DIR") or (Path.cwd() / "cms-data"))
    base.mkdir(parents=True, exist_ok=True)
    return base


def _content_file() -> Path:
    return _data_dir() / "content.json"


def _version_file() -> Path:
    return _data_dir() / ".cms-version.json"


def _env_file() -> Path:
    return _data_dir() / ".cms-env.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> Dict[str, Any]:
    f = _content_file()
    if not f.exists():
        f.write_text(json.dumps({"elements": {}, "version": 1}, indent=2))
    return json.loads(f.read_text() or "{}")


def get_content() -> Dict[str, Any]:
    with _LOCK:
        return _ensure()


def save_content(content: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        data = {
            "elements": content.get("elements", {}),
            "version": int(content.get("version", 0)) + 1,
            "updated_at": _now(),
        }
        _content_file().write_text(json.dumps(data, indent=2))
        return data


def update_element(element_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        current = _ensure()
        existing = current["elements"].get(element_id, {})
        existing.update(patch)
        existing["updated_at"] = _now()
        existing["id"] = element_id
        current["elements"][element_id] = existing
        return save_content(current)


def merge_elements(discovered: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    with _LOCK:
        current = _ensure()
        new_count = 0
        total = 0
        for el in discovered:
            total += 1
            eid = el.get("id")
            if not eid:
                continue
            existing = current["elements"].get(eid)
            if not existing:
                current["elements"][eid] = {
                    **el,
                    "published": False,
                    "created_at": _now(),
                    "updated_at": _now(),
                }
                new_count += 1
            else:
                # Keep saved content but refresh metadata
                existing["tag"] = el.get("tag", existing.get("tag"))
                existing["type"] = el.get("type", existing.get("type"))
                existing["label"] = el.get("label", existing.get("label"))
                existing["page"] = el.get("page", existing.get("page"))
                current["elements"][eid] = existing
        save_content(current)
        return {"merged": total, "new": new_count}


def get_published() -> Dict[str, Any]:
    current = get_content()
    return {
        eid: entry
        for eid, entry in current.get("elements", {}).items()
        if entry.get("published")
    }


# ---- Lightweight local secrets store (no .env.local tinkering in Emergent) ----

def get_env(key: str) -> Optional[str]:
    f = _env_file()
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text())
    except Exception:
        return None
    return data.get(key)


def set_env(updates: Dict[str, str]) -> None:
    f = _env_file()
    data: Dict[str, str] = {}
    if f.exists():
        try:
            data = json.loads(f.read_text())
        except Exception:
            data = {}
    data.update(updates)
    f.write_text(json.dumps(data, indent=2))
    try:
        os.chmod(f, 0o600)
    except Exception:
        pass


def read_local_version() -> Dict[str, Any]:
    f = _version_file()
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            pass
    return {"sha": None, "updated_at": None}


def write_local_version(sha: str) -> None:
    _version_file().write_text(json.dumps({"sha": sha, "updated_at": _now()}, indent=2))
