from pydantic import BaseModel, Field, field_validator
import shutil
import os

class Input(BaseModel):

    base_config: str = Field(..., frozen=True)
    modified_config: str = Field(..., frozen=True)
    patch: str | None = Field(..., frozen=True)
    output_dir: str | None = Field(default=None, frozen=True)

    @field_validator('base_config', 'modified_config', 'patch')
    @classmethod
    def validate_file_exists(cls, v: str | None) -> str | None:
        if v is not None and not os.path.exists(v):
            raise ValueError(f'File {v} does not exist.')
        return os.path.abspath(v) if v is not None else None

    @field_validator('output_dir')
    @classmethod
    def setup_output_dir(cls, v: str | None) -> str:
        if v is None:
            v = os.path.join(os.getcwd(), 'agent-repair-attempts')
        else:
            v = os.path.join(os.path.abspath(v), 'agent-repair-attempts')
        
        if os.path.exists(v):
            shutil.rmtree(v)
        
        os.makedirs(v, exist_ok=True)
        return v
