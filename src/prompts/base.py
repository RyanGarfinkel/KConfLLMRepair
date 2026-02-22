from langchain_messages import SystemMessage, HumanMessage
from abc import ABC, abstractmethod
from .session import Session

class BasePrompt(ABC):

    @property
    @abstractmethod
    def _role(self) -> SystemMessage:
        pass

    @property
    @abstractmethod
    def _goals(self) -> SystemMessage:
        pass

    @property
    @abstractmethod
    def _guidelines(self) -> SystemMessage:
        pass

    def _original_state(self, session: Session) -> HumanMessage:
        pass
    
    def _current_state(self, session: Session) -> HumanMessage:
        pass

    @abstractmethod
    def get(self, session: Session) -> str:
        pass