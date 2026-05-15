from src.kernel.diffconfig import diffconfig
from unittest.mock import patch, MagicMock

# Compare configs: Success
def test_compare_success():
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = 'CONFIG_A=y\nCONFIG_B=m'

	with patch('subprocess.run', return_value=mock_result):
		diff_lines, count = diffconfig.compare('/fake/base.config', '/fake/modified.config')

	assert diff_lines == ['CONFIG_A=y', 'CONFIG_B=m']
	assert count == 2

# Compare configs: Failure
def test_compare_failure():
	mock_result = MagicMock()
	mock_result.returncode = 1

	with patch('subprocess.run', return_value=mock_result):
		diff_lines, count = diffconfig.compare('/fake/base.config', '/fake/modified.config')

	assert diff_lines == []
	assert count == -1
