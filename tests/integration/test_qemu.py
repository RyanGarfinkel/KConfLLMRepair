from src.config import settings
import subprocess
import hashlib
import shutil
import pytest
import time
import os

BOOT_SECONDS = int(os.environ.get('BOOT_SECONDS', '60'))

AAVMF_PATHS = [
	'/usr/share/AAVMF/AAVMF_CODE.fd',
	'/usr/share/qemu-efi-aarch64/QEMU_EFI.fd',
	'/usr/share/edk2/aarch64/QEMU_EFI.fd',
]

CASES = [
	('qemu-system-x86_64', 'DEBIAN_IMG', []),
	('qemu-system-aarch64', 'DEBIAN_IMG_ARM64', ['-machine', 'virt', '-cpu', 'cortex-a57']),
]

def _image(env):
	if env == 'DEBIAN_IMG':
		return settings.kernel.DEBIAN_IMG
	return os.environ.get(env, '')

def _firmware():
	return next((p for p in AAVMF_PATHS if os.path.exists(p)), None)

def _setup(qemu, env, machine):
	image = _image(env)
	if qemu == 'qemu-system-aarch64':
		machine = [*machine, '-bios', _firmware()]
	return image, machine

def _sha256(path):
	h = hashlib.sha256()
	with open(path, 'rb') as f:
		for chunk in iter(lambda: f.read(1 << 16), b''):
			h.update(chunk)
	return h.hexdigest()

def _boot_and_kill(qemu, machine, image, snapshot, log):
	drive = f'file={image},format=raw,file.locking=off'
	if snapshot:
		drive += ',snapshot=on'

	cmd = [qemu, '-m', '1G', *machine, '-drive', drive, '-display', 'none', '-no-reboot']

	with open(log, 'wb') as out:
		proc = subprocess.Popen(cmd, stdout=out, stderr=out)

	try:
		time.sleep(BOOT_SECONDS)
	finally:
		proc.terminate()
		try:
			proc.wait(timeout=10)
		except subprocess.TimeoutExpired:
			proc.kill()
			proc.wait()

# Snapshot keeps base image pristine through a dirty boot and kill: Success
@pytest.mark.parametrize('qemu,env,machine', CASES, ids=['x86', 'arm64'])
def test_snapshot_protects_base(qemu, env, machine, tmp_path):
	image, machine = _setup(qemu, env, machine)
	base = f'{tmp_path}/base.img'
	shutil.copy(image, base)
	before = _sha256(base)
	_boot_and_kill(qemu, machine, base, snapshot=True, log=f'{tmp_path}/snapshot.log')
	assert _sha256(base) == before

# Without snapshot the same dirty boot and kill mutates the base image: Success
@pytest.mark.parametrize('qemu,env,machine', CASES, ids=['x86', 'arm64'])
def test_without_snapshot_mutates_base(qemu, env, machine, tmp_path):
	image, machine = _setup(qemu, env, machine)
	base = f'{tmp_path}/base.img'
	shutil.copy(image, base)
	before = _sha256(base)
	_boot_and_kill(qemu, machine, base, snapshot=False, log=f'{tmp_path}/plain.log')
	assert _sha256(base) != before
