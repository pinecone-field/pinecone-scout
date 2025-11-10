"""Pinecone service for managing indexes and vector operations."""
from typing import List, Optional, Dict, Any
from pinecone import PineconeAsyncio, ServerlessSpec, CloudProvider, AwsRegion, Metric, VectorType
from app.config import settings


class PineconeService:
    """Service for managing Pinecone indexes and operations."""
    
    def __init__(self):
        """Initialize Pinecone client."""
        self.client: Optional[PineconeAsyncio] = None
        self.users_index = None
        self.items_index = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Pinecone client and ensure indexes exist."""
        if self._initialized:
            return
        
        self.client = PineconeAsyncio(api_key=settings.pinecone_api_key)
        
        # Ensure users_index exists
        if not await self.client.has_index(settings.users_index_name):
            await self.client.create_index(
                name=settings.users_index_name,
                dimension=settings.embedding_dimension,
                metric=Metric.COSINE,
                spec=ServerlessSpec(
                    cloud=CloudProvider.AWS,
                    region=AwsRegion.US_EAST_1
                ),
                vector_type=VectorType.DENSE
            )
        
        # Ensure items_index exists
        if not await self.client.has_index(settings.items_index_name):
            await self.client.create_index(
                name=settings.items_index_name,
                dimension=settings.embedding_dimension,
                metric=Metric.COSINE,
                spec=ServerlessSpec(
                    cloud=CloudProvider.AWS,
                    region=AwsRegion.US_EAST_1
                ),
                vector_type=VectorType.DENSE
            )
        
        # Get index descriptions to get hosts
        users_desc = await self.client.describe_index(settings.users_index_name)
        items_desc = await self.client.describe_index(settings.items_index_name)
        
        # Initialize index connections
        self.users_index = self.client.IndexAsyncio(host=users_desc.host)
        self.items_index = self.client.IndexAsyncio(host=items_desc.host)
        
        self._initialized = True
    
    async def close(self):
        """Close Pinecone client connections."""
        if self.client:
            await self.client.close()
            self._initialized = False
    
    async def upsert_user(
        self,
        user_id: str,
        vector: List[float],
        metadata: Dict[str, Any]
    ):
        """Upsert a user vector to users_index."""
        if not self.users_index:
            await self.initialize()
        
        await self.users_index.upsert(
            vectors=[{
                "id": user_id,
                "values": vector,
                "metadata": metadata
            }]
        )
    
    async def upsert_item(
        self,
        item_id: str,
        vector: List[float],
        metadata: Dict[str, Any]
    ):
        """Upsert an item vector to items_index."""
        if not self.items_index:
            await self.initialize()
        
        await self.items_index.upsert(
            vectors=[{
                "id": item_id,
                "values": vector,
                "metadata": metadata
            }]
        )
    
    async def query_users(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ):
        """Query similar users from users_index."""
        if not self.users_index:
            await self.initialize()
        
        response = await self.users_index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        return response
    
    async def query_items(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ):
        """Query similar items from items_index."""
        if not self.items_index:
            await self.initialize()
        
        response = await self.items_index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        return response
    
    async def fetch_user(self, user_id: str):
        """Fetch a user by ID from users_index."""
        if not self.users_index:
            await self.initialize()
        
        response = await self.users_index.fetch(ids=[user_id])
        return response
    
    async def fetch_item(self, item_id: str):
        """Fetch an item by ID from items_index."""
        if not self.items_index:
            await self.initialize()
        
        response = await self.items_index.fetch(ids=[item_id])
        return response


# Global instance
pinecone_service = PineconeService()

