from langchain.messages import SystemMessage, HumanMessage
from langchain_core.messages.base import BaseMessage
from singleton_decorator import singleton
from src.config import settings
from src.models import Attempt
from .session import Session

@singleton
class Prompt:

	def system(self, session: Session) -> SystemMessage:

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

		hard_constraints = ''
		if session.hard_define or session.hard_undefine:
			define_line = f'  MUST DEFINE: {session.hard_define}\n' if session.hard_define else ''
			undefine_line = f'  MUST UNDEFINE: {session.hard_undefine}\n' if session.hard_undefine else ''
			hard_constraints = (
				'\nHARD CONSTRAINTS - you must include these in every response without exception:\n'
				f'{define_line}{undefine_line}'
			)

		return SystemMessage(content=
			'You are an expert Linux kernel configuration repair agent. '
			f'Your goal is to fix a non-booting {settings.kernel.ARCH} kernel by identifying which '
			'Kconfig options are causing build or boot failures and correcting them.'
			f'{hard_constraints}\n\n'

			'HOW KCONFIG CHANGES ARE APPLIED\n'
			'You output a define list and an undefine list each iteration. '
			'KLocalizer applies them to the original config every time, not to the previous modified config. '
			'Your response must always contain the complete set of changes you want. '
			'If you defined an option in a previous attempt and omit it now, it will be dropped silently. '
			'KLocalizer resolves Kconfig dependencies automatically and may define or undefine '
			'additional options beyond what you specify to satisfy the dependency graph.\n\n'

			'WORKFLOW\n'
			'Follow these steps in order each attempt:\n'
			'1. Read the attempt history. Identify the current failure stage (klocalizer / build / boot) '
			'and note what options were already tried and what effect they had.\n'
			f'2. Build failure: grep for "error:" to find the first compiler or linker error. {log_instruction}\n'
			'3. Boot failure: grep for "error", "panic", or "failed" to identify the failure point.\n'
			'4. Look up the implicated options in the original and latest config to see their current state.\n'
			'5. If the same error persists after defining an option, the root cause is likely a missing '
			'dependency. Search for related options or grep the config for options referenced in the error.\n'
			'6. Respond with the complete cumulative define and undefine lists and clear reasoning '
			'explaining which error each change addresses.\n\n'

			'CONSTRAINTS\n'
			f'You have {settings.agent.MAX_TOOL_CALLS} tool calls per attempt. '
			'Use targeted patterns, do not grep broadly. '
			'If you are running low, stop investigating and submit your best response immediately '
			'rather than exhausting the budget without responding.\n\n'

			'GOAL\n'
			'Repair the config so the kernel boots successfully. '
			f'You have at most {settings.agent.MAX_ITERATIONS} attempts.'
		)

	def user(self, session: Session) -> HumanMessage:

		attempt_num = len(session.attempts) - 1
		past_attempts = session.attempts[:-1]

		content = (
			f'ATTEMPT {attempt_num} / {settings.agent.MAX_ITERATIONS}\n\n'
			'INSTRUCTIONS\n'
			'1. Review the history below to identify the current failure stage and what has already been tried.\n'
			'2. Grep for "error:" or "panic" in the relevant log to pinpoint the root cause.\n'
			'3. Look up the implicated options in the original config (and latest config if available).\n'
			'4. Respond with the COMPLETE cumulative define and undefine lists (every option you want changed, '
			f'not just new additions). Constraints: {settings.agent.MAX_TOOL_CALLS} tool calls.\n\n'
		)

		content += 'HISTORY\n'

		if not past_attempts:
			content += 'None - this is the first attempt.'
			return HumanMessage(content=content)

		content += self.__format_initial(past_attempts[0])

		for i, attempt in enumerate(past_attempts[1:], 1):
			content += self.__format_attempt(i, attempt)

		return HumanMessage(content=content)

	def __format_initial(self, attempt: Attempt) -> str:
		return (
			'Initial config test:\n'
			f'  Build: {"Success" if attempt.build_succeeded else "Failed"}\n'
			f'  Boot:  {attempt.boot_succeeded}\n'
		)

	def __format_attempt(self, i: int, attempt: Attempt) -> str:
		define = attempt.response.define if attempt.response else None
		undefine = attempt.response.undefine if attempt.response else None
		reasoning = attempt.response.reasoning if attempt.response else None

		return (
			f'\nAttempt {i} / {settings.agent.MAX_ITERATIONS}:\n'
			f'  KLocalizer: {attempt.klocalizer_status}\n'
			f'  Build:      {"Success" if attempt.build_succeeded else "Failed"}\n'
			f'  Boot:       {attempt.boot_succeeded}\n'
			f'  Defined:    {define}\n'
			f'  Undefined:  {undefine}\n'
			f'  Reasoning:  {reasoning}\n'
		)

	def prompt(self, session: Session) -> list[BaseMessage]:
		return [self.system(session), self.user(session)]

prompt = Prompt()
