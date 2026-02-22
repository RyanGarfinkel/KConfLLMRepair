from singleton_decorator import singleton
from src.agent import model

@singleton
class AnalyzeNode:

    def __get_tools(self, session: Session) -> list[StructuredTool]:

        pass
    
    def run(self, session: Session):

        llm = model.get_llm()
