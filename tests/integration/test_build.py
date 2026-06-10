from src.core.kernel import Kernel
from src.config import settings
import subprocess
import shutil
import os

KERNEL_SRC = settings.kernel.KERNEL_SRC

def _tinyconfig(arch, tmp_path):
	subprocess.run(
		['make.cross', 'LLVM=1', f'ARCH={arch}', 'tinyconfig'],
		cwd=KERNEL_SRC, check=True,
		stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
	)
	config = f'{tmp_path}/tiny.config'
	shutil.copy(f'{KERNEL_SRC}/.config', config)
	return config

# Tiny config builds the x86 kernel image: Success
def test_build_succeeds(tmp_path, monkeypatch):
	monkeypatch.setattr(settings.kernel, 'ARCH', 'x86_64')
	config = _tinyconfig('x86_64', tmp_path)
	kernel = Kernel(KERNEL_SRC)
	result = kernel.build(str(tmp_path), config)
	assert result.ok is True
	assert os.path.exists(f'{KERNEL_SRC}/{settings.kernel.BZIMAGE}')

# Arm64 kernel builds via build-kernel.sh: Success
def test_arm64_build(arm64_build):
	result, image = arm64_build
	assert result.ok is True
	assert os.path.exists(image)

# Build fails on a source tree that cannot produce the image: Failure
def test_build_fails(tmp_path, monkeypatch):
	monkeypatch.setattr(settings.kernel, 'ARCH', 'x86_64')
	broken_src = f'{tmp_path}/broken'
	os.makedirs(broken_src)
	with open(f'{broken_src}/Makefile', 'w') as f:
		f.write('all:\n\t@false\n')
	config = f'{tmp_path}/broken.config'
	with open(config, 'w') as f:
		f.write('# not a real kernel config\n')
	kernel = Kernel(broken_src)
	result = kernel.build(str(tmp_path), config)
	assert result.ok is False
