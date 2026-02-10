from src.agent import get_agent_tools, Session, prompt, model
from src.models import Input, AgentResponse
from singleton_decorator import singleton
from langchain.agents import create_agent
from src.config import settings
from .kernel import Kernel
from src.utils import log
import shutil
import os

@singleton
class Agent:

    def repair(self, input: Input, kernel: Kernel) -> Session:
        
        session = Session(input.base_config, input.modified_config, input.patch, input.output_dir)

        llm = model.get()

        if os.path.exists(session.dir):
            shutil.rmtree(session.dir)

        os.makedirs(session.dir, exist_ok=True)

        messages = []
        latest_response = None

        session.add_attempt(messages, latest_response)
        session.attempts[-1].config = session.base

        for i in range(settings.agent.MAX_ITERATIONS + 1):

            log.info(f'Iteration {i} / {settings.agent.MAX_ITERATIONS}...')

            if self.verify(kernel, session):
                break
            
            # Agent Setup             
            tools = get_agent_tools(session)
            agent = create_agent(llm, response_format=AgentResponse, tools=tools)

            # Agent Response & Processing
            response = agent.invoke({'messages': prompt.prompt(session)})

            latest_response = response['structured_response'] if 'structured_response' in response else None

            session.save(f'{input.output_dir}/summary.json')

            session.add_attempt(messages, latest_response)
            if not self.run_klocalizer(session, kernel, latest_response.define, latest_response.undefine):
                log.info('KLocalizer failed to run with the given configuration changes.')
                break

            session.save(f'{input.output_dir}/summary.json')

        if session.status != 'Success':
            log.error('Failed to repair the configuration within the maximum number of iterations.')
        else:
            log.info('Successfully repaired the configuration!')
            log.info(f'Saving repaired configuration to {input.output_dir}/repaired.config...')
            shutil.copyfile(session.attempts[-1].config, f'{input.output_dir}/repaired.config')

        return session
    
    def run_klocalizer(self, session: Session, kernel: Kernel, define: list[str], undefine: list[str]) -> bool:

        session.attempts[-1].klocalizer_log = f'{session.attempts[-1].dir}/klocalizer.log'
        if not kernel.run_klocalizer(session.patch, session.attempts[-1].klocalizer_log, define, undefine):
            session.attempts[-1].klocalizer_succeeded = False
            log.info('KLocalizer failed to run with the given configuration changes.')
            return False
        
        session.attempts[-1].klocalizer_succeeded = True
        session.attempts[-1].config = f'{session.attempts[-1].dir}/modified.config'
        shutil.copyfile(f'{kernel.src}/.config', session.attempts[-1].config)

        return True

    def verify(self, kernel: Kernel, session: Session) -> bool:

        if not session.attempts[-1].klocalizer_succeeded:
            log.info('Skipping verification since KLocalizer did not succeed in the last attempt.')
            return False
        
        if not kernel.load_config(session.latest):
            log.info('Failed to load latest configuration for verification.')
            return False            
        
        session.attempts[-1].build_log = f'{session.attempts[-1].dir}/build.log'
        print(session.attempts[-1].build_log)
        if not kernel.build(session.attempts[-1].config, session.attempts[-1].build_log):
            log.info('Build failed with the given configuration changes.')
            return False

        session.attempts[-1].build_succeeded = True
        
        session.attempts[-1].boot_log = f'{session.attempts[-1].dir}/boot.log'
        if not kernel.boot(session.attempts[-1].boot_log):
            log.info('Boot failed with the given configuration changes.')
            return False
        
        session.attempts[-1].boot_succeeded = True
        
        log.info('Modified configuration boots successfully.')

        return True

agent = Agent()
