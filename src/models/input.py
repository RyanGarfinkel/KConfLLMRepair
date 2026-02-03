from pydantic import BaseModel, Field

class Input(BaseModel):

    base_config: str = Field(..., frozen=True)
    modified_config: str = Field(..., frozen=True)
    patch: str = Field(..., frozen=True)
    output_dir: str = Field(..., frozen=True)
