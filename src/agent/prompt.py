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
            1. You will be given access to query the build and boot logs of the previous attempt, depending on availability.
            If the latest klocalizer attempt did not succeed, the build and boot logs will be unavailable. If the latest build
            attempt failed, the boot log will be unavailable. If the latest boot attempt failed, all logs will be available.
            {"Use semantic search queries to retrieve relevant sections of each log." if settings.runtime.USE_RAG else "Use grep to search logs by pattern, and chunk to retrieve lines around a specific line number."}
            2. You will also have access to the original and latest (if not the first attempt) configuration files. Search these
            to understand the options likely causing the failure. You may query multiple options at once, but be mindful that you
            have a limit of {settings.agent.MAX_TOOL_CALLS} tool calls per attempt. Reserve at least one call for your final
            response. If the previous klocalizer attempt did not succeed, the latest configuration file will be unavailable.
            3. Once you have gathered enough information, respond with what configuration options should be defined and undefined,
            and your reasoning. KLocalizer will apply these changes to the original configuration each time, so include all options
            that should be defined or undefined — not just new changes from the previous attempt. If KLocalizer generates a new
            configuration, it will automatically attempt to build and boot it. If it fails, you will have access to the new logs
            on the next attempt.
            IMPORTANT: You must always submit a structured response before your tool call budget is exhausted. If you are running
            low on tool calls, stop querying and submit your best response immediately with the information you have gathered so far.
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

        content += f"""
            INSTRUCTIONS:
            1. Check which tools are available to you. Start by querying the latest log files to gather information about the failure.
            2. If the latest configuration is available, compare it to the original to see what options have changed.
            3. You have a budget of {settings.agent.MAX_TOOL_CALLS} tool calls. Once you have gathered enough information — or before
            you exhaust your budget — submit your structured response with the options to define and undefine and your reasoning.
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
            KLOCALIZER: {attempt.klocalizer_status}
            BUILD: {"Success" if attempt.build_succeeded else "Failed"}
            BOOT: { attempt.boot_succeeded }
            OPTIONS INCLUDED: {attempt.response.define if attempt.response else None}
            OPTIONS EXCLUDED: {attempt.response.undefine if attempt.response else None}
            REASONING: {attempt.response.reasoning if attempt.response else None}
        """
    
    def prompt(self, session: Session) -> list[BaseMessage]:
        return [self.system, self.user(session)]
    
prompt = Prompt()
