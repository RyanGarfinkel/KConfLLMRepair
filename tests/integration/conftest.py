from src.core.kernel import Kernel
from src.config import settings
import subprocess
import shutil
import pytest

@pytest.fixture(scope='session')
def arm64_build(tmp_path_factory):
	src = settings.kernel.KERNEL_SRC
	work = str(tmp_path_factory.mktemp('arm64'))
	subprocess.run(
		['make.cross', 'LLVM=1', 'ARCH=arm64', 'tinyconfig'],
		cwd=src, check=True,
		stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
	)
	config = f'{work}/tiny.config'
	shutil.copy(f'{src}/.config', config)

	original_arch = settings.kernel.ARCH
	settings.kernel.ARCH = 'arm64'
	try:
		result = Kernel(src).build(work, config)
		image = f'{src}/{settings.kernel.BZIMAGE}'
	finally:
		settings.kernel.ARCH = original_arch

	return result, image
