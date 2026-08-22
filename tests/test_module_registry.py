# tests/test_module_registry.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from module_registry import ModuleInfo, ModuleRegistry


class TestModuleInfo:
    def test_fields_exist(self):
        info = ModuleInfo(
            key="prosync",
            display_name="ProSync",
            filename="ProSyncStart_V3.1.py",
        )
        assert info.key == "prosync"
        assert info.display_name == "ProSync"
        assert info.filename == "ProSyncStart_V3.1.py"
        assert info.configured_path == ""
        assert info.resolved_path is None
        assert info.available is False

    def test_available_when_resolved(self):
        p = Path("/some/path/ProSyncStart_V3.1.py")
        info = ModuleInfo("prosync", "ProSync", "ProSyncStart_V3.1.py",
                          resolved_path=p, available=True)
        assert info.available is True
        assert info.resolved_path == p


class TestModuleRegistry:
    def test_known_modules_includes_prosync(self):
        reg = ModuleRegistry(base_dir=Path("."))
        keys = [m.key for m in reg.all_modules()]
        assert "prosync" in keys

    def test_known_modules_includes_sqliteviewer(self):
        reg = ModuleRegistry(base_dir=Path("."))
        keys = [m.key for m in reg.all_modules()]
        assert "sqliteviewer" in keys

    def test_module_unavailable_when_not_found(self, tmp_path):
        reg = ModuleRegistry(base_dir=tmp_path)
        module = reg.get("prosync")
        assert module is not None
        assert module.available is False
        assert module.resolved_path is None

    def test_detects_module_in_same_dir(self, tmp_path):
        (tmp_path / "SQLiteViewer.py").touch()
        reg = ModuleRegistry(base_dir=tmp_path)
        module = reg.get("sqliteviewer")
        assert module.available is True
        assert module.resolved_path is not None

    def test_detects_module_in_sibling_dir(self, tmp_path):
        sibling = tmp_path / "REL-PUB_ProSync"
        sibling.mkdir()
        (sibling / "ProSyncStart_V3.1.py").touch()
        project_dir = tmp_path / "REL-PUB_ProFiler"
        project_dir.mkdir()
        reg = ModuleRegistry(base_dir=project_dir)
        module = reg.get("prosync")
        assert module.available is True

    def test_configured_path_takes_priority(self, tmp_path):
        custom = tmp_path / "custom"
        custom.mkdir()
        (custom / "SQLiteViewer.py").touch()
        reg = ModuleRegistry(
            base_dir=tmp_path,
            configured_paths={"sqliteviewer": str(custom / "SQLiteViewer.py")},
        )
        module = reg.get("sqliteviewer")
        assert module.available is True
        assert str(module.resolved_path) == str(custom / "SQLiteViewer.py")

    def test_configured_path_with_windows_env_var(self, tmp_path, monkeypatch):
        custom = tmp_path / "custom"
        custom.mkdir()
        tool_file = custom / "SQLiteViewer.py"
        tool_file.touch()
        monkeypatch.setenv("_PFTEST_REG_DIR", str(custom))

        reg = ModuleRegistry(
            base_dir=tmp_path,
            configured_paths={"sqliteviewer": r"%_PFTEST_REG_DIR%\SQLiteViewer.py"},
        )
        module = reg.get("sqliteviewer")
        assert module is not None
        assert module.available is True
        assert module.resolved_path == tool_file.resolve()

    def test_configured_path_directory_with_env_var(self, tmp_path, monkeypatch):
        custom = tmp_path / "custom"
        custom.mkdir()
        tool_file = custom / "ProSync.exe"
        tool_file.touch()
        monkeypatch.setenv("_PFTEST_REG_DIR", str(custom))

        reg = ModuleRegistry(
            base_dir=tmp_path,
            configured_paths={"prosync": r"%_PFTEST_REG_DIR%"},
        )
        module = reg.get("prosync")
        assert module is not None
        assert module.available is True
        assert module.resolved_path == tool_file.resolve()

    def test_configured_path_whitespace_is_ignored(self, tmp_path):
        reg = ModuleRegistry(
            base_dir=tmp_path,
            configured_paths={"sqliteviewer": "   "},
        )
        module = reg.get("sqliteviewer")
        assert module is not None
        assert module.available is False

    def test_does_not_execute_known_filename_from_arbitrary_sibling(self, tmp_path):
        untrusted = tmp_path / "untrusted-download"
        untrusted.mkdir()
        (untrusted / "SQLiteViewer.py").touch()
        project_dir = tmp_path / "REL-PUB_ProFiler"
        project_dir.mkdir()

        module = ModuleRegistry(base_dir=project_dir).get("sqliteviewer")

        assert module is not None
        assert module.available is False

    def test_get_unknown_key_returns_none(self):
        reg = ModuleRegistry(base_dir=Path("."))
        assert reg.get("nichtvorhandenes_modul") is None

    def test_all_modules_returns_list(self):
        reg = ModuleRegistry(base_dir=Path("."))
        modules = reg.all_modules()
        assert isinstance(modules, list)
        assert len(modules) >= 4


class TestGetByFilename:
    def test_get_by_filename_found(self):
        reg = ModuleRegistry(base_dir=Path("."))
        info = reg.get_by_filename("SQLiteViewer.py")
        assert info is not None
        assert info.key == "sqliteviewer"

    def test_get_by_filename_unknown_returns_none(self):
        reg = ModuleRegistry(base_dir=Path("."))
        assert reg.get_by_filename("UnbekanntesDing.py") is None
