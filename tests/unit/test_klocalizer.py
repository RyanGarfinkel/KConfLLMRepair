from unittest.mock import patch, MagicMock
from src.tools.klocalizer import klocalizer
import pytest
import os

@pytest.fixture
def log_path(tmp_path):
	return str(tmp_path / 'klocalizer.log')

def test_conflicting_constraints(log_path):
	result = klocalizer.run('/fake/src', log_path, define=['A'], undefine=['A'])
	assert result == 'no-satisfying-constraints'

def test_run_success(log_path, tmp_path):
	mock_result = MagicMock()
	mock_result.returncode = 0
	with patch('src.tools.klocalizer.subprocess.run', return_value=mock_result):
		result = klocalizer.run('/fake/src', log_path, define=['X'], undefine=['Y'])
	assert result == 'success'
	assert os.path.exists(str(tmp_path / 'constraints.txt'))

def test_run_no_satisfying(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 11
	with patch('src.tools.klocalizer.subprocess.run', return_value=mock_result):
		result = klocalizer.run('/fake/src', log_path)
	assert result == 'no-satisfying-constraints'

def test_run_error(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 1
	with patch('src.tools.klocalizer.subprocess.run', return_value=mock_result):
		result = klocalizer.run('/fake/src', log_path)
	assert result == 'error'

def test_run_patch_success(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 0
	with patch('src.tools.klocalizer.subprocess.run', return_value=mock_result):
		result = klocalizer.run_patch('/fake/src', '/fake/patch', log_path, define=['A'])
	assert result == 'success'

def test_run_patch_no_satisfying(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 11
	with patch('src.tools.klocalizer.subprocess.run', return_value=mock_result):
		result = klocalizer.run_patch('/fake/src', '/fake/patch', log_path)
	assert result == 'no-satisfying-constraints'

def test_constraints_file_content(log_path, tmp_path):
	mock_result = MagicMock()
	mock_result.returncode = 0
	with patch('src.tools.klocalizer.subprocess.run', return_value=mock_result):
		klocalizer.run('/fake/src', log_path, define=['X'], undefine=['Y'])
	with open(str(tmp_path / 'constraints.txt')) as f:
		content = f.read()
	assert 'X\n' in content
	assert '!Y\n' in content
