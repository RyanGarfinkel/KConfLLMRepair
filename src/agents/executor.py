from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.agents.structured_output import ToolStrategy
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from src.models import ExecutorSummary, IterationSummary
from langchain_core.tools import StructuredTool
from langchain.agents import create_agent

class Executor:

    def __init__(self, llm: BaseChatModel, tools: list[StructuredTool]):

        self.llm = llm
        self.tools = tools

        middleware = []

        for tool in tools:
            if tool.name == 'apply_and_test':
                middleware.append(ToolCallLimitMiddleware(tool_name=tool.name, thread_limit=1))
            else:
                middleware.append(ToolCallLimitMiddleware(tool_name=tool.name, thread_limit=10))

        self.agent = create_agent(
            llm,
            tools=tools,
            middleware=middleware,
            response_format=ToolStrategy(ExecutorSummary),
        )

    def __format_response(self, response: dict) -> IterationSummary:

        executor_summary = response.get('structured_response', None)
        if not executor_summary:
            print('No structured response found in agent output.')

        tool_calls = []
        for message in response.get('messages', []):
            if isinstance(message, AIMessage) and message.tool_calls:
                tool_calls.extend(message.tool_calls)

        return IterationSummary(
            executor_summary=executor_summary,
            token_usage=0,
            tools_used=tool_calls,
        )

    def iterate(self, system_prompt: SystemMessage, user_prompt: HumanMessage) -> IterationSummary:

        payload = {
            'messages': [system_prompt, user_prompt]
        }

        result: dict = self.agent.invoke(payload)

        with open('agent_response.json', 'w') as f:
            import json
            def default(o):
                if hasattr(o, "dict"):
                    return o.dict()
                if hasattr(o, "model_dump"):
                    return o.model_dump()
                return str(o)
            json.dump(result, f, indent=4, default=default)

        return self.__format_response(result)
