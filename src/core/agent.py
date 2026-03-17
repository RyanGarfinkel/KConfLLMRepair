from langchain.agents.middleware import ToolCallLimitMiddleware
from src.models import Input, AgentResponse, Attempt, LLMUsage
from src.agent import agent_tools, Session, prompt, model
from langchain_core.language_models import BaseChatModel
from singleton_decorator import singleton
from langchain.agents import create_agent
from src.config import settings
from .kernel import Kernel
from src.utils import log
import shutil
import time
import json
import os

@singleton
class Agent:

    def __init__(self):
        self.middleware = [ToolCallLimitMiddleware(run_limit=settings.agent.MAX_TOOL_CALLS)]

    def repair(self, input: Input, kernel: Kernel) -> Session:

        output_dir = settings.runtime.OUTPUT_DIR
        self.__make_dir(output_dir)

        session = Session(input.original_config, output_dir, patch=input.patch)
        llm = model.get_llm()

        inital_attempt = self.__inital_attempt(kernel, session)
        session.attempts.append(inital_attempt)

        if inital_attempt.boot_succeeded == 'yes':
            session.end_time = time.time()
            return session

        log.info('Beginning repair process...')

        for i in range(settings.agent.MAX_ITERATIONS):
            
            if session.status in ('success', 'success-maintenance'):
                break

            log.info(f'Iteration {i + 1} / {settings.agent.MAX_ITERATIONS}...')

            self.__attempt(llm, kernel, session)

            session.save(f'{output_dir}/summary.json')

        session.end_time = time.time()

        if session.status == 'success':
            log.success('Repair process completed successfully!')
            shutil.copyfile(session.attempts[-1].config, f'{output_dir}/repaired.config')
        elif session.status == 'success-maintenance':
            log.info('Repair process completed, but the kernel boots into maintenance mode.')
            shutil.copyfile(session.attempts[-1].config, f'{output_dir}/repaired.config')
        else:
            log.error('Repair process failed. Maximum iterations reached without success.')

        return session
    
    def __make_dir(self, path: str):
        if os.path.exists(path):
            shutil.rmtree(path)

        os.makedirs(path, exist_ok=True)
    
    def __inital_attempt(self, kernel: Kernel, session: Session) -> Attempt:

        log.info('Checking input configuration bootability...')

        dir = f'{session.dir}/attempt_0'
        self.__make_dir(dir)

        attempt = Attempt(id=0, dir=dir, config=session.base)

        build = kernel.build(dir, session.base)
        attempt.build_log = build.log
        if not build.ok:
            log.info('Build failed with the input configuration.')
            return attempt

        boot = kernel.boot(dir)
        attempt.boot_log = boot.log
        attempt.boot_succeeded = boot.status

        if boot.status == 'yes':
            log.info('Input configuration boots successfully. No repair needed.')
        elif boot.status == 'maintenance':
            log.info('Input configuration boots into maintenance mode.')
        else:
            log.info('Input configuration failed to boot.')

        return attempt

    def __attempt(self, llm: BaseChatModel, kernel: Kernel, session: Session):

        dir = f'{session.dir}/attempt_{len(session.attempts)}'
        self.__make_dir(dir)

        attempt = Attempt(id=len(session.attempts), dir=dir)
        session.attempts.append(attempt)

        tools = agent_tools.get(session)
        agent = create_agent(llm, response_format=AgentResponse, tools=tools, middleware=self.middleware)

        response = agent.invoke({ 'messages': prompt.prompt(session) })

        attempt.token_usage = LLMUsage.from_response(response)
        self.__save_raw_response(f'{dir}/raw-agent-response.json', response)

        agent_response = response.get('structured_response', None)

        if agent_response is None:
            log.error('Agent failed to provide a structured response. Skipping attempt.')
            return

        attempt.response = agent_response

        klocalizer = kernel.run_klocalizer(dir, session.base, agent_response.define, agent_response.undefine)
        attempt.klocalizer_log = klocalizer.log
        attempt.klocalizer_status = klocalizer.status
        if klocalizer.status != 'success':
            return

        attempt.config = f'{dir}/modified.config'
        shutil.copyfile(f'{kernel.src}/.config', attempt.config)

        build = kernel.build(dir, attempt.config)
        attempt.build_log = build.log
        if not build.ok:
            return

        attempt.build_succeeded = True

        boot = kernel.boot(dir)
        attempt.boot_log = boot.log
        attempt.boot_succeeded = boot.status
        
    def __save_raw_response(self, path, response: dict):
        with open(path, 'w') as f:
            def default(o):
                if hasattr(o, "dict"):
                    return o.dict()
                if hasattr(o, "model_dump"):
                    return o.model_dump()
                return str(o)
            json.dump(response, f, indent=4, default=default)
    
agent = Agent()
