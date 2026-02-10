from pydantic import BaseModel, Field

class Sample(BaseModel):
    
    patch: str | None = Field(default=None)
    base_config: str = Field(default='')
    modified_config: str = Field(default='')
    sample_dir: str = Field(..., frozen=True)
    kernel_src: str = Field(..., frozen=True)
    kernel_version: str = Field(..., frozen=True)
    start_commit: str | None= Field(..., frozen=True)
    start_commit_date: str | None = Field(..., frozen=True)
    end_commit: str | None= Field(..., frozen=True)
    end_commit_date: str | None = Field(..., frozen=True)
    base_builds: bool = Field(default=False)
    base_boots: bool = Field(default=False)
