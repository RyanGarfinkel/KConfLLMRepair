from src.models import Input, AgentResponse, Attempt, ToolCall, TokenUsage
from src.agent import get_agent_tools, Session, prompt, model
from langchain_core.language_models import BaseChatModel
from singleton_decorator import singleton
from langchain.agents import create_agent
from src.config import settings
from src.utils import file_lock
from .kernel import Kernel
from src.utils import log
import shutil
import json
import os

@singleton
class Agent:

    def repair(self, input: Input, kernel: Kernel) -> Session:
        
        session = Session(input.config, input.output)
        llm = model.get_llm()

        self.__make_dir(session.dir)

        inital_attempt = self.__inital_attempt(kernel, session)
        session.attempts.append(inital_attempt)

        if inital_attempt.boot_succeeded == 'yes':
            return session

        log.info('Beginning repair process...')

        for i in range(settings.agent.MAX_ITERATIONS):
            
            if session.status == 'success':
                break

            log.info(f'Iteration {i + 1} / {settings.agent.MAX_ITERATIONS}...')

            self.__attempt(llm, kernel, session)

            session.save(f'{input.output}/summary.json')

        if session.status == 'success':
            log.success('Repair process completed successfully!')
            shutil.copyfile(session.attempts[-1].config, f'{input.output}/repaired.config')
        elif session.status == 'success-maintenance':
            log.info('Repair process completed, but the kernel boots into maintenance mode.')
            shutil.copyfile(session.attempts[-1].config, f'{input.output}/repaired.config')
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

        attempt = Attempt(
            id=0,
            dir=dir,
            config=session.base,
        )

        # Load config
        if not kernel.load_config(session.base):
            return attempt
        
        # Build
        attempt.build_log = f'{dir}/build.log'
        if not kernel.build(attempt.build_log):
            log.info('Build failed with the input configuration.')
            return attempt
        
        # Boot
        attempt.boot_log = f'{dir}/boot.log'
        attempt.boot_succeeded = kernel.boot(attempt.boot_log)

        if attempt.boot_succeeded == 'yes':
            log.info('Input configuration boots successfully. No repair needed.')
        elif attempt.boot_succeeded == 'maintenance':
            log.info('Input configuration boots into maintenance mode.')
        else:
            log.info('Input configuration failed to boot.')

        return attempt

    def __attempt(self, llm: BaseChatModel, kernel: Kernel, session: Session):

        dir = f'{session.dir}/attempt_{len(session.attempts)}'
        self.__make_dir(dir)

        attempt = Attempt(
            id=len(session.attempts),
            dir=dir,
        )

        session.attempts.append(attempt)

        # Agent
        tools = get_agent_tools(session)
        agent = create_agent(llm, response_format=AgentResponse, tools=tools)

        response = agent.invoke({ 'messages': prompt.prompt(session) })

        token_usage = self.__extract_token_usage(response)
        attempt.token_usage = token_usage
        
        self.__save_raw_response(f'{dir}/raw-agent-response.json', response)

        # Apply Changes
        agent_response = response.get('structured_response', None)

        if agent_response is None:
            log.error('Agent failed to provide a structured response. Skipping attempt.')
            return
        
        attempt.response = agent_response
        
        if not kernel.load_config(session.base):
            return
        
        attempt.klocalizer_log = f'{dir}/klocalizer.log'
        if not kernel.run_klocalizer(attempt.klocalizer_log, agent_response.define, agent_response.undefine):
            return
        
        attempt.klocalizer_succeeded = True
        attempt.config = f'{dir}/modified.config'

        shutil.copyfile(f'{kernel.src}/.config', attempt.config)

        # Build and Boot Test
        attempt.build_log = f'{dir}/build.log'
        if not kernel.build(attempt.build_log):
            return
        
        attempt.build_succeeded = True

        attempt.boot_log = f'{dir}/boot.log'
        attempt.boot_succeeded = kernel.boot(attempt.boot_log)
        
    def __extract_token_usage(self, response: dict) -> TokenUsage:
        
        messages = response.get('messages', [])

        ai_messages = [msg for msg in messages if msg.type == 'ai']

        input_tokens = sum(msg.usage_metadata['input_tokens'] for msg in ai_messages if msg.usage_metadata)
        output_tokens = sum(msg.usage_metadata['output_tokens'] for msg in ai_messages if msg.usage_metadata)
        total_tokens = sum(msg.usage_metadata['total_tokens'] for msg in ai_messages if msg.usage_metadata)

        return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total_tokens)

    def __save_raw_response(self, path, response: dict):
        with file_lock:
            with open(path, 'w') as f:
                def default(o):
                    if hasattr(o, "dict"):
                        return o.dict()
                    if hasattr(o, "model_dump"):
                        return o.model_dump()
                    return str(o)
                json.dump(response, f, indent=4, default=default)
    
agent = Agent()
