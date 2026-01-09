from langchain.agents import create_agent
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from src.utils.signature import extract_boot_signature
from src.llm.prompt import system_prompt
import json

class Agent:

    def __init__(self, dir, tools):

        # self.model = ChatGoogleGenerativeAI(
        #     model='gemini-2.5-flash',
        # )

        self.model = ChatOpenAI(model='gpt-4o-mini')

        self.tools = tools
        self.dir = dir

        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
        )

    def repair(self):
        
        signatures = extract_boot_signature(f'{self.dir}/try_0/qemu.log')
        if signatures and len(signatures) > 0:
            input = f"The kernel failed to boot with panic signatures: {', '.join(signatures)}"
        else:
            input = "The kernel failed to boot. Please analyze the qemu log to determine the cause."

        result = self.agent.invoke({
            'messages': [
                ('system', system_prompt),
                ('user', input),
            ]
        })

        with open(f'{self.dir}/result.json', 'w') as f:
            json.dump(result, f, indent=4)

        output = result['output'].lower()
        success = 'successfully' in output or 'you may stop now' in output

        return success
