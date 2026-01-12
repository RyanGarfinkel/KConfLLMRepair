from langchain_google_genai import ChatGoogleGenerativeAI
from singleton_decorator import singleton
from langchain_openai import ChatOpenAI
from src.config import settings

@singleton
class Factory:

    def get_llm(self, override: str | None = None):

        if override:
            return self.__init_model(override)

        if settings.OPENAI_API_KEY:
            return self.__init_model('gpt-4o-mini')
        elif settings.GOOGLE_API_KEY:
            return self.__init_model('gemini-2.5-flash')
        else:
            raise ValueError('Must have at least one valid API key to initialize LLM.')

    
    def __init_model(self, provider: str):

        if provider.startswith('gpt'):
            return ChatOpenAI(model=provider, api_key=settings.OPENAI_API_KEY)
        elif provider.startswith('gemini'):
            return ChatGoogleGenerativeAI(model=provider, api_key=settings.GOOGLE_API_KEY)
        else:
            raise ValueError(f'Unknown provider: {provider} or missing API key.')

factory = Factory()
