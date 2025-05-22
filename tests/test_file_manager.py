import pytest
from pyAdmin import FileManager
import os


@pytest.fixture
def fm():
    return FileManager()


def test_copy_file_success(fm, tmp_path):
    src = tmp_path / "test.txt"
    src.write_text("Hello World")
    dest = tmp_path / "copy.txt"

    assert fm.copy_file(str(src), str(dest)) is True
    assert os.path.exists(dest)


def test_copy_file_failure(fm):
    assert fm.copy_file("non_existent.txt", "dest.txt") is False


def test_compress_files(fm, tmp_path):
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content")
    zip_path = tmp_path / "archive.zip"

    assert fm.compress_files([str(file1)], str(zip_path)) is True
    assert zip_path.exists()


def test_system_status(fm):
    status = fm.get_system_status()
    if status:  # Если psutil установлен
        assert 'disk' in status
        assert 'memory' in status
        assert 'cpu' in status
