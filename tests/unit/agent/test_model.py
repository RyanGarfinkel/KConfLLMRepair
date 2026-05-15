from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from src.agent.model import model
from unittest.mock import patch
import sys

model_module = sys.modules['src.agent.model']

# Google Gemini model: Success
def test_get_llm_google():
	with patch.object(model_module, 'settings') as mock_settings:
		mock_settings.agent.PROVIDER = 'google'
		mock_settings.agent.MODEL = 'gemini-2.0-flash'
		mock_settings.agent.GOOGLE_API_KEY = 'fake-google-key'
		llm = model.get_llm()
	
	assert isinstance(llm, ChatGoogleGenerativeAI)

# OpenAI GPT model: Success
def test_get_llm_openai():
	with patch.object(model_module, 'settings') as mock_settings:
		mock_settings.agent.PROVIDER = 'openai'
		mock_settings.agent.MODEL = 'gpt-4o'
		mock_settings.agent.OPENAI_API_KEY = 'fake-openai-key'
		llm = model.get_llm()
	
	assert isinstance(llm, ChatOpenAI)

# Google model with missing API key: Failure
def test_get_llm_google_missing_key():
	with patch.object(model_module, 'settings') as mock_settings:
		mock_settings.agent.PROVIDER = 'google'
		mock_settings.agent.GOOGLE_API_KEY = None

		try:
			model.get_llm()
			assert False, 'Expected ValueError'
		except ValueError as e:
			assert 'Google API key' in str(e)

# OpenAI model with missing API key: Failure
def test_get_llm_openai_missing_key():
	with patch.object(model_module, 'settings') as mock_settings:
		mock_settings.agent.PROVIDER = 'openai'
		mock_settings.agent.OPENAI_API_KEY = None

		try:
			model.get_llm()
			assert False, 'Expected ValueError'
		except ValueError as e:
			assert 'OpenAI API key' in str(e)

# Unknown provider in get_llm: Failure
def test_get_llm_unknown_provider():
	with patch.object(model_module, 'settings') as mock_settings:
		mock_settings.agent.PROVIDER = 'unknown'
		mock_settings.agent.MODEL = 'some-model'

		try:
			model.get_llm()
			assert False, 'Expected ValueError'
		except ValueError as e:
			assert 'Unknown model provider' in str(e)

# Google embedding model: Success
def test_get_embedding_model_google():
	with patch.object(model_module, 'settings') as mock_settings:
		mock_settings.agent.PROVIDER = 'google'
		result = model.get_embedding_model()
	
	assert result is model_module.gemini_embeddings

# OpenAI embedding model not implemented: Failure
def test_get_embedding_model_openai_not_implemented():
	with patch.object(model_module, 'settings') as mock_settings:
		mock_settings.agent.PROVIDER = 'openai'
		try:
			model.get_embedding_model()
			assert False, 'Expected NotImplementedError'
		except NotImplementedError:
			pass

# Unknown provider in get_embedding_model: Failure
def test_get_embedding_model_unknown_provider():
	with patch.object(model_module, 'settings') as mock_settings:
		mock_settings.agent.PROVIDER = 'unknown'
		try:
			model.get_embedding_model()
			assert False, 'Expected ValueError'
		except ValueError as e:
			assert 'Unknown model provider' in str(e)
