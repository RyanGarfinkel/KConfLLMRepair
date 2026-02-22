from pydantic import BaseModel, Field
from .attempt import Attempt

class Session(BaseModel):

    original_config: str = Field(..., frozen=True)

    original_
    attempts: list[Attempt] = Field(default_factory=list)