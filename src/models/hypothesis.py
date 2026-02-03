from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Hypothesis(BaseModel):

    guess: str = Field(..., frozen=True)
    status: Literal['current','discarded', 'success', 'failed'] = Field(default='current')
