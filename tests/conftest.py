import pytest
import os

os.environ['GOOGLE_API_KEY'] = 'fake-key-for-testing'

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

def _copy_fixture(name, tmp_path):
	src = os.path.join(FIXTURES_DIR, name)
	dst = tmp_path / name
	dst.write_bytes(open(src, 'rb').read())
	return str(dst)

@pytest.fixture(autouse=True)
def chdir_tmp(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)

@pytest.fixture
def tmp_config(tmp_path):
	return _copy_fixture('sample.config', tmp_path)

@pytest.fixture
def tmp_patch(tmp_path):
	return _copy_fixture('sample.patch', tmp_path)
