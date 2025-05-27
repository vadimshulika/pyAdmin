import pytest
import shutil
import stat
from pathlib import Path
from pyAdmin.file_manager import FileManager
import zipfile

def test_caller_dir():
    fm = FileManager()
    expected_dir = Path(__file__).parent.resolve()
    assert fm.caller_dir == expected_dir

def test_resolve_path():
    fm = FileManager()
    test_path = "test.txt"
    resolved = fm._resolve_path(test_path)
    expected = Path(__file__).parent.resolve() / test_path
    assert resolved == expected

def test_copy_file_success(tmp_path):
    src = tmp_path / "source.txt"
    src.write_text("test")
    dest = tmp_path / "subdir" / "dest.txt"
    
    fm = FileManager()
    fm.caller_dir = tmp_path  # Переопределяем базовый путь
    assert fm.copy_file(src.name, dest.relative_to(tmp_path)) is True
    assert dest.exists()

def test_copy_file_not_found(tmp_path):
    fm = FileManager()
    fm.caller_dir = tmp_path
    assert fm.copy_file("nonexistent.txt", "dest.txt") is False

def test_move_file_success(tmp_path):
    src = tmp_path / "file.txt"
    src.write_text("content")
    dest = tmp_path / "moved.txt"
    
    fm = FileManager()
    fm.caller_dir = tmp_path
    assert fm.move_file(src.name, dest.name) is True
    assert not src.exists()
    assert dest.exists()

def test_compress_files(tmp_path):
    files = [tmp_path / "a.txt", tmp_path / "b.log"]
    for f in files:
        f.write_text("data")
    
    fm = FileManager()
    fm.caller_dir = tmp_path
    assert fm.compress_files([f.name for f in files], "test.zip") is True
    
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path) as z:
        assert len(z.namelist()) == 2

def test_get_file_metadata(tmp_path):
    test_file = tmp_path / "meta.txt"
    test_file.write_text("metadata")
    
    fm = FileManager()
    fm.caller_dir = tmp_path
    meta = fm.get_file_metadata(test_file.name)
    
    assert meta['size_bytes'] == 8
    assert meta['extension'] == '.txt'
    assert 'absolute_path' in meta

def test_copy_file_generic_error(tmp_path, monkeypatch):
    """Общий Exception при копировании"""
    fm = FileManager()
    fm.caller_dir = tmp_path

def test_copy_file_generic_error(tmp_path, monkeypatch, capsys):
    fm = FileManager()
    fm.caller_dir = tmp_path
    (tmp_path / "dummy.txt").touch()

    def mock_copy(*args, **kwargs):
        raise RuntimeError("Simulated error")

    monkeypatch.setattr(shutil, 'copy', mock_copy)
    
    result = fm.copy_file("dummy.txt", "error.txt")
    captured = capsys.readouterr()
    assert "Copy error: Simulated error" in captured.out
    assert result is False

def test_move_file_generic_error(tmp_path, monkeypatch, capsys):
    fm = FileManager()
    fm.caller_dir = tmp_path
    (tmp_path / "test.txt").touch()

    def mock_move(*args, **kwargs):
        raise RuntimeError("Move failed")

    monkeypatch.setattr(shutil, 'move', mock_move)
    
    result = fm.move_file("test.txt", "error.txt")
    captured = capsys.readouterr()
    assert "Move error: Move failed" in captured.out
    assert result is False

def test_compress_invalid_files(tmp_path, capsys):
    fm = FileManager()
    fm.caller_dir = tmp_path
    dir_path = tmp_path / "empty_dir"
    dir_path.mkdir()
    
    result = fm.compress_files([dir_path.name, "ghost.file"], "test.zip")
    captured = capsys.readouterr()
    assert "Skipping" in captured.out
    assert result is False

def test_compress_empty_archive(tmp_path, capsys):
    fm = FileManager()
    fm.caller_dir = tmp_path
    
    result = fm.compress_files(["non_existent.txt"], "empty.zip")
    captured = capsys.readouterr()
    assert "created with 0 files" in captured.out
    assert result is False

def test_metadata_nonexistent_file(tmp_path, capsys):
    fm = FileManager()
    fm.caller_dir = tmp_path
    
    meta = fm.get_file_metadata("ghost.file")
    captured = capsys.readouterr()
    assert "not found" in captured.out
    assert meta == {}

