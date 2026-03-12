from src.core.kernel import Kernel
from src.config import settings
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

ARCHES = ['x86_64', 'arm64']

OUTCOME_CONFIGS = {
	'yes': 'repaired.config',
	'no': 'failed.config',
	'maintenance': 'maintenance.config',
}

def _test_outcome(tmp_path, outcome):
	kernel = Kernel(settings.kernel.KERNEL_SRC)
	for arch in ARCHES:
		settings.kernel.ARCH = arch
		config = os.path.join(FIXTURES_DIR, OUTCOME_CONFIGS[outcome])
		assert kernel.load_config(config)
		assert kernel.build(str(tmp_path / f'build-{arch}.log'))
		assert kernel.boot(str(tmp_path / f'boot-{arch}.log')) == outcome

def test_boot_success(tmp_path):
	_test_outcome(tmp_path, 'yes')

def test_boot_fail(tmp_path):
	_test_outcome(tmp_path, 'no')

def test_boot_maintenance(tmp_path):
	_test_outcome(tmp_path, 'maintenance')
