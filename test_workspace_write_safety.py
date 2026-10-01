import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace

import pytest
import workspace_exchange as module


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    profile = tmp_path / 'profile'
    monkeypatch.setattr(module, 'config_path', lambda name: profile / name)
    monkeypatch.setattr(module, 'resolve_read_path', lambda name: profile / name)
    monkeypatch.setattr(module, 'PRIVACY_CONFIG_PATH', profile / 'datenschutzampel.json')
    monkeypatch.setattr(module, 'IMPORTED_WORKSPACE_PATH', profile / 'preview.json')
    source = tmp_path / 'index.sqlite'
    db = sqlite3.connect(source)
    db.execute('create table versions(name text)')
    db.execute("insert into versions values ('synthetic.pdf')")
    db.commit()
    db.close()
    updates = []
    settings = SimpleNamespace(data={'theme': 'dark'}, set=lambda k, v: updates.append((k, v)))
    search = SimpleNamespace(dbs=[str(source)])
    connections = SimpleNamespace(list_connections=list)
    return search, settings, connections, source, updates


@pytest.mark.parametrize('failure', ['none', 'json', 'encoding', 'fsync', 'replace'])
@pytest.mark.parametrize('existing', [True, False])
def test_writer_owns_only_its_private_temporary_file(tmp_path, monkeypatch, failure, existing):
    target = tmp_path / 'output.json'
    if existing:
        target.write_bytes(b'previous')
    foreign = tmp_path / 'output.json.tmp'
    foreign.write_bytes(b'foreign')
    marker = tmp_path / '.profiler-workspace-foreign.tmp'
    marker.write_bytes(b'marker')
    payload = {'value': 'Grüße'}
    if failure == 'json':
        payload['value'] = object()
    if failure == 'encoding':
        payload['value'] = '\ud800'
    if failure in ('fsync', 'replace'):
        def fail(*_):
            raise OSError('injected failure')
        monkeypatch.setattr(module.os, failure, fail)
    if failure == 'none':
        module._write_json_atomic(target, payload)
        assert json.loads(target.read_text(encoding='utf-8')) == payload
        assert target.read_bytes().endswith(b'\n')
        assert not target.read_bytes().startswith(b'\xef\xbb\xbf')
    else:
        with pytest.raises((OSError, TypeError, UnicodeError)):
            module._write_json_atomic(target, payload)
        assert (target.read_bytes() == b'previous') if existing else not target.exists()
    assert foreign.read_bytes() == b'foreign'
    assert marker.read_bytes() == b'marker'
    assert list(tmp_path.glob('.profiler-workspace-*.tmp')) == [marker]


def test_concurrent_writers_have_independent_staging(tmp_path, monkeypatch):
    target = tmp_path / 'output.json'
    barrier = Barrier(2)
    original = module.os.replace
    sources = []
    def replace(source, destination):
        sources.append(Path(source))
        barrier.wait(timeout=10)
        return original(source, destination)
    monkeypatch.setattr(module.os, 'replace', replace)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda i: module._write_json_atomic(target, {'value': i}), [1, 2]))
    assert len(set(sources)) == 2
    assert json.loads(target.read_text()) in ({'value': 1}, {'value': 2})
    assert not list(tmp_path.glob('.profiler-workspace-*.tmp'))


@pytest.mark.parametrize('kind', ['direct', 'hardlink', 'wal', 'missing-wal', 'config', 'manager-config', 'legacy'])
def test_export_cannot_replace_known_sources(workspace, tmp_path, monkeypatch, kind):
    search, settings, connections, source, _updates = workspace
    before = source.read_bytes()
    target = source
    if kind == 'hardlink':
        target = tmp_path / 'alias.json'
        os.link(source, target)
    elif kind in ('wal', 'missing-wal'):
        target = Path(str(source) + '-wal')
        if kind == 'wal':
            target.write_bytes(b'wal')
    elif kind == 'config':
        target = module.config_path('profiler_settings.json')
        target.parent.mkdir()
        target.write_bytes(b'config')
    elif kind == 'manager-config':
        target = tmp_path / 'custom-config.json'
        target.write_bytes(b'config')
        connections.path = str(target)
    elif kind == 'legacy':
        target = tmp_path / 'legacy-settings.json'
        target.write_bytes(b'legacy')
        original = module.resolve_read_path
        monkeypatch.setattr(module, 'resolve_read_path', lambda name: target if name == 'profiler_settings.json' else original(name))
    target_before = target.read_bytes() if target.exists() else None
    with pytest.raises(module.WorkspaceFormatError):
        module.export_workspace(str(target), search, settings, connections, privacy_config={})
    assert source.read_bytes() == before
    assert (target.read_bytes() == target_before) if target_before is not None else not target.exists()


@pytest.mark.parametrize('alias', [False, True])
def test_import_preview_preserves_input_before_settings(workspace, tmp_path, alias):
    search, settings, connections, _source, updates = workspace
    payload = module.build_workspace_export(search, settings, connections, privacy_config={})
    input_path = tmp_path / 'input.json'
    input_path.write_text(json.dumps(payload), encoding='utf-8')
    target = input_path
    if alias:
        target = tmp_path / 'preview-alias.json'
        os.link(input_path, target)
    before = input_path.read_bytes()
    with pytest.raises(module.WorkspaceFormatError):
        module.import_workspace(str(input_path), settings, preview_path=str(target))
    assert input_path.read_bytes() == before
    assert updates == []


def test_preview_write_error_does_not_apply_settings(workspace, tmp_path, monkeypatch):
    search, settings, connections, _source, updates = workspace
    payload = module.build_workspace_export(search, settings, connections, privacy_config={})
    input_path = tmp_path / 'input.json'
    input_path.write_text(json.dumps(payload), encoding='utf-8')
    def fail(*_):
        raise PermissionError('replace denied')
    monkeypatch.setattr(module.os, 'replace', fail)
    with pytest.raises(PermissionError):
        module.import_workspace(str(input_path), settings, preview_path=str(tmp_path / 'preview.json'))
    assert updates == []


def test_late_hardlink_to_source_rejected(workspace, tmp_path, monkeypatch):
    search, settings, connections, source, _updates = workspace
    target = tmp_path / 'late.json'
    before = source.read_bytes()
    original = module.os.fsync
    def link(fd):
        original(fd)
        os.link(source, target)
    monkeypatch.setattr(module.os, 'fsync', link)
    with pytest.raises(module.WorkspaceFormatError):
        module.export_workspace(str(target), search, settings, connections, privacy_config={})
    assert source.read_bytes() == before


@pytest.mark.skipif(os.name != 'nt', reason='Win32 filename normalization')
@pytest.mark.parametrize('suffix', ['.', ' '])
def test_windows_sidecar_normalization_rejected(workspace, suffix):
    search, settings, connections, source, _updates = workspace
    reserved = Path(str(source) + '-wal')
    with pytest.raises(module.WorkspaceFormatError):
        module.export_workspace(str(reserved) + suffix, search, settings, connections, privacy_config={})
    assert not reserved.exists()
