from src.tools.klocalizer import klocalizer
from unittest.mock import patch, MagicMock
import pytest
import os

@pytest.fixture
def log_path(tmp_path):
	return str(tmp_path / 'klocalizer.log')

# Conflicting constraints: Failure
def test_conflicting_constraints(log_path):
	result = klocalizer.run('/fake/src', log_path, define=['A'], undefine=['A'])
	assert result == 'no-satisfying-constraints'

# Klocalizer succeeds
def test_run_success(log_path, tmp_path):
	mock_result = MagicMock()
	mock_result.returncode = 0
	with patch('subprocess.run', return_value=mock_result):
		result = klocalizer.run('/fake/src', log_path, define=['X'], undefine=['Y'])
	assert result == 'success'
	assert os.path.exists(str(tmp_path / 'constraints.txt'))

# Klocalizer returns no satisfying constraints: Failure
def test_run_no_satisfying(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 11
	with patch('subprocess.run', return_value=mock_result):
		result = klocalizer.run('/fake/src', log_path)
	assert result == 'no-satisfying-constraints'

# Klocalizer returns error: Failure
def test_run_error(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 1
	with patch('subprocess.run', return_value=mock_result):
		result = klocalizer.run('/fake/src', log_path)
	assert result == 'error'

# Patch mode succeeds: Success
def test_run_patch_success(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 0
	with patch('subprocess.run', return_value=mock_result):
		result = klocalizer.run_patch('/fake/src', '/fake/patch', log_path, define=['A'])
	assert result == 'success'

# Patch mode returns no satisfying constraints: Failure
def test_run_patch_no_satisfying(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 11
	with patch('subprocess.run', return_value=mock_result):
		result = klocalizer.run_patch('/fake/src', '/fake/patch', log_path)
	assert result == 'no-satisfying-constraints'

# Patch mode passes undefine args to subprocess: Success
def test_run_patch_with_undefine(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 0
	with patch('subprocess.run', return_value=mock_result) as mock_run:
		result = klocalizer.run_patch('/fake/src', '/fake/patch', log_path, undefine=['B'])
	assert result == 'success'
	cmd = mock_run.call_args[0][0]
	assert '--undefine' in cmd
	assert 'B' in cmd

# Patch mode returns error: Failure
def test_run_patch_error(log_path):
	mock_result = MagicMock()
	mock_result.returncode = 1
	with patch('subprocess.run', return_value=mock_result):
		result = klocalizer.run_patch('/fake/src', '/fake/patch', log_path)
	assert result == 'error'

# Constraints file written with define and undefine format: Success
def test_constraints_file_content(log_path, tmp_path):
	mock_result = MagicMock()
	mock_result.returncode = 0
	with patch('subprocess.run', return_value=mock_result):
		klocalizer.run('/fake/src', log_path, define=['X'], undefine=['Y'])
	with open(str(tmp_path / 'constraints.txt')) as f:
		content = f.read()
	assert 'X\n' in content
	assert '!Y\n' in content
