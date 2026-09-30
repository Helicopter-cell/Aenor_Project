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