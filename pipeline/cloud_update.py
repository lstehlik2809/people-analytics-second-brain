"""Small, data-only control and scoped publication helpers for update-brain.yml."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent.parent
REQUEST_PATH = ".github/brain-update-request.json"
GENERATED_PATHS = (
    "README.md", "vault", "pipeline/cache/manifest.json", "pipeline/cache/llms.txt",
    "pipeline/cache/llms-full.txt", "pipeline/cache/semantic_index.json",
)


def git(root, *args, check=True):
    return subprocess.run(["git", "-C", str(root), *args], check=check,
                          capture_output=True, text=True, encoding="utf-8")


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate request field: {key}")
        result[key] = value
    return result


def parse_request(text):
    request = json.loads(text, object_pairs_hook=no_duplicate_keys)
    if not isinstance(request, dict) or set(request) != {"mode", "request_id"}:
        raise ValueError("Request must contain exactly mode and request_id; no commands or refs.")
    if request["mode"] not in ("preview", "publish"):
        raise ValueError("Request mode must be preview or publish.")
    request_id = request["request_id"]
    if not isinstance(request_id, str):
        raise ValueError("request_id must be a fresh canonical UUID.")
    try:
        valid = str(uuid.UUID(request_id)) == request_id
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("request_id must be a fresh canonical UUID.")
    return request


def resolve_request(root, event_name, event, dispatch_mode, ref, dispatch_request_id=None):
    if event_name == "workflow_dispatch":
        request_id = (str(uuid.uuid4()) if dispatch_request_id in (None, "")
                      else dispatch_request_id)
        request = {"mode": dispatch_mode, "request_id": request_id}
        request = parse_request(json.dumps(request))
    elif event_name == "push":
        request = parse_request((root / REQUEST_PATH).read_text(encoding="utf-8"))
        before = event.get("before", "")
        if not re.fullmatch(r"[0-9a-f]{40}", before):
            raise ValueError("Push event is missing its previous commit SHA.")
        previous = git(root, "show", f"{before}:{REQUEST_PATH}", check=False)
        if previous.returncode == 0:
            # A corrected request must be able to recover from an earlier
            # malformed control file; only an actually reused ID is rejected.
            try:
                prior = json.loads(previous.stdout)
            except ValueError:
                prior = None
            previous_id = prior.get("request_id") if isinstance(prior, dict) else None
            if previous_id == request["request_id"]:
                raise ValueError("request_id was already used; submit a fresh UUID.")
    else:
        raise ValueError(f"Unsupported event: {event_name}")
    if request["mode"] == "publish" and ref != "refs/heads/main":
        raise ValueError("Publishing is allowed only from main; use preview for other branches.")
    return request


def changed_files(root):
    tracked = git(root, "diff", "--name-only", "-z", "HEAD", "--", *GENERATED_PATHS).stdout
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z",
                    "--", *GENERATED_PATHS).stdout
    return sorted(set(filter(None, (tracked + untracked).split("\0"))))


def changed_slugs(paths):
    return sorted({p.split("/")[2].removesuffix(".md") for p in paths
                   if p.startswith("vault/posts/") and len(p.split("/")) >= 3})


def publish(root, mode, request_id, source_sha):
    parse_request(json.dumps({"mode": mode, "request_id": request_id}))
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("Source SHA must be a full commit SHA.")
    files = changed_files(root)
    result = {"published": False, "sha": "", "changed_files": files,
              "changed_slugs": changed_slugs(files)}
    # Preview returns before staging, committing, fetching, or pushing.
    if mode == "preview" or not files:
        return result
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise ValueError("Refusing publication with pre-staged changes.")
    git(root, "fetch", "--no-tags", "origin", "main")
    base = git(root, "rev-parse", "HEAD").stdout.strip()
    remote = git(root, "rev-parse", "FETCH_HEAD").stdout.strip()
    if base != remote:
        raise ValueError("main advanced during generation. Run a new update from main; "
                         "no content was committed or pushed.")
    git(root, "add", "-A", "--", *GENERATED_PATHS)
    git(root, "diff", "--cached", "--check")
    git(root, "-c", "user.name=github-actions[bot]", "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com", "commit",
        "-m", "Update second brain content", "-m",
        f"Source: {source_sha}\nRequest: {request_id}")
    sha = git(root, "rev-parse", "HEAD").stdout.strip()
    try:
        git(root, "push", "origin", "HEAD:refs/heads/main")
    except subprocess.CalledProcessError as error:
        raise ValueError("Push failed (possibly main advanced). No force push was attempted. "
                         "Start a new update from main; inspect the remote before retrying.") from error
    result.update(published=True, sha=sha)
    return result


def outputs(values):
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            for key, value in values.items():
                if not isinstance(value, str):
                    value = json.dumps(value, separators=(",", ":"))
                output.write(f"{key}={value}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validation = subparsers.add_parser("validate-request")
    validation.add_argument("--request-id", default=os.environ.get("DISPATCH_REQUEST_ID", ""))
    publication = subparsers.add_parser("publish")
    publication.add_argument("--mode", required=True, choices=("preview", "publish"))
    publication.add_argument("--request-id", required=True)
    publication.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    try:
        if args.command == "validate-request":
            event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
            result = resolve_request(ROOT, os.environ["GITHUB_EVENT_NAME"], event,
                                     os.environ.get("DISPATCH_MODE", "preview"),
                                     os.environ.get("GITHUB_REF", ""), args.request_id)
        else:
            result = publish(ROOT, args.mode, args.request_id, args.source_sha)
        outputs(result)
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"Cloud update stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
