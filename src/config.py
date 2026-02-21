from pydantic import field_validator, model_validator, ValidationInfo, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class KernelSettings(BaseModel):

    KERNEL_SRC: str = Field(default=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workspace', 'kernel')))
    BZIMAGE: str = Field(default='arch/x86/boot/bzImage', frozen=True)
    SYZKCONF_INSTANCE: str = Field(default='upstream-apparmor-kasan', frozen=True)
    DIFFCONFIG: str = Field(default='scripts/diffconfig', frozen=True)

    @property
    def WORKTREE_DIR(self) -> str:
        return os.path.join(os.path.dirname(__file__), '..', 'workspace', 'worktrees')

    @field_validator('KERNEL_SRC')
    def validate_kernel_exists(cls, v: str, info: ValidationInfo) -> str:
        if not os.path.exists(v):
            raise ValueError(f'{info.field_name} path does not exist: {v}')

        return v

class RuntimeSettings(BaseModel):

    COMMIT_WINDOW: int = Field(default=250, ge=1)
    MAX_THREADS: int = Field(default=1, ge=1)
    JOBS: int = Field(default=8, ge=1)
    CHUNK_WINDOW: int = 20
    CLEANUP: bool = Field(default=False)

    SAMPLE_DIR: str = Field(default=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workspace', 'samples')))

    @field_validator('SAMPLE_DIR')
    def validate(cls, v: str) -> str:
        if v:
            os.makedirs(v, exist_ok=True)

        return v
    
class AgentSettings(BaseModel):

    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    
    MODEL: str = Field(default='gemini-3-pro-preview')
    @property
    def PROVIDER(self) -> str:
        if self.MODEL.startswith('gemini'):
            return 'google'
        elif self.MODEL.startswith('gpt'):
            return 'openai'
        else:
            raise ValueError(f'Unknown model provider for model: {self.MODEL}')
        
    @property
    def EMBEDDING_MODEL(self) -> str:
        if self.PROVIDER == 'google':
            return 'gemini-embedding-001'
        elif self.PROVIDER == 'openai':
            return 'text-embedding-3-small'
        else:
            raise ValueError(f'Unknown embedding model for provider: {self.PROVIDER}')

    MAX_ITERATIONS: int = Field(default=5, ge=1)
    MAX_MATCHES: int = 5

    @model_validator(mode='after')
    def verify_api_key(self):
        if self.GOOGLE_API_KEY or self.OPENAI_API_KEY:
            return self

        raise ValueError('At least one API key must be provided.')

class ScriptSettings(BaseModel):

    @property
    def RAND_CONFIG_SCRIPT(self) -> str:
        path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'rand-config.sh')
        return os.path.abspath(path)
    
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

        kernel_data = {k: src.get(k) for k in KernelSettings.model_fields if k in src}
        runtime_data = {k: src.get(k) for k in RuntimeSettings.model_fields if k in src}
        agent_data = {k: src.get(k) for k in AgentSettings.model_fields if k in src}
        scripts_data = {k: src.get(k) for k in ScriptSettings.model_fields if k in src}

        return {
            'kernel': kernel_data,
            'runtime': runtime_data,
            'agent': agent_data,
            'scripts': scripts_data,
        }

settings = None

try:
    settings = Settings()

    print('[INFO] Configuration initialized successfully.')

    print(f'[INFO] Using {settings.agent.MODEL}')
    print(f'[INFO] Model from {settings.agent.PROVIDER}')
    print(f'[INFO] kernel-src {settings.kernel.KERNEL_SRC}')
except Exception as e:
    raise RuntimeError(f'Failed to load configuration: {e}')
