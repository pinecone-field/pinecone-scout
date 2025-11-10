"""Predictive Module service (P2) - Enhanced conversational suggestions."""
from typing import Optional, List, Dict, Any
import json
import logging
from openai import AsyncOpenAI
from app.services.pinecone_service import pinecone_service
from app.services.embedding_service import embedding_service
from app.services.user_profile_manager import user_profile_manager
from app.models import PredictiveSuggestion, PredictiveSuggestResponse
from app.config import settings

# Set up logger for this module
logger = logging.getLogger(__name__)


class PredictiveModule:
    """Predictive suggestion module for contextual, conversational recommendations."""
    
    def __init__(self):
        """Initialize the predictive module."""
        # Initialize OpenAI client for LLM-based topic detection and query enhancement
        self.llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Minimum similarity threshold for product suggestions
    MIN_SIMILARITY_THRESHOLD = 0.40
    
    async def generate_suggestion(
        self,
        user_id: str,
        conversation_context: str,
        detected_topic: Optional[str] = None,
        previous_topics: Optional[List[str]] = None  # Previous conversation messages/context strings
    ) -> PredictiveSuggestResponse:
        """
        Generate a predictive suggestion based on conversation context.
        
        This method:
        1. Detects topics in the conversation using embeddings + keywords
        2. Determines if a suggestion is appropriate (not too pushy)
        3. Searches for relevant products based on context
        4. Generates conversational, natural suggestions
        """
        # Build enriched context from previous conversation messages if provided
        enriched_context = conversation_context
        if previous_topics and isinstance(previous_topics, list) and len(previous_topics) > 0:
            # previous_topics contains previous conversation messages/strings
            # Combine them with current context for better understanding
            previous_context = ". ".join(previous_topics[-3:])  # Use last 3 previous messages
            enriched_context = f"{previous_context}. {conversation_context}"
            logger.debug(f"Enriched context with {len(previous_topics)} previous messages")
        
        # Detect rejected/negative mentions of products
        rejected_products = await self._detect_rejected_products(enriched_context)
        if rejected_products:
            logger.debug(f"Detected rejected products: {rejected_products}")
        
        # Detect topic if not provided (use enriched context for better detection)
        if not detected_topic:
            logger.debug("Detecting topic from conversation context")
            detected_topic = await self._detect_topic_advanced(enriched_context)
            logger.debug(f"Detected topic: {detected_topic}")
        
        # Check if suggestion is appropriate (don't be too pushy)
        # Use CURRENT context (not enriched) to focus on the current conversation topic
        # This prevents previous unrelated messages from triggering suggestions
        should_suggest = await self._should_suggest(conversation_context, detected_topic)
        logger.debug(f"should_suggest={should_suggest}")
        if not should_suggest:
            logger.debug("Returning empty response (should_suggest=False)")
            return PredictiveSuggestResponse(
                suggestion=None,
                opt_in_required=False
            )
        
        # Get user profile for personalization
        user_profile = await user_profile_manager.get_user_profile(user_id)
        
        # Try to find relevant products first (more valuable than partner offers)
        # Use CURRENT context (not enriched) for product search to ensure we match the current intent
        # Only use enriched context for detecting rejected products and topic detection
        # Pass rejected products to exclude them from suggestions
        logger.debug("Searching for relevant products")
        logger.debug(f"Using conversation_context for product search: {conversation_context[:100]}...")
        product_suggestion = await self._find_relevant_product(
            conversation_context=conversation_context,  # Use CURRENT context only for product search
            user_profile=user_profile,
            detected_topic=detected_topic,
            rejected_products=rejected_products,
            previous_topics=previous_topics  # Pass conversation history for style matching only
        )
        
        if product_suggestion:
            logger.debug(f"Found product suggestion: {product_suggestion.item_name}")
            return PredictiveSuggestResponse(
                suggestion=product_suggestion,
                opt_in_required=False  # Product suggestions don't require opt-in
            )
        
        logger.debug("No product suggestion found, trying partner offers")
        # Fall back to partner offers if no relevant products found
        partner_suggestion = await self._get_partner_offer(detected_topic, enriched_context)
        if partner_suggestion:
            logger.debug("Found partner suggestion")
            return PredictiveSuggestResponse(
                suggestion=partner_suggestion,
                opt_in_required=True  # Partner offers require opt-in
            )
        
        logger.debug("No suggestions found, returning empty response")
        return PredictiveSuggestResponse(
            suggestion=None,
            opt_in_required=False
        )
    
    async def _detect_topic_advanced(self, text: str) -> Optional[str]:
        """
        Detect topic using LLM - let the LLM determine what topics are relevant.
        """
        return await self._detect_topic_with_llm(text)
    
    async def _detect_topic_with_llm(self, text: str) -> Optional[str]:
        """
        Use LLM to detect topics from conversation context.
        The LLM determines what topics are relevant - no hardcoded topic list.
        """
        try:
            prompt = f"""Analyze this conversation and identify the primary topic or interest related to products.

Conversation: "{text}"

Respond with ONLY a JSON object in this exact format:
{{
  "topic": "a brief topic name (e.g., 'gaming', 'entertainment', 'art_design', 'home_theater', 'sports', 'work', 'family', 'apartment', 'budget', 'premium') or null if no clear topic",
  "confidence": "high" or "medium" or "low",
  "reasoning": "brief explanation"
}}

If no clear topic is detected, set topic to null.

JSON response:"""

            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a topic detection assistant. Analyze conversations and identify the primary topic or interest. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Only return topic if confidence is medium or high
            if result.get("topic") and result.get("confidence") in ["high", "medium"]:
                return result["topic"]
            
            return None
            
        except Exception as e:
            logger.debug(f"LLM topic detection failed: {e}", exc_info=True)
            return None
    
    async def _should_suggest(self, conversation_context: str, detected_topic: Optional[str]) -> bool:
        """
        Use LLM to determine if we should make a suggestion (don't be too pushy).
        
        This system can suggest any type of purchasable product or service, including:
        - Electronics (TVs, televisions, etc.)
        - Furniture and home decor
        - Travel and vacation packages (cruises, trips, etc.)
        - Activities and experiences (tours, classes, workshops, etc.)
        - Any other products or services available in the catalog
        """
        try:
            prompt = f"""Analyze this conversation and determine if it's appropriate to suggest a product or service.

Conversation: "{conversation_context}"
Detected topic: {detected_topic or "none"}

This system can suggest various types of products and services, including:
- Electronics (TVs, televisions, etc.)
- Furniture and home decor
- Travel and vacation packages (cruises, trips, etc.)
- Activities and experiences (tours, classes, workshops, etc.)
- Any other purchasable products or services

Do NOT suggest if the conversation is about:
- General advice or non-purchasable topics
- Personal problems or emotional support
- Questions that don't relate to products/services
- The user explicitly said they don't want suggestions or are done shopping

Respond with ONLY a JSON object:
{{
  "should_suggest": true or false,
  "reasoning": "brief explanation"
}}

Important considerations:
- Suggest if the conversation is about ANY purchasable product or service (not just specific types)
- Travel/vacation conversations → could suggest cruises or travel packages
- Home/furniture conversations → could suggest furniture or home decor
- Activity/experience conversations → could suggest tours, classes, or experiences
- Product shopping conversations → could suggest relevant products
- If the user rejected ONE specific product but is still discussing products/services, suggest ALTERNATIVES (should_suggest = true)
- If the user explicitly said they don't want help, suggestions, or are done shopping, then should_suggest = false
- Rejecting a single product does NOT mean they don't want suggestions - they likely want alternatives
- Be flexible and open to suggesting any relevant product or service type

JSON response:"""

            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that determines when product/service suggestions are appropriate. This system can suggest ANY type of purchasable product or service (electronics, furniture, travel packages, experiences, etc.). Be flexible and open-minded - if the conversation relates to any purchasable product or service, suggest it. Only return false if the conversation is about non-purchasable topics (general advice, personal problems) or the user explicitly doesn't want suggestions. If a user rejects one product but is still shopping, suggest alternatives. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            should = result.get("should_suggest", False)
            logger.debug(f"LLM should_suggest decision: {should} - {result.get('reasoning', '')}")
            return should
            
        except Exception as e:
            logger.debug(f"LLM should_suggest failed: {e}", exc_info=True)
            # Fallback: suggest if topic is detected
            return detected_topic is not None
    
    async def _find_relevant_product(
        self,
        conversation_context: str,
        user_profile: Optional[Dict[str, Any]],
        detected_topic: Optional[str],
        rejected_products: Optional[List[str]] = None,
        previous_topics: Optional[List[str]] = None
    ) -> Optional[PredictiveSuggestion]:
        """
        Find a relevant product based on conversation context.
        
        Uses LLM to enhance the search query, then searches items_index.
        """
        try:
            logger.debug("Starting product search")
            logger.debug(f"Original context: {conversation_context[:100]}...")
            logger.debug(f"Detected topic: {detected_topic}")
            
            # Remove mentions of rejected products from context
            cleaned_context = conversation_context
            if rejected_products:
                for rejected in rejected_products:
                    cleaned_context = cleaned_context.replace(rejected, "")
                logger.debug(f"Cleaned context (removed rejected products): {cleaned_context[:100]}...")
            
            # Use LLM to enhance the search query based on context and topic
            # This also identifies the product type for category filtering
            search_result = await self._enhance_search_query_with_llm(
                cleaned_context, 
                detected_topic,
                rejected_products
            )
            
            search_query = search_result.get("search_query", cleaned_context)
            product_type = search_result.get("product_type", "unknown")
            
            logger.debug(f"Enhanced search query: {search_query[:200]}...")
            logger.debug(f"LLM identified product type: {product_type}")
            
            # Map product type to category filter
            category_filter = self._map_product_type_to_category(product_type)
            if category_filter:
                logger.debug(f"Filtering by category: {category_filter}")
            
            # Generate embedding for search
            logger.debug("Generating embedding for search query")
            search_embedding = await embedding_service.embed_text(search_query)
            logger.debug(f"Embedding generated (dimension: {len(search_embedding)})")
            
            # Combine with user profile if available
            if user_profile:
                logger.debug("User profile found, combining with search embedding")
                user_vector = user_profile["values"]
                # Weighted combination: 70% conversation, 30% user profile
                search_embedding = [
                    0.7 * s + 0.3 * u
                    for s, u in zip(search_embedding, user_vector)
                ]
                logger.debug("Combined embedding (70% search, 30% user profile)")
            else:
                logger.debug("No user profile found, using search embedding only")
            
            # Search items_index with category filter
            logger.debug(f"Searching items_index (threshold: {self.MIN_SIMILARITY_THRESHOLD})")
            search_results = await pinecone_service.query_items(
                vector=search_embedding,
                top_k=10,  # Get more results since we're filtering by category
                filter=category_filter
            )
            
            logger.debug(f"Search completed, found {len(search_results.matches) if search_results.matches else 0} matches")
            
            if not search_results.matches:
                logger.debug("No search results found - items_index may be empty or query didn't match")
                return None
            
            # Filter by similarity threshold and user preferences
            logger.debug(f"Evaluating {len(search_results.matches)} matches against threshold {self.MIN_SIMILARITY_THRESHOLD}")
            best_match = None
            for i, match in enumerate(search_results.matches):
                logger.debug(f"Match {i+1}: {match.id}, score={match.score:.4f}, threshold={self.MIN_SIMILARITY_THRESHOLD}, passes={match.score >= self.MIN_SIMILARITY_THRESHOLD}")
                
                if match.score < self.MIN_SIMILARITY_THRESHOLD:
                    logger.debug(f"Rejected {match.id}: score {match.score:.4f} below threshold {self.MIN_SIMILARITY_THRESHOLD}")
                    continue
                
                # Skip if user has disliked this item
                if user_profile:
                    disliked_items = user_profile.get("metadata", {}).get("disliked_items", [])
                    if match.id in disliked_items:
                        logger.debug(f"Rejected {match.id}: item is in user's disliked items")
                        continue
                
                # Skip if this product was rejected/mentioned negatively in conversation
                if rejected_products:
                    item_name = (match.metadata or {}).get("name", "").lower()
                    item_id = match.id.lower()
                    is_rejected = False
                    
                    for rejected in rejected_products:
                        rejected_lower = rejected.lower()
                        # Check if rejected product name appears in item name or ID
                        if rejected_lower in item_name or rejected_lower in item_id:
                            logger.debug(f"Rejected {match.id}: user mentioned '{rejected}' negatively in conversation")
                            is_rejected = True
                            break
                        # Check for partial matches (e.g., "Frame" matches "The Frame", "Frame TV")
                        # Split rejected name into words and check if any significant word appears in item name
                        rejected_words = rejected_lower.split()
                        for word in rejected_words:
                            if len(word) > 3 and word in item_name:  # Only check words longer than 3 chars to avoid false matches
                                logger.debug(f"Rejected {match.id}: contains rejected word '{word}' from '{rejected}'")
                                is_rejected = True
                                break
                        # Special case: "Frame" or "Frame TV" should match "The Frame"
                        if "frame" in rejected_lower and "frame" in item_name:
                            logger.debug(f"Rejected {match.id}: user rejected Frame TV (matched 'frame' keyword)")
                            is_rejected = True
                            break
                    
                    if is_rejected:
                        continue
                
                logger.debug(f"Accepted {match.id} as best match (score: {match.score:.4f})")
                best_match = match
                break
            
            if not best_match:
                logger.debug("No match passed threshold/filtering - all matches were below threshold or filtered out")
                return None
            
            logger.debug(f"Selected best match: {best_match.id} (score: {best_match.score:.4f})")
            
            # Generate conversational suggestion text using LLM for natural, friend-like tone
            # Use CURRENT context for the suggestion text (not enriched) to ensure it matches current intent
            # Pass previous_topics for style matching only
            metadata = best_match.metadata or {}
            suggestion_text = await self._generate_conversational_suggestion_llm(
                conversation_context=conversation_context,  # Use CURRENT context only
                product_name=metadata.get("name", "this TV"),
                product_price=metadata.get("price", 0),
                product_description=metadata.get("description", ""),
                product_brand=metadata.get("brand", ""),
                detected_topic=detected_topic,
                rejected_products=rejected_products,
                previous_topics=previous_topics  # Pass conversation history for style matching only
            )
            
            # Extract all available metadata fields
            logger.debug(f"Product metadata available: {list(metadata.keys())}")
            url_value = metadata.get("url")
            logger.debug(f"URL value from metadata: '{url_value}' (type: {type(url_value)})")
            
            return PredictiveSuggestion(
                text=suggestion_text,
                partner=None,
                is_sponsored=False,
                item_id=best_match.id,
                item_name=metadata.get("name"),
                item_price=metadata.get("price", 0),
                item_url=url_value if url_value else None  # URL field from metadata, convert empty string to None
            )
        except Exception as e:
            # Log error but don't fail
            logger.debug(f"Exception occurred while finding relevant product: {e}", exc_info=True)
            return None
    
    def _generate_conversational_suggestion(
        self,
        conversation_context: str,
        product_name: str,
        product_price: float,
        detected_topic: Optional[str],
        similarity_score: float
    ) -> str:
        """
        Generate a natural, conversational suggestion text.
        
        The goal is to make suggestions feel helpful and contextual, not pushy.
        """
        text_lower = conversation_context.lower()
        
        # Extract size if mentioned
        size_mentioned = None
        for size in ["32", "43", "50", "55", "65", "75", "85", "98"]:
            if f"{size}\"" in text_lower or f"{size}-inch" in text_lower:
                size_mentioned = size
                break
        
        # Different suggestion styles based on context
        if "looking for" in text_lower or "need" in text_lower:
            if size_mentioned:
                return f"Since you're looking for a {size_mentioned}\" TV, you might want to check out the {product_name}. It's ${product_price:.0f} and seems like a good fit for what you're describing."
            else:
                return f"Based on what you're looking for, the {product_name} might be worth considering. It's ${product_price:.0f} and could be a great match."
        
        elif "wondering" in text_lower or "thinking about" in text_lower:
            return f"If you're thinking about upgrading, the {product_name} (${product_price:.0f}) could be a solid option. It aligns well with what you mentioned."
        
        elif "help" in text_lower or "recommend" in text_lower:
            return f"I'd suggest checking out the {product_name} (${product_price:.0f}). It seems to match what you're looking for."
        
        elif detected_topic == "gaming":
            return f"For gaming, you might want to consider the {product_name} (${product_price:.0f}). It has features that work well for gaming."
        
        elif detected_topic == "art_design":
            return f"If aesthetics matter to you, the {product_name} (${product_price:.0f}) has a design-focused approach that might appeal to you."
        
        elif detected_topic == "apartment":
            return f"For smaller spaces, the {product_name} (${product_price:.0f}) could work well. It's designed with compact living in mind."
        
        else:
            # Default conversational suggestion
            return f"You might find the {product_name} (${product_price:.0f}) interesting. It seems relevant to what you're discussing."
    
    async def _generate_conversational_suggestion_llm(
        self,
        conversation_context: str,
        product_name: str,
        product_price: float,
        product_description: str,
        product_brand: str,
        detected_topic: Optional[str],
        rejected_products: Optional[List[str]] = None,
        previous_topics: Optional[List[str]] = None
    ) -> str:
        """
        Generate a natural, conversational suggestion using LLM.
        
        The goal is to make suggestions feel like a friend making a recommendation,
        matching the user's conversation style and being contextually relevant.
        """
        try:
            rejected_context = ""
            if rejected_products:
                rejected_context = f" The user previously mentioned/rejected: {', '.join(rejected_products)}. If they said something was 'too expensive', naturally mention that this is more affordable."
            
            topic_context = f" The conversation topic is: {detected_topic}." if detected_topic else ""
            
            # Include conversation history to match user's style
            style_context = ""
            if previous_topics and isinstance(previous_topics, list) and len(previous_topics) > 0:
                recent_history = ". ".join(previous_topics[-3:])  # Last 3 messages for style reference
                style_context = f"\n\nPrevious conversation (for style reference): \"{recent_history}\""
            
            prompt = f"""Generate a natural, conversational product suggestion that feels like a friend making a recommendation.

Current conversation: "{conversation_context}"{topic_context}{rejected_context}{style_context}

Product to suggest:
- Name: {product_name}
- Price: ${product_price:.2f}
- Brand: {product_brand}
- Description: {product_description[:200]}

Create a suggestion that:
- Feels natural and conversational, like a friend would say it
- Matches the tone and style of the previous conversation (if provided)
- Is contextually relevant to what the user is currently discussing
- If they rejected something for being too expensive, naturally mention this is more affordable
- If they liked aspects of a rejected product, acknowledge that and explain how this product has similar qualities
- Keep it brief (1-2 sentences)
- Don't be pushy or salesy
- Feel helpful and genuine
- Use the same conversational style as the user's previous messages (casual, formal, etc.)

Examples:
- If user said "I liked The Frame but it was too expensive" → "If you liked The Frame's aesthetic, the {product_name} might be a good alternative. It's ${product_price:.0f} and has a similar design-focused approach."
- If user is just browsing → "The {product_name} could be worth checking out. It's ${product_price:.0f} and seems to match what you're looking for."
- If user asked for help → "You might want to consider the {product_name}. At ${product_price:.0f}, it's a solid option that fits your needs."

Respond with ONLY the suggestion text (no quotes, no JSON, just the natural conversational text):

Suggestion:"""

            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful friend making product recommendations. Generate natural, conversational suggestions that match the user's conversation style. Be brief, helpful, and genuine - never pushy or salesy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Higher temperature for more natural variation
                max_tokens=150
            )
            
            suggestion = response.choices[0].message.content.strip()
            # Remove any quotes if the LLM added them
            if suggestion.startswith('"') and suggestion.endswith('"'):
                suggestion = suggestion[1:-1]
            if suggestion.startswith("'") and suggestion.endswith("'"):
                suggestion = suggestion[1:-1]
            
            logger.debug(f"Generated conversational suggestion: {suggestion}")
            return suggestion
            
        except Exception as e:
            logger.debug(f"LLM suggestion generation failed: {e}, using fallback", exc_info=True)
            # Fallback to simple suggestion
            return f"The {product_name} (${product_price:.0f}) might be worth considering. It seems relevant to what you're discussing."
    
    async def _get_partner_offer(self, topic: Optional[str], conversation_context: str) -> Optional[PredictiveSuggestion]:
        """Get a partner offer using LLM if appropriate (fallback)."""
        # For now, return None - partner offers can be added later if needed
        return None
    
    async def _detect_rejected_products(self, context: str) -> List[str]:
        """
        Use LLM to detect products that were mentioned negatively or rejected in the conversation.
        Also detects price-related rejections (too expensive, too much).
        """
        try:
            prompt = f"""Analyze this conversation and identify any products that were mentioned negatively or rejected.

Conversation: "{context}"

Respond with ONLY a JSON object:
{{
  "rejected_products": ["product name 1", "product name 2"] or [],
  "reasoning": "brief explanation"
}}

Include products that were:
- Explicitly rejected or disliked
- Mentioned as "too expensive", "too much", "out of budget", "can't afford"
- Said to be "not for me" or similar negative sentiment

If the user says they liked something but it was "too much" or "too expensive", that product should be in rejected_products.

If no products were rejected, return an empty array.

JSON response:"""

            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that identifies rejected or negatively mentioned products. Be thorough - if a user says they 'liked' a product but it was 'too expensive' or 'too much', that product is still REJECTED and should be in the list. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            rejected = result.get("rejected_products", [])
            if rejected:
                logger.debug(f"LLM detected rejected products: {rejected} - {result.get('reasoning', '')}")
            return rejected if isinstance(rejected, list) else []
            
        except Exception as e:
            logger.debug(f"LLM rejected products detection failed: {e}", exc_info=True)
            return []
    
    def _map_product_type_to_category(self, product_type: str) -> Optional[Dict[str, Any]]:
        """
        Map LLM-identified product type to Pinecone category filter.
        
        Returns a Pinecone filter dict or None if no filter should be applied.
        """
        if not product_type or product_type.lower() == "unknown":
            return None
        
        product_type_lower = product_type.lower()
        
        # Map product types to category filters
        if "cruise" in product_type_lower or "travel" in product_type_lower:
            # Filter for cruises category
            return {"category": {"$eq": "cruises"}}
        elif "furniture" in product_type_lower:
            # Filter for any furniture category - use $in for all furniture subcategories
            return {"category": {"$in": ["furniture_living_room", "furniture_bedroom", "furniture_kitchen", "furniture_bathroom"]}}
        elif "tv" in product_type_lower or "television" in product_type_lower or "electronic" in product_type_lower:
            # Filter for televisions category
            return {"category": {"$eq": "televisions"}}
        elif "experience" in product_type_lower:
            # Filter for any experience category - use $in for all experience subcategories
            return {"category": {"$in": ["experiences_outdoor", "experiences_cultural", "experiences_food", "experiences_wellness", "experiences_entertainment"]}}
        
        return None
    
    async def _enhance_search_query_with_llm(
        self,
        conversation_context: str,
        detected_topic: Optional[str],
        rejected_products: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to enhance the search query based on conversation context and topic.
        This creates a better search query for product matching.
        """
        try:
            rejected_text = f" Rejected products (DO NOT include these): {', '.join(rejected_products)}" if rejected_products else ""
            topic_text = f" Detected topic: {detected_topic}." if detected_topic else ""
            
            # Check if user mentioned price constraints
            price_context = ""
            context_lower = conversation_context.lower()
            if any(phrase in context_lower for phrase in ["too much", "too expensive", "out of budget", "can't afford", "cheaper", "less expensive", "affordable"]):
                price_context = " IMPORTANT: The user mentioned price concerns. Find similar products but at LOWER prices. If they liked a product but said it was too expensive, find alternatives with similar features/design but cheaper."
            
            prompt = f"""Analyze this conversation and create an enhanced search query for finding relevant products or services.

Conversation: "{conversation_context}"{topic_text}{rejected_text}{price_context}

STEP 1 - IDENTIFY PRODUCT/SERVICE TYPE: First, infer what TYPE of product or service the user is looking for based on the conversation context. Consider:
- What is the user actually trying to accomplish or obtain?
- What category of product or service would fulfill their need?
- Examples: vacation/travel needs → cruises/travel packages, home furnishing needs → furniture, entertainment/display needs → TVs/electronics, activity/learning needs → experiences
- Use context and intent, not just keywords

STEP 2 - REASONING: Infer from the conversation:
- What TYPE of product/service are they looking for? (CRITICAL - must match the right category)
- What did the user LIKE about any mentioned products? (e.g., design, aesthetic, features, size, brand, destination)
- What did the user DISLIKE or reject? (e.g., price, specific features, size, location)
- What are they ACTUALLY looking for? (e.g., similar design but cheaper, different size, specific destination, specific features)

STEP 3 - SEARCH QUERY: Create a search query that:
- Reflects the identified product/service type naturally (don't force keywords, but ensure the query captures the right category)
- Includes the POSITIVE aspects the user liked (if they said "I liked The Frame", include: aesthetic, art mode, decorative, stylish design)
- EXCLUDES the NEGATIVE aspects (if they said "too expensive", emphasize: affordable, budget-friendly, lower price)
- NEVER includes rejected product names in the search query
- Focuses on finding ALTERNATIVES that match what they liked but address what they didn't like
- Use natural language that would match product descriptions in the catalog

Available product categories include: televisions, furniture (living_room, bedroom, kitchen, bathroom), cruises, experiences (outdoor, cultural, food, wellness, entertainment).

Examples:
- "I need a vacation" 
  → Product type: CRUISES/TRAVEL
  → Reasoning: User wants a vacation/travel experience
  → Query: "cruise travel package vacation trip destination holiday all-inclusive"
  
- "Looking for a new sofa for my living room"
  → Product type: FURNITURE
  → Reasoning: Needs living room furniture, specifically a sofa
  → Query: "sofa couch living room furniture comfortable seating modern"
  
- "I liked The Frame but it was too expensive" 
  → Reasoning: Liked aesthetic/art mode design, disliked price
  → Query: "aesthetic television TV, art mode, decorative design, stylish, modern, minimalist, affordable, budget-friendly, lower price, similar aesthetic to Frame TV but cheaper"
  
- "I checked out The Frame and wasn't impressed"
  → Reasoning: Rejected The Frame entirely, but may still want aesthetic TVs
  → Query: "aesthetic television TV, art mode, decorative design, stylish, modern, alternative to Frame TV"
  
- "Looking for a 55 inch TV for gaming"
  → Reasoning: Needs 55 inch size, gaming features
  → Query: "55 inch television TV, gaming features, low input lag, Game Mode"

Respond with ONLY a JSON object:
{{
  "product_type": "the type of product/service (cruises, furniture, TVs/electronics, experiences, etc.)",
  "reasoning": "brief explanation of what user liked/disliked and what they're looking for",
  "search_query": "enhanced search query text that captures their needs and includes the correct product type keywords"
}}

JSON response:"""

            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that creates optimized search queries for product/service matching. CRITICALLY IMPORTANT: You must correctly infer the TYPE of product or service the user is looking for based on their intent and context, not just keywords. Understand what they're trying to accomplish (vacation → cruises, home furnishing → furniture, entertainment → TVs, activities → experiences). Create natural search queries that reflect the user's intent and would match relevant product descriptions. When users say they liked a product but it was 'too expensive' or 'too much', create queries that find similar products (same features, design, aesthetic) but at lower prices. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=250,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            enhanced_query = result.get("search_query", conversation_context)
            product_type = result.get("product_type", "unknown")
            reasoning = result.get("reasoning", "")
            logger.debug(f"LLM identified product type: {product_type}")
            logger.debug(f"LLM reasoning: {reasoning}")
            logger.debug(f"LLM enhanced query: {enhanced_query}")
            
            return {
                "search_query": enhanced_query,
                "product_type": product_type,
                "reasoning": reasoning
            }
            
        except Exception as e:
            logger.debug(f"LLM query enhancement failed: {e}, using original context", exc_info=True)
            return {
                "search_query": conversation_context,
                "product_type": "unknown",
                "reasoning": "LLM query enhancement failed"
            }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


# Global instance
predictive_module = PredictiveModule()
