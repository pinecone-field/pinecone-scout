"""User Profile Manager service."""
from typing import Optional, Dict, Any, List
from app.services.pinecone_service import pinecone_service
from app.services.embedding_service import embedding_service
from app.models import UserProfileMetadata
from datetime import datetime


class UserProfileManager:
    """Service for managing user profiles in Pinecone."""
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile from Pinecone."""
        response = await pinecone_service.fetch_user(user_id)
        
        if not response.vectors or user_id not in response.vectors:
            return None
        
        vector_data = response.vectors[user_id]
        return {
            "id": user_id,
            "values": vector_data.values,
            "metadata": vector_data.metadata
        }
    
    async def create_or_update_user_profile(
        self,
        user_id: str,
        metadata: UserProfileMetadata,
        embedding_vector: Optional[List[float]] = None
    ):
        """Create or update a user profile in Pinecone."""
        # If no embedding vector provided, generate one from user metadata
        if embedding_vector is None:
            # Create a text representation of user preferences for embedding
            preference_text = self._build_preference_text(metadata)
            embedding_vector = await embedding_service.embed_text(preference_text)
        
        # Update metadata with current timestamp
        metadata_dict = metadata.model_dump()
        metadata_dict["last_updated"] = datetime.utcnow().isoformat()
        
        # Upsert to Pinecone
        await pinecone_service.upsert_user(
            user_id=user_id,
            vector=embedding_vector,
            metadata=metadata_dict
        )
    
    async def update_user_preferences(
        self,
        user_id: str,
        item_id: str,
        feedback_type: str  # "like" or "dislike"
    ):
        """Update user preferences based on feedback."""
        # Get existing profile
        profile = await self.get_user_profile(user_id)
        
        if profile is None:
            # Create new profile if it doesn't exist
            metadata = UserProfileMetadata()
        else:
            # Load existing metadata
            metadata = UserProfileMetadata(**profile["metadata"])
        
        # Update preferences
        if feedback_type == "like":
            if item_id not in metadata.liked_items:
                metadata.liked_items.append(item_id)
            # Remove from disliked if present
            if item_id in metadata.disliked_items:
                metadata.disliked_items.remove(item_id)
        elif feedback_type == "dislike":
            if item_id not in metadata.disliked_items:
                metadata.disliked_items.append(item_id)
            # Remove from liked if present
            if item_id in metadata.liked_items:
                metadata.liked_items.remove(item_id)
        
        # Generate new embedding based on updated preferences
        preference_text = self._build_preference_text(metadata)
        embedding_vector = await embedding_service.embed_text(preference_text)
        
        # Update profile
        await self.create_or_update_user_profile(
            user_id=user_id,
            metadata=metadata,
            embedding_vector=embedding_vector
        )
    
    def _build_preference_text(self, metadata: UserProfileMetadata) -> str:
        """Build a text representation of user preferences for embedding."""
        parts = []
        
        if metadata.age_range:
            parts.append(f"Age range: {metadata.age_range}")
        if metadata.household_size:
            parts.append(f"Household size: {metadata.household_size}")
        if metadata.city:
            parts.append(f"City: {metadata.city}")
        if metadata.style_preference:
            parts.append(f"Style preference: {metadata.style_preference}")
        if metadata.liked_items:
            parts.append(f"Liked items: {', '.join(metadata.liked_items)}")
        if metadata.disliked_items:
            parts.append(f"Disliked items: {', '.join(metadata.disliked_items)}")
        
        return ". ".join(parts) if parts else "New user with no preferences"


# Global instance
user_profile_manager = UserProfileManager()

