from unittest.mock import patch, MagicMock
from src.tools.qemu import qemu

def _result(returncode):
	result = MagicMock()
	result.returncode = returncode
	return result

# Boot success exit code returns yes: Success
def test_returns_yes():
	with patch('subprocess.run', return_value=_result(0)):
		assert qemu.test('/fake/src', '/fake/boot.log') == 'yes'

# Maintenance exit code returns maintenance: Success
def test_returns_maintenance():
	with patch('subprocess.run', return_value=_result(2)):
		assert qemu.test('/fake/src', '/fake/boot.log') == 'maintenance'

# Kernel panic in log returns panic: Failure
def test_returns_panic(tmp_path):
	log = f'{tmp_path}/boot.log'
	with open(log, 'w') as f:
		f.write('booting...\nKernel panic - not syncing: VFS\n')
	with patch('subprocess.run', return_value=_result(1)):
		assert qemu.test('/fake/src', log) == 'panic'

# Non-empty log without panic returns timeout: Failure
def test_returns_timeout(tmp_path):
	log = f'{tmp_path}/boot.log'
	with open(log, 'w') as f:
		f.write('booting...\nstill running\n')
	with patch('subprocess.run', return_value=_result(1)):
		assert qemu.test('/fake/src', log) == 'timeout'

# Missing log returns no: Failure
def test_returns_no(tmp_path):
	with patch('subprocess.run', return_value=_result(1)):
		assert qemu.test('/fake/src', f'{tmp_path}/missing.log') == 'no'
