from typing import Annotated, List, Literal, TypedDict, Optional, Any, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

class TokenUsage(BaseModel):
    
    input_tokens: int = Field(..., frozen=True, ge=0)
    output_tokens: int = Field(..., frozen=True, ge=0)
    total_tokens: int = Field(..., frozen=True, ge=0)

class ToolCall(BaseModel):

    name: str = Field(..., frozen=True)
    args: Dict[str, Any] = Field(..., frozen=True)
    return_content: Dict[str, Any] = Field(..., frozen=True)
    token_usage: TokenUsage = Field(..., frozen=True)

class Phase(BaseModel):

    name: Literal['verify', 'analyze', 'collect'] = Field(...)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    
    @property
    def total_token_usage(self) -> TokenUsage:
        input = sum(call.token_usage.input_tokens for call in self.tool_calls)
        output = sum(call.token_usage.output_tokens for call in self.tool_calls)

        return TokenUsage(
            input_tokens=input,
            output_tokens=output,
            total_tokens=input + output
        )

class Guess(BaseModel):
    
    guess: str = Field(..., frozen=True)
    status: Literal['discarded', 'success', 'failed'] = Field(..., frozen=True)

class Hypothesis(BaseModel):
    
    current: Optional[str] = Field(default=None)
    history: List[Guess] = Field(default_factory=list)

class Attempt(BaseModel):

    dir: str = Field(..., frozen=True)
    klocalizer_log: Optional[str] = Field(default=None)
    config: Optional[str] = Field(default=None, frozen=True)
    build_log: Optional[str] = Field(default=None)
    boot_log: Optional[str] = Field(default=None)

class State(TypedDict):

    messages: Annotated[List[BaseMessage], add_messages]

    hypothesis: Hypothesis
    phases: List[Phase]
    
    sample_dir: str
    
    base_config: str
    patch: str
    
    attempts: List[Attempt]
