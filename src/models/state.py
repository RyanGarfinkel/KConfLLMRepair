from typing import Annotated, List, Literal, TypedDict, Optional
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from src.core import Kernel
from operator import add

class ToolCall(BaseModel):

    name: str = Field(..., frozen=True)
    args: dict[str, str] = Field(..., frozen=True)
    return_content: dict = Field(..., frozen=True)
    token_usage: dict['input_tokens': int, 'output_tokens': int, 'total_tokens': int] = Field(..., frozen=True)

class Phase(BaseModel):

    name: Literal['verify', 'analyze', 'collect'] = Field(...)
    tool_calls: List[ToolCall] = Field(default_factory=list)

class Hypothesis(BaseModel):
    
    current: Optional[str] = Field(default=None)
    history: List[dict['guess': str, 'status': Literal['discarded', 'success', 'failed']]] = Field(default_factory=list)

class Attempt(BaseModel):

    dir: str = Field(..., frozen=True)
    klocalizer_log: Optional[str] = Field(default=None)
    config: Optional[str] = Field(default=None, frozen=True)
    build_log: Optional[str] = Field(default=None)
    boot_log: Optional[str] = Field(default=None)


class State(TypedDict):

    messages: Annotated[List[BaseMessage], add]
    
    hypothesis: Hypothesis
    phases: List[Phase]
    
    kernel: Kernel
    
    sample_dir: str
    
    base_config: str
    patch: str
    
    attempts: List[Attempt] = Field(default_factory=list)
    @property
    def num_attempts(self) -> int:
        return len(self.attempts)










# from langchain_core.language_models import BaseChatModel
# from langchain_core.messages import BaseMessage
# from typing import Annotated, List, Optional
# from typing_extensions import Literal
# from pydantic import BaseModel, Field
# from src.core import Kernel
# from operator import add

# class Hypothesis(BaseModel):
    
#     text: str = Field(...)
#     status: Literal['current', 'discarded', 'success', 'failed'] = Field(default='current')

# class Counter(BaseModel):

#     tool_count: int = Field(default=0, ge=0)
#     repair_attempts: int = Field(default=0, ge=0)
#     test_attempts: int = Field(default=0, ge=0)

# class State(BaseModel):

#     llm: BaseChatModel = Field(..., frozen=True)

#     messages: Annotated[List[BaseMessage], add] = Field(default_factory=list)
#     phase: Literal['init', 'verify', 'analyze', 'collect', 'done'] = Field(default='init')

#     @property
#     def current_hypothesis(self) -> Optional[Hypothesis]:
#         for hypothesis in self.hypotheses:
#             if hypothesis.status == 'current':
#                 return hypothesis
            
#         return None

#     hypotheses: List[Hypothesis] = Field(default_factory=list)

#     patch: str = Field(..., frozen=True)
#     base_config: str = Field(..., frozen=True)
#     sample_dir: str = Field(..., frozen=True)

#     latest_config: str = Field(...)
#     latest_klocalizer: Optional[str] = Field(default=None)
#     latest_build: Optional[str] = Field(default=None)
#     latest_boot: Optional[str] = Field(default=None)

#     kernel: Kernel = Field(..., frozen=True)

#     counter: Counter = Field(default_factory=Counter)
#     boot_succeeded: bool = Field(default=False)
