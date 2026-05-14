from unittest.mock import patch, MagicMock
from src.core.kernel import Kernel
import pytest
import os

@pytest.fixture
def fake_kernel_src(tmp_path):
	makefile = tmp_path / 'Makefile'
	makefile.write_text(
		'VERSION = 7\n'
		'PATCHLEVEL = 0\n'
		'SUBLEVEL = 0\n'
		'EXTRAVERSION = -rc1\n'
	)
	(tmp_path / '.config').touch()
	return str(tmp_path)

@pytest.fixture
def config_file(tmp_path):
	p = tmp_path / 'test.config'
	p.touch()
	return str(p)

# Kernel init: Success
def test_kernel_init_valid(fake_kernel_src):
	kernel = Kernel(fake_kernel_src)
	assert kernel.src == fake_kernel_src

# Kernel init: Failure
def test_kernel_init_invalid():
	with pytest.raises(ValueError):
		Kernel('/nonexistent/kernel/path')

# Kernel version: Success
def test_kernel_version(fake_kernel_src):
	kernel = Kernel(fake_kernel_src)
	assert kernel.version == '7.0.0-rc1'

# Load config: Success
def test_load_config_success(fake_kernel_src, config_file):
	kernel = Kernel(fake_kernel_src)
	assert kernel.load_config(config_file) is True
	assert os.path.exists(f'{fake_kernel_src}/.config')

# Load config wrong extension: Failure
def test_load_config_wrong_extension(fake_kernel_src, tmp_path):
	bad_file = str(tmp_path / 'test.txt')
	open(bad_file, 'w').close()
	kernel = Kernel(fake_kernel_src)
	assert kernel.load_config(bad_file) is False

# Load config missing file: Failure
def test_load_config_missing_file(fake_kernel_src):
	kernel = Kernel(fake_kernel_src)
	assert kernel.load_config('/nonexistent/test.config') is False

# Make rand config: Success
def test_make_rand_config_success(fake_kernel_src, tmp_path):
	kernel = Kernel(fake_kernel_src)
	with patch('src.core.kernel.randconfig.make', return_value=True):
		result = kernel.make_rand_config(str(tmp_path / 'out.config'), seed=42)
	assert result is True

# Make rand config: Failure
def test_make_rand_config_failure(fake_kernel_src, tmp_path):
	kernel = Kernel(fake_kernel_src)
	with patch('src.core.kernel.randconfig.make', return_value=False):
		result = kernel.make_rand_config(str(tmp_path / 'out.config'), seed=42)
	assert result is False

# Run klocalizer no patch: Success
def test_run_klocalizer_no_patch(fake_kernel_src, config_file, tmp_path):
	kernel = Kernel(fake_kernel_src)
	with patch('src.core.kernel.klocalizer.run', return_value='success'):
		result = kernel.run_klocalizer(str(tmp_path), config_file)
	assert result.status == 'success'

# Run klocalizer with patch: Success
def test_run_klocalizer_patch(fake_kernel_src, config_file, tmp_path):
	kernel = Kernel(fake_kernel_src)
	patch_file = str(tmp_path / 'changes.patch')
	open(patch_file, 'w').close()
	with patch('src.core.kernel.klocalizer.run_patch', return_value='success'):
		result = kernel.run_klocalizer(str(tmp_path), config_file, patch=patch_file)
	assert result.status == 'success'

# Run klocalizer no satisfying constraints: Failure
def test_run_klocalizer_no_satisfying(fake_kernel_src, config_file, tmp_path):
	kernel = Kernel(fake_kernel_src)
	with patch('src.core.kernel.klocalizer.run', return_value='no-satisfying-constraints'):
		result = kernel.run_klocalizer(str(tmp_path), config_file)
	assert result.status == 'no-satisfying-constraints'

# Build: Success
def test_build_success(fake_kernel_src, config_file, tmp_path):
	kernel = Kernel(fake_kernel_src)
	with patch('src.core.kernel.builder.build', return_value=True):
		result = kernel.build(str(tmp_path), config_file)
	assert result.ok is True

# Build: Failure
def test_build_failure(fake_kernel_src, config_file, tmp_path):
	kernel = Kernel(fake_kernel_src)
	with patch('src.core.kernel.builder.build', return_value=False):
		result = kernel.build(str(tmp_path), config_file)
	assert result.ok is False

# Make patch: Success
def test_make_patch_success(fake_kernel_src, tmp_path):
	kernel = Kernel(fake_kernel_src)
	patch_path = str(tmp_path / 'out.patch')
	mock_repo = MagicMock()
	mock_repo.git.diff.return_value = 'some diff content'
	with patch('src.core.kernel.Repo', return_value=mock_repo):
		result = kernel.make_patch(patch_path)
	assert result is True
	with open(patch_path) as f:
		assert f.read() == 'some diff content'

# Make patch: Failure
def test_make_patch_failure(fake_kernel_src, tmp_path):
	kernel = Kernel(fake_kernel_src)
	patch_path = str(tmp_path / 'out.patch')
	with patch('src.core.kernel.Repo', side_effect=Exception('git error')):
		result = kernel.make_patch(patch_path)
	assert result is False
