from langchain.messages import SystemMessage, HumanMessage
from langchain_core.messages.base import BaseMessage
from singleton_decorator import singleton
from src.config import settings
from src.models import Attempt
from .session import Session

@singleton
class Prompt:
    
    @property
    def system(self) -> SystemMessage:
        return SystemMessage(content=f"""
            ROLE: You are an expert Linux kernel configuration agent tasked with repairing a non-booting kernel configuration.
            You specialize in reading and understanding build and boot logs, and are knowledgeable about how different configuration
            options impact the build and boot process.
            WORKFLOW:
            1. You will be given acccess to query the klocalizer, build, and boot logs of the previous attempt, depending if
            they are available. Use this information first to gather as much information as possible about the failure. If the latest
            klocalizer attemp failed, then the build and boot logs will be unavailable. If the lastest build attempt failed, then the boot
            log will be unavailable. If the latest boot attempt failed, then all logs will be available.
            2. You will also have access to see the original and latest (if not the first attempt) configuration files. Search
            these to understand the options that are likely causing the failure. You may query multiple options at once, but try to
            limit the number of times you call these tools. If the previous klocalizer attempt failed, then the latest configuration file
            will be unavailable.
            3. Once you have gathered enough information, respond with what configuration options should be defined and undefined, as
            well as a reason for these changes. Afterwards, the klocalizer tool will attempt to generate a new, satifiable configuration
            based on your response. Klocalizer will apply to these changes to the original configuration each time, so be sure to include
            all the options that should be defined or undefined in each response, not just the new changes from the previous attempt. If
            klocalizer is able to generate a new configuration based on your response, then it will automatically attempt to build and boot
            it. If it fails, then you will have access to the new logs to gather more information and update your response with new options
            to define and undefine, as well as new reasoning based on the new information.
            GOAL: Repair the kernel configuration so that it successfully boots. You will have at most {settings.agent.MAX_ITERATIONS}
            attempts to do this.
        """)
        
    def user(self, session: Session) -> HumanMessage:

        content = ''

        if len(session.attempts) == 1:
            content += """
                STATUS: Initial Attempt.
            """
        else:
            content += f"""
                STATUS: Attempt {len(session.attempts) - 1} / {settings.agent.MAX_ITERATIONS}.
            """

        content += """
            INSTRUCTIONS:
            1. Check which tools are available to you. Start by gather information about the failure by querying the latest log files.
            2. If the latest configuration is available, compare it to the original configuration to see what options have changed. Use
            this inforamtion to confirm which options are likely causing the failure.
            3. Once you have used all the tools available to gather enough information, respond with a list of options to define and undefine,
            and your reasoning for why. The klocalizer tool will then automatically attempt to create a new, satisfiable configuration based on
            your response, by applying the changes you suggest to the original configuration.
        """

        if len(session.attempts) == 1:
            return HumanMessage(content=content)
        
        content += 'HISTORY:'

        for i, attempt in enumerate(session.attempts):
            content += self.__format_attempt(i + 1, attempt)

        return HumanMessage(content=content)

    def __format_attempt(self, i: int, attempt: Attempt) -> str:
        return f"""
            ATTEMPT {i} / {settings.agent.MAX_ITERATIONS}:
            KLOCALIZER: {"Success" if attempt.klocalizer_succeeded else "Failed"}
            BUILD: {"Success" if attempt.build_succeeded else "Failed"}
            BOOT: { attempt.boot_succeeded }
            OPTIONS INCLUDED: {attempt.response.define if attempt.response else None}
            OPTIONS EXCLUDED: {attempt.response.undefine if attempt.response else None}
            REASONING: {attempt.response.reasoning if attempt.response else None}
        """
    
    def prompt(self, session: Session) -> list[BaseMessage]:
        return [self.system, self.user(session)]
    
prompt = Prompt()
