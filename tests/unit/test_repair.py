from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from src.cli.repair import get_input, repair_config, main
from src.config import settings
import click
import pytest
import os

@pytest.fixture(autouse=True)
def restore_settings():
	saved = {
		'OUTPUT_DIR': settings.runtime.OUTPUT_DIR,
		'JOBS': settings.runtime.JOBS,
		'USE_RAG': settings.runtime.USE_RAG,
		'MODEL': settings.agent.MODEL,
		'MAX_ITERATIONS': settings.agent.MAX_ITERATIONS,
		'ARCH': settings.kernel.ARCH,
		'DEBIAN_IMG': settings.kernel.DEBIAN_IMG,
	}
	yield
	settings.runtime.OUTPUT_DIR = saved['OUTPUT_DIR']
	settings.runtime.JOBS = saved['JOBS']
	settings.runtime.USE_RAG = saved['USE_RAG']
	settings.agent.MODEL = saved['MODEL']
	settings.agent.MAX_ITERATIONS = saved['MAX_ITERATIONS']
	settings.kernel.ARCH = saved['ARCH']
	settings.kernel.DEBIAN_IMG = saved['DEBIAN_IMG']

@pytest.fixture
def config_file(tmp_path):
	p = tmp_path / 'test.config'
	p.touch()
	return p

@pytest.fixture
def patch_files(tmp_path):
	original = tmp_path / 'original.config'
	modified = tmp_path / 'modified.config'
	pf = tmp_path / 'changes.patch'
	original.touch()
	modified.touch()
	pf.touch()
	return original, modified, pf

@pytest.fixture
def constraints_file(tmp_path):
	p = tmp_path / 'constraints.txt'
	p.touch()
	return p

runner = CliRunner()

# --- get_input tests ---

def test_get_input_config_mode(config_file):
	inp = get_input(config=str(config_file))
	assert inp.original_config == os.path.abspath(str(config_file))
	assert inp.modified_config is None
	assert inp.patch is None

def test_get_input_patch_mode(patch_files):
	original, modified, pf = patch_files
	inp = get_input(original=str(original), modified=str(modified), patch=str(pf))
	assert inp.original_config == os.path.abspath(str(original))
	assert inp.modified_config == os.path.abspath(str(modified))
	assert inp.patch == os.path.abspath(str(pf))

def test_get_input_with_constraints(config_file, constraints_file):
	inp = get_input(config=str(config_file), constraints=str(constraints_file))
	assert inp.hard_constraints == os.path.abspath(str(constraints_file))

def test_get_input_error_both_modes(config_file, patch_files):
	original, modified, pf = patch_files
	with pytest.raises(click.UsageError):
		get_input(config=str(config_file), original=str(original), modified=str(modified), patch=str(pf))

def test_get_input_error_neither_mode():
	with pytest.raises(click.UsageError):
		get_input()

def test_get_input_error_partial_patch(patch_files):
	original, modified, pf = patch_files
	with pytest.raises(click.UsageError):
		get_input(original=str(original), patch=str(pf))

# --- repair_config tests ---

def test_repair_config_calls_kernel(config_file, tmp_path):
	inp = get_input(config=str(config_file))
	with patch('src.cli.repair.Kernel') as mock_kernel_cls, \
		 patch('src.cli.repair.agent.repair'):
		repair_config(inp, str(tmp_path))
		mock_kernel_cls.assert_called_once_with(str(tmp_path))

def test_repair_config_calls_agent_repair(config_file, tmp_path):
	inp = get_input(config=str(config_file))
	with patch('src.cli.repair.Kernel') as mock_kernel_cls, \
		 patch('src.cli.repair.agent.repair') as mock_repair:
		kernel_instance = mock_kernel_cls.return_value
		repair_config(inp, str(tmp_path))
		mock_repair.assert_called_once_with(inp, kernel_instance)

# --- main() tests ---

def test_main_config_mode(config_file, tmp_path):
	with patch('src.cli.repair.repair_config') as mock_repair, \
		 patch('src.cli.repair.log_settings'):
		result = runner.invoke(main, ['--config', str(config_file), '--src', str(tmp_path)])
		assert result.exit_code == 0
		mock_repair.assert_called_once()

def test_main_patch_mode(patch_files, tmp_path):
	original, modified, pf = patch_files
	with patch('src.cli.repair.repair_config') as mock_repair, \
		 patch('src.cli.repair.log_settings'):
		result = runner.invoke(main, [
			'--original', str(original),
			'--modified', str(modified),
			'--patch', str(pf),
			'--src', str(tmp_path),
		])
		assert result.exit_code == 0
		mock_repair.assert_called_once()

def test_main_output_sets_settings(config_file, tmp_path):
	output = str(tmp_path / 'out')
	with patch('src.cli.repair.repair_config'), patch('src.cli.repair.log_settings'):
		runner.invoke(main, ['--config', str(config_file), '--src', str(tmp_path), '--output', output])
	assert settings.runtime.OUTPUT_DIR == f'{output}/agent_repair'

def test_main_model_sets_settings(config_file, tmp_path):
	with patch('src.cli.repair.repair_config'), patch('src.cli.repair.log_settings'):
		runner.invoke(main, ['--config', str(config_file), '--src', str(tmp_path), '--model', 'gpt-4o'])
	assert settings.agent.MODEL == 'gpt-4o'

def test_main_jobs_sets_settings(config_file, tmp_path):
	with patch('src.cli.repair.repair_config'), patch('src.cli.repair.log_settings'):
		runner.invoke(main, ['--config', str(config_file), '--src', str(tmp_path), '--jobs', '4'])
	assert settings.runtime.JOBS == 4

def test_main_iterations_sets_settings(config_file, tmp_path):
	with patch('src.cli.repair.repair_config'), patch('src.cli.repair.log_settings'):
		runner.invoke(main, ['--config', str(config_file), '--src', str(tmp_path), '--iterations', '5'])
	assert settings.agent.MAX_ITERATIONS == 5

def test_main_rag_flag_sets_settings(config_file, tmp_path):
	with patch('src.cli.repair.repair_config'), patch('src.cli.repair.log_settings'):
		runner.invoke(main, ['--config', str(config_file), '--src', str(tmp_path), '--rag'])
	assert settings.runtime.USE_RAG is True

def test_main_arch_sets_settings(config_file, tmp_path):
	with patch('src.cli.repair.repair_config'), patch('src.cli.repair.log_settings'):
		runner.invoke(main, ['--config', str(config_file), '--src', str(tmp_path), '--arch', 'arm64'])
	assert settings.kernel.ARCH == 'arm64'

def test_main_img_sets_settings(config_file, tmp_path):
	with patch('src.cli.repair.repair_config'), patch('src.cli.repair.log_settings'):
		runner.invoke(main, ['--config', str(config_file), '--src', str(tmp_path), '--img', '/path/img'])
	assert settings.kernel.DEBIAN_IMG == '/path/img'

def test_main_src_resolves_absolute(config_file, tmp_path):
	with patch('src.cli.repair.repair_config') as mock_repair, patch('src.cli.repair.log_settings'):
		runner.invoke(main, ['--config', str(config_file), '--src', str(tmp_path)])
		mock_repair.assert_called_once()
		assert os.path.isabs(mock_repair.call_args[0][1])

def test_main_src_missing_raises(config_file):
	result = runner.invoke(main, ['--config', str(config_file), '--src', '/nonexistent/path'])
	assert result.exit_code != 0

def test_main_src_fallback_to_env(config_file, tmp_path, monkeypatch):
	monkeypatch.setattr(settings.kernel, 'KERNEL_SRC', str(tmp_path))
	with patch('src.cli.repair.repair_config') as mock_repair, patch('src.cli.repair.log_settings'):
		result = runner.invoke(main, ['--config', str(config_file)])
		assert result.exit_code == 0
		mock_repair.assert_called_once()
		assert mock_repair.call_args[0][1] == os.path.abspath(str(tmp_path))
