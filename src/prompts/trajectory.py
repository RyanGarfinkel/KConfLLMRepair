from langchain.messages import HumanMessage
from singleton_decorator import singleton
from src.models import Attempt
from ..agent.session import Session

@singleton
class Trajectory:

    def __summarize(self, attempt: Attempt) -> str:
        return f"""
        Attempt {attempt.id}:
        Hypothesis: {attempt.analyze.hypothesis}
        Outcome: {attempt.status}
        Define: {attempt.apply.define}
        Undefine: {attempt.apply.undefine}
        Reasoning: {attempt.apply.reasoning}
        """
    
    def get(self, session: Session) -> HumanMessage:

        if len(session.attempts) <= 1:
            return HumanMessage(content='INITIAL ATTEMPT')
        
        history = '\n'.join([self.__summarize(attempt) for attempt in session.attempts])

        content = f"""
        HISTORY:
        {history}
        """

        return HumanMessage(content=content)

trajectory = Trajectory()
