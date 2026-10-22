import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import embed_link
import convert


class EnvironmentTests(unittest.TestCase):
    def test_converter_windows_default_and_cloud_override(self):
        for value, expected in [(None, r"D:\_WORKFORCE_ANALYTICS\People_Analytics_Blog\_posts"),
                                ("/home/runner/work/blog/_posts", "/home/runner/work/blog/_posts")]:
            with self.subTest(value=value), patch.dict(os.environ, {}, clear=True):
                if value is not None:
                    os.environ["BLOG_POSTS"] = value
                spec = importlib.util.spec_from_file_location(
                    "convert_environment_test", Path(__file__).with_name("convert.py"))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertEqual(module.BLOG_POSTS, Path(expected))

    def test_embedding_environment_precedence_and_local_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("OPENAI_API_KEY=local-test-key\nOPENAI_EMBEDDING_MODEL=local-model\n")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(embed_link.embedding_config(env_file),
                                 ("local-test-key", "local-model"))
            with patch.dict(os.environ, {"OPENAI_API_KEY": "cloud-test-key",
                                         "OPENAI_EMBEDDING_MODEL": "cloud-model"}, clear=True):
                with patch.object(embed_link, "dotenv_values", side_effect=AssertionError("Local secrets read")):
                    self.assertEqual(embed_link.embedding_config(env_file),
                                     ("cloud-test-key", "cloud-model"))

    def test_missing_key_has_actionable_error_and_default_model(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            env_file = Path(directory) / ".env"
            with self.assertRaisesRegex(ValueError, "Missing OPENAI_API_KEY.*environment"):
                embed_link.embedding_config(env_file)
            os.environ["OPENAI_API_KEY"] = "test-key"
            self.assertEqual(embed_link.embedding_config(env_file),
                             ("test-key", "text-embedding-3-large"))


class SourceFingerprintTests(unittest.TestCase):
    def test_lf_and_crlf_text_have_same_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "post.Rmd"
            rendered = root / "post.html"
            source.write_bytes(b"---\ntitle: Example\n---\nSome evidence.\n")
            rendered.write_bytes(b"<article>\nSome evidence.\n</article>\n")
            lf = convert.source_fingerprint(root, source)
            source.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))
            rendered.write_bytes(rendered.read_bytes().replace(b"\n", b"\r\n"))
            self.assertEqual(convert.source_fingerprint(root, source), lf)
            source.write_bytes(source.read_bytes().replace(b"Some evidence", b"New evidence"))
            self.assertNotEqual(convert.source_fingerprint(root, source), lf)

    def test_rendered_change_and_binary_attachment_bytes_are_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "post.Rmd"
            source.write_bytes(b'---\ntitle: Example\n---\n<object data="chart.pdf"></object>\n')
            attachment = root / "chart.pdf"
            attachment.write_bytes(b"binary\r\npayload")
            before = convert.source_fingerprint(root, source)
            attachment.write_bytes(b"binary\npayload")
            after_binary_change = convert.source_fingerprint(root, source)
            self.assertNotEqual(before, after_binary_change)
            (root / "post.html").write_bytes(b"<p>New rendered output</p>\n")
            self.assertNotEqual(after_binary_change, convert.source_fingerprint(root, source))


if __name__ == "__main__":
    unittest.main()
