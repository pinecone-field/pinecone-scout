"""Collaborative Filtering service (P1)."""
from typing import List, Dict, Any, Optional
from app.services.pinecone_service import pinecone_service
from app.services.user_profile_manager import user_profile_manager
from app.models import RecommendationItem


class CollaborativeFiltering:
    """Collaborative filtering service to find similar users."""
    
    async def enhance_recommendations(
        self,
        user_id: str,
        recommendations: List[RecommendationItem],
        top_k_similar_users: int = 5
    ) -> List[RecommendationItem]:
        """Enhance recommendations using collaborative filtering."""
        # Get user profile
        user_profile = await user_profile_manager.get_user_profile(user_id)
        
        if not user_profile:
            return recommendations
        
        # Find similar users
        user_vector = user_profile["values"]
        similar_users = await pinecone_service.query_users(
            vector=user_vector,
            top_k=top_k_similar_users + 1,  # +1 to exclude self
            filter=None
        )
        
        # Extract liked items from similar users
        similar_user_items = {}
        for match in similar_users.matches:
            if match.id == user_id:
                continue  # Skip self
            
            metadata = match.metadata or {}
            liked_items = metadata.get("liked_items", [])
            
            for item_id in liked_items:
                if item_id not in similar_user_items:
                    similar_user_items[item_id] = 0
                similar_user_items[item_id] += match.score  # Weight by similarity
        
        # Boost recommendations that similar users liked
        recommendation_dict = {rec.item_id: rec for rec in recommendations}
        
        for item_id, boost_score in similar_user_items.items():
            if item_id in recommendation_dict:
                # Boost existing recommendation
                rec = recommendation_dict[item_id]
                rec.similar_user_signal = True
                rec.similarity_score += boost_score * 0.1  # Small boost
            else:
                # Add new recommendation from similar users
                # Fetch item details
                item_response = await pinecone_service.fetch_item(item_id)
                if item_response.vectors and item_id in item_response.vectors:
                    item_metadata = item_response.vectors[item_id].metadata or {}
                    recommendations.append(RecommendationItem(
                        item_id=item_id,
                        name=item_metadata.get("name", "Unknown"),
                        price=item_metadata.get("price", 0.0),
                        similarity_score=boost_score * 0.1,
                        rationale="Popular with similar users",
                        similar_user_signal=True
                    ))
        
        # Sort by similarity score
        recommendations.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return recommendations


# Global instance
collaborative_filtering = CollaborativeFiltering()

