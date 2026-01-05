from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from toolbox import get_agent_tools

max_iterations = 5

class Agent:

    def __init__(self, id):

        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-pro',
        )

        self.tools = get_agent_tools(id)

        self.prompt = ''

        self.agent = create_react_agent(self.llm, self.tools, self.prompt)

        self.executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=max_iterations,
        )

    def repair(self, log_path):

        with open(log_path, 'r') as f:
            log = f.read()

        prompt = f"""Given the following kernel build log, identify the most likely cause of the build failure and suggest a potential fix.