"""FastAPI routes for the recommendation system."""
from fastapi import APIRouter, HTTPException
from app.models import (
    RecommendRequest,
    RecommendationResponse,
    FeedbackRequest,
    FeedbackResponse,
    ProfileResponse,
    PredictiveSuggestRequest,
    PredictiveSuggestResponse
)
from app.services.recommendation_engine import recommendation_engine
from app.services.collaborative_filtering import collaborative_filtering
from app.services.user_profile_manager import user_profile_manager
from app.services.predictive_module import predictive_module

router = APIRouter()


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendRequest):
    """
    Generate product recommendations based on user query and profile.
    
    This endpoint implements the core recommendation flow (P0) and optionally
    enhances results with collaborative filtering (P1).
    """
    try:
        # Get base recommendations
        response = await recommendation_engine.get_recommendations(
            user_id=request.user_id,
            query=request.query,
            top_k=3
        )
        
        # Enhance with collaborative filtering (P1)
        # In production, this could be a feature flag
        response.recommendations = await collaborative_filtering.enhance_recommendations(
            user_id=request.user_id,
            recommendations=response.recommendations
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback (like/dislike) for a product recommendation.
    
    This updates the user's profile in Pinecone with their preferences.
    """
    if request.feedback_type not in ["like", "dislike"]:
        raise HTTPException(
            status_code=400,
            detail="feedback_type must be 'like' or 'dislike'"
        )
    
    try:
        await user_profile_manager.update_user_preferences(
            user_id=request.user_id,
            item_id=request.item_id,
            feedback_type=request.feedback_type
        )
        
        return FeedbackResponse(
            status="success",
            profile_updated=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating feedback: {str(e)}")


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """
    Retrieve user profile information including preferences and metadata.
    """
    try:
        profile = await user_profile_manager.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        from app.models import UserProfileMetadata
        metadata = UserProfileMetadata(**profile["metadata"])
        
        preferences_count = len(metadata.liked_items) + len(metadata.disliked_items)
        
        return ProfileResponse(
            user_id=user_id,
            metadata=metadata,
            preferences_count=preferences_count,
            last_updated=metadata.last_updated
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")


@router.post("/predictive_suggest", response_model=PredictiveSuggestResponse)
async def predictive_suggest(request: PredictiveSuggestRequest):
    """
    Generate predictive suggestions based on conversation context (P2).
    
    This endpoint:
    - Detects topics in the conversation using embeddings and keyword matching
    - Determines if a suggestion is appropriate (not too pushy)
    - Searches for relevant products based on context and user profile
    - Generates conversational, natural suggestions
    - Falls back to partner offers if no relevant products found
    """
    try:
        # Normalize empty strings to None for optional fields
        detected_topic = request.detected_topic if request.detected_topic else None
        previous_topics = request.previous_topics if request.previous_topics else None
        
        response = await predictive_module.generate_suggestion(
            user_id=request.user_id,
            conversation_context=request.conversation_context,
            detected_topic=detected_topic,
            previous_topics=previous_topics
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestion: {str(e)}")

