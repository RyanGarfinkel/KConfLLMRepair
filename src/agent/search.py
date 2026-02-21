from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from src.models import TokenUsage
from src.config import settings
from typing import Literal
from .model import model
import numpy as np
import os

klocalizer_separators =  [
    '\nTraceback (most recent call last):',
    '\nERROR:',
    '\nWARNING: Failed to compute',
    '\nWARNING: Syntax analysis',
    '\nINFO: Build with',
    '\nINFO: Trying',
    '\nINFO: Computing line',
    '\nINFO: Sampling and writing',
    '\n[STEP 1/3]',
    '\n[STEP 2/3]',
    '\n[STEP 3/3]',
    '\nWARNING:',
    '\nINFO:',
]

build_separators = [
    '\n',
    '\nHOSTCC ',
    '\nHOSTLD ',
    '\nCC ',
    '\nLD ',
    '\nAR ',
    '\nAS ',
    '\nLINK ',
    '\nOBJCOPY ',
    '\nINSTALL ',
    '\nBUILD ',
    '\nmake',
    'warning:',
    'error:',
    'fatal error:',
    'undefined reference to',
    'In file included from',
    'note:'
]

qemu_separators = [
    '\n',
    '\nKASAN',
    '\nBUG',
    '\nCall Trace',
    '\nKernel panic',
    '\npanic:',
    '\nOops:',
    'WARNING: CPU',
    'WARNING:',
    'Traceback',
    'task ',
    'initcall',
    'ACPI:',
    'PCI:',
    'Booting Linux',
    'Kernel command line'
]

SPLITTER_CONFIGS = {
    'klocalizer': {'chunk_size': 3000, 'chunk_overlap': 500},
    'build': {'chunk_size': 1500, 'chunk_overlap': 300},
    'qemu':  {'chunk_size': 1200, 'chunk_overlap': 300},
}

class LogSearch:

    def __init__(self, path: str, type: Literal['klocalizer', 'build', 'boot']):

        self.path = path

        if type == 'klocalizer':
            self.separators = klocalizer_separators
            self.chunk_size = SPLITTER_CONFIGS['klocalizer']['chunk_size']
            self.chunk_overlap = SPLITTER_CONFIGS['klocalizer']['chunk_overlap']
        elif type == 'build':
            self.separators = build_separators
            self.chunk_size = SPLITTER_CONFIGS['build']['chunk_size']
            self.chunk_overlap = SPLITTER_CONFIGS['build']['chunk_overlap']
        elif type == 'boot':
            self.separators = qemu_separators
            self.chunk_size = SPLITTER_CONFIGS['qemu']['chunk_size']
            self.chunk_overlap = SPLITTER_CONFIGS['qemu']['chunk_overlap']

        self.model = model.get_embedding_model()
        self.token_usage = 0

        self.__load()

    def __load(self):
        
        if self.path is None or not os.path.exists(self.path):
            return
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            keep_separator=True,
        )

        loader = TextLoader(self.path, encoding='utf-8', autodetect_encoding=True)
        docs = loader.load()

        splits = splitter.split_documents(docs)
        self.chunks = [split.page_content for split in splits]

        embeddings, tokens = self.model.embed(self.chunks, task_type='RETRIEVAL_DOCUMENT')

        self.embeddings = embeddings
        self.token_usage = tokens

    def __cosine_similarity(self, a: list[float], b: list[float]) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def query(self, query: str) -> tuple[str, TokenUsage]:

        if self.path is None or not os.path.exists(self.path):
            return 'File does not exist', TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0)
        
        query_embedding, tokens = self.model.embed(query, task_type='RETRIEVAL_QUERY')
        token_usage = TokenUsage(input_tokens=tokens, output_tokens=0, total_tokens=tokens)

        scores = [self.__cosine_similarity(query_embedding[0], chunk_embedding) for chunk_embedding in self.embeddings]

        top_matches = sorted(zip(scores, self.chunks), key=lambda x: x[0], reverse=True)[:settings.agent.MAX_MATCHES]

        chunks = [chunk for _, chunk in top_matches]

        return '\n'.join(chunks), token_usage
