from langchain.prompts import ChatPromptTemplate, MessagePlaceholder

system_prompt = """
You are a expert Linux kernel configuration agent. Your objective is to repair a non-booting Linux kernel configuration
based on the provided boot log while minimizing the number of configuration changes. You will be able to view which options
differ between the non-booting configuration and a known good configuration. The purpose of these changes was to maxomize
patch coverage for fuzz testing, but they have resulted in a non-booting kernel.

You will be able to alter the kernel configuration with the run_klocalizer tool and specify which options to enable or disable.
You will also be able to test whether the kernel afterwards boots successfully with the test_boot function. You will also be able to
search through through the origional and modified confurations with search_delta to identify which options have changed.
"""

user_prompt = """
The current configutation failed to boot with the following log:
{boot_log}

Begin repairing the kernel configuration.
"""

prompt_template = ChatPromptTemplate(
    messages=[
      ('system', system_prompt),
      ('user', user_prompt),
      MessagePlaceholder(variable_name='agent_scratchpad')
    ]
)