from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents import Context, Executor, Tools
from src.models import Sample, AgentResult
from singleton_decorator import singleton
from langchain_openai import ChatOpenAI
from src.config import settings
from src.utils import log

@singleton
class Agent:

    def __init__(self, model_override: str | None):

        self.llm = self.__get_llm(model_override)

    def __get_llm(self, override: str | None = None):

        if override:
            return self.__init_model(override)

        if settings.agent.OPENAI_API_KEY:
            return self.__init_model('gpt-4o-mini')
        elif settings.agent.GOOGLE_API_KEY:
            return self.__init_model('gemini-2.5-flash')
        else:
            raise ValueError('Must have at least one valid API key to initialize LLM.')
  
    def __init_model(self, provider: str):

        if provider.startswith('gpt'):
            return ChatOpenAI(model=provider, api_key=settings.agent.OPENAI_API_KEY)
        elif provider.startswith('gemini'):
            return ChatGoogleGenerativeAI(model=provider, api_key=settings.agent.GOOGLE_API_KEY)
        else:
            raise ValueError(f'Unknown provider: {provider} or missing API key.')

    def repair(self, sample: Sample) -> AgentResult:

        context = Context()
        tools = Tools(sample)
        executor = Executor(self.llm, tools.get_tools())

        for i in range(settings.agent.MAX_ITERATIONS):

            log.info(f'Iteration {i + 1} / {settings.agent.MAX_ITERATIONS}...')

            system_prompt = context.system_prompt
            user_prompt = context.user_prompt(tools.latest_log)

            iter_summary = executor.iterate(system_prompt, user_prompt)

            if iter_summary is None:
                log.info(f'No output from agent in iteration {i + 1}. Ending.')
                break

            iter_summary.tools_used = tools.tools_used
            tools.tools_used = []

            context.history.append(iter_summary)

        return AgentResult(
            iterations=len(context.history),
            history=context.history,
            config=tools.config,
            token_usage=sum(iter_summary.token_usage for iter_summary in context.history),
            status='success' if tools.succeeded else 'max_iterations' if len(context.history) == settings.agent.MAX_ITERATIONS else 'failure'
        )
