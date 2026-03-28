from src.core.kernel import Kernel
from src.config import settings
import pytest
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

ARCHES = ['x86_64', 'arm64']

OUTCOME_CONFIGS = {
	'yes': 'repaired.config',
	'no': 'failed.config',
	'maintenance': 'maintenance.config',
}

@pytest.mark.parametrize('arch', ARCHES)
def test_boot_success(tmp_path, arch):
	settings.kernel.ARCH = arch
	kernel = Kernel(settings.kernel.KERNEL_SRC)
	assert kernel.load_config(f'{FIXTURES_DIR}/{OUTCOME_CONFIGS['yes']}')
	assert kernel.build(f'{tmp_path}/build.log')
	assert kernel.boot(f'{tmp_path}/boot.log') == 'yes'

@pytest.mark.parametrize('arch', ARCHES)
def test_boot_fail(tmp_path, arch):
	settings.kernel.ARCH = arch
	kernel = Kernel(settings.kernel.KERNEL_SRC)
	assert kernel.load_config(f'{FIXTURES_DIR}/{OUTCOME_CONFIGS['no']}')
	assert kernel.build(f'{tmp_path}/build.log')
	assert kernel.boot(f'{tmp_path}/boot.log') == 'no'

@pytest.mark.parametrize('arch', ARCHES)
def test_boot_maintenance(tmp_path, arch):
	settings.kernel.ARCH = arch
	kernel = Kernel(settings.kernel.KERNEL_SRC)
	assert kernel.load_config(f'{FIXTURES_DIR}/{OUTCOME_CONFIGS['maintenance']}')
	assert kernel.build(f'{tmp_path}/build.log')
	assert kernel.boot(f'{tmp_path}/boot.log') == 'maintenance'
