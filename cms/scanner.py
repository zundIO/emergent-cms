"""
The Monolith CMS - JSX Scanner

Walks the host website's frontend source files, identifies static, editable
elements (h1-h6, p, button, a, img with simple text/src), and returns a
list of suggestions. Optionally injects `data-cms-id` attributes back into
the source files so they can be picked up by the public client.js script.

Uses tree-sitter for robust AST-based parsing — no regex hacks.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple


def _get_tsx_parser():
    """Lazy import tree-sitter so the module is importable even if deps are missing."""
    from tree_sitter_language_pack import get_parser
    return get_parser("tsx")


# Element tags we consider editable
EDITABLE_TAGS = {
    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",
    "p": "paragraph",
    "button": "button",
    "a": "button",
    "span": "paragraph",
}
SELF_CLOSING_EDITABLE = {"img": "image"}

# Skip files matching these patterns (no edits intended for these)
SKIP_DIR_PARTS = {"node_modules", "components/ui", "components\\ui", "ui", "dist", "build", ".git"}
SKIP_FILE_PATTERNS = (
    re.compile(r".*\.test\.(js|jsx|ts|tsx)$"),
    re.compile(r".*\.spec\.(js|jsx|ts|tsx)$"),
    re.compile(r".*\.d\.ts$"),
    re.compile(r".*\.stories\.(js|jsx|ts|tsx)$"),
)


@dataclass
class Suggestion:
    file: str            # absolute path
    rel_file: str        # path relative to scan root
    line: int            # 1-indexed line
    column: int          # 1-indexed column of opening tag
    tag: str             # h1, p, button, img, ...
    element_type: str    # heading, paragraph, button, image
    text: str            # static text (or src for img)
    suggested_id: str    # generated id
    has_existing_id: bool
    existing_id: Optional[str]
    page_slug: str       # derived from file path
    insert_offset: int   # byte offset where to insert data-cms-id


def _slugify_filename(rel_path: str) -> str:
    name = os.path.splitext(os.path.basename(rel_path))[0]
    # HomePage -> home-page; AboutPage -> about-page
    name = re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()
    name = name.replace("page", "").strip("-")
    return name or "page"


def _derive_page_slug(rel_file: str) -> str:
    """Heuristic: pages/HomePage.js → '/'; pages/AboutPage.js → '/about'."""
    name = _slugify_filename(rel_file)
    if name in ("home", "index", "main", "landing", ""):
        return "/"
    return "/" + name


def _stable_id(rel_file: str, tag: str, text: str, index: int) -> str:
    """Generate a stable, readable id for an element."""
    base = _slugify_filename(rel_file)
    snippet = re.sub(r"[^a-z0-9]+", "-", text.lower())[:24].strip("-")
    suffix = f"{tag}-{index}"
    if snippet:
        return f"{base}-{snippet}-{suffix}".strip("-")
    return f"{base}-{suffix}".strip("-")


def _node_text(src: bytes, node) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _has_dynamic_children(node) -> bool:
    """True if any non-text/non-static child exists."""
    for child in node.children:
        if child.type in ("jsx_expression", "jsx_element", "jsx_self_closing_element"):
            return True
    return False


def _extract_static_text(src: bytes, node) -> Optional[str]:
    """Concatenate all jsx_text children of a jsx_element. Returns None if dynamic."""
    parts = []
    for child in node.children:
        if child.type == "jsx_text":
            parts.append(_node_text(src, child).strip())
        elif child.type in ("jsx_opening_element", "jsx_closing_element"):
            continue
        elif child.type == "jsx_expression":
            return None  # dynamic content -> skip
        elif child.type in ("jsx_element", "jsx_self_closing_element"):
            return None  # nested elements -> skip (too complex)
    text = " ".join(p for p in parts if p)
    return text if text else None


def _find_attribute(opening_node, attr_name: str, src: bytes) -> Optional[Tuple[str, object]]:
    """Find an attribute by name on a jsx_opening_element. Returns (raw_value, node) or None."""
    for child in opening_node.children:
        if child.type == "jsx_attribute":
            name_node = child.child_by_field_name("name") or (child.children[0] if child.children else None)
            if name_node and _node_text(src, name_node) == attr_name:
                value_node = child.child_by_field_name("value")
                if value_node is None and len(child.children) > 1:
                    value_node = child.children[-1]
                if value_node is None:
                    return ("", child)
                # Strip surrounding quotes/braces
                raw = _node_text(src, value_node)
                if raw.startswith('"') and raw.endswith('"'):
                    raw = raw[1:-1]
                elif raw.startswith("'") and raw.endswith("'"):
                    raw = raw[1:-1]
                return (raw, child)
    return None


def _opening_tag_name(opening_node, src: bytes) -> Optional[str]:
    name_node = opening_node.child_by_field_name("name")
    if name_node is None and opening_node.children:
        # First child after '<' is typically the identifier
        for c in opening_node.children:
            if c.type in ("identifier", "jsx_identifier", "nested_identifier", "member_expression"):
                name_node = c
                break
    if name_node is None:
        return None
    return _node_text(src, name_node)


def _is_html_lowercase(name: Optional[str]) -> bool:
    """True if name looks like an HTML primitive (lowercase, no dot)."""
    return bool(name) and name.islower() and "." not in name


def scan_file(path: str, root: str, start_index: int = 0) -> List[Suggestion]:
    """Parse a single JSX/TSX file and return suggestions."""
    with open(path, "rb") as f:
        src = f.read()

    # Use tsx parser — handles both .js with JSX and .tsx
    parser = _get_tsx_parser()
    tree = parser.parse(src)
    rel_file = os.path.relpath(path, root)
    page_slug = _derive_page_slug(rel_file)

    suggestions: List[Suggestion] = []
    counter = {"i": start_index}

    def visit(node):
        if node.type == "jsx_element":
            opening = next((c for c in node.children if c.type == "jsx_opening_element"), None)
            if opening:
                tag = _opening_tag_name(opening, src)
                if _is_html_lowercase(tag) and tag in EDITABLE_TAGS:
                    text = _extract_static_text(src, node)
                    if text and len(text) >= 2 and len(text) <= 500:
                        existing = _find_attribute(opening, "data-cms-id", src)
                        existing_id = existing[0] if existing else None
                        sid = existing_id or _stable_id(rel_file, tag, text, counter["i"])
                        # Insert position: just before the closing > of the opening tag
                        # tree-sitter gives the opening tag end_byte at the position AFTER the >
                        # So we insert at end_byte - 1 (before the >). For self-closing it's end_byte - 2.
                        insert_offset = opening.end_byte - 1
                        suggestions.append(Suggestion(
                            file=path,
                            rel_file=rel_file,
                            line=opening.start_point[0] + 1,
                            column=opening.start_point[1] + 1,
                            tag=tag,
                            element_type=EDITABLE_TAGS[tag],
                            text=text,
                            suggested_id=sid,
                            has_existing_id=bool(existing_id),
                            existing_id=existing_id,
                            page_slug=page_slug,
                            insert_offset=insert_offset,
                        ))
                        counter["i"] += 1
        elif node.type == "jsx_self_closing_element":
            tag = _opening_tag_name(node, src)
            if _is_html_lowercase(tag) and tag in SELF_CLOSING_EDITABLE:
                src_attr = _find_attribute(node, "src", src)
                if src_attr and src_attr[0] and not src_attr[0].startswith("{"):
                    existing = _find_attribute(node, "data-cms-id", src)
                    existing_id = existing[0] if existing else None
                    sid = existing_id or _stable_id(rel_file, tag, src_attr[0], counter["i"])
                    # For self-closing: <img ... />, end_byte points after />
                    # Insert before the trailing /> by going back 2 chars
                    insert_offset = node.end_byte - 2
                    suggestions.append(Suggestion(
                        file=path,
                        rel_file=rel_file,
                        line=node.start_point[0] + 1,
                        column=node.start_point[1] + 1,
                        tag=tag,
                        element_type=SELF_CLOSING_EDITABLE[tag],
                        text=src_attr[0],
                        suggested_id=sid,
                        has_existing_id=bool(existing_id),
                        existing_id=existing_id,
                        page_slug=page_slug,
                        insert_offset=insert_offset,
                    ))
                    counter["i"] += 1

        for child in node.children:
            visit(child)

    visit(tree.root_node)
    return suggestions


def _is_skipped(rel_path: str) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    if any(p in SKIP_DIR_PARTS for p in parts):
        return True
    if any(p.match(rel_path) for p in SKIP_FILE_PATTERNS):
        return True
    return False


def scan_directory(root: str, max_files: int = 200) -> List[Suggestion]:
    """Walk a directory, scan all JSX/TSX files, return all suggestions."""
    all_suggestions: List[Suggestion] = []
    counter = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # In-place prune skipped dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS]
        for fn in filenames:
            if not fn.endswith((".js", ".jsx", ".ts", ".tsx")):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            if _is_skipped(rel):
                continue
            try:
                suggestions = scan_file(full, root, start_index=counter)
                if suggestions:
                    all_suggestions.extend(suggestions)
                    counter += len(suggestions)
            except Exception as e:
                print(f"[CMS scanner] Failed on {rel}: {e}")
            if counter >= max_files * 30:
                break
    return all_suggestions


def apply_suggestions(suggestions: List[Suggestion]) -> dict:
    """Inject data-cms-id="..." into the source files for the given suggestions.

    Suggestions are applied per-file, sorted by insert_offset DESC so earlier
    edits don't shift later offsets within the same file.
    """
    by_file: dict[str, List[Suggestion]] = {}
    for s in suggestions:
        if s.has_existing_id:
            continue  # already has an id, leave alone
        by_file.setdefault(s.file, []).append(s)

    files_modified = 0
    elements_added = 0

    for path, items in by_file.items():
        # Sort descending by offset so earlier edits don't shift later ones
        items.sort(key=lambda x: x.insert_offset, reverse=True)
        with open(path, "rb") as f:
            src = bytearray(f.read())
        for s in items:
            inject = f' data-cms-id="{s.suggested_id}"'.encode("utf-8")
            src[s.insert_offset:s.insert_offset] = inject
            elements_added += 1
        with open(path, "wb") as f:
            f.write(bytes(src))
        files_modified += 1

    return {"files_modified": files_modified, "elements_added": elements_added}


def build_schema_from_suggestions(
    suggestions: List[Suggestion],
    project_name: str = "Auto-detected Site",
) -> dict:
    """Group suggestions into a CMS schema (project + pages + elements)."""
    from datetime import datetime, timezone

    # Group by page slug
    pages_map: dict[str, list] = {}
    for s in suggestions:
        pages_map.setdefault(s.page_slug, []).append(s)

    pages = []
    for slug, items in pages_map.items():
        page_name = "Homepage" if slug == "/" else slug.strip("/").replace("-", " ").title() or "Page"
        elements = []
        for s in items:
            element_id = s.existing_id if s.has_existing_id else s.suggested_id
            content_field = "src" if s.element_type == "image" else "text"
            elements.append({
                "id": element_id,
                "type": s.element_type,
                "tag": s.tag,
                "label": f"{s.element_type.title()} ({s.tag})",
                "content": {content_field: s.text},
                "style": {},
                "children": [],
            })
        pages.append({
            "name": page_name,
            "slug": slug,
            "elements": elements,
        })

    return {
        "project_name": project_name,
        "source_updated_at": datetime.now(timezone.utc).isoformat(),
        "pages": pages,
    }


def suggestions_to_dicts(suggestions: List[Suggestion]) -> List[dict]:
    return [asdict(s) for s in suggestions]
