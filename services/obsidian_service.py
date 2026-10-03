"""Load Obsidian Markdown notes as graph data for the scenario page."""

import html
import re
from pathlib import Path, PurePosixPath
from urllib.parse import quote

import bleach
import markdown


WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
ALLOWED_HTML_TAGS = {
    "a", "blockquote", "br", "code", "del", "em", "h1", "h2", "h3",
    "h4", "h5", "h6", "hr", "li", "ol", "p", "pre", "strong", "table",
    "tbody", "td", "th", "thead", "tr", "ul",
}
HTML_CLEANER = bleach.Cleaner(
    tags=ALLOWED_HTML_TAGS,
    attributes={"a": ["href", "title"], "code": ["class"]},
    protocols={"http", "https", "mailto"},
    strip=True,
    strip_comments=True,
)


def _note_key(value: str) -> str:
    normalized = value.strip().replace("\\", "/").split("#", 1)[0]
    if normalized.lower().endswith(".md"):
        normalized = normalized[:-3]
    return PurePosixPath(normalized).as_posix().strip("./").casefold()


def _plain_summary(text: str, title: str) -> str:
    lines = text.splitlines()
    if lines and HEADING_RE.match(lines[0]):
        lines = lines[1:]
    paragraph = []
    for line in lines:
        if not line.strip():
            if paragraph:
                break
            continue
        if HEADING_RE.match(line):
            continue
        paragraph.append(line.strip())
    summary = " ".join(paragraph)
    summary = WIKILINK_RE.sub(lambda match: match.group(1).split("|", 1)[-1], summary)
    summary = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", summary)
    summary = re.sub(r"<[^>]*>|[*_~`>#]", "", summary)
    summary = re.sub(r"\s+", " ", summary).strip()
    if not summary:
        summary = title
    return summary[:237].rstrip() + ("..." if len(summary) > 240 else "")


def parse_obsidian_vault(vault_path: Path) -> dict:
    """Return nodes and directed links for Markdown files under ``vault_path``."""
    notes = []
    for path in sorted(vault_path.rglob("*.md")) if vault_path.exists() else []:
        if not path.is_file():
            continue
        relative_path = path.relative_to(vault_path)
        note_id = relative_path.with_suffix("").as_posix()
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        title_match = HEADING_RE.search(text)
        title = title_match.group(1).strip(" #") if title_match else path.stem
        notes.append({
            "id": note_id,
            "title": title,
            "summary": _plain_summary(text, title),
            "source": text,
        })

    exact_lookup = {_note_key(note["id"]): note for note in notes}
    basename_lookup = {}
    for note in notes:
        basename_lookup.setdefault(_note_key(Path(note["id"]).name), []).append(note)

    def resolve(target: str):
        key = _note_key(target)
        if not key:
            return None
        if key in exact_lookup:
            return exact_lookup[key]
        candidates = basename_lookup.get(_note_key(PurePosixPath(key).name), [])
        return candidates[0] if len(candidates) == 1 else None

    nodes = []
    edge_counts = {}
    link_number = 0
    for note in notes:
        replacements = {}

        def replace_wikilink(match):
            nonlocal link_number
            raw_link = match.group(1)
            target, separator, alias = raw_link.partition("|")
            target_note = resolve(target)
            display = alias.strip() if separator else PurePosixPath(target.strip()).name
            if target_note is None or target_note["id"] == note["id"]:
                return html.escape(display or target.strip())

            pair = tuple(sorted((note["id"], target_note["id"])))
            edge_counts[pair] = edge_counts.get(pair, 0) + 1
            link_number += 1
            token = f"OBSIDIANLINKTOKEN{link_number}END"
            href = quote(f"vault-{target_note['id']}", safe="/")
            replacements[token] = (
                f'<a href="#{html.escape(href, quote=True)}">'
                f"{html.escape(display or target_note['title'])}</a>"
            )
            return token

        markdown_source = WIKILINK_RE.sub(replace_wikilink, note["source"])
        preview_html = markdown.markdown(markdown_source, extensions=["extra", "sane_lists"])
        for token, link_html in replacements.items():
            preview_html = preview_html.replace(token, link_html)
        preview_html = HTML_CLEANER.clean(preview_html)
        nodes.append({
            "id": note["id"],
            "title": note["title"],
            "summary": note["summary"],
            "content_html": preview_html,
        })

    notes_by_id = {note["id"]: note for note in notes}
    edges = [
        {
            "id": f"edge-{index}",
            "from": source_id,
            "to": target_id,
            "value": count,
            "title": f"{notes_by_id[source_id]['title']} - {notes_by_id[target_id]['title']} ({count})",
        }
        for index, ((source_id, target_id), count) in enumerate(sorted(edge_counts.items()), start=1)
    ]
    return {"nodes": nodes, "edges": edges}


def build_obsidian_outline(vault_path: Path) -> str:
    """Build a hierarchical Markdown outline of folders and note contents."""
    root = {"label": "Coffre Obsidian", "children": []}
    folders = {}

    def add_node(parent, label):
        node = {"label": html.escape(label, quote=False), "children": []}
        parent["children"].append(node)
        return node

    def clean_label(value):
        value = WIKILINK_RE.sub(
            lambda match: match.group(1).partition("|")[2].strip()
            or match.group(1).partition("|")[0].strip(),
            value,
        )
        value = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", value)
        value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
        value = re.sub(r"[`*_~]", "", value)
        return re.sub(r"\s+", " ", value).strip()

    def sentences(value):
        cleaned = clean_label(value)
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]

    for path in sorted(vault_path.rglob("*.md")) if vault_path.exists() else []:
        if not path.is_file():
            continue

        relative_path = path.relative_to(vault_path)
        parent = root
        folder_key = []
        for part in relative_path.parent.parts:
            folder_key.append(part)
            key = "/".join(folder_key)
            if key not in folders:
                folders[key] = add_node(parent, part)
            parent = folders[key]

        text = path.read_text(encoding="utf-8-sig", errors="replace")
        title_match = HEADING_RE.search(text)
        title = title_match.group(1).strip(" #") if title_match else path.stem
        file_node = add_node(parent, clean_label(title))
        section_stack = [(0, file_node)]
        list_stack = []
        in_code_fence = False
        file_title_key = clean_label(title).casefold()

        lines = text.splitlines()
        if lines and lines[0].strip() == "---":
            lines = lines[1:]
            in_front_matter = True
        else:
            in_front_matter = False

        for line in lines:
            stripped = line.strip()
            if in_front_matter:
                if stripped == "---":
                    in_front_matter = False
                continue
            if not stripped:
                continue
            if re.match(r"^(```|~~~)", stripped):
                in_code_fence = not in_code_fence
                continue

            if not in_code_fence:
                heading = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
                if heading:
                    level = len(heading.group(1))
                    heading_label = clean_label(heading.group(2))
                    if level == 1 and heading_label.casefold() == file_title_key:
                        list_stack.clear()
                        continue
                    while len(section_stack) > 1 and section_stack[-1][0] >= level:
                        section_stack.pop()
                    section = add_node(section_stack[-1][1], heading_label)
                    section_stack.append((level, section))
                    list_stack.clear()
                    continue

                bullet = re.match(r"^(\s*)(?:[-*+]\s+|\d+[.)]\s+)(.+)$", line)
                if bullet:
                    indentation = len(bullet.group(1).expandtabs(4))
                    while list_stack and list_stack[-1][0] >= indentation:
                        list_stack.pop()
                    list_parent = list_stack[-1][1] if list_stack else section_stack[-1][1]
                    label = re.sub(r"^\[[ xX]\]\s*", "", bullet.group(2))
                    bullet_node = add_node(list_parent, clean_label(label))
                    list_stack.append((indentation, bullet_node))
                    for sentence in sentences(label):
                        if sentence != clean_label(label):
                            add_node(bullet_node, sentence)
                    continue

            content_parent = list_stack[-1][1] if list_stack else section_stack[-1][1]
            content = stripped[1:-1] if in_code_fence and stripped.startswith("`") and stripped.endswith("`") else stripped
            for sentence in sentences(content):
                add_node(content_parent, sentence)

    result = ["# Coffre Obsidian"]

    def write_children(node, depth=0):
        for child in node["children"]:
            result.append(f"{'  ' * depth}- {child['label']}")
            write_children(child, depth + 1)

    write_children(root)
    return "\n".join(result)

