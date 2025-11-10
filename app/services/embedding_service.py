"""Embedding service using OpenAI."""
from typing import List
from openai import AsyncOpenAI
from app.config import settings


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimension
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimension
        )
        return [item.embedding for item in response.data]


# Global instance
embedding_service = EmbeddingService()

