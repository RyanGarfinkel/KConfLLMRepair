from unittest.mock import patch, MagicMock
from src.kernel.builder import builder

def test_build_success(tmp_path):
	log_file = str(tmp_path / 'build.log')
	mock_result = MagicMock()
	mock_result.returncode = 0
	with patch('src.kernel.builder.subprocess.run', return_value=mock_result):
		result = builder.build('/fake/src', log_file)
	assert result is True

def test_build_failure(tmp_path):
	log_file = str(tmp_path / 'build.log')
	mock_result = MagicMock()
	mock_result.returncode = 1
	with patch('src.kernel.builder.subprocess.run', return_value=mock_result):
		result = builder.build('/fake/src', log_file)
	assert result is False
