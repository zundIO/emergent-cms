"""JSX source-code scanner (refined).

Walks ``frontend/src`` and finds *customer-editable* content in JSX/TSX files.
The emphasis is on being **conservative**: we only want strings that are
actually visible to end-users on the rendered website, not strings that live
inside UI library internals, icon references, or developer scaffolding.

Heuristics:
  * Skip entire directories that typically contain library / design-system
    code (``components/ui``, ``ui``, ``radix``, ``shadcn``, ``node_modules``).
  * Skip short / identifier-like strings (e.g. Material Icon names such as
    ``shopping_cart``).
  * Skip content that's obviously JSX expressions (``{variable}``).
  * Elements with ``data-cms-id`` already are kept as-is.

The scanner also knows how to **undo** its own source patches for users who
want to remove the injected ``data-cms-id`` attributes.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

SCAN_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}

# Directories whose contents are almost certainly NOT customer-editable content.
SKIP_DIR_NAMES = {
    "node_modules", ".next", ".git", "build", "dist", "coverage",
    "ui", "radix", "shadcn", "hooks", "lib", "utils", "utilities",
    "assets", "styles", "cms",
}

# Files that are definitely not content pages.
SKIP_FILE_PATTERNS = (
    re.compile(r"\.(test|spec|stories)\.(js|jsx|ts|tsx)$", re.IGNORECASE),
    re.compile(r"(^|/)(index|setupTests|reportWebVitals)\.(js|jsx|ts|tsx)$"),
)

# HTML tags we consider editable content
TEXT_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "button", "li", "blockquote")
TAGS_UNION = "|".join(TEXT_TAGS)

# Identifier / icon-name pattern: single snake_case or kebab-case word
ICON_LIKE = re.compile(r"^[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*$")

# Text that's almost certainly not customer-facing content
def _is_noise(text: str, tag: str) -> bool:
    t = text.strip()
    if not t:
        return True
    if len(t) < 2:
        return True
    # Material-Icon-style single tokens: "shopping_cart", "arrow-left", "home"
    if ICON_LIKE.match(t) and len(t) < 30 and " " not in t:
        return True
    # Purely numeric / dates / ids
    if re.fullmatch(r"[0-9\s.,/-]+", t):
        return True
    return False


def _find_frontend_src() -> Optional[Path]:
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
        if any(part.lower() in SKIP_DIR_NAMES for part in path.parts):
            continue
        if any(p.search(str(path)) for p in SKIP_FILE_PATTERNS):
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
    m = re.search(rf'{name}\s*=\s*"([^"]*)"', attr_blob)
    if m:
        return m.group(1)
    m = re.search(rf"{name}\s*=\s*'([^']*)'", attr_blob)
    if m:
        return m.group(1)
    return ""


def scan_and_patch(inject: bool = True) -> Dict[str, Any]:
    """Scan JSX source files and optionally inject ``data-cms-id`` attributes."""
    root = _find_frontend_src()
    if not root:
        return {"success": False, "error": "frontend/src not found"}

    discovered: List[Dict[str, Any]] = []
    patched_files: List[str] = []

    text_pat = re.compile(
        rf"<({TAGS_UNION})((?:\s+[^>]*?)?)>([^<{{}}]+?)</\1>",
        re.DOTALL | re.IGNORECASE,
    )
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

            if _is_noise(text, tag):
                return m.group(0)

            if "data-cms-id" in attrs:
                existing_id = _extract_attr(attrs, "data-cms-id")
                entry = {
                    "id": existing_id,
                    "tag": tag,
                    "type": _classify(tag),
                    "label": text[:60],
                    "content": {"text": text},
                    "page": relative,
                }
                if tag == "a":
                    entry["content"]["href"] = _extract_attr(attrs, "href")
                discovered.append(entry)
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

            # Skip tiny decorative / dynamic imgs
            if not src or src.startswith("{") or len(src) < 4:
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


# ---------------------------------------------------------------------------
# Undo: strip injected data-cms-id attributes from source files.
# ---------------------------------------------------------------------------

_DATA_CMS_ID_ATTR = re.compile(r"\s+data-cms-id=\"[^\"]*\"")


def undo_patch() -> Dict[str, Any]:
    root = _find_frontend_src()
    if not root:
        return {"success": False, "error": "frontend/src not found"}

    cleaned_files: List[str] = []
    total_removed = 0

    for path in _iter_source_files(root):
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        count = len(_DATA_CMS_ID_ATTR.findall(original))
        if count == 0:
            continue
        new_src = _DATA_CMS_ID_ATTR.sub("", original)
        if new_src != original:
            try:
                path.write_text(new_src, encoding="utf-8")
                cleaned_files.append(str(path.relative_to(root)).replace("\\", "/"))
                total_removed += count
            except OSError:
                continue

    return {
        "success": True,
        "cleaned_files": cleaned_files,
        "attributes_removed": total_removed,
    }
