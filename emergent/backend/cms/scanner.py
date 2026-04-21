"""JSX source-code scanner.

Walks ``frontend/src`` recursively, finds editable elements in .js/.jsx/.ts/.tsx
files, extracts their current text/src content, generates stable IDs, and
optionally injects ``data-cms-id`` attributes into the source so the browser
client can later apply content overrides.

This is what lets the CMS discover elements WITHOUT anybody having to visit
the running website first.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCAN_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}
SKIP_DIR_NAMES = {"node_modules", ".next", ".git", "build", "dist", "coverage"}

# Plain HTML tags that can carry editable content. We only scan LOWERCASE tags
# — uppercase names are React components, not editable DOM.
TEXT_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "button", "li", "blockquote", "span")
TAGS_UNION = "|".join(TEXT_TAGS)


def _find_frontend_src() -> Optional[Path]:
    """Locate the project's ``frontend/src`` directory.

    Search order accounts for the common layouts:
    - CWD is project root                 -> ``./frontend/src``
    - CWD is ``backend/`` inside the proj -> ``../frontend/src``
    - Emergent fixed layout               -> ``/app/frontend/src``
    """
    candidates = [
        Path.cwd() / "frontend" / "src",
        Path.cwd().parent / "frontend" / "src",
        Path("/app/frontend/src"),
    ]
    for c in candidates:
        try:
            if c.exists() and c.is_dir():
                return c.resolve()
        except OSError:
            continue
    return None


def _iter_source_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.name.startswith("."):
            continue
        yield path


def _classify(tag: str) -> str:
    tag = tag.lower()
    if re.match(r"^h[1-6]$", tag):
        return "heading"
    if tag == "img":
        return "image"
    if tag == "a":
        return "link"
    if tag == "button":
        return "button"
    if tag in ("p", "blockquote"):
        return "paragraph"
    return "text"


def _extract_attr(attr_blob: str, name: str) -> str:
    """Extract a string attribute value from a JSX attribute blob.

    Handles ``attr="value"``, ``attr='value'``.  Expressions like
    ``attr={value}`` are intentionally left empty so we don't mangle dynamic
    bindings.
    """
    m = re.search(rf'{name}\s*=\s*"([^"]*)"', attr_blob)
    if m:
        return m.group(1)
    m = re.search(rf"{name}\s*=\s*'([^']*)'", attr_blob)
    if m:
        return m.group(1)
    return ""


def scan_and_patch(inject: bool = True) -> Dict[str, Any]:
    """Scan JSX source files and optionally inject ``data-cms-id`` attributes.

    Args:
        inject: when True, rewrites files in-place to add ``data-cms-id``
            attributes on elements that don't already have one.

    Returns a summary dict with discovered elements.
    """
    root = _find_frontend_src()
    if not root:
        return {"success": False, "error": "frontend/src not found"}

    discovered: List[Dict[str, Any]] = []
    patched_files: List[str] = []

    # Regex patterns (compiled once)
    # 1) <tag ...>TEXT</tag>   — only captures plain text (no JSX expressions / children)
    text_pat = re.compile(
        rf"<({TAGS_UNION})((?:\s+[^>]*?)?)>([^<{{}}]+?)</\1>",
        re.DOTALL | re.IGNORECASE,
    )
    # 2) <img ... />  or  <img ...>
    img_pat = re.compile(r"<img\b((?:\s+[^>]*?)?)\s*(/?)>", re.IGNORECASE)

    for path in _iter_source_files(root):
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        counter: Dict[str, int] = {}
        relative = str(path.relative_to(root)).replace("\\", "/")

        def _next_id(tag: str) -> str:
            idx = counter.get(tag, 0)
            counter[tag] = idx + 1
            return f"{relative}:{tag}:{idx}"

        def replace_text(m: "re.Match[str]") -> str:
            tag = m.group(1).lower()
            attrs = m.group(2) or ""
            text = m.group(3).strip()

            if not text:
                return m.group(0)

            # Skip empty placeholders
            if len(text) < 1 or len(text) > 2000:
                return m.group(0)

            if "data-cms-id" in attrs:
                # Already tagged — still include in discovery list
                existing_id = _extract_attr(attrs, "data-cms-id")
                discovered.append({
                    "id": existing_id,
                    "tag": tag,
                    "type": _classify(tag),
                    "label": text[:60],
                    "content": {"text": text, **({"href": _extract_attr(attrs, "href")} if tag == "a" else {})},
                    "page": relative,
                })
                return m.group(0)

            el_id = _next_id(tag)
            entry = {
                "id": el_id,
                "tag": tag,
                "type": _classify(tag),
                "label": text[:60],
                "content": {"text": text},
                "page": relative,
            }
            if tag == "a":
                entry["content"]["href"] = _extract_attr(attrs, "href")
            discovered.append(entry)

            if inject:
                new_attrs = attrs + f' data-cms-id="{el_id}"'
                return f"<{tag}{new_attrs}>{m.group(3)}</{tag}>"
            return m.group(0)

        def replace_img(m: "re.Match[str]") -> str:
            attrs = m.group(1) or ""
            self_closing = m.group(2) or ""
            src = _extract_attr(attrs, "src")
            alt = _extract_attr(attrs, "alt")

            if not src:
                return m.group(0)

            if "data-cms-id" in attrs:
                existing_id = _extract_attr(attrs, "data-cms-id")
                discovered.append({
                    "id": existing_id,
                    "tag": "img",
                    "type": "image",
                    "label": alt or src or existing_id,
                    "content": {"src": src, "alt": alt},
                    "page": relative,
                })
                return m.group(0)

            el_id = _next_id("img")
            discovered.append({
                "id": el_id,
                "tag": "img",
                "type": "image",
                "label": (alt or src or el_id)[:60],
                "content": {"src": src, "alt": alt},
                "page": relative,
            })
            if inject:
                return f"<img{attrs} data-cms-id=\"{el_id}\"{(' ' + self_closing).rstrip()}>"
            return m.group(0)

        new_src = text_pat.sub(replace_text, original)
        new_src = img_pat.sub(replace_img, new_src)

        if inject and new_src != original:
            try:
                path.write_text(new_src, encoding="utf-8")
                patched_files.append(relative)
            except OSError:
                pass

    # Merge into storage
    from . import storage
    result = storage.merge_elements(discovered)

    return {
        "success": True,
        "root": str(root),
        "discovered": len(discovered),
        "new": result.get("new", 0),
        "patched_files": patched_files,
        "injected": inject,
    }
