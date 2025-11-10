"""Recommendation Engine service."""
from typing import List, Dict, Any, Optional
from app.services.pinecone_service import pinecone_service
from app.services.embedding_service import embedding_service
from app.services.user_profile_manager import user_profile_manager
from app.models import RecommendationItem, UserContext, RecommendationResponse


class RecommendationEngine:
    """Core recommendation engine (P0)."""
    
    async def get_recommendations(
        self,
        user_id: str,
        query: str,
        top_k: int = 3
    ) -> RecommendationResponse:
        """Generate recommendations based on user query and profile."""
        # Embed the user query
        query_embedding = await embedding_service.embed_text(query)
        
        # Get user profile
        user_profile = await user_profile_manager.get_user_profile(user_id)
        
        # Build context vector (combine query with user profile if available)
        context_vector = query_embedding
        memory_recall = None
        
        if user_profile:
            # Combine query embedding with user profile embedding
            # Simple weighted average (can be improved with more sophisticated methods)
            user_vector = user_profile["values"]
            context_vector = [
                0.6 * q + 0.4 * u
                for q, u in zip(query_embedding, user_vector)
            ]
            
            # Build memory recall message
            metadata = user_profile.get("metadata", {})
            liked_items = metadata.get("liked_items", [])
            if liked_items:
                memory_recall = f"You previously liked {len(liked_items)} item(s)"
        
        # Search items_index for similar products
        search_results = await pinecone_service.query_items(
            vector=context_vector,
            top_k=top_k * 2  # Get more results to filter
        )
        
        # Filter out disliked items and format recommendations
        recommendations = []
        if user_profile:
            disliked_items = user_profile.get("metadata", {}).get("disliked_items", [])
        else:
            disliked_items = []
        
        for match in search_results.matches:
            item_id = match.id
            if item_id in disliked_items:
                continue
            
            metadata = match.metadata or {}
            recommendations.append(RecommendationItem(
                item_id=item_id,
                name=metadata.get("name", "Unknown"),
                price=metadata.get("price", 0.0),
                similarity_score=match.score,
                rationale=self._generate_rationale(metadata, query),
                similar_user_signal=False
            ))
            
            if len(recommendations) >= top_k:
                break
        
        # Build user context
        user_context = UserContext(
            profile_updated=False,
            memory_recall=memory_recall
        )
        
        return RecommendationResponse(
            recommendations=recommendations,
            user_context=user_context
        )
    
    def _generate_rationale(self, metadata: Dict[str, Any], query: str) -> str:
        """Generate a rationale for why this item was recommended."""
        name = metadata.get("name", "this item")
        description = metadata.get("description", "")
        
        # Simple rationale generation (can be enhanced with LLM)
        if description:
            return f"Matches your search: {description[:100]}"
        return f"Matches your search for {query}"


# Global instance
recommendation_engine = RecommendationEngine()

