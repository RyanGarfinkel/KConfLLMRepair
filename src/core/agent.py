from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents import Context, Executor, Tools
from src.models import Sample, AgentResult
from singleton_decorator import singleton
from langchain_openai import ChatOpenAI
from src.config import settings
from src.utils import log
import shutil

@singleton
class Agent:

    def __init__(self):

        self.llm = self.__get_llm(settings.agent.MODEL)

    def __get_llm(self, model: str):

        if model.startswith('gpt'):
            return ChatOpenAI(model=model, api_key=settings.agent.OPENAI_API_KEY)
        elif model.startswith('gemini'):
            return ChatGoogleGenerativeAI(model=model, api_key=settings.agent.GOOGLE_API_KEY)
        else:
            raise ValueError(f'Unknown provider for model: {model}')

    def repair(self, sample: Sample) -> AgentResult:

        context = Context()
        tools = Tools(sample)
        executor = Executor(self.llm, tools.get_tools())

        for i in range(settings.agent.MAX_ITERATIONS):

            if tools.succeeded:
                break

            log.info(f'Iteration {i + 1} / {settings.agent.MAX_ITERATIONS}...')

            system_prompt = context.system_prompt
            user_prompt = context.user_prompt(tools.latest_log)

            iter_summary = executor.iterate(system_prompt, user_prompt)

            if iter_summary is None:
                log.info(f'No output from agent in iteration {i + 1}. Ending.')
                break

            iter_summary.tools_used = tools.tools_used

            context.history.append(iter_summary)

        config = f'{sample.output}/.config'
        shutil.copyfile(f'{sample.output}/attempt_{len(context.history)}/modified.config', config)

        return AgentResult(
            provider=settings.agent.PROVIDER,
            model=settings.agent.MODEL,
            iterations=len(context.history),
            history=context.history,
            config=config,
            token_usage=sum(iter_summary.token_usage for iter_summary in context.history),
            status='success' if tools.succeeded else 'max_iterations' if len(context.history) == settings.agent.MAX_ITERATIONS else 'failure'
        )
