"""Verify source-to-vault integrity and generated/built exports before publication."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
import yaml

from cloud_update import changed_files, changed_slugs, git, ROOT

SITE_URL = "https://lstehlik2809.github.io/people-analytics-second-brain"
BLOG_URL = "https://blog-about-people-analytics.netlify.app/posts/"
FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
RELATED = re.compile(r"<!-- RELATED:BEGIN -->.*?<!-- RELATED:END -->", re.S)
FENCES = re.compile(r"```[^\n]*\n.*?```", re.S)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def metadata(path):
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
    require(match is not None, f"Missing frontmatter: {path}")
    meta = yaml.safe_load(match.group(1))
    require(isinstance(meta, dict), f"Invalid metadata: {path}")
    return meta, text[match.end():]


def expected_notes(source):
    require(source.is_dir(), f"BLOG_POSTS directory does not exist: {source}")
    notes = {}
    for directory in sorted(p for p in source.iterdir() if p.is_dir()):
        files = sorted(directory.glob("*.Rmd"))
        if not files:
            continue
        meta, _ = metadata(files[0])
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", directory.name)
        if slug in notes:
            slug = directory.name
        date = re.match(r"^\d{4}-\d{2}-\d{2}", directory.name)
        notes[slug] = {
            "title": str(meta.get("title", slug)),
            "description": re.sub(r"\s+", " ", str(meta.get("description") or "")).strip(),
            "date": date.group() if date else str(meta.get("date", "")),
            "tags": [re.sub(r"[^a-z0-9]+", "-", tag.lower().strip()).strip("-")
                     for tag in meta.get("categories") or []],
            "original": f"{BLOG_URL}{directory.name}/",
        }
    require(bool(notes), "No source posts found; refusing an empty update.")
    return notes


def local_assets(body):
    body = FENCES.sub("", RELATED.sub("", body))
    refs = [m.group(1).strip().strip("<>").split(' "', 1)[0]
            for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", body)]
    soup = BeautifulSoup(body if "<" in body else "", "html.parser")
    # Plotly's srcdoc contains its local runtime; standalone widget files have
    # their own dependencies, verified recursively below.
    for frame in list(soup.find_all("iframe", srcdoc=True)):
        refs.extend(local_assets(frame["srcdoc"]))
    for element in soup.find_all(True):
        for attr in ("src", "data", "poster"):
            if element.get(attr):
                refs.append(element[attr])
        href = element.get("href", "")
        if urlsplit(href).path.lower().endswith((".pdf", ".js", ".css")):
            refs.append(href)
    return [ref for ref in refs if ref and not urlsplit(ref).scheme
            and not ref.startswith(("//", "#"))]


def check_assets(note_path, body, vault, visited=None):
    visited = visited if visited is not None else set()
    for ref in local_assets(body):
        parsed = urlsplit(ref)
        target = ((vault if parsed.path.startswith("/") else note_path.parent) /
                  unquote(parsed.path).lstrip("/")).resolve()
        require(target.is_relative_to(vault.resolve()), f"Asset escapes vault: {ref}")
        require(target.is_file(), f"Missing changed-note asset: {note_path.name}: {ref}")
        if target.suffix.lower() in (".htm", ".html") and target not in visited:
            visited.add(target)
            check_assets(target, target.read_text(encoding="utf-8"), vault, visited)


def asset_check_slugs(root, paths, changes):
    selected = {path.split("/")[2] for path in changes
                if path.startswith("vault/posts/") and len(path.split("/")) > 3}
    for slug, path in paths.items():
        previous = git(root, "show", f"HEAD:vault/posts/{slug}.md", check=False)
        if previous.returncode != 0:
            selected.add(slug)
            continue
        match = FRONTMATTER.match(previous.stdout)
        old_body = previous.stdout[match.end():] if match else previous.stdout
        _, body = metadata(path)

        def normalized(text):
            return RELATED.sub("", text).replace("\r\n", "\n").strip()

        if normalized(old_body) != normalized(body):
            selected.add(slug)
    return selected


def verify(root, source, asset_slugs=None, built=None):
    expected = expected_notes(source)
    vault = root / "vault"
    paths = {path.stem: path for path in (vault / "posts").glob("*.md")}
    require(set(paths) == set(expected), "Source/vault slug mismatch: "
            f"missing={sorted(set(expected) - set(paths))}; extra={sorted(set(paths) - set(expected))}")
    manifest = json.loads((root / "pipeline/cache/manifest.json").read_text(encoding="utf-8"))
    require(set(manifest) == set(paths), "Manifest/vault slug mismatch.")
    if asset_slugs is None:
        # Relinking alone must not turn unrelated legacy asset warnings into
        # update failures. Check notes whose prose/markup or assets changed.
        asset_slugs = asset_check_slugs(root, paths, changed_files(root))
    for slug, path in paths.items():
        meta, body = metadata(path)
        for key, value in expected[slug].items():
            require(meta.get(key) == value, f"Source metadata mismatch: {slug}: {key}")
        require(body.count("<!-- RELATED:BEGIN -->") == 1 and
                body.count("<!-- RELATED:END -->") == 1, f"Missing/duplicate related block: {slug}")
        block = RELATED.search(body)
        require(block is not None, f"Invalid related block: {slug}")
        for other in re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", block.group()):
            require(other in paths and other != slug, f"Invalid related-note target: {slug} -> {other}")
        if slug in asset_slugs:
            check_assets(path, body, vault)

    for relative in ("README.md", "vault/index.md"):
        text = (root / relative).read_text(encoding="utf-8")
        counts = re.findall(r"<!--N-->(\d+)<!--/N-->", text)
        require(bool(counts) and all(int(n) == len(paths) for n in counts),
                f"Visible note count mismatch: {relative}")
    cache = root / "pipeline/cache"
    llms = (cache / "llms.txt").read_text(encoding="utf-8")
    full = (cache / "llms-full.txt").read_text(encoding="utf-8")
    index_slugs = re.findall(re.escape(SITE_URL) + r"/posts/([^\s)]+)", llms)
    full_slugs = re.findall(r"^URL: " + re.escape(SITE_URL) + r"/posts/(\S+)$", full, re.M)
    for name, slugs in (("llms.txt", index_slugs), ("llms-full.txt", full_slugs)):
        require(len(slugs) == len(paths) and set(slugs) == set(paths), f"{name} slug/count mismatch.")

    index = json.loads((cache / "semantic_index.json").read_text(encoding="utf-8"))
    posts = index.get("posts", [])
    require(len(posts) == len(paths) and {p["slug"] for p in posts} == set(paths),
            "Semantic index slug/count mismatch.")
    require(index.get("schema") == 3 and index.get("dims") == 384, "Unexpected semantic index schema/dimensions.")
    vector_count = 0
    for post in posts:
        slug = post["slug"]
        for key in ("title", "description", "date", "tags"):
            require(post.get(key) == expected[slug][key], f"Semantic index metadata mismatch: {slug}: {key}")
        passages, vectors = post.get("passages", []), post.get("vecs", [])
        require(bool(passages) and len(passages) == len(vectors), f"Passage/vector mismatch: {slug}")
        for vector in vectors:
            require(len(vector) == 384 and all(isinstance(v, (float, int)) and math.isfinite(v) for v in vector),
                    f"Invalid semantic vector: {slug}")
        vector_count += len(vectors)
    require(vector_count == index.get("vectorCount"), "Semantic index vector count mismatch.")

    if built is not None:
        for slug in paths:
            page = built / "posts" / f"{slug}.html"
            require(page.is_file() and page.stat().st_size > 0, f"Missing built page: {slug}")
        for name in ("llms.txt", "llms-full.txt", "semantic_index.json"):
            require((built / name).read_bytes() == (cache / name).read_bytes(), f"Built export mismatch: {name}")
        for name in ("semantic-search.html", "hybrid-search.mjs"):
            require((built / name).read_bytes() == (root / "pipeline/static" / name).read_bytes(),
                    f"Built search file mismatch: {name}")
    return {"note_count": len(paths), "asset_slugs_checked": sorted(asset_slugs),
            "vector_count": vector_count, "built_verified": built is not None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=os.environ.get("BLOG_POSTS"))
    parser.add_argument("--built", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        require(args.source is not None, "Set BLOG_POSTS or --source to the source _posts directory.")
        result = verify(ROOT, Path(args.source), built=args.built)
        files = changed_files(ROOT)
        result.update(changed_files=files, changed_slugs=changed_slugs(files),
                      source_sha=git(Path(args.source), "rev-parse", "HEAD").stdout.strip(),
                      request_id=os.environ.get("REQUEST_ID", ""))
        if args.report:
            args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
                summary.write(f"### Verified update ({os.environ.get('UPDATE_MODE', 'local')})\n\n"
                              f"Request: `{result['request_id'] or '(local)'}`\n\n"
                              f"Source commit: `{result['source_sha']}`\n\n"
                              f"Notes: {result['note_count']}; vectors: {result['vector_count']}\n\n"
                              f"Changed slugs: {', '.join(result['changed_slugs']) or '(none)'}\n\n")
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"Update verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
