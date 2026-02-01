
from langchain_core.messages import ToolMessage
from src.models import Attempt
from langgraph.types import Command
from src.tools import grep, chunk
from typing import Any
import os

def make_command(update: dict[str, Any], goto: str) -> Command:
    return Command(
        update=update,
        goto=goto
    )

def grep_command(attempt: Attempt, type: str, id: str, pattern: str) -> Command:
    
    log_path = attempt.klocalizer_log if type == 'klocalizer' else attempt.build_log if type == 'build' else attempt.boot_log if type == 'qemu' else None
    
    return make_command({
        'messages': [ToolMessage(
            tool_call_id=id,
            name=f'grep_{type}_log',
            content=grep(log_path, pattern) if log_path else f'The {type} log does not exist.'
        )],
    }, goto='analyze')

def chunk_command(attempt: Attempt, type: str, id: str, line_start: int) -> Command:
    
    log_path = attempt.klocalizer_log if type == 'klocalizer' else attempt.build_log if type == 'build' else attempt.boot_log if type == 'qemu' else None
    
    return make_command({
        'messages': [ToolMessage(
            tool_call_id=id,
            name=f'chunk_{type}_log',
            content=chunk(log_path, line_start) if log_path else f'The {type} log does not exist.'
        )],
    }, goto='analyze')
    
def search_config_command(path: str | None, options: list[str], id: str, tool_name: str) -> Command:
    
    if not path or not os.path.exists(path):
        return make_command({
            'messages': [ToolMessage(
                tool_call_id=id,
                name=tool_name,
                content=f'{path} does not exist.'
            )]
        }, goto='collect')
    
    results = []
    with open(path, 'r', errors='replace') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            for option in options:
                if line.startswith(f'{option}=') or line == f'# {option} is not set':
                    results.append(line)


    return make_command({
        'messages': [ToolMessage(
            tool_call_id=id,
            name=tool_name,
            content='\n'.join(results)
        )]
    }, goto='collect')
