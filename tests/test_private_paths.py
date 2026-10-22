import contextlib
import hashlib
import importlib.util
import io
import pathlib
import subprocess
import tempfile
import unittest
import zipfile
from unittest import mock


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check_private_paths.py"
SPEC = importlib.util.spec_from_file_location("privacy_check", SCRIPT)
MAC_HOME = "/" + "Users/" + "fixture-user"
LINUX_HOME = "/" + "home/" + "fixture-user"
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class PathDetectionTests(unittest.TestCase):
    def test_local_paths_and_utf16(self):
        samples = [MAC_HOME + "/work/input.html", LINUX_HOME + "/work",
                   "C:" + chr(92) + "Users" + chr(92) + "fixture-user" + chr(92) + "work",
                   "file://" + MAC_HOME + "/work"]
        for text in samples:
            for encoding in ("utf-8", "utf-16-le", "utf-16-be"):
                with self.subTest(text=text, encoding=encoding):
                    self.assertTrue(CHECK.scan(text.encode(encoding), "example.txt"))

    def test_web_addresses_relative_paths_and_placeholders_are_allowed(self):
        text = '\n'.join(["https://school.example/home/portal", "http://school.example/home/o3",
                          "http://school.example/gmis/(S(example))/home/portal",
                          "src/assets/lookup-base.css", "/Users/<user>/project", "/home/<user>/project"])
        self.assertFalse(CHECK.scan(text.encode(), "example.txt"))

    def test_nested_archives_and_member_names(self):
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("details.xml", "<path>" + MAC_HOME + "/work</path>")
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("nested.xlsx", inner.getvalue())
        self.assertTrue(CHECK.scan(outer.getvalue(), "archive.zip"))

    def test_private_terms_are_case_insensitive_and_redacted_in_labels(self):
        self.assertTrue(CHECK.scan(b"Fixture-Private-Value", "note.txt", ["fixture-private-value"]))
        self.assertEqual(CHECK.safe_label("Fixture-Private-Value.txt", ["fixture-private-value"]),
                         "[private].txt")

    def test_archive_limit_fails_closed(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as z:
            z.writestr("note.txt", "safe")
        self.assertTrue(CHECK.scan(output.getvalue(), "archive.zip", depth=4))

    def test_public_source_exception_is_content_pinned_and_private_terms_still_apply(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("workbook.xml", "<path>" + MAC_HOME + "/work</path>")
        data = output.getvalue()
        approved = {hashlib.sha256(data).hexdigest()}
        self.assertFalse(CHECK.scan(data, "official.xlsx", approved_hashes=approved))
        self.assertTrue(CHECK.scan(data + b"changed", "official.xlsx", approved_hashes=approved))
        self.assertTrue(CHECK.scan(data, "official.xlsx", ["fixture-user"], approved_hashes=approved))


class GitIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.patch = mock.patch.object(CHECK, "ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.git("init", "-q")
        self.git("config", "user.name", "Privacy test")
        self.git("config", "user.email", "privacy-test@example.invalid")
        self.git("config", "core.hooksPath", "/dev/null")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.DEVNULL)

    def run_check(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = CHECK.main(list(args))
        return code, stdout.getvalue() + stderr.getvalue()

    def test_staged_blob_is_checked_even_when_working_copy_is_cleaned(self):
        path = self.root / "sample.txt"
        path.write_text(MAC_HOME + "/private")
        self.git("add", "sample.txt")
        path.write_text("safe working copy")
        code, log = self.run_check("--staged")
        self.assertEqual(code, 1)
        self.assertNotIn("fixture-user", log)

    def test_unstaged_private_content_is_not_mistaken_for_staged_blob(self):
        path = self.root / "sample.txt"
        path.write_text("safe staged copy")
        self.git("add", "sample.txt")
        path.write_text(MAC_HOME + "/private")
        self.assertEqual(self.run_check("--staged")[0], 0)

    def test_history_detects_a_leak_removed_in_latest_commit(self):
        path = self.root / "sample.txt"
        path.write_text(MAC_HOME + "/private")
        self.git("add", "sample.txt")
        self.git("commit", "-qm", "historical fixture")
        path.write_text("safe now")
        self.git("add", "sample.txt")
        self.git("commit", "-qm", "clean latest fixture")
        self.assertEqual(self.run_check()[0], 0)
        self.assertEqual(self.run_check("--history")[0], 1)

    def test_forced_add_of_private_configuration_is_blocked(self):
        folder = self.root / ".privacy-local"
        folder.mkdir()
        (folder / "blocked-terms.txt").write_text("fixture-private-value\n")
        self.git("add", ".privacy-local/blocked-terms.txt")
        code, log = self.run_check("--staged")
        self.assertEqual(code, 1)
        self.assertNotIn("fixture-private-value", log)

    def test_public_tag_is_scanned_but_private_tool_snapshot_is_not(self):
        path = self.root / "sample.txt"
        path.write_text(MAC_HOME + "/private")
        self.git("add", "sample.txt")
        self.git("commit", "-qm", "private fixture")
        original_branch = self.git("symbolic-ref", "HEAD").decode().strip()
        original_commit = self.git("rev-parse", "HEAD").decode().strip()
        self.git("update-ref", "refs/private/tool-snapshot", original_commit)
        self.git("checkout", "--orphan", "clean-public")
        path.write_text("safe public content")
        self.git("add", "sample.txt")
        self.git("commit", "-qm", "clean public fixture")
        self.git("update-ref", "-d", original_branch)
        self.assertEqual(self.run_check("--history")[0], 0)
        self.git("tag", "public-fixture", original_commit)
        self.assertEqual(self.run_check("--history")[0], 1)


if __name__ == "__main__":
    unittest.main()
