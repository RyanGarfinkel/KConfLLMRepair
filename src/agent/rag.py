import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import StructuredTool
from langchain_openai import OpenAIEmbeddings
from src.config import settings

patch_separators = [
    '\n',
    'diff --git',
    'index ',
    '--- ',
    '+++ ',
    '\n@@',
    '\n+',
    '\n-',
    'commit ',
    'Author:',
    'Date:',
    'new file mode',
    'deleted file mode',
    'rename from',
    'rename to',
    'Binary files '
]

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
    'patch': {'chunk_size': 3000, 'chunk_overlap': 500},
    'klocalizer': {'chunk_size': 3000, 'chunk_overlap': 500},
    'build': {'chunk_size': 1500, 'chunk_overlap': 300},
    'qemu':  {'chunk_size': 1200, 'chunk_overlap': 300},
}

class RAG:

    def __init__(self, path: str, type: str):

        self.path = path

        if type == 'patch':
            self.separators = patch_separators
            self.chunk_size = SPLITTER_CONFIGS['patch']['chunk_size']
            self.chunk_overlap = SPLITTER_CONFIGS['patch']['chunk_overlap']
        elif type == 'klocalizer':
            self.separators = klocalizer_separators
            self.chunk_size = SPLITTER_CONFIGS['klocalizer']['chunk_size']
            self.chunk_overlap = SPLITTER_CONFIGS['klocalizer']['chunk_overlap']
        elif type == 'build':
            self.separators = build_separators
            self.chunk_size = SPLITTER_CONFIGS['build']['chunk_size']
            self.chunk_overlap = SPLITTER_CONFIGS['build']['chunk_overlap']
        elif type == 'qemu':
            self.separators = qemu_separators
            self.chunk_size = SPLITTER_CONFIGS['qemu']['chunk_size']
            self.chunk_overlap = SPLITTER_CONFIGS['qemu']['chunk_overlap']
        else:
            raise ValueError(f'Unknown RAG type: {type}')

        self.embedding_model = self.__get_embedding_model()
        self.__load_vector_store()

        self.queries = []
        self.type = type
        
    def __get_embedding_model(self):

        if settings.agent.PROVIDER == 'google':
            return GoogleGenerativeAIEmbeddings(model='gemini-embedding-001', api_key=settings.agent.GOOGLE_API_KEY)
        else:
            return OpenAIEmbeddings(api_key=settings.agent.OPENAI_API_KEY)
        
    def __load_vector_store(self):

        if self.path is None or not os.path.exists(self.path):
            self.vector_store = None
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

        self.vector_store = FAISS.from_documents(splits, self.embedding_model)

    def reload(self, new_path: str):

        self.path = new_path
        self.__load_vector_store()
    
    def search(self, query: str) -> str:
        
        if not self.vector_store:
            self.queries.append({
                'file': self.type,
                'query': query,
                'results': 'No data available. File not found.',
            })
            
            return 'No data available. File not found.'
        
        results = self.vector_store.similarity_search(query, k=settings.agent.MAX_MATCHES)

        self.queries.append({
                'type': self.type,
                'file': self.path,
                'query': query,
                'results': [doc.page_content for doc in results],
            })

        return '\n'.join(self.queries[-1]['results'])
    
    def as_tool(self, name: str, desc: str) -> StructuredTool:       
        return StructuredTool.from_function(
            name=name,
            description=desc,
            func=self.search,
        )
