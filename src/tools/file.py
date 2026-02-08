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
                if pattern.lower() in line.lower():
                    results.append(f'Line {i + 1}: {line.strip()}')

        return results

    def chunk(self, path: str | None, line_start: int) -> list[str]:

        if path is None or not os.path.exists(path):
            return [f'{path} does not exist.']
        
        results = []
        with open(path, 'r', errors='replace') as f:
            for i, line in enumerate(f):
                if i >= line_start and i < line_start + settings.runtime.CHUNK_WINDOW:
                    results.append(f'Line {i + 1}: {line.strip()}')
                elif i >= line_start + settings.runtime.CHUNK_WINDOW:
                    break

        return results
    
    def search_config(self, path: str | None, options: list[str]) -> list[str]:

        if path is None or not os.path.exists(path):
            return [f'{path} does not exist.']

        map = {}
        with open(path, 'r', errors='replace') as f:
            for line in f:
                line = line.strip()

                if '=' in line and not line.startswith('#'):
                    key = line.split('=', 1)[0]
                    map[key] = line
                elif line.startswith('# ') and line.endswith(' is not set'):
                    key = line[2:-len(' is not set')]
                    map[key] = line
        
        results = []
        for option in options:
            if option in map:
                results.append(map[option])
            else:
                results.append(f'{option} not found in config.')

        return results

file = FileTool()
