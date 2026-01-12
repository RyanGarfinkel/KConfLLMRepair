from pydantic import BaseModel, Field

class IterationSummary(BaseModel):

    thoughts: str = Field(
        description='The reasoning behind the actions taken in this iteration.'
    )

    observations: str = Field(
        description='The observations made during this iteration.'
    )

    suggestions: str = Field(
        description='The suggestions for the next steps to take in the repair process.'
    )

    token_usage: int = Field(
        description='The number of tokens used in this iteration.'
    )
