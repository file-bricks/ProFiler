"""Unit-Tests für github_installer.py (alle netzwerkfrei via Mock)."""

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from github_installer import (
    _SIBLING_DIRS,
    GITHUB_REPOS,
    InstallResult,
    ReleaseInfo,
    extract_zip_to_sibling,
    fetch_latest_release,
    find_zip_asset,
    install_module,
    parse_release,
)

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _make_release_json(tag="v1.2.3", assets=None):
    return {
        "tag_name": tag,
        "name": f"Release {tag}",
        "zipball_url": f"https://api.github.com/repos/file-bricks/ProSync/zipball/{tag}",
        "assets": assets or [],
    }


def _make_fake_zip(tmp_path: Path, prefix: str = "repo-v1/") -> Path:
    """Erstellt ein minimales ZIP mit GitHub-typischer Verzeichnisstruktur."""
    zip_path = tmp_path / "module.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(f"{prefix}main.py", "# main")
        zf.writestr(f"{prefix}README.md", "Readme")
        zf.writestr(f"{prefix}sub/helper.py", "# helper")
    return zip_path


# ---------------------------------------------------------------------------
# fetch_latest_release
# ---------------------------------------------------------------------------

class TestFetchLatestRelease(TestCase):
    def test_returns_dict_on_success(self):
        data = _make_release_json()
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = fetch_latest_release("file-bricks", "ProSync")

        self.assertEqual(result["tag_name"], "v1.2.3")

    def test_returns_none_on_404(self):
        import urllib.error
        http_err = urllib.error.HTTPError(
            url="https://api.github.com/repos/x/y/releases/latest",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=http_err):
            result = fetch_latest_release("x", "y")

        self.assertIsNone(result)

    def test_raises_on_non_404_http_error(self):
        import urllib.error
        http_err = urllib.error.HTTPError(
            url="https://api.github.com/repos/x/y/releases/latest",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=http_err):
            with self.assertRaises(urllib.error.HTTPError):
                fetch_latest_release("x", "y")

    def test_includes_auth_header_when_token_given(self):
        data = _make_release_json()
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        captured_req = []

        def fake_urlopen(req, timeout=None):
            captured_req.append(req)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            fetch_latest_release("file-bricks", "ProSync", token="gh_secret")

        self.assertIn("Authorization", captured_req[0].headers)
        self.assertIn("gh_secret", captured_req[0].headers["Authorization"])


# ---------------------------------------------------------------------------
# find_zip_asset / parse_release
# ---------------------------------------------------------------------------

class TestFindZipAsset(TestCase):
    def test_prefers_explicit_zip_asset(self):
        data = _make_release_json(assets=[
            {"name": "ProSync-v1.2.3.zip", "browser_download_url": "https://example.com/ps.zip"},
            {"name": "ProSync-v1.2.3.tar.gz", "browser_download_url": "https://example.com/ps.tar.gz"},
        ])
        url, name = find_zip_asset(data)
        self.assertEqual(url, "https://example.com/ps.zip")
        self.assertEqual(name, "ProSync-v1.2.3.zip")

    def test_falls_back_to_zipball_url(self):
        data = _make_release_json(assets=[])
        url, name = find_zip_asset(data)
        self.assertIn("zipball", url)
        self.assertIsNone(name)

    def test_parse_release_returns_release_info(self):
        data = _make_release_json(tag="v2.0.0")
        info = parse_release(data)
        self.assertIsInstance(info, ReleaseInfo)
        self.assertEqual(info.tag_name, "v2.0.0")
        self.assertIsNotNone(info.zip_asset_url)


# ---------------------------------------------------------------------------
# extract_zip_to_sibling
# ---------------------------------------------------------------------------

class TestExtractZipToSibling(TestCase):
    def test_extracts_with_github_prefix(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            zip_path = _make_fake_zip(tmp_p, prefix="repo-v1.0/")
            out_dir = tmp_p / "output"
            extract_zip_to_sibling(zip_path, out_dir)
            self.assertTrue((out_dir / "main.py").exists())
            self.assertTrue((out_dir / "README.md").exists())
            self.assertTrue((out_dir / "sub" / "helper.py").exists())

    def test_extracts_without_prefix(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            zip_path = tmp_p / "flat.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("main.py", "# flat")
            out_dir = tmp_p / "flat_out"
            extract_zip_to_sibling(zip_path, out_dir)
            self.assertTrue((out_dir / "main.py").exists())

    def test_creates_target_directory(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            zip_path = _make_fake_zip(tmp_p)
            out_dir = tmp_p / "deep" / "nested" / "dir"
            self.assertFalse(out_dir.exists())
            extract_zip_to_sibling(zip_path, out_dir)
            self.assertTrue(out_dir.exists())


# ---------------------------------------------------------------------------
# install_module
# ---------------------------------------------------------------------------

class TestInstallModule(TestCase):
    def test_unknown_key_returns_error(self):
        result = install_module("nichts_davon")
        self.assertFalse(result.success)
        self.assertIn("Unbekannter Modul-Schlüssel", result.error or "")

    def test_no_repo_returns_graceful_message(self):
        with patch.dict(GITHUB_REPOS, {"testkey": None}):
            result = install_module("testkey")
        self.assertFalse(result.success)
        self.assertIsNone(result.error)
        self.assertIn("kein GitHub-Repository", result.message)

    def test_no_releases_returns_graceful_message(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(GITHUB_REPOS, {"prosync": ("file-bricks", "ProSync")}):
                with patch("github_installer.fetch_latest_release", return_value=None):
                    result = install_module("prosync", parent_dir=Path(tmp))
            self.assertFalse(result.success)
            self.assertIn("kein release", result.message.lower())

    def test_network_error_returns_error_result(self):
        import tempfile
        import urllib.error
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "github_installer.fetch_latest_release",
                side_effect=urllib.error.URLError("offline"),
            ):
                result = install_module("prosync", parent_dir=Path(tmp))
            self.assertFalse(result.success)
            self.assertIn("Netzwerkfehler", result.error or "")

    def test_successful_install(self):
        import tempfile
        release_data = _make_release_json()

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            zip_bytes = io.BytesIO()
            with zipfile.ZipFile(zip_bytes, "w") as zf:
                zf.writestr("repo-v1/ProSyncStart_V3.1.py", "# prosync")
            zip_bytes.seek(0)
            archive_bytes = zip_bytes.getvalue()
            expected_sha256 = hashlib.sha256(archive_bytes).hexdigest()

            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(release_data).encode(),
                zip_bytes.read(),
            ]
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)

            def fake_urlopen(req, timeout=None):
                return mock_resp

            def fake_download(_url, destination, token=None):
                destination.write_bytes(archive_bytes)

            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                with patch("github_installer.fetch_latest_release", return_value=release_data):
                    with patch("github_installer.download_file", side_effect=fake_download):
                        with patch("github_installer.extract_zip_to_sibling") as mock_extract:
                            result = install_module(
                                "prosync",
                                parent_dir=parent,
                                expected_sha256=expected_sha256,
                            )

            self.assertTrue(result.success, result.error)
            mock_extract.assert_called_once()


# ---------------------------------------------------------------------------
# Struktur-Tests
# ---------------------------------------------------------------------------

class TestGithubReposStructure(TestCase):
    def test_all_known_keys_have_entry_in_github_repos(self):
        from module_registry import _KNOWN
        known_keys = {item[0] for item in _KNOWN}
        for key in known_keys:
            self.assertIn(key, GITHUB_REPOS, f"Kein GITHUB_REPOS-Eintrag für Modul '{key}'")

    def test_all_keys_have_sibling_dir_entry(self):
        from module_registry import _KNOWN
        known_keys = {item[0] for item in _KNOWN}
        for key in known_keys:
            self.assertIn(key, _SIBLING_DIRS, f"Kein _SIBLING_DIRS-Eintrag für Modul '{key}'")

    def test_repo_info_is_tuple_or_none(self):
        for key, info in GITHUB_REPOS.items():
            if info is not None:
                self.assertIsInstance(info, tuple, f"GITHUB_REPOS[{key!r}] ist kein Tuple")
                self.assertEqual(len(info), 2, f"GITHUB_REPOS[{key!r}] hat nicht 2 Elemente")

    def test_install_result_fields_exist(self):
        r = InstallResult(key="test", success=True, message="ok")
        self.assertEqual(r.key, "test")
        self.assertTrue(r.success)
        self.assertIsNone(r.error)
        self.assertIsNone(r.installed_path)
