"""MCP Server for ChatGPT Apps SDK integration."""
import asyncio
import httpx
import json
import sys
from app.config import settings


# Backend API base URL
# Use backend_url from settings if provided, otherwise default to localhost
if settings.backend_url:
    BACKEND_URL = settings.backend_url
else:
    BACKEND_URL = f"http://localhost:{settings.port}/api"


# Tool definitions
TOOLS = [
    {
        "name": "recommend",
        "description": (
            "Generate product recommendations based on user query and profile. "
            "Returns a list of recommended products with details like name, price, "
            "similarity score, and rationale."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Unique identifier for the user"
                },
                "query": {
                    "type": "string",
                    "description": "User's search query or request for recommendations"
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional session identifier for tracking"
                }
            },
            "required": ["user_id", "query"]
        }
    },
    {
        "name": "submit_feedback",
        "description": (
            "Submit user feedback (like or dislike) for a product recommendation. "
            "This updates the user's profile to improve future recommendations."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Unique identifier for the user"
                },
                "item_id": {
                    "type": "string",
                    "description": "Identifier of the product item"
                },
                "feedback_type": {
                    "type": "string",
                    "enum": ["like", "dislike"],
                    "description": "Type of feedback: 'like' or 'dislike'"
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional session identifier"
                }
            },
            "required": ["user_id", "item_id", "feedback_type"]
        }
    },
    {
        "name": "get_user_profile",
        "description": (
            "Retrieve user profile information including preferences, "
            "liked/disliked items, and metadata like age range, city, style preferences."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Unique identifier for the user"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "predictive_suggest",
        "description": (
            "Generate predictive suggestions based on conversation context. "
            "Detects topics in the conversation and suggests relevant partner offers "
            "or recommendations. This is a P2 feature for contextual suggestions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Unique identifier for the user"
                },
                "conversation_context": {
                    "type": "string",
                    "description": "The conversation context or user message to analyze for suggestions"
                },
                "detected_topic": {
                    "type": "string",
                    "description": "Optional pre-detected topic (e.g., 'gaming', 'entertainment', 'art_design'). If not provided, will be detected automatically."
                },
                "previous_topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of previous conversation messages/context strings (not topic names). These will be combined with conversation_context to build richer context for better suggestions. Use this to emulate an ongoing ChatGPT session."
                },
                "conversation_history": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["user", "assistant"]},
                            "content": {"type": "string"}
                        },
                        "required": ["role", "content"]
                    },
                    "description": "Optional full conversation history as array of {role, content} objects. If provided, recent messages will be used to build richer context."
                }
            },
            "required": ["user_id", "conversation_context"]
        }
    }
]


class PineconeScoutMCPServer:
    """MCP Server that exposes recommendation tools to ChatGPT."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.client = httpx.AsyncClient(base_url=BACKEND_URL, timeout=30.0)
    
    async def _handle_tool_call(self, name: str, arguments: dict) -> dict:
        """Handle tool calls from ChatGPT."""
        try:
            if name == "recommend":
                result = await self._handle_recommend(arguments)
            elif name == "submit_feedback":
                result = await self._handle_feedback(arguments)
            elif name == "get_user_profile":
                result = await self._handle_get_profile(arguments)
            elif name == "predictive_suggest":
                result = await self._handle_predictive_suggest(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": result if isinstance(result, str) else json.dumps(result)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error calling tool {name}: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _handle_recommend(self, arguments: dict) -> str:
        """Handle recommend tool call."""
        user_id = arguments.get("user_id")
        query = arguments.get("query")
        session_id = arguments.get("session_id")
        
        response = await self.client.post(
            "/recommend",
            json={
                "user_id": user_id,
                "query": query,
                "session_id": session_id
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Format recommendations for ChatGPT
        recommendations = data.get("recommendations", [])
        user_context = data.get("user_context", {})
        
        result_text = "Here are my recommendations:\n\n"
        
        if user_context.get("memory_recall"):
            result_text += f"💡 {user_context['memory_recall']}\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            result_text += f"{i}. **{rec['name']}**\n"
            result_text += f"   - Price: ${rec['price']:.2f}\n"
            result_text += f"   - Similarity Score: {rec.get('similarity_score', 0):.3f}\n"
            result_text += f"   - {rec['rationale']}\n"
            if rec.get("similar_user_signal"):
                result_text += f"   - 🔥 Popular with similar users\n"
            result_text += f"   - Item ID: {rec['item_id']}\n\n"
        
        return result_text
    
    async def _handle_feedback(self, arguments: dict) -> str:
        """Handle submit_feedback tool call."""
        user_id = arguments.get("user_id")
        item_id = arguments.get("item_id")
        feedback_type = arguments.get("feedback_type")
        session_id = arguments.get("session_id")
        
        response = await self.client.post(
            "/feedback",
            json={
                "user_id": user_id,
                "item_id": item_id,
                "feedback_type": feedback_type,
                "session_id": session_id
            }
        )
        response.raise_for_status()
        data = response.json()
        
        emoji = "👍" if feedback_type == "like" else "👎"
        result_text = f"{emoji} Thank you! I've saved your {feedback_type} for this item. "
        result_text += "I'll keep this in mind for future recommendations."
        
        return result_text
    
    async def _handle_get_profile(self, arguments: dict) -> str:
        """Handle get_user_profile tool call."""
        user_id = arguments.get("user_id")
        
        response = await self.client.get(
            "/profile",
            params={"user_id": user_id}
        )
        response.raise_for_status()
        data = response.json()
        
        metadata = data.get("metadata", {})
        
        result_text = f"**User Profile for {user_id}**\n\n"
        result_text += f"Preferences Count: {data.get('preferences_count', 0)}\n"
        result_text += f"Last Updated: {data.get('last_updated', 'N/A')}\n\n"
        
        if metadata.get("age_range"):
            result_text += f"Age Range: {metadata['age_range']}\n"
        if metadata.get("household_size"):
            result_text += f"Household Size: {metadata['household_size']}\n"
        if metadata.get("city"):
            result_text += f"City: {metadata['city']}\n"
        if metadata.get("style_preference"):
            result_text += f"Style Preference: {metadata['style_preference']}\n"
        
        liked = metadata.get("liked_items", [])
        disliked = metadata.get("disliked_items", [])
        
        if liked:
            result_text += f"\n✅ Liked Items ({len(liked)}): {', '.join(liked[:5])}"
            if len(liked) > 5:
                result_text += f" and {len(liked) - 5} more"
            result_text += "\n"
        
        if disliked:
            result_text += f"\n❌ Disliked Items ({len(disliked)}): {', '.join(disliked[:5])}"
            if len(disliked) > 5:
                result_text += f" and {len(disliked) - 5} more"
            result_text += "\n"
        
        return result_text
    
    async def _handle_predictive_suggest(self, arguments: dict) -> str:
        """Handle predictive_suggest tool call."""
        user_id = arguments.get("user_id")
        conversation_context = arguments.get("conversation_context")
        detected_topic = arguments.get("detected_topic")
        previous_topics = arguments.get("previous_topics")  # Array of topic strings
        conversation_history = arguments.get("conversation_history")  # Full conversation history
        
        # Validate required fields
        if not user_id or not isinstance(user_id, str):
            return "Error: user_id is required and must be a string"
        
        # Handle conversation context - can come from direct input or conversation history
        # Extract previous_topics from conversation_history if provided
        if conversation_history and isinstance(conversation_history, list) and len(conversation_history) > 0:
            # Extract recent messages from conversation history
            # Get last 5-7 messages for context (mix of user and assistant for natural flow)
            recent_messages = conversation_history[-7:] if len(conversation_history) > 7 else conversation_history
            
            # Build previous_topics from recent messages (as conversation strings)
            if not previous_topics:
                previous_topics = []
            
            # Extract message content from recent history
            for msg in recent_messages[:-1]:  # Exclude the last message (current context)
                if isinstance(msg, dict) and msg.get("content"):
                    # Include both user and assistant messages for full context
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if content:
                        previous_topics.append(content)
            
            # Use last user message as conversation_context if not provided
            # IMPORTANT: Only use the LAST user message, not the full history
            if not conversation_context:
                for msg in reversed(recent_messages):
                    if isinstance(msg, dict) and msg.get("role") == "user" and msg.get("content"):
                        conversation_context = msg.get("content")
                        break
            else:
                # If conversation_context is provided, ensure it's only the current message
                # Extract just the last sentence if it contains multiple messages
                # This handles cases where the context might have been concatenated
                if conversation_context and len(conversation_context) > 200:
                    # If context is very long, it might contain multiple messages
                    # Try to extract just the last part (most recent message)
                    parts = conversation_context.split(".. ")
                    if len(parts) > 1:
                        # Use the last part as it's likely the most recent message
                        conversation_context = parts[-1].strip()
                        # Log the extraction (using print since logger may not be available)
                        print(f"[MCP] Extracted last message from long context: {conversation_context[:100]}...")
        
        if not conversation_context or not isinstance(conversation_context, str):
            return "Error: conversation_context is required and must be a string (or provide conversation_history)"
        
        # Normalize optional fields
        # Convert empty string to None for detected_topic
        if detected_topic == "" or (detected_topic is not None and not isinstance(detected_topic, str)):
            detected_topic = None
        
        # Ensure previous_topics is a list of conversation strings or None
        if previous_topics is not None:
            if not isinstance(previous_topics, list):
                previous_topics = None
            elif len(previous_topics) == 0:
                previous_topics = None
            else:
                # Ensure all items are strings (conversation messages)
                previous_topics = [str(t).strip() for t in previous_topics if t and str(t).strip()]
                if len(previous_topics) == 0:
                    previous_topics = None
                else:
                    # Limit to last 5 messages to avoid overly long context
                    previous_topics = previous_topics[-5:]
        
        # Build request payload
        payload = {
            "user_id": str(user_id),
            "conversation_context": str(conversation_context)
        }
        
        # Only include optional fields if they have values
        if detected_topic:
            payload["detected_topic"] = str(detected_topic)
        if previous_topics:
            payload["previous_topics"] = previous_topics
        
        try:
            response = await self.client.post(
                "/predictive_suggest",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            # Better error handling for 422 validation errors
            if e.response.status_code == 422:
                error_detail = e.response.json().get("detail", "Validation error")
                return f"Validation error: {error_detail}. Please check that user_id and conversation_context are provided."
            raise
        
        suggestion = data.get("suggestion")
        if not suggestion:
            # Return empty string so ChatGPT doesn't show anything if no suggestion
            # This is expected behavior when no appropriate suggestion is found
            return ""
        
        # Format suggestion naturally
        result_text = f"{suggestion['text']}"
        
        # If it's a product suggestion, add item details
        if suggestion.get("item_id") and not suggestion.get("is_sponsored"):
            result_text += f"\n\n**{suggestion.get('item_name', 'Product')}** - ${suggestion.get('item_price', 0):.2f}"
            result_text += f"\nItem ID: {suggestion['item_id']}"
            # Add URL if available (check for both None and empty string)
            item_url = suggestion.get("item_url")
            if item_url and item_url.strip():  # Check for non-empty string
                result_text += f"\nURL: {item_url}"
        
        # Add sponsored label if applicable
        if suggestion.get("is_sponsored"):
            result_text += "\n\n*[Sponsored Partner Offer]*"
            if data.get("opt_in_required"):
                result_text += " *Opt-in required*"
        
        return result_text
    
    async def handle_request(self, request: dict) -> dict:
        """Handle MCP protocol requests."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                # MCP initialization
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "pinecone-scout",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self._handle_tool_call(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }


async def main():
    """Main entry point for the MCP server - reads from stdin, writes to stdout."""
    server = PineconeScoutMCPServer()
    
    # Read from stdin line by line (MCP uses JSON-RPC over stdio)
    for line in sys.stdin:
        if not line.strip():
            continue
            
        request = None
        try:
            request = json.loads(line.strip())
            
            # Skip notifications (requests without id)
            if "id" not in request:
                continue
                
            response = await server.handle_request(request)
            
            # Write response to stdout
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            # Send parse error response
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if request else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())

