from pydantic import field_validator, model_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.utils import log
import sys
import os

class Settings(BaseSettings):

    # Core 
    KERNEL_SRC: str
    BASE_CONFIG: str
    SAMPLE_DIR: str
    EXPERIMENT_DIR: str
    WORKTREE_DIR: str

    # Runtime Arguments
    COMMIT_WINDOW: int = 250
    JOBS: int = 8

    # Dependency
    SUPERC_PATH: str
    ARCH: str

    # API Keys
    GOOGLE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    # Local Paths
    BZIMAGE: str = 'arch/x86/boot/bzImage'

    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        env_file='.env',
    )

    # Scripts
    @property
    def QEMU_TEST_SCRIPT(self) -> str:
        path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'qemu-test.sh')
        return os.path.abspath(path)
    
    @property
    def BUILD_SCRIPT(self) -> str:
        path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'build-kernel.sh')
        return os.path.abspath(path)
    
    @property
    def RUN_KLOCALIZER_SCRIPT(self) -> str:
        path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'run-klocalizer.sh')
        return os.path.abspath(path)

    # Validation
    @field_validator('SAMPLE_DIR', 'EXPERIMENT_DIR', 'WORKTREE_DIR')
    def validate(cls, v: str) -> str:
        os.makedirs(v, exist_ok=True)

        return v

    @field_validator('KERNEL_SRC', 'BASE_CONFIG', 'SUPERC_PATH')
    def validate_kernel_exists(cls, v: str, info: ValidationInfo) -> str:
        if not os.path.exists(v):
            raise ValueError(f'{info.field_name} path does not exist: {v}')

        return v

    @model_validator(mode='after')
    def verify_api_key(self):
        if self.GOOGLE_API_KEY or self.OPENAI_API_KEY:
            return self

        raise ValueError('At least one API key must be provided.')

try:
    settings = Settings()
except Exception as e:
    log.error(f'Error loading configuration: {e}')
    sys.exit(1)
