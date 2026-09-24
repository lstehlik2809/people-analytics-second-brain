"""Convert distill .Rmd blog posts into a Quartz-ready markdown vault.

Idempotent: re-run any time; only notes whose source .Rmd or rendered .html
changed are rewritten.
Usage: python pipeline/convert.py [--force]
"""

import argparse
import base64
import binascii
import hashlib
import json
import re
import shutil
import sys
from html import escape as html_escape
from html import unescape as html_unescape
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from urllib.parse import unquote, unquote_to_bytes

BLOG_POSTS = Path(r"D:\_WORKFORCE_ANALYTICS\People_Analytics_Blog\_posts")
BLOG_BASE_URL = "https://blog-about-people-analytics.netlify.app/posts/"
ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "vault"
NOTES_DIR = VAULT / "posts"
CACHE = ROOT / "pipeline" / "cache"
MANIFEST = CACHE / "manifest.json"

# target is parsed in img_sub, so filenames containing spaces still match
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
TITLE_RE = re.compile(r"\s+\"[^\"]*\"\s*$")
HTML_IMG_RE = re.compile(r"<img\b([^>]*?)/?>", re.I)
HTML_OBJECT_RE = re.compile(r"<object\b([^>]*?)>", re.I)
HTML_LINK_RE = re.compile(r"<a\b([^>]*?)>", re.I)
HTML_MEDIA_RE = re.compile(r"<(?:source|video|audio|embed)\b([^>]*?)/?>", re.I)
ATTR_KV_RE = re.compile(r"""([\w-]+)\s*=\s*(["'])(.*?)\2""")
ATTR_RE = re.compile(r"(\)|\`)\{[^{}\n]*\}")  # pandoc attribute blocks after ) or `
CHUNK_RE = re.compile(r"^```\{(r|R)\b[^}]*\}\s*$", re.M)
PY_CHUNK_RE = re.compile(r"^```\{python[^}]*\}\s*$", re.M)
OTHER_CHUNK_RE = re.compile(r"^```\{[^}]*\}\s*$", re.M)
R_CHUNK_RE = re.compile(r"^```\{[rR]\b[^}]*\}\s*\n(.*?)^```\s*$", re.M | re.S)
YOUTUBE_CALL_RE = re.compile(
    r'''vembedr::embed_youtube\(\s*["']([A-Za-z0-9_-]{11})["']\s*\)'''
)
# Distill sometimes embeds knitr figures directly into the rendered HTML even
# when other post assets are external. Including a converter marker in the
# content hash rebuilds only posts with this representation when support for it
# changes, rather than invalidating the entire manifest.
EMBEDDED_FIGURE_RE = re.compile(
    rb"<div[^>]*class=[\"'][^\"']*\bfigure\b[^\"']*[\"'][^>]*>"
    rb".*?<img[^>]+src=[\"']data:image/",
    re.I | re.S,
)
EMBEDDED_FIGURE_HASH_MARKER = b"\0embedded-generated-figures-v1"
# Keep local attachments embedded through raw HTML (for example a PDF carousel)
# alongside their note. The marker lets existing manifests rebuild only affected
# posts when this support is introduced.
LOCAL_HTML_ASSET_RE = re.compile(
    rb"<(?:object|a)\b[^>]*(?:data|href)\s*=\s*[\"']files/"
    rb"|<(?:source|video|audio)\b[^>]*src\s*=\s*[\"'](?!https?://|//|data:)",
    re.I,
)
LOCAL_HTML_ASSET_HASH_MARKER = b"\0local-html-assets-v2"
# Local documents can be referenced directly (rather than from a ``files/``
# subdirectory), especially when the same attachment is embedded by multiple
# posts. Hash those referenced files too, so a document-only update rebuilds
# every note that embeds it.
LOCAL_DIRECT_ATTACHMENT_RE = re.compile(
    rb"(?:data|href|src)\s*=\s*[\"'](?!https?://|//|data:|#)([^\"']+)", re.I)
LOCAL_DIRECT_ATTACHMENT_HASH_MARKER = b"\0local-direct-attachments-v1"
PLOTLY_WIDGET_RE = re.compile(
    rb"<div[^>]*class=[\"'][^\"']*\bplotly\b[^\"']*\bhtml-widget\b[^\"']*[\"']",
    re.I,
)
PLOTLY_WIDGET_HASH_MARKER = b"\0plotly-widgets-v2"
OUTPUT_WIDGET_RE = re.compile(
    rb'<div[^>]*class=["\'][^"\']*\b(?:datatables|r2d3|forceNetwork|swipeR)\b[^"\']*\bhtml-widget\b',
    re.I,
)
OUTPUT_WIDGET_HASH_MARKER = b"\0rendered-output-widgets-v1"
RELATED_BLOCK_RE = re.compile(r"<!-- RELATED:BEGIN -->.*?<!-- RELATED:END -->", re.S)
DATA_IMAGE_RE = re.compile(
    r"^data:(image/[a-z0-9.+-]+)((?:;[^,]*)?),(.*)$", re.I | re.S)


def slugify_tag(tag: str) -> str:
    # "/" must not survive: Quartz reads it as tag hierarchy, so a category
    # like "i/o psychology" would spawn a nonsensical parent tag "i"
    return re.sub(r"[^a-z0-9]+", "-", tag.lower().strip()).strip("-")


def note_slug(post_dir_name: str) -> str:
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", post_dir_name)


def split_frontmatter(text: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None, text
    meta = yaml.safe_load(m.group(1))
    return meta, text[m.end():]


def clean_description(desc) -> str:
    if not desc:
        return ""
    return re.sub(r"\s+", " ", str(desc)).strip()


def convert_body(body: str, post_dir: Path, asset_dir: Path, slug: str, warnings: list) -> str:
    # A vembedr chunk produces a video in the rendered blog, but Quartz does
    # not run R. Replace simple video-only chunks with the equivalent embed.
    def youtube_chunk_sub(m):
        lines = [line.strip() for line in m.group(1).splitlines() if line.strip()]
        calls = [YOUTUBE_CALL_RE.fullmatch(line) for line in lines
                 if line != "library(vembedr)"]
        if len(calls) != 1 or calls[0] is None:
            return m.group(0)
        video_id = calls[0].group(1)
        return (
            '<iframe title="YouTube video" '
            f'src="https://www.youtube.com/embed/{video_id}" '
            'style="width:100%;aspect-ratio:16/9;border:0" '
            'loading="lazy" allowfullscreen></iframe>'
        )

    body = R_CHUNK_RE.sub(youtube_chunk_sub, body)
    # code chunk headers -> plain fenced blocks
    body = CHUNK_RE.sub("```r", body)
    body = PY_CHUNK_RE.sub("```python", body)
    body = OTHER_CHUNK_RE.sub("```", body)

    def copy_asset(path: str):
        """Copy a local asset into the note's asset dir; return its new ref,
        or None if it is remote or missing."""
        if path.startswith(("http://", "https://", "data:")):
            return None
        src = post_dir / unquote(path)
        if not src.exists():
            warnings.append(f"{slug}: missing image {path}")
            return None
        # spaces in a filename break markdown links, so normalize on copy
        dest_name = src.name.replace(" ", "-")
        asset_dir.mkdir(parents=True, exist_ok=True)
        dest = asset_dir / dest_name
        if not dest.exists() or src.read_bytes() != dest.read_bytes():
            shutil.copy2(src, dest)
        return f"./{slug}/{dest_name}"

    def img_sub(m):
        alt, target = m.group(1), m.group(2).strip()
        path = TITLE_RE.sub("", target).strip().strip("<>")
        return f"![{alt}]({copy_asset(path) or path})"

    body = IMG_RE.sub(img_sub, body)

    # posts also embed figures with raw <img src="..."> tags; rewrite them as
    # markdown so Quartz resolves their paths the same way it does elsewhere
    def html_img_sub(m):
        attrs = dict((k.lower(), v) for k, _, v in ATTR_KV_RE.findall(m.group(1)))
        src = attrs.get("src", "").strip()
        if (slug == "interpretable-ml" and src in {"charts.png", "./charts.png"}
                and not (post_dir / "charts.png").exists()):
            warnings.append(f"{slug}: omitted missing raw image {src}")
            return ""
        new = copy_asset(src)
        return f"![{attrs.get('alt', '')}]({new})" if new else m.group(0)

    body = HTML_IMG_RE.sub(html_img_sub, body)

    media_extensions = {
        ".mp4", ".m4v", ".mov", ".ogv", ".webm", ".avi",
        ".mp3", ".m4a", ".ogg", ".oga", ".wav",
    }
    attachment_extensions = {".pdf"}

    def html_asset_sub(m, attr: str, *, media: bool = False):
        attrs = dict((k.lower(), v) for k, _, v in ATTR_KV_RE.findall(m.group(1)))
        path = attrs.get(attr, "").strip()
        # Only rewrite post-local attachments. Other relative links can point to
        # pages or anchors and should remain untouched.
        suffix = Path(unquote(path).split("?", 1)[0]).suffix.lower()
        is_attachment = path.startswith("files/") or suffix in attachment_extensions
        is_media = media and suffix in media_extensions
        if not (is_attachment or is_media):
            return m.group(0)
        new = copy_asset(path)
        if not new:
            return m.group(0)
        return re.sub(
            rf"({attr}\s*=\s*)([\"']).*?\2",
            lambda match: f"{match.group(1)}{match.group(2)}{new}{match.group(2)}",
            m.group(0), count=1, flags=re.I,
        )

    body = HTML_OBJECT_RE.sub(lambda m: html_asset_sub(m, "data"), body)
    body = HTML_LINK_RE.sub(lambda m: html_asset_sub(m, "href"), body)
    body = HTML_MEDIA_RE.sub(lambda m: html_asset_sub(m, "src", media=True), body)
    # strip pandoc attribute blocks like ){width=100%}
    body = ATTR_RE.sub(r"\1", body)
    body = escape_inline_hashtags(body)
    body = blank_pad_html_wrappers(body)
    return body.strip()


FENCE_SPLIT_RE = re.compile(r"(```.*?```)", re.S)
# a decorative hashtag in prose (e.g. "#HappySummer"); Quartz would turn it
# into a real tag, polluting the tag list and graph. Headings are safe: they
# require a space after the hashes. URLs are safe: "#" follows "/" or a word.
INLINE_HASHTAG_RE = re.compile(r"(^|[ \t])#([A-Za-z][\w-]*)", re.M)


def escape_inline_hashtags(body: str) -> str:
    parts = FENCE_SPLIT_RE.split(body)
    for i in range(0, len(parts), 2):  # even indices are outside code fences
        parts[i] = INLINE_HASHTAG_RE.sub(r"\1\\#\2", parts[i])
    return "".join(parts)


WRAP_OPEN_RE = re.compile(r"^<(div|center|aside|p|figure)\b[^>]*>$", re.I)
WRAP_CLOSE_RE = re.compile(r"^</(div|center|aside|p|figure)>$", re.I)


def blank_pad_html_wrappers(body: str) -> str:
    """Pandoc parses markdown inside HTML blocks; CommonMark does not unless
    the markdown is separated from the wrapper tags by blank lines. Pad them
    so e.g. images centered via <div> or <figure> wrappers still render on
    the site."""
    lines = body.split("\n")
    out = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if WRAP_CLOSE_RE.match(stripped) and out and out[-1].strip():
            out.append("")
        out.append(line)
        if (WRAP_OPEN_RE.match(stripped)
                and i + 1 < len(lines) and lines[i + 1].strip()):
            out.append("")
    return "\n".join(out)


def norm_code(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\xa0", " ").strip().splitlines()]
    return "\n".join(ln for ln in lines if ln)


def widget_position(anchor, fences, used):
    if anchor:
        for i, (code, end) in enumerate(fences):
            if code == anchor and i not in used:
                used.add(i)
                return end
        for code, end in fences:
            if code == anchor:
                return end
    return None


def extract_output_widgets(post_dir: Path, base_name: str, warnings: list):
    """Read rendered data tables and specialty widgets in document order."""
    html_path = post_dir / f"{base_name}.html"
    if not html_path.exists():
        return []
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    widgets, last_pre = [], None
    kinds = {"datatables", "r2d3", "forceNetwork", "swipeR"}
    for el in soup.find_all(["pre", "div"]):
        if el.name == "pre":
            last_pre = norm_code(el.get_text())
            continue
        kind = next((name for name in kinds if name in (el.get("class") or [])), None)
        if not kind or "html-widget" not in (el.get("class") or []):
            continue
        widget_id = el.get("id")
        data_tag = soup.find("script", attrs={"data-for": widget_id}) if widget_id else None
        if data_tag is None:
            warnings.append(f"{base_name}: missing {kind} widget data")
            continue
        try:
            payload = json.loads(data_tag.string or data_tag.get_text())
        except (ValueError, TypeError):
            warnings.append(f"{base_name}: malformed {kind} widget data")
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("x"), dict):
            warnings.append(f"{base_name}: invalid {kind} widget data")
            continue
        widgets.append((kind, last_pre, el, data_tag, payload, soup))
    return widgets


def render_table_preview(payload, original_url: str):
    """Return bounded static HTML, or None for an inconsistent table payload."""
    x = payload["x"]
    columns = x.get("data")
    if not isinstance(columns, list) or not columns or any(not isinstance(c, list) for c in columns):
        return None
    row_count = len(columns[0])
    if any(len(c) != row_count for c in columns):
        return None
    container = BeautifulSoup(x.get("container", ""), "html.parser")
    headers = [th.get_text(" ", strip=True) for th in container.select("thead th")]
    if len(headers) != len(columns):
        return None
    head = "".join(f"<th>{html_escape(h)}</th>" for h in headers)
    def cell_text(value):
        if value is None:
            return ""
        text = html_unescape(str(value))
        return html_escape(re.sub(r"[ \t]+(?=\r?\n)", "", text).rstrip())
    rows = "".join(
        "<tr>" + "".join(
            f"<td>{cell_text(columns[col][row])}</td>"
            for col in range(len(columns))) + "</tr>"
        for row in range(min(20, row_count))
    )
    return (
        f'<div class="data-table-preview"><p>Showing {min(20, row_count)} of {row_count:,} rows '
        f'and all {len(columns)} columns. <a href="{html_escape(original_url, quote=True)}">'
        'View the full interactive table in the original post</a>.</p>'
        '<div style="overflow-x:auto;max-width:100%"><table><thead><tr>'
        f'{head}</tr></thead><tbody>{rows}</tbody></table></div></div>'
    )


SPECIALTY_DEPS = {
    "r2d3": ("htmlwidgets-", "r2d3-render-", "r2d3-binding-", "d3v4-"),
    "forceNetwork": ("htmlwidgets-", "d3-", "forceNetwork-binding-"),
    "swipeR": ("htmlwidgets-", "Swiper-", "swipeRstyles-", "swipeR-binding-"),
}


def render_specialty_widget(kind, element, data_tag, payload, soup,
                            post_dir: Path, asset_dir: Path, slug: str,
                            number: int, warnings: list):
    """Bundle an htmlwidget with only the local dependencies its binding uses."""
    deps = []
    for tag in soup.find_all(["script", "link"]):
        ref = tag.get("src") or tag.get("href")
        if not ref or not any(part in ref for part in SPECIALTY_DEPS[kind]):
            continue
        relative = Path(unquote(ref))
        if relative.is_absolute() or ".." in relative.parts or not (post_dir / relative).is_file():
            warnings.append(f"{slug}: missing or invalid {kind} dependency {ref}")
            return None
        emitted_ref = f"widget-deps/{kind.lower()}/{relative.as_posix().lower()}"
        deps.append((tag.name, emitted_ref, relative))
    if not deps or not any("htmlwidgets-" in ref for _, ref, _ in deps):
        warnings.append(f"{slug}: missing {kind} runtime dependencies")
        return None
    image_paths = []
    if kind == "swipeR":
        fragment = BeautifulSoup(payload["x"].get("html", ""), "html.parser")
        image_paths = [img.get("src", "") for img in fragment.find_all("img")]
        if not image_paths:
            warnings.append(f"{slug}: missing swipeR slide images")
            return None
    for ref in image_paths:
        relative = Path(unquote(ref))
        if relative.is_absolute() or ".." in relative.parts or not (post_dir / relative).is_file():
            warnings.append(f"{slug}: missing or invalid swipeR slide {ref}")
            return None
    for _, emitted_ref, relative in deps:
        dest = asset_dir / emitted_ref
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.read_bytes() != (post_dir / relative).read_bytes():
            shutil.copy2(post_dir / relative, dest)
    for ref in image_paths:
        relative = Path(unquote(ref))
        dest = asset_dir / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.read_bytes() != (post_dir / relative).read_bytes():
            shutil.copy2(post_dir / relative, dest)
    includes = "\n".join(
        f'<script src="{html_escape(ref, quote=True)}"></script>' if tag == "script"
        else f'<link rel="stylesheet" href="{html_escape(ref, quote=True)}">'
        for tag, ref, _ in deps
    )
    frame = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>html,body{margin:0;width:100%;height:100%;overflow:auto}</style>'
        f'{includes}</head><body>{str(element)}{str(data_tag)}</body></html>'
    )
    name = f"widget-{kind.lower()}-{number:02d}.htm"
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / name).write_text(frame, encoding="utf-8", newline="\n")
    height_match = re.search(r"height:\s*(\d+)px", element.get("style", ""))
    height = int(height_match.group(1)) if height_match else 600
    return (f'<iframe src="./{slug}/{name}" title="Interactive {html_escape(kind)} widget" '
            f'loading="lazy" style="width:100%;height:{height}px;border:0"></iframe>')


def inject_output_widgets(body: str, widgets, post_dir: Path, asset_dir: Path,
                          slug: str, original_url: str, warnings: list):
    fences = [(norm_code(m.group(1)), m.end()) for m in FENCE_RE.finditer(body)]
    used, insertions, appendix = set(), [], []
    serial = {kind: 0 for kind in SPECIALTY_DEPS}
    for kind, anchor, element, data_tag, payload, soup in widgets:
        if kind == "datatables":
            output = render_table_preview(payload, original_url)
            if output is None:
                warnings.append(f"{slug}: invalid datatables columns or headers")
                continue
        else:
            serial[kind] += 1
            output = render_specialty_widget(kind, element, data_tag, payload,
                                             soup, post_dir, asset_dir, slug,
                                             serial[kind], warnings)
            if output is None:
                continue
        pos = widget_position(anchor, fences, used)
        if pos is None:
            appendix.append(output)
        else:
            insertions.append((pos, len(insertions), output))
    for pos, _, output in sorted(insertions, key=lambda x: (-x[0], -x[1])):
        body = body[:pos] + "\n\n" + output + body[pos:]
    if appendix:
        body += "\n\n## Rendered outputs\n\n" + "\n\n".join(appendix)
    return body


def extract_generated_figures(post_dir: Path, base_name: str):
    """Find knitr figures, whether external or embedded as image data.

    Each figure is anchored to the code block that precedes it in the rendered
    HTML (None = no code anchor). Embedded data images are accepted only inside
    a knitr ``div.figure`` so ordinary inline images are not duplicated.
    """
    html_path = post_dir / f"{base_name}.html"
    if not html_path.exists():
        return []
    soup = BeautifulSoup(
        html_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    figs, last_pre = [], None
    for el in soup.find_all(["pre", "img"]):
        if el.name == "pre":
            last_pre = norm_code(el.get_text())
        else:
            src = el.get("src") or ""
            external = (f"{base_name}_files/" in src and
                        src.lower().endswith(
                            (".png", ".jpg", ".jpeg", ".svg", ".gif")))
            embedded = (src.lower().startswith("data:image/") and
                        el.find_parent("div", class_="figure") is not None)
            if external or embedded:
                alt = el.get("alt") or el.get("aria-label") or ""
                figs.append((last_pre, src, alt))
    return figs


def extract_plotly_widgets(post_dir: Path, base_name: str):
    """Extract standard R Plotly htmlwidgets from rendered post HTML.

    Quartz deliberately does not execute scripts embedded in markdown pages.
    Each widget is therefore rendered in a local iframe with its original
    serialized Plotly figure and library, preserving the chart's interactivity.
    """
    html_path = post_dir / f"{base_name}.html"
    if not html_path.exists():
        return []
    soup = BeautifulSoup(
        html_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    library = next((script.get("src") for script in soup.find_all("script")
                    if "plotly-main" in (script.get("src") or "")
                    and (script.get("src") or "").endswith(".js")), None)
    if not library:
        return []

    widgets, last_pre = [], None
    for el in soup.find_all(["pre", "div"]):
        if el.name == "pre":
            last_pre = norm_code(el.get_text())
            continue
        classes = set(el.get("class") or [])
        if not {"plotly", "html-widget"}.issubset(classes):
            continue
        widget_id = el.get("id")
        data_tag = soup.find("script", attrs={"data-for": widget_id})
        if not widget_id or data_tag is None:
            continue
        try:
            widget = json.loads(data_tag.string or data_tag.get_text())
        except json.JSONDecodeError:
            continue
        figure = widget.get("x")
        # Widgets requiring custom JavaScript hooks cannot safely be recreated
        # with Plotly.newPlot alone.
        if (not isinstance(figure, dict) or "data" not in figure
                or widget.get("evals") or widget.get("jsHooks")):
            continue
        widgets.append((last_pre, figure, library))
    return widgets


FENCE_RE = re.compile(r"```[a-z]*\n(.*?)\n```", re.S)


def decode_data_image(src: str):
    """Return ``(bytes, extension)`` for a data-image URI, else ``None``."""
    match = DATA_IMAGE_RE.match(src)
    if not match:
        return None
    mime, params, payload = match.groups()
    subtype = mime.split("/", 1)[1].lower()
    extension = {
        "jpeg": "jpg",
        "jpg": "jpg",
        "png": "png",
        "gif": "gif",
        "svg+xml": "svg",
        "webp": "webp",
    }.get(subtype)
    if extension is None:
        return None
    try:
        if ";base64" in params.lower():
            data = base64.b64decode(re.sub(r"\s+", "", payload), validate=True)
        else:
            data = unquote_to_bytes(payload)
    except (binascii.Error, ValueError):
        return None
    return (data, extension) if data else None


def inject_figures(body: str, figs, post_dir: Path, asset_dir: Path,
                   slug: str, warnings: list) -> str:
    if not figs:
        return body
    fences = [(norm_code(m.group(1)), m.end()) for m in FENCE_RE.finditer(body)]
    used = set()
    insertions, appendix = [], []
    for figure_number, (anchor, src, alt) in enumerate(figs, start=1):
        asset_dir.mkdir(parents=True, exist_ok=True)
        if src.lower().startswith("data:image/"):
            decoded = decode_data_image(src)
            if decoded is None:
                warnings.append(
                    f"{slug}: invalid or unsupported embedded generated figure")
                continue
            data, extension = decoded
            dest_name = f"generated-figure-{figure_number:02d}.{extension}"
            dest = asset_dir / dest_name
            if not dest.exists() or dest.read_bytes() != data:
                dest.write_bytes(data)
        else:
            img = post_dir / unquote(src)
            if not img.exists():
                warnings.append(f"{slug}: missing generated figure {src}")
                continue
            dest_name = img.name.replace(" ", "-")
            dest = asset_dir / dest_name
            if not dest.exists() or img.read_bytes() != dest.read_bytes():
                shutil.copy2(img, dest)
        md_img = f"![{alt}](./{slug}/{dest_name})"
        pos = None
        if anchor:
            for i, (code, end) in enumerate(fences):
                if code == anchor and i not in used:
                    used.add(i)
                    pos = end
                    break
            if pos is None:  # same chunk emitted several figures
                for code, end in fences:
                    if code == anchor:
                        pos = end
                        break
        if pos is None:
            appendix.append(md_img)
        else:
            insertions.append((pos, len(insertions), md_img))
    # insert back-to-front; reverse tiebreak keeps same-anchor figures in order
    for pos, _, md_img in sorted(insertions, key=lambda x: (-x[0], -x[1])):
        body = body[:pos] + f"\n\n{md_img}" + body[pos:]
    if appendix:
        body += "\n\n## Figures\n\n" + "\n\n".join(appendix)
    return body


def inject_plotly_widgets(body: str, widgets, post_dir: Path, asset_dir: Path,
                          slug: str, warnings: list) -> str:
    """Write standalone Plotly iframes and place them after their code blocks."""
    if not widgets:
        return body
    fences = [(norm_code(m.group(1)), m.end()) for m in FENCE_RE.finditer(body)]
    used = set()
    insertions, appendix = [], []
    asset_dir.mkdir(parents=True, exist_ok=True)
    for number, (anchor, figure, library_ref) in enumerate(widgets, start=1):
        library = post_dir / unquote(library_ref)
        if not library.exists():
            warnings.append(f"{slug}: missing Plotly library {library_ref}")
            continue
        library_name = f"plotly-widget-{number:02d}.min.js"
        library_dest = asset_dir / library_name
        if not library_dest.exists() or library.read_bytes() != library_dest.read_bytes():
            shutil.copy2(library, library_dest)

        payload = json.dumps(
            {"data": figure["data"], "layout": figure.get("layout", {}),
             "config": figure.get("config", {})},
            ensure_ascii=False, separators=(",", ":"),
        ).replace("</", "<\\/")
        frame = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<style>html,body,#chart{{width:100%;height:100%;margin:0}}body{{overflow:hidden}}</style>
</head><body><div id=\"chart\"></div><script src=\"./{slug}/{library_name}\"></script><script>
const figure={payload};
Plotly.newPlot(\"chart\",figure.data,figure.layout,{{...figure.config,responsive:true}});
</script></body></html>
"""

        height = figure.get("layout", {}).get("height", 600)
        try:
            height = max(240, int(height))
        except (TypeError, ValueError):
            height = 600
        iframe = (
            f'<iframe srcdoc="{html_escape(frame, quote=True)}" '
            f'title="Interactive Plotly chart" '
            f'loading="lazy" style="width:100%; height:{height}px; border:0;"></iframe>'
        )
        pos = None
        if anchor:
            for i, (code, end) in enumerate(fences):
                if code == anchor and i not in used:
                    used.add(i)
                    pos = end
                    break
            if pos is None:
                for code, end in fences:
                    if code == anchor:
                        pos = end
                        break
        if pos is None:
            appendix.append(iframe)
        else:
            insertions.append((pos, len(insertions), iframe))
    for pos, _, iframe in sorted(insertions, key=lambda x: (-x[0], -x[1])):
        body = body[:pos] + f"\n\n{iframe}" + body[pos:]
    if appendix:
        body += "\n\n## Interactive charts\n\n" + "\n\n".join(appendix)
    return body


def build_note(post_dir: Path) -> tuple[str, str] | None:
    rmds = sorted(post_dir.glob("*.Rmd"))
    if not rmds:
        return None
    text = rmds[0].read_text(encoding="utf-8", errors="replace")
    meta, body = split_frontmatter(text)
    if meta is None:
        return None

    slug = note_slug(post_dir.name)
    # dir names always start with an ISO date; source YAML dates are mixed-format
    m = re.match(r"^\d{4}-\d{2}-\d{2}", post_dir.name)
    date = m.group(0) if m else str(meta.get("date", ""))
    tags = [slugify_tag(c) for c in (meta.get("categories") or [])]
    original_url = f"{BLOG_BASE_URL}{post_dir.name}/"
    warnings = []
    converted = convert_body(body, post_dir, NOTES_DIR / slug, slug, warnings)
    figs = extract_generated_figures(post_dir, rmds[0].stem)
    converted = inject_figures(converted, figs, post_dir, NOTES_DIR / slug,
                               slug, warnings)
    widgets = extract_plotly_widgets(post_dir, rmds[0].stem)
    converted = inject_plotly_widgets(converted, widgets, post_dir,
                                      NOTES_DIR / slug, slug, warnings)
    output_widgets = extract_output_widgets(post_dir, rmds[0].stem, warnings)
    converted = inject_output_widgets(converted, output_widgets, post_dir,
                                      NOTES_DIR / slug, slug, original_url, warnings)
    for w in warnings:
        print(f"  warn: {w}")

    fm = {
        "title": str(meta.get("title", slug)),
        "description": clean_description(meta.get("description")),
        "date": date,
        "tags": tags,
        "original": original_url,
    }
    front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=10000).strip()
    note = (
        f"---\n{front}\n---\n\n"
        f"{converted}\n\n"
        f"<!-- RELATED:BEGIN -->\n<!-- RELATED:END -->\n\n"
        f"---\n"
        f"> 📄 Read the [original post with full outputs]({original_url}) on my blog.\n"
    )
    return slug, note


def preserve_related_block(note: str, previous: str) -> str:
    """Keep computed related links when refreshing a note's rendered outputs."""
    old = RELATED_BLOCK_RE.search(previous)
    if old is None:
        return note
    return RELATED_BLOCK_RE.sub(lambda _: old.group(0), note, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="rebuild all notes")
    ap.add_argument("--slug", action="append", default=[],
                    help="rebuild only this note slug (repeatable)")
    args = ap.parse_args()
    selected_slugs = set(args.slug)

    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() and not args.force else {}

    seen_slugs = {}
    written = skipped = 0
    for post_dir in sorted(p for p in BLOG_POSTS.iterdir() if p.is_dir()):
        rmds = sorted(post_dir.glob("*.Rmd"))
        if not rmds:
            print(f"  warn: no .Rmd in {post_dir.name}")
            continue
        # hash .Rmd + rendered .html so re-rendered figures also trigger updates
        h = hashlib.sha256(b"v2:" + rmds[0].read_bytes())
        html = post_dir / f"{rmds[0].stem}.html"
        if html.exists():
            html_bytes = html.read_bytes()
            h.update(html_bytes)
            if EMBEDDED_FIGURE_RE.search(html_bytes):
                h.update(EMBEDDED_FIGURE_HASH_MARKER)
            if LOCAL_HTML_ASSET_RE.search(html_bytes):
                h.update(LOCAL_HTML_ASSET_HASH_MARKER)
            if PLOTLY_WIDGET_RE.search(html_bytes):
                h.update(PLOTLY_WIDGET_HASH_MARKER)
            if OUTPUT_WIDGET_RE.search(html_bytes):
                h.update(OUTPUT_WIDGET_HASH_MARKER)
        for path_bytes in LOCAL_DIRECT_ATTACHMENT_RE.findall(rmds[0].read_bytes()):
            path = unquote_to_bytes(path_bytes.decode("utf-8", errors="replace")).decode(
                "utf-8", errors="replace")
            asset = post_dir / path.split("?", 1)[0]
            if asset.is_file():
                h.update(LOCAL_DIRECT_ATTACHMENT_HASH_MARKER)
                h.update(path_bytes)
                h.update(asset.read_bytes())
        src_hash = h.hexdigest()
        slug = note_slug(post_dir.name)
        if slug in seen_slugs:
            slug = post_dir.name  # de-collide by keeping the date prefix
        seen_slugs[slug] = post_dir.name

        if selected_slugs and slug not in selected_slugs:
            continue
        if (not args.force and slug not in selected_slugs and
                manifest.get(slug) == src_hash and (NOTES_DIR / f"{slug}.md").exists()):
            skipped += 1
            continue
        result = build_note(post_dir)
        if result is None:
            print(f"  warn: could not parse {post_dir.name}")
            continue
        _, note = result
        note_path = NOTES_DIR / f"{slug}.md"
        if note_path.exists():
            note = preserve_related_block(note, note_path.read_text(encoding="utf-8"))
        note_path.write_text(note, encoding="utf-8", newline="\n")
        manifest[slug] = src_hash
        written += 1
        print(f"  wrote: {slug}")

    MANIFEST.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"done: {written} notes written, {skipped} unchanged, {len(seen_slugs)} total")


if __name__ == "__main__":
    sys.exit(main())
