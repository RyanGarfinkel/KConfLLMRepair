from pydantic import field_validator, model_validator, ValidationInfo, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.utils import log
import sys
import os

class SyzkconfSettings(BaseModel):

    INSTANCE: str = 'upstream-apparmor-kasan'

class KernelSettings(BaseModel):

    KERNEL_SRC: str
    SUPERC_PATH: str
    BZIMAGE: str = 'arch/x86/boot/bzImage'
    DIFFCONFIG: str = Field(default='scripts/diffconfig', frozen=True)

    @field_validator('KERNEL_SRC', 'SUPERC_PATH')
    def validate_kernel_exists(cls, v: str, info: ValidationInfo) -> str:
        if not os.path.exists(v):
            raise ValueError(f'{info.field_name} path does not exist: {v}')

        return v

class RuntimeSettings(BaseModel):

    COMMIT_WINDOW: int = 250
    JOBS: int = 8
    MAX_THREADS: int = 1
    SAMPLE_DIR: str
    WORKTREE_DIR: str
    BASE_CONFIG: str

    @field_validator('SAMPLE_DIR', 'WORKTREE_DIR')
    def validate(cls, v: str) -> str:
        os.makedirs(v, exist_ok=True)

        return v

class AgentSettings(BaseModel):

    GOOGLE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    MAX_ITERATIONS: int = 5
    PROVIDER: str = 'openai'
    MODEL: str = 'gpt-5.2'
    MAX_MATCHES: int = 5

    @model_validator(mode='after')
    def verify_api_key(self):
        if self.GOOGLE_API_KEY or self.OPENAI_API_KEY:
            return self

        raise ValueError('At least one API key must be provided.')

class ScriptSettings(BaseModel):

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
    
    @property
    def SYZ_KCONF_SCRIPT(self) -> str:
        path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'syz-kconf.sh')
        return os.path.abspath(path)

class Settings(BaseSettings):

    kernel: KernelSettings = Field(default_factory=KernelSettings)
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    scripts: ScriptSettings = Field(default_factory=ScriptSettings)
    syzkconf: SyzkconfSettings = Field(default_factory=SyzkconfSettings)

    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        env_file='.env',
        extra='allow',
        case_sensitive=True,
    )
    
    @model_validator(mode='before')
    def nest_flat_env_vars(cls, values: dict) -> dict:
        
        src = os.environ.copy()
        src.update(values)
        
        syzkconf_data = {k: src.get(k) for k in SyzkconfSettings.model_fields if k in src}
        kernel_data = {k: src.get(k) for k in KernelSettings.model_fields if k in src}
        runtime_data = {k: src.get(k) for k in RuntimeSettings.model_fields if k in src}
        agent_data = {k: src.get(k) for k in AgentSettings.model_fields if k in src}
        scripts_data = {k: src.get(k) for k in ScriptSettings.model_fields if k in src}

        return {
            'syzkconf': syzkconf_data,
            'kernel': kernel_data,
            'runtime': runtime_data,
            'agent': agent_data,
            'scripts': scripts_data,
        }

try:
    settings = Settings()
except Exception as e:
    log.error(f'Error loading configuration: {e}')
    sys.exit(1)
