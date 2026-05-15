from src.kernel.randconfig import randconfig
from unittest.mock import patch, MagicMock

# Make randconfig: Success
def test_make_success():
	mock_result = MagicMock()
	mock_result.returncode = 0

	with patch('subprocess.run', return_value=mock_result):
		result = randconfig.make('/fake/kernel', '/fake/out.config', seed=42)

	assert result is True

# Make randconfig: Failure
def test_make_failure():
	mock_result = MagicMock()
	mock_result.returncode = 1
	mock_result.stderr = ''

	with patch('subprocess.run', return_value=mock_result):
		result = randconfig.make('/fake/kernel', '/fake/out.config', seed=42)

	assert result is False

# Make randconfig with stderr: Failure
def test_make_failure_with_stderr():
	mock_result = MagicMock()
	mock_result.returncode = 1
	mock_result.stderr = 'some error output'

	with patch('subprocess.run', return_value=mock_result):
		result = randconfig.make('/fake/kernel', '/fake/out.config', seed=42)
		
	assert result is False
