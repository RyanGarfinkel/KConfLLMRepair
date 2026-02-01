from src.config import settings
import os

def grep(path: str | None, pattern: str) -> str:

    if path is None or not os.path.exists(path):
        return f'{path} does not exist.'
    
    results = []
    with open(path, 'r', errors='replace') as f:
        for i, line in enumerate(f):
            if pattern in line:
                results.append(f'Line {i + 1}: {line.strip()}')

    return '\n'.join(results)

def chunk(path: str | None, line_start: int) -> str:

    if path is None or not os.path.exists(path):
        return f'{path} does not exist.'
    
    results = []
    with open(path, 'r', errors='replace') as f:
        for i, line in enumerate(f):
            if i >= line_start and i < line_start + settings.config.CHUNK_WINDOW:
                results.append(f'Line {i + 1}: {line.strip()}')
            elif i >= line_start + settings.config.CHUNK_WINDOW:
                break

    return '\n'.join(results)
