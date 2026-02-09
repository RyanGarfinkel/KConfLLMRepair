from src.agent import get_agent_tools, Session, prompt, model
from src.models import Sample, AgentResponse
from singleton_decorator import singleton
from langchain.agents import create_agent
from src.config import settings
from .kernel import Kernel
from src.utils import log
import shutil
import os

@singleton
class Agent:

    def repair(self, sample: Sample) -> Session:
        
        session = Session(sample.base, sample.patch, f'{sample.output}/agent-repair')
        kernel = Kernel(sample.kernel_src)

        llm = model.get()

        if os.path.exists(session.dir):
            shutil.rmtree(session.dir)

        os.makedirs(session.dir, exist_ok=True)

        messages = []
        latest_response = None

        for i in range(settings.agent.MAX_ITERATIONS + 1):

            log.info(f'Iteration {i} / {settings.agent.MAX_ITERATIONS}...')

            session.add_attempt(messages, latest_response)

            if self.verify(kernel, session):
                break
            
            # Agent Setup             
            tools = get_agent_tools(session)
            agent = create_agent(llm, response_format=AgentResponse, tools=tools)

            # Agent Response & Processing
            response = agent.invoke(prompt.prompt(session))

            latest_response = response['structured_response'] if 'structured_response' in response else None

            session.save(f'{sample.output}/summary.json')

        if session.status != 'success':
            log.error('Failed to repair the configuration within the maximum number of iterations.')
        else:
            log.info('Successfully repaired the configuration!')
            log.info(f'Saving repaired configuration to {sample.output}/repaired.config...')
            shutil.copyfile(session.attempts[-1].config, f'{sample.output}/repaired.config')

        return session

    def verify(self, kernel: Kernel, session: Session) -> bool:
        
        define = session.attempts[-1].response.define if session.attempts[-1].response else []
        undefine = session.attempts[-1].response.undefine if session.attempts[-1].response else []

        kernel.load_config(session.base)

        session.attempts[-1].klocalizer_log = f'{session.attempts[-1].dir}/klocalizer.log'
        if not kernel.run_klocalizer(session.attempts[-1].dir, define, undefine):
            log.info('KLocalizer failed to run with the given configuration changes.')
            return False
        
        session.attempts[-1].klocalizer_succeeded = True
        session.attempts[-1].config = f'{session.attempts[-1].dir}/modified.config'
        
        session.attempts[-1].build_log = f'{session.attempts[-1].dir}/build.log'
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
