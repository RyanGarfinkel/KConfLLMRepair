from langchain.messages import SystemMessage, HumanMessage
from src.models import ExecutorSummary
from src.config import settings

class Context:

    def __init__(self):
        self.history = []

    @property
    def num_iterations(self) -> int:
        return len(self.history)

    @property
    def system_prompt(self) -> SystemMessage:
        return SystemMessage(content=f"""
            You are an expert Linux kernel configuration agent. Your objective is to repair a non-booting Linux kernel configuration
            while minimizing the number of configuration changes. You will be have tools available to search through the build log,
            kloclalizer log, the QEMU boot log, and be able to search through options in the base (bootable) and the latest (unbootable)
            configuration. The purpose of the original changes was to maximize patch coverage for fuzz testing, but they have resulted in
            a non-booting kernel.\n
            
            You will only be able to use each tool at most once per iteration, an you should try to minimize the number of iterations.
            You will have at most {settings.agent.MAX_ITERATIONS} tries. Please maximize the use of the search tools availble to get as much
            information as you need to make informed decisions about which configuration options to change. You should only make changes
            that are necessary to fix the boot issue.
        """)
    
    def user_prompt(self, log) -> HumanMessage:

        content = ''

        if self.num_iterations == 0:
            content += """
                STATUS: Initial Attempt.\n
            """
        else:
            content += f"""
                STATUS: Attempt {self.num_iterations} / {settings.agent.MAX_ITERATIONS}.\n
            """

        content += """
            INSTRUCTIONS:\n
            1. Use all the tools available at most once. Start by gathering information about the failure by searching the logs, then
               search the configuration options to find the ones that are most likely to be the cause of the failure. Finally, make the
               apply and test new configuration changes.\n
            2. Once you have made new changes, new logs and a new latest configuration will become available. Use that new information to
               help you make informed decision about which configuration options to change next.\n
            3. Once you have called apply_and_test in the current iteration, you must stop and output your iteration summary. Do not try
               to perform any further searches or apply any more changes after calling apply_and_test.
        """

        content += f"""
            END OF LOG:\n
            {log}
        """

        if self.num_iterations == 0:
            return HumanMessage(content=content)
        
        content += 'HISTORY:\n'

        for i, iteration in enumerate(self.history):
            content += self.__format_iteration(i + 1, iteration.executor_summary)

        return HumanMessage(content=content)

    def append(self, summary: ExecutorSummary):
        self.history.append(summary)

    def __format_iteration(self, i: int, iteration: ExecutorSummary) -> str:
        return f"""
            STEP {i} / {settings.agent.MAX_ITERATIONS}:\n
            THOUGHTS: {iteration.thoughts}\n
            OBSERVATIONS: {iteration.observations}\n
            SUGGESTIONS: {iteration.suggestions}\n
        """