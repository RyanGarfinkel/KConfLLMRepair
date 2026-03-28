from src.tools.klocalizer import klocalizer
from src.config import settings
import subprocess
import pytest
import os


@pytest.fixture(scope='module', autouse=True)
def kernel_config():
	subprocess.run(['make', '-C', settings.kernel.KERNEL_SRC, 'ARCH=x86_64', 'defconfig'], check=True)

	yield
	
	os.remove(f'{settings.kernel.KERNEL_SRC}/.config')


# Config KLocalizer: Success
def test_run(tmp_path):
	log = f'{tmp_path}/klocalizer.log'
	result = klocalizer.run(settings.kernel.KERNEL_SRC, log, define=['CONFIG_SMP'])
	assert result == 'success'

# Patch KLocalizer: Success
def test_run_patch(tmp_path, tmp_patch):
	log = f'{tmp_path}/klocalizer.log'
	result = klocalizer.run_patch(settings.kernel.KERNEL_SRC, tmp_patch, log, define=['CONFIG_SMP'])
	assert result == 'success'

# Config KLocalizer: No Satisfying Constraints
def test_run_no_satisfying_constraints(tmp_path):
	log = f'{tmp_path}/klocalizer.log'
	result = klocalizer.run(settings.kernel.KERNEL_SRC, log, define=['CONFIG_SMP'], undefine=['CONFIG_SMP'])
	assert result == 'no-satisfying-constraints'

# Patch KLocalizer: No Satisfying Constraints
def test_run_patch_no_satisfying_constraints(tmp_path, tmp_patch):
	log = f'{tmp_path}/klocalizer.log'
	result = klocalizer.run_patch(settings.kernel.KERNEL_SRC, tmp_patch, log, define=['CONFIG_SMP'], undefine=['CONFIG_SMP'])
	assert result == 'no-satisfying-constraints'

# Config KLocalizer: Error
def test_run_error(tmp_path):
	log = f'{tmp_path}/klocalizer.log'
	result = klocalizer.run('nonexistent/kernel', log, define=['CONFIG_SMP'])
	assert result == 'error'

# Patch KLocalizer: Error
def test_run_patch_error(tmp_path, tmp_patch):
	log = f'{tmp_path}/klocalizer.log'
	result = klocalizer.run_patch('nonexistent/kernel', tmp_patch, log, define=['CONFIG_SMP'])
	assert result == 'error'

# Config KLocalizer: Constraints File
def test_run_constraints_file(tmp_path):
	log = f'{tmp_path}/klocalizer.log'
	klocalizer.run(settings.kernel.KERNEL_SRC, log, define=['CONFIG_SMP'], undefine=['CONFIG_X'])
	assert os.path.exists(f'{tmp_path}/constraints.txt')
