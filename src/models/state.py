from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing import Annotated, List, TypedDict

class State(TypedDict):

    messages: Annotated[List[BaseMessage], add_messages]

    hypothesis: str | None

    tool_calls: int
    klocalizer_runs: int
    verify_attempts: int

    klocalizer_succeeded: bool
    verify_succeeded: bool

    base_config: str
    modified_config: str
    patch: str

    build_log: str
    boot_log: str
    klocalizer_log: str

    output_dir: str
