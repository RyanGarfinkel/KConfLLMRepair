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
            ROLE: You are an expert Linux kernel configuration agent tasked with repairing a non-booting kernel configuration.
            WORKFLOW:
            1. Diagnosis & Investigation:
            - You must first search the QEMU boot log (if previous build didn't fail) then the build log to identify the root cause of
              the boot failure.
            - You have access to the patch file that caused some options to change. Search through it to understand why.
            2. Verification:
            - Do not guess configuration names. Search the base and the latest configuration files to see what options changed and cross
              reference that with the errors found in the logs.
            3. Action:
            - Only after gathering sufficient information from the logs and config files, call 'apply_and_test'. 
            CONSTRAINTS:
            - You have at most {settings.agent.MAX_ITERATIONS} iterations to fix the configuration.
            - You should minimize the number of configuration changes made.
            - You can only use the 'apply_and_test' tool once per iteration.
            - You should make use of the search tools to gather as much information as possible before making changes.
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
            1. Use all the tools available. Start by gathering information about the failure by searching the logs, then
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
            ACTIONS TAKEN: {iteration.actions}\n
            SUGGESTED NEXT STEPS: {iteration.next_steps}\n
        """