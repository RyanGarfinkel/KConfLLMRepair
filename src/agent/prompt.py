from langchain.messages import SystemMessage, HumanMessage
from langchain_core.messages.base import BaseMessage
from singleton_decorator import singleton
from src.config import settings
from src.models import Attempt
from .session import Session

@singleton
class Prompt:

	def system(self, session: Session) -> SystemMessage:
		return SystemMessage(content=
			self.__role() +
			self.__kconfig_explanation() +
			self.__workflow(session) +
			self.__constraints(session) +
			self.__goal(session)
		)

	def user(self, session: Session) -> HumanMessage:
		past_attempts = session.attempts[:-1]
		content = self.__instructions(len(past_attempts))
		content += self.__history(past_attempts)
		
		if past_attempts:
			content += self.__current_failure(past_attempts[-1])
				
		return HumanMessage(content=content)

	def prompt(self, session: Session) -> list[BaseMessage]:
		return [self.system(session), self.user(session)]

	def __role(self) -> str:
		return (
			'You are an expert Linux kernel configuration repair agent. '
			f'Your goal is to fix a non-booting {settings.kernel.ARCH} kernel by identifying which '
			'Kconfig options are causing build or boot failures and correcting them.\n\n'
		)

	def __kconfig_explanation(self) -> str:
		return (
			'HOW KCONFIG CHANGES ARE APPLIED\n'
			'You output a define list and an undefine list each iteration. '
			'KLocalizer applies them to the original config every time, not to the previous modified config. '
			'Your response must always contain the complete set of changes you want. '
			'If you defined an option in a previous attempt and omit it now, it will be dropped silently. '
			'KLocalizer resolves Kconfig dependencies automatically and may define or undefine '
			'additional options beyond what you specify to satisfy the dependency graph.\n\n'
		)

	def __workflow(self, session: Session) -> str:
		if settings.runtime.USE_RAG:
			log_instruction = (
				'Use semantic search queries describing the failure mode or kernel subsystem '
				'rather than quoting log text directly.'
			)
		else:
			log_instruction = (
				'Use grep with targeted patterns like "error:" or "panic". '
				'Use chunk to get surrounding context around a specific line number.'
			)

		content = (
			'WORKFLOW\n'
			'Follow these steps in order each attempt:\n'
			'1. Read the attempt history. Identify the current failure stage (klocalizer / build / boot) '
			'and note what options were already tried and what effect they had.\n'
			f'2. Build failure: a summary of compiler errors is included in the history. {log_instruction} if the summary is insufficient.\n'
			'3. Boot failure: a failure summary is included in the history showing the panic message, '
			'last boot output, or failed systemd units depending on the failure type. '
			'Use grep for deeper investigation if needed.\n'
			'4. Look up the implicated options in the original and latest config to see their current state.\n'
			'5. If the same error persists after defining an option, the root cause is likely a missing '
			'dependency. Search for related options or grep the config for options referenced in the error.\n'
			'6. Respond with the complete cumulative define and undefine lists and clear reasoning '
			'explaining which error each change addresses.\n'
		)

		if session.patch is not None and settings.runtime.MIN_COVERAGE > 0:
			content += (
				'7. If the config boots but coverage is still below target, use the get_file_coverage and the patch '
				'tools to see which parts of the patch are excluded, then suggest options to include that maximize '
				'patch coverage.\n'
			)

		return content + '\n'

	def __constraints(self, session: Session) -> str:
		hard = ''
		if session.hard_define or session.hard_undefine:
			define_line = f'  MUST DEFINE: {session.hard_define}\n' if session.hard_define else ''
			undefine_line = f'  MUST UNDEFINE: {session.hard_undefine}\n' if session.hard_undefine else ''
			hard = f'Hard config constraints (include in every response):\n{define_line}{undefine_line}'
		return (
			'CONSTRAINTS\n'
			f'You have {settings.agent.MAX_TOOL_CALLS} tool calls per attempt. '
			'Use targeted patterns, do not grep broadly. '
			'If you are running low, stop investigating and submit your best response immediately '
			f'rather than exhausting the budget without responding.\n{hard}\n'
		)

	def __goal(self, session: Session) -> str:
		content = (
			'GOAL\n'
			'Repair the config so the kernel boots successfully. '
			f'You have at most {settings.agent.MAX_ITERATIONS} attempts.'
		)

		if session.patch is not None and settings.runtime.MIN_COVERAGE > 0:
			content += f' The config must also cover more than {(settings.runtime.MIN_COVERAGE * 100):.1f}% of the patch.'

		return content

	def __instructions(self, attempt_num: int) -> str:
		return (
			f'ATTEMPT {attempt_num} / {settings.agent.MAX_ITERATIONS}\n\n'
			'INSTRUCTIONS\n'
			'1. Review the history below to identify the current failure stage and what has already been tried.\n'
			'2. Grep for "error:" or "panic" in the relevant log to pinpoint the root cause.\n'
			'3. Look up the implicated options in the original config (and latest config if available).\n'
			'4. Respond with the COMPLETE cumulative define and undefine lists (every option you want changed, '
			f'not just new additions). Constraints: {settings.agent.MAX_TOOL_CALLS} tool calls.\n\n'
		)

	def __history(self, past_attempts: list[Attempt]) -> str:
		content = 'HISTORY\n'
		if not past_attempts:
			return content + 'None. This is the first attempt.'
		
		content += self.__format_initial(past_attempts[0])

		for i, attempt in enumerate(past_attempts[1:], 1):
			content += self.__format_attempt(i, attempt)
		
		return content

	def __current_failure(self, attempt: Attempt) -> str:
		content = ''
		if attempt.build_summary:
			content += f'\nCURRENT BUILD ERRORS\n{attempt.build_summary}\n'
		elif attempt.boot_summary:
			content += f'\nCURRENT BOOT FAILURE ({attempt.boot_succeeded})\n{attempt.boot_summary}\n'
		elif attempt.boot_succeeded == 'yes' and attempt.coverage_summary:
			content += f'\nCURRENT COVERAGE\n{attempt.coverage_summary}\n'
		return content

	def __format_initial(self, attempt: Attempt) -> str:
		build_status = 'Success' if attempt.build_succeeded else 'Failed'
		content = (
			'Initial config test:\n'
			f'  Build: {build_status}\n'
			f'  Boot:  {attempt.boot_succeeded}\n'
		)
		if attempt.coverage is not None:
			content += f'  Coverage: {(attempt.coverage * 100):.1f}%\n'
		return content

	def __format_attempt(self, i: int, attempt: Attempt) -> str:
		define = attempt.response.define if attempt.response else None
		undefine = attempt.response.undefine if attempt.response else None
		reasoning = attempt.response.reasoning if attempt.response else None
		build_status = 'Success' if attempt.build_succeeded else 'Failed'

		content = (
			f'\nAttempt {i} / {settings.agent.MAX_ITERATIONS}:\n'
			f'  KLocalizer: {attempt.klocalizer_status}\n'
			f'  Build:      {build_status}\n'
			f'  Boot:       {attempt.boot_succeeded}\n'
		)
		if attempt.coverage is not None:
			content += f'  Coverage:   {(attempt.coverage * 100):.1f}%\n'
		content += (
			f'  Defined:    {define}\n'
			f'  Undefined:  {undefine}\n'
			f'  Reasoning:  {reasoning}\n'
		)
		return content

prompt = Prompt()
