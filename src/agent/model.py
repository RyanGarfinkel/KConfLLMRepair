from src.embeddings import BaseEmbedding, gemini_embeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from singleton_decorator import singleton
from langchain_openai import ChatOpenAI
from src.config import settings

@singleton
class Model:

    def get_llm(self) -> BaseChatModel:

        if settings.agent.PROVIDER == 'openai':
            if settings.agent.OPENAI_API_KEY:
                return ChatOpenAI(model_name=settings.agent.MODEL, api_key=settings.agent.OPENAI_API_KEY)
            else:
                raise ValueError('OpenAI API key is not configured.')
        elif settings.agent.PROVIDER == 'google':
            if settings.agent.GOOGLE_API_KEY:
                return ChatGoogleGenerativeAI(model=settings.agent.MODEL, api_key=settings.agent.GOOGLE_API_KEY)
            else:
                raise ValueError('Google API key is not configured.')
        else:
            raise ValueError(f'Unknown model provider for model: {settings.agent.MODEL}')
        
    def get_embedding_model(self) -> BaseEmbedding:
        if settings.agent.PROVIDER == 'openai':
            raise NotImplementedError('OpenAI embedding model is not implemented yet.')
        elif settings.agent.PROVIDER == 'google':
            return gemini_embeddings
        else:
            raise ValueError(f'Unknown model provider for embedding model: {settings.agent.PROVIDER}')

model = Model()
