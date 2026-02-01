from pydantic import BaseModel, Field

class Sample(BaseModel):
    
    patch: str = Field(default='')
    base_config: str = Field(default='')
    modified_config: str = Field(default='')
    sample_dir: str = Field(..., frozen=True)
    kernel_src: str = Field(..., frozen=True)
    kernel_version: str = Field(..., frozen=True)
    start_commit: str = Field(..., frozen=True)
    start_commit_date: str = Field(..., frozen=True)
    end_commit: str = Field(..., frozen=True)
    end_commit_date: str = Field(..., frozen=True)
    base_builds: bool = Field(default=False)
    base_boots: bool = Field(default=False)
