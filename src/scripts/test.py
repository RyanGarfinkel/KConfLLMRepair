
from src.core import RepairEngine
import pandas as pd
from src.config import settings
from src.models import Sample

df = pd.read_csv(f'{settings.SAMPLE_DIR}/summary.csv')
samples = Sample.get_samples(n=1)

engine = RepairEngine(samples[0], model_override=None, max_iterations=5)

result = engine.run()

print(f'Agent Results for Sample {result.sample}:')
print(f'Status: {result.status}')
print(f'Iterations: {result.iterations}')
print(f'Token Usage: {result.token_usage}')
print('History:')
for i, iteration in enumerate(result.history):
    print(f'  Iteration {i+1}:')
    print(f'    Thoughts: {iteration.thoughts}')
    print(f'    Observations: {iteration.observations}')
    print(f'    Suggestions: {iteration.suggestions}')
    print(f'    Token Usage: {iteration.token_usage}')

engine.cleanup()
