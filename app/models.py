"""Data models for the recommendation system."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class UserProfileMetadata(BaseModel):
    """User profile metadata stored in Pinecone."""
    age_range: Optional[str] = None
    household_size: Optional[str] = None
    city: Optional[str] = None
    style_preference: Optional[str] = None
    liked_items: List[str] = Field(default_factory=list)
    disliked_items: List[str] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProductItemMetadata(BaseModel):
    """Product item metadata stored in Pinecone."""
    name: str
    category: str
    price: float
    description: str
    brand: Optional[str] = None
    features: List[str] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    """A single recommendation item."""
    item_id: str
    name: str
    price: float
    similarity_score: float
    rationale: str
    similar_user_signal: bool = False


class UserContext(BaseModel):
    """User context information for recommendations."""
    profile_updated: bool = False
    memory_recall: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response from the recommendation endpoint."""
    recommendations: List[RecommendationItem]
    user_context: UserContext
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RecommendRequest(BaseModel):
    """Request for recommendations."""
    user_id: str
    query: str
    session_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Request for feedback submission."""
    user_id: str
    item_id: str
    feedback_type: str  # "like" or "dislike"
    session_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response from feedback endpoint."""
    status: str
    profile_updated: bool


class ProfileResponse(BaseModel):
    """Response from profile endpoint."""
    user_id: str
    metadata: UserProfileMetadata
    preferences_count: int
    last_updated: str


class PredictiveSuggestRequest(BaseModel):
    """Request for predictive suggestions."""
    user_id: str
    conversation_context: str
    detected_topic: Optional[str] = None
    previous_topics: Optional[List[str]] = None  # Previous conversation messages/context strings (not topic names)


class PredictiveSuggestion(BaseModel):
    """A predictive suggestion."""
    text: str
    partner: Optional[str] = None
    is_sponsored: bool = False
    item_id: Optional[str] = None  # If suggesting a product
    item_name: Optional[str] = None
    item_price: Optional[float] = None
    item_url: Optional[str] = None  # URL to purchase the item


class PredictiveSuggestResponse(BaseModel):
    """Response from predictive suggest endpoint."""
    suggestion: Optional[PredictiveSuggestion] = None
    opt_in_required: bool = True

