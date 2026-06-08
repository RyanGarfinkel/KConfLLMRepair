from src.core.kernel import Kernel
from src.config import settings
from pathlib import Path
import subprocess
import shutil
import pytest
import os

KERNEL_SRC = settings.kernel.KERNEL_SRC

requires_build = pytest.mark.skipif(
	shutil.which('make.cross') is None or not Path(KERNEL_SRC, 'Kconfig').exists(),
	reason='kernel source or make.cross not available',
)

def _tinyconfig(arch, tmp_path):
	subprocess.run(
		['make.cross', 'LLVM=1', f'ARCH={arch}', 'tinyconfig'],
		cwd=KERNEL_SRC, check=True,
		stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
	)
	config = tmp_path / 'tiny.config'
	shutil.copy(f'{KERNEL_SRC}/.config', config)
	return str(config)

# Tiny config builds the kernel image: Success
@requires_build
@pytest.mark.parametrize('arch', ['x86_64', 'arm64'])
def test_build_succeeds(arch, tmp_path, monkeypatch):
	monkeypatch.setattr(settings.kernel, 'ARCH', arch)
	config = _tinyconfig(arch, tmp_path)
	kernel = Kernel(KERNEL_SRC)
	result = kernel.build(str(tmp_path), config)
	assert result.ok is True
	assert os.path.exists(f'{KERNEL_SRC}/{settings.kernel.BZIMAGE}')

# Build fails on a source tree that cannot produce the image: Failure
@requires_build
def test_build_fails(tmp_path, monkeypatch):
	monkeypatch.setattr(settings.kernel, 'ARCH', 'x86_64')
	broken_src = tmp_path / 'broken'
	broken_src.mkdir()
	(broken_src / 'Makefile').write_text('all:\n\t@false\n')
	config = tmp_path / 'broken.config'
	config.write_text('# not a real kernel config\n')
	kernel = Kernel(str(broken_src))
	result = kernel.build(str(tmp_path), str(config))
	assert result.ok is False
