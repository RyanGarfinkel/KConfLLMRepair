
from langchain_community.callbacks.manager import get_openai_callback
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from src.models import IterationSummary
from src.agents import system_prompt

class Agent:

    def __init__(self, llm: BaseChatModel, tools: list[callable]):
        
        self.llm = llm
        self.tools = tools

        self.agent = create_agent(
            llm,
            tools=tools,
            system_prompt=system_prompt,
            response_format=ToolStrategy(IterationSummary),
            middleware=[
                ToolCallLimitMiddleware(thread_limit=7, exit_behavior='end'),
                ToolCallLimitMiddleware(tool_name='apply_and_test', thread_limit=1, exit_behavior='end'),
            ]
        )

    def run(self, context: str) -> IterationSummary:

        import langchain_core.globals as globals

        # globals.set_debug(True)
        
        payload = [HumanMessage(content=context)]
        
        response = self.agent.invoke({
            'messages': payload
        })

        print()
        print()
        print(response)
        print()
        print()

        if 'output' in response and response['output']:
            iter_response: IterationSummary = response['output']

            with get_openai_callback() as cb:
                iter_response.token_usage = cb.total_tokens

            return iter_response
        
        messages = response.get('messages', [])
        
        summary = self.llm.with_structured_output(IterationSummary).invoke(
            messages + [SystemMessage(
                content="Provide IterationSummary based on conversation above."
            )]
        )

        return summary
