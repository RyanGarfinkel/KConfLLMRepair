from pydantic import BaseModel, Field

class Sample(BaseModel):

    original_config: str = Field(default='')
    modified_config: str | None = Field(default=None)
    patch: str | None = Field(default=None)
    seed: int = Field(default=0)
    sample_dir: str = Field(..., frozen=True)
    kernel_src: str = Field(..., frozen=True)
    kernel_version: str = Field(..., frozen=True)
    built: bool | None = Field(default=None)
    boot_status: str | None = Field(default=None)
    start_commit: str | None = Field(default=None)
    start_commit_date: str | None = Field(default=None)
    end_commit: str = Field(..., frozen=True)
    end_commit_date: str = Field(..., frozen=True)
