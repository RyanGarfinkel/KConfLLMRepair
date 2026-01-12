from src.models.iteration import IterationSummary
from src.models import AgentResult, Sample
from src.agents import factory, Agent
from src.core.kernel import Kernel
from src.kernel import KernelRepo
from src.tools import AgentTools
from src.utils import log

class RepairEngine:

    def __init__(self, sample: Sample, model_override: str | None, max_iterations: int):

        self.kernel = Kernel(sample.end_commit)

        llm = factory.get_llm(model_override)
        self.tools = AgentTools(self.kernel, sample)
        self.agent = Agent(llm, self.tools.get_tools())
        self.max_iterations = max_iterations
        self.sample = sample    

    def run(self) -> AgentResult:

        log.info(f'Starting repair engine for sample {self.sample.id} with {self.max_iterations} iterations.')

        history = []

        i = 0
        while i < self.max_iterations and not self.tools.succeeded:

            log.info(f'Starting iteration {i+1} for sample {self.sample.id}.')

            context = self.__build_context(i, history)

            summary = self.agent.run(context)

            history.append(summary)

            i += 1

        log.info(f'Finished repair engine for sample {self.sample.id} after {i} iterations.')

        result = AgentResult(
            sample=self.sample.dir,
            status='success' if self.tools.succeeded else 'max_iterations' if i == self.max_iterations else 'failure',
            iterations=i,
            config=self.tools.config,
            token_usage=sum(iteration.token_usage for iteration in history),
            history=history
        )
        
        return result
    
    def __build_context(self, i: int, history: list[IterationSummary]) -> str:
        
        prompt = (
            f'MISSION: Fix the kernel boot failure.\n'
            f'ITERATION: {i}/{self.max_iterations}\n'
        )

        if i == 0:
            prompt += (
                f'STATUS: Initial attempt.\n' +
                'Start by searching the through the configs and logs to find any clues about the failure.\n'
            )
        else:
            prompt += (
                'STATUS: Previous attempt failed.\n'
            )

        if history:
            prompt += (
                'HISTORY:\n'
            )

        for i, iteration in enumerate(history):
            prompt += (
                f'ITERATION {i + 1}:\n' +
                f'THOUGHTS: {iteration.thoughts}\n' +
                f'OBSERVATIONS: {iteration.observations}\n' +
                f'SUGGESTIONS: {iteration.suggestions}\n'
            )
        
        prompt += (
            'INSTRUCTIONS:\n' +
            '1. Analyze the history and the current state of the kernel to avoid repeating mistakes.\n' +
            '2. If you made applied any changes, check the new logs to see why it failed.\n' +
            '3. Use the tools available, apply changes, and test the kernel.\n'
        )

        return prompt

    def cleanup(self):

        self.kernel.cleanup()

