from singleton_decorator import singleton
from src.config import settings
import os

@singleton
class FileTool:

    def grep(self, path: str | None, pattern: str) -> list[str]:

        if path is None or not os.path.exists(path):
            return [f'{path} does not exist.']
        
        results = []
        with open(path, 'r', errors='replace') as f:
            for i, line in enumerate(f):
                if pattern in line:
                    results.append(f'Line {i + 1}: {line.strip()}')

        return results

    def chunk(self, path: str | None, line_start: int) -> list[str]:

        if path is None or not os.path.exists(path):
            return [f'{path} does not exist.']
        
        results = []
        with open(path, 'r', errors='replace') as f:
            for i, line in enumerate(f):
                if i >= line_start and i < line_start + settings.config.CHUNK_WINDOW:
                    results.append(f'Line {i + 1}: {line.strip()}')
                elif i >= line_start + settings.config.CHUNK_WINDOW:
                    break

        return results
    
    def search_config(self, path: str | None, options: list[str]) -> list[str]:

        if path is None or not os.path.exists(path):
            return [f'{path} does not exist.']
        
        results = []
        with open(path, 'r', errors='replace') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                for option in options:
                    if line.startswith(f'{option}=') or line == f'# {option} is not set':
                        results.append(line)

        return results

file = FileTool()
