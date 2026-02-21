from singleton_decorator import singleton
from google.genai import Client, types
from src.config import settings
from .base import BaseEmbedding
from typing import Literal

@singleton
class GoogleEmbedding(BaseEmbedding):

    def __init__(self):
        self.client = Client(api_key=settings.agent.GOOGLE_API_KEY)

    def embed(self, content: list[str], task_type: Literal['RETRIEVAL_QUERY', 'RETRIEVAL_DOCUMENT']) -> tuple[list[list[float]], int]:

        embeddings = []
        total_tokens = 0
        batch_size = 100

        for i in range(0, len(content), batch_size):
            batch = content[i : i + batch_size]

            embedding_response = self.client.models.embed_content(
                model=settings.agent.EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type)
            )

            embeddings.extend([e.values for e in embedding_response.embeddings])

            token_response = self.client.models.count_tokens(
                model=settings.agent.EMBEDDING_MODEL,
                contents=batch
            )
            
            total_tokens += token_response.total_tokens

        return embeddings, total_tokens

gemini_embeddings = GoogleEmbedding()
