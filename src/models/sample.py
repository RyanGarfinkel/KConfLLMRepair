from pydantic import BaseModel, Field

class Sample(BaseModel):

    config: str = Field(default='')
    seed: int = Field(default=0)
    sample_dir: str = Field(..., frozen=True)
    kernel_src: str = Field(..., frozen=True)
    kernel_version: str = Field(..., frozen=True)
    end_commit: str = Field(..., frozen=True)
    end_commit_date: str = Field(..., frozen=True)
