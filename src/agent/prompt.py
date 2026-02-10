from langchain.messages import SystemMessage, HumanMessage
from langchain_core.messages.base import BaseMessage
from singleton_decorator import singleton
from src.config import settings
from src.models import Attempt
from .session import Session

@singleton
class Prompt:

    @property
    def system_mutex(self) -> SystemMessage:
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
            3. Output:
            - After gathering sufficient information from the logs and config files, output a response containing the configuration changes you want to make and your reasoning for those changes.
            CONSTRAINTS:
            - You have at most {settings.agent.MAX_ITERATIONS} iterations to fix the configuration.
            - You should make use of the search tools to gather as much information as possible before making changes.
            - You should minimize the number of configuration changes made.
        """)
    
    @property
    def system_config(self) -> SystemMessage:
        return SystemMessage(content=f"""
            ROLE: You are an expert Linux kernel configuration agent tasked with repairing a non-booting kernel configuration.
            WORKFLOW:
            1. Diagnosis & Investigation:
            - You must first search the QEMU boot log (if previous build didn't fail) then the build log to identify the root cause of
              the boot failure.
            2. Verification:
            - Do not guess configuration names. Search the configuration file to see what options are included and which are not.
            3. Output:
            - After gathering sufficient information from the logs and config files, output a response containing the configuration changes you want to make and your reasoning for those changes.
            CONSTRAINTS:
            - You have at most {settings.agent.MAX_ITERATIONS} iterations to fix the configuration.
            - You should minimize the number of configuration changes made.
            - You should make use of the search tools to gather as much information as possible before making changes.
        """)
    
    def prompt(self, session: Session) -> list[BaseMessage]:
        if session.patch:
            return [self.system_mutex, self.user(session)]
        else:
            return [self.system_config, self.user(session)]
        
    def user(self, session: Session) -> HumanMessage:

        content = ''

        if len(session.attempts) == 1:
            content += """
                STATUS: Initial Attempt.\n
            """
        else:
            content += f"""
                STATUS: Attempt {len(session.attempts)} / {settings.agent.MAX_ITERATIONS}.\n
            """

        content += """
            INSTRUCTIONS:\n
            1. Use all the tools available. Start by gathering information about the failure by searching the logs, then
               search the configuration options to find the ones that are most likely to be the cause of the failure.
            2. Once you have made new changes, new logs and a new latest configuration will become available. Use that new information to
               help you make informed decision about which configuration options to change next.\n
            3. Once you have used all the availble tools to gather information, format your response containing the configuration changes
               you want to make and your reasoning for those changes.\n
        """

        if len(session.attempts) == 1:
            return HumanMessage(content=content)
        
        content += 'HISTORY:\n'

        for i, attempt in enumerate(session.attempts):
            content += self.__format_attempt(i + 1, attempt)

        return HumanMessage(content=content)

    def __format_attempt(self, i: int, attempt: Attempt) -> str:
        return f"""
            ATTEMPT {i} / {settings.agent.MAX_ITERATIONS}:\n
            KLOCALIZER: {"Success" if attempt.klocalizer_succeeded else "Failed"}\n
            BUILD: {"Success" if attempt.build_succeeded else "Failed"}\n
            BOOT: {"Success" if attempt.boot_succeeded else "Failed"}\n
            OPTIONS INCLUDED: {attempt.response.define if attempt.response else None}\n
            OPTIONS EXCLUDED: {attempt.response.undefine if attempt.response else None}\n
            REASONING: {attempt.response.reasoning if attempt.response else None}\n
        """

prompt = Prompt()
