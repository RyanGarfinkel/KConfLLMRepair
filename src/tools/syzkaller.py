from singleton_decorator import singleton
from src.config import settings
@singleton
class Syzkaller:

    def __get_kernel_version(self, kernel_src: str) -> str:

        with open(f'{kernel_src}/Makefile', 'r') as f:
            for line in f:
                if line.startswith('VERSION'):
                    version = line.split('=')[1].strip()
                elif line.startswith('PATCHLEVEL'):
                    patchlevel = line.split('=')[1].strip()
                elif line.startswith('SUBLEVEL'):
                    sublevel = line.split('=')[1].strip()
                elif line.startswith('EXTRAVERSION'):
                    extraversion = line.split('=')[1].strip()

        kernel_version = f"{version}.{patchlevel}.{sublevel}{extraversion}"

        return kernel_version

        