import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import cloud_update as cloud
import verify_update as verify

REQUEST_ID = "456c8c45-f4a9-4e1d-83b8-9899c5cef66e"
SOURCE_SHA = "a" * 40


class RequestTests(unittest.TestCase):
    def test_fixed_data_schema_accepts_preview_and_publish(self):
        for mode in ("preview", "publish"):
            self.assertEqual(cloud.parse_request(json.dumps(
                {"mode": mode, "request_id": REQUEST_ID})),
                {"mode": mode, "request_id": REQUEST_ID})

    def test_rejects_invalid_or_executable_inputs(self):
        cases = ["{", "[]", '{}',
                 '{"mode":"preview","mode":"publish","request_id":"' + REQUEST_ID + '"}',
                 json.dumps({"mode": "publish", "request_id": REQUEST_ID, "ref": "other"}),
                 json.dumps({"mode": "shell", "request_id": REQUEST_ID}),
                 json.dumps({"mode": "preview", "request_id": "$(touch unexpected)"}),
                 json.dumps({"mode": "preview", "request_id": 12})]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                cloud.parse_request(value)

    def test_repeated_request_and_nonmain_publication_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            request = json.dumps({"mode": "publish", "request_id": REQUEST_ID})
            (root / cloud.REQUEST_PATH).write_text(request)
            with patch.object(cloud, "git", return_value=subprocess.CompletedProcess([], 0, request)):
                with self.assertRaisesRegex(ValueError, "already used"):
                    cloud.resolve_request(root, "push", {"before": SOURCE_SHA}, "", "refs/heads/main")
            with patch.object(cloud, "git", return_value=subprocess.CompletedProcess([], 0, "{bad json")):
                self.assertEqual(cloud.resolve_request(root, "push", {"before": SOURCE_SHA}, "", "refs/heads/main"),
                                 {"mode": "publish", "request_id": REQUEST_ID})
            with self.assertRaisesRegex(ValueError, "only from main"):
                cloud.resolve_request(root, "workflow_dispatch", {}, "publish", "refs/heads/feature")

    def test_invalid_dispatch_exits_before_generation_or_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            event.write_text("{}")
            env = {**os.environ, "GITHUB_EVENT_PATH": str(event), "GITHUB_EVENT_NAME": "workflow_dispatch",
                   "DISPATCH_MODE": "bad-mode", "GITHUB_REF": "refs/heads/main"}
            before = cloud.git(cloud.ROOT, "status", "--porcelain").stdout
            result = subprocess.run([sys.executable, str(Path(cloud.__file__)), "validate-request"],
                                    env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("mode must be preview or publish", result.stderr)
            self.assertEqual(cloud.git(cloud.ROOT, "status", "--porcelain").stdout, before)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "brain"
        self.origin = Path(self.temp.name) / "origin.git"
        self.root.mkdir()
        cloud.git(self.root, "init", "--initial-branch=main")
        cloud.git(self.root, "config", "user.name", "Fixture")
        cloud.git(self.root, "config", "user.email", "fixture@example.test")
        cloud.git(self.root, "config", "core.autocrlf", "false")
        for path in cloud.GENERATED_PATHS:
            target = self.root / ("vault/posts/alpha.md" if path == "vault" else path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("baseline\n")
        (self.root / ".gitignore").write_text(".env\npipeline/cache/embeddings.json\n")
        cloud.git(self.root, "add", ".")
        cloud.git(self.root, "commit", "-m", "Fixture baseline")
        cloud.git(self.root, "init", "--bare", "--initial-branch=main", str(self.origin))
        cloud.git(self.root, "remote", "add", "origin", str(self.origin))
        cloud.git(self.root, "push", "origin", "main")
        self.base = cloud.git(self.root, "rev-parse", "HEAD").stdout.strip()

    def tearDown(self):
        self.temp.cleanup()

    def change_content(self):
        (self.root / "vault/posts/alpha.md").write_text("updated\n", newline="\n")
        (self.root / ".env").write_text("FAKE_TEST_SECRET=never-publish\n")
        (self.root / "pipeline/cache/embeddings.json").write_text('{"fake":"private cache"}')
        (self.root / "unrelated.txt").write_text("leave me alone\n")

    def test_preview_never_stages_commits_or_pushes(self):
        self.change_content()
        result = cloud.publish(self.root, "preview", REQUEST_ID, SOURCE_SHA)
        self.assertFalse(result["published"])
        self.assertEqual(result["changed_slugs"], ["alpha"])
        self.assertEqual(cloud.git(self.root, "rev-parse", "HEAD").stdout.strip(), self.base)
        self.assertEqual(cloud.git(self.origin, "rev-parse", "main").stdout.strip(), self.base)
        self.assertEqual(cloud.git(self.root, "diff", "--cached", "--name-only").stdout, "")

    def test_publish_pushes_only_generated_content_and_returns_exact_sha(self):
        self.change_content()
        result = cloud.publish(self.root, "publish", REQUEST_ID, SOURCE_SHA)
        self.assertTrue(result["published"])
        self.assertNotEqual(result["sha"], self.base)
        self.assertEqual(result["sha"], cloud.git(self.origin, "rev-parse", "main").stdout.strip())
        self.assertEqual(cloud.git(self.origin, "show", "main:vault/posts/alpha.md").stdout, "updated\n")
        changed = cloud.git(self.root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").stdout.splitlines()
        self.assertEqual(changed, ["vault/posts/alpha.md"])
        tracked = cloud.git(self.origin, "ls-tree", "-r", "--name-only", "main").stdout
        self.assertNotIn(".env\n", tracked)
        self.assertNotIn("embeddings.json", tracked)
        self.assertNotIn("unrelated.txt", tracked)
        again = cloud.publish(self.root, "publish", REQUEST_ID, SOURCE_SHA)
        self.assertFalse(again["published"])
        self.assertEqual(cloud.git(self.origin, "rev-parse", "main").stdout.strip(), result["sha"])

    def test_stale_generation_fails_before_content_commit(self):
        self.change_content()
        other = Path(self.temp.name) / "other"
        cloud.git(self.root, "clone", str(self.origin), str(other))
        (other / "README.md").write_text("concurrent change\n")
        cloud.git(other, "add", "README.md")
        cloud.git(other, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                  "commit", "-m", "Concurrent edit")
        cloud.git(other, "push", "origin", "main")
        remote = cloud.git(self.origin, "rev-parse", "main").stdout.strip()
        with self.assertRaisesRegex(ValueError, "main advanced"):
            cloud.publish(self.root, "publish", REQUEST_ID, SOURCE_SHA)
        self.assertEqual(cloud.git(self.root, "rev-parse", "HEAD").stdout.strip(), self.base)
        self.assertEqual(cloud.git(self.origin, "rev-parse", "main").stdout.strip(), remote)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "blog/_posts"
        post = self.source / "2026-10-01-alpha"
        post.mkdir(parents=True)
        (post / "alpha.Rmd").write_text(
            '---\ntitle: Fixture\ndescription: Some evidence.\ncategories: [People Analytics]\n---\n\nBody.\n')
        self.note = self.root / "vault/posts/alpha.md"
        self.note.parent.mkdir(parents=True)
        self.note.write_text(
            '---\ntitle: Fixture\ndescription: Some evidence.\ndate: "2026-10-01"\n'
            'tags: [people-analytics]\noriginal: ' + verify.BLOG_URL + '2026-10-01-alpha/\n---\n\nBody.\n'
            '<!-- RELATED:BEGIN -->\n<!-- RELATED:END -->\n')
        (self.root / "README.md").write_text("<!--N-->1<!--/N-->")
        (self.root / "vault/index.md").write_text("<!--N-->1<!--/N-->")
        self.cache = self.root / "pipeline/cache"
        self.cache.mkdir(parents=True)
        (self.cache / "manifest.json").write_text(json.dumps({"alpha": SOURCE_SHA}))
        (self.cache / "llms.txt").write_text(f"- [Fixture]({verify.SITE_URL}/posts/alpha): Some evidence.")
        (self.cache / "llms-full.txt").write_text(f"URL: {verify.SITE_URL}/posts/alpha\nBody.\n")
        self.index = {"schema": 3, "dims": 384, "vectorCount": 1, "posts": [
            {"slug": "alpha", "title": "Fixture", "description": "Some evidence.", "date": "2026-10-01",
             "tags": ["people-analytics"], "passages": ["Some evidence."], "vecs": [[0.1] * 384]}]}
        self.write_index()

    def tearDown(self):
        self.temp.cleanup()

    def write_index(self):
        (self.cache / "semantic_index.json").write_text(json.dumps(self.index))

    def check(self):
        return verify.verify(self.root, self.source, asset_slugs={"alpha"})

    def test_matching_source_note_and_exports_pass(self):
        self.assertEqual(self.check()["note_count"], 1)

    def test_source_metadata_and_index_mismatch_fail(self):
        self.index["posts"][0]["tags"] = ["obsolete"]
        self.write_index()
        with self.assertRaisesRegex(ValueError, "Semantic index metadata mismatch.*tags"):
            self.check()
        self.index["posts"][0]["tags"] = ["people-analytics"]
        self.write_index()
        self.note.write_text(self.note.read_text().replace("title: Fixture", "title: Old title"))
        with self.assertRaisesRegex(ValueError, "Source metadata mismatch.*title"):
            self.check()

    def test_missing_changed_asset_fails_and_existing_asset_passes(self):
        self.note.write_text(self.note.read_text() + '\n![A chart](./alpha/chart.png)\n')
        with self.assertRaisesRegex(ValueError, "Missing changed-note asset.*chart.png"):
            self.check()
        asset = self.note.parent / "alpha/chart.png"
        asset.parent.mkdir()
        asset.write_bytes(b"chart bytes")
        self.assertEqual(self.check()["asset_slugs_checked"], ["alpha"])

    def test_nested_widget_dependency_missing_fails(self):
        asset = self.note.parent / "alpha/widget.htm"
        asset.parent.mkdir()
        asset.write_text('<script src="runtime.js"></script>')
        self.note.write_text(self.note.read_text() + '\n<iframe src="./alpha/widget.htm"></iframe>')
        with self.assertRaisesRegex(ValueError, "Missing changed-note asset.*runtime.js"):
            self.check()

    def test_relink_or_manifest_only_changes_preserve_legacy_asset_tolerance(self):
        self.note.write_text(self.note.read_text() + '\n![Old chart](./alpha/legacy-missing.png)\n')
        cloud.git(self.root, "init", "--initial-branch=main")
        cloud.git(self.root, "add", ".")
        cloud.git(self.root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                  "commit", "-m", "Legacy fixture")
        (self.cache / "manifest.json").write_text(json.dumps({"alpha": "b" * 40}))
        self.note.write_text(self.note.read_text().replace("<!-- RELATED:END -->", "\n<!-- RELATED:END -->"))
        result = verify.verify(self.root, self.source)
        self.assertEqual(result["asset_slugs_checked"], [])
        self.note.write_text(self.note.read_text() + "\nNew prose.\n")
        with self.assertRaisesRegex(ValueError, "Missing changed-note asset.*legacy-missing"):
            verify.verify(self.root, self.source)

    def test_broken_related_note_and_export_count_fail(self):
        text = self.note.read_text()
        self.note.write_text(text.replace("<!-- RELATED:END -->", "- [[missing|Missing]]\n<!-- RELATED:END -->"))
        with self.assertRaisesRegex(ValueError, "Invalid related-note target"):
            self.check()
        self.note.write_text(text)
        (self.cache / "llms.txt").write_text("No entries")
        with self.assertRaisesRegex(ValueError, "llms.txt slug/count mismatch"):
            self.check()

    def test_missing_built_page_and_mismatched_public_export_fail(self):
        built = self.root / "public"
        built.mkdir()
        with self.assertRaisesRegex(ValueError, "Missing built page: alpha"):
            verify.verify(self.root, self.source, asset_slugs=set(), built=built)
        (built / "posts").mkdir()
        (built / "posts/alpha.html").write_text("<h1>Fixture</h1>")
        for name in ("llms.txt", "llms-full.txt", "semantic_index.json"):
            (built / name).write_bytes((self.cache / name).read_bytes())
        static = self.root / "pipeline/static"
        static.mkdir()
        for name in ("semantic-search.html", "hybrid-search.mjs"):
            (static / name).write_text("fixture")
            (built / name).write_text("fixture")
        self.assertTrue(verify.verify(self.root, self.source, asset_slugs=set(), built=built)["built_verified"])
        (built / "llms.txt").write_text("stale export")
        with self.assertRaisesRegex(ValueError, "Built export mismatch: llms.txt"):
            verify.verify(self.root, self.source, asset_slugs=set(), built=built)


if __name__ == "__main__":
    unittest.main()
