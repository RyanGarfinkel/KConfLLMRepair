from abc import ABC, abstractmethod

class BaseEmbedding(ABC):

    @abstractmethod
    def embed(self, content, task_type):
        pass
