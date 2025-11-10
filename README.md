# Pinecone Scout Backend

A FastAPI-based backend service for ChatGPT-powered product recommendations using Pinecone vector database, integrated with OpenAI's Apps SDK.

## Features

- **Core Recommendation Engine (P0)**: Semantic search-based recommendations using user queries and profiles
- **Collaborative Filtering (P1)**: Recommendations enhanced by similar user preferences
- **Predictive Suggestions (P2)**: Context-aware suggestions based on conversation topics
- **User Profile Management**: Persistent user preferences stored in Pinecone
- **Feedback System**: Like/dislike feedback that updates user profiles
- **ChatGPT Apps SDK Integration**: MCP server for seamless ChatGPT integration

## Architecture

```bash
┌─────────────────────────────────────┐
│      FastAPI Application            │
│  ┌───────────────────────────────┐  │
│  │  API Endpoints                │  │
│  │  - POST /recommend            │  │
│  │  - POST /feedback             │  │
│  │  - GET  /profile              │  │
│  │  - POST /predictive_suggest   │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Services                     │  │
│  │  - Recommendation Engine      │  │
│  │  - Collaborative Filtering    │  │
│  │  - User Profile Manager       │  │
│  │  - Embedding Service (OpenAI) │  │
│  │  - Pinecone Service           │  │
│  └───────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼──────────┐  ┌──────▼──────────┐
│ users_index  │  │  items_index    │
│ (Pinecone)   │  │  (Pinecone)     │
└──────────────┘  └─────────────────┘
         │
         │ MCP Server
         ▼
┌─────────────────────┐
│   ChatGPT Apps SDK  │
│   (Frontend UI)     │
└─────────────────────┘
```

## Setup

### Prerequisites

- Python 3.9+
- Pinecone API key
- OpenAI API key

### Installation

1. Clone the repository:

    ```bash
    git clone <repository-url>
    cd pinecone-scout
    ```

2. Create a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file from `.env.example`:

    ```bash
    cp .env.example .env
    ```

5. Update `.env` with your API keys:

    ```env
    PINECONE_API_KEY=your_pinecone_api_key
    OPENAI_API_KEY=your_openai_api_key
    ```

## Running the Application

### Start the Backend Server

```bash
python run.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI) is available at `http://localhost:8000/docs`

### Connect to ChatGPT

1. **Start the MCP Server**: The MCP server is configured to run via `python -m app.mcp_server`
2. **Configure ChatGPT**: Add the MCP server configuration from `chatgpt_app/mcp_config.json`
3. **Load the App**: Use the app manifest in `chatgpt_app/app_manifest.json`

See [chatgpt_app/README.md](chatgpt_app/README.md) for detailed ChatGPT integration instructions.

## API Endpoints

### POST /api/recommend

Generate product recommendations based on user query.

**Request:**

```json
{
  "user_id": "user_123",
  "query": "Looking for a 50-inch TV for my apartment",
  "session_id": "session_456"
}
```

**Response:**

```json
{
  "recommendations": [
    {
      "item_id": "item_001",
      "name": "Samsung Frame TV 50\"",
      "price": 1299.0,
      "similarity_score": 0.89,
      "rationale": "Matches your search: Art mode, slim design...",
      "similar_user_signal": false
    }
  ],
  "user_context": {
    "profile_updated": false,
    "memory_recall": "You previously liked 2 item(s)"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### POST /api/feedback

Submit user feedback (like/dislike) for a product.

**Request:**

```json
{
  "user_id": "user_123",
  "item_id": "item_001",
  "feedback_type": "like",
  "session_id": "session_456"
}
```

### GET /api/profile

Retrieve user profile information.

**Query Parameters:**

- `user_id`: User identifier

**Response:**

```json
{
  "user_id": "user_123",
  "metadata": {
    "age_range": "25-34",
    "household_size": "2-3",
    "city": "New York",
    "style_preference": "modern",
    "liked_items": ["item_001", "item_045"],
    "disliked_items": ["item_023"],
    "last_updated": "2024-01-15T10:30:00Z"
  },
  "preferences_count": 3,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### POST /api/predictive_suggest

Generate predictive suggestions based on conversation context.

**Request:**

```json
{
  "user_id": "user_123",
  "conversation_context": "I'm planning a trip to Europe",
  "detected_topic": "travel"
}
```

## ChatGPT Integration

The app includes a complete ChatGPT Apps SDK integration:

- **MCP Server** (`app/mcp_server.py`): Exposes backend API as tools to ChatGPT
- **Web Component** (`chatgpt_app/index.html`): UI for displaying recommendations in ChatGPT
- **Configuration Files**: MCP config and app manifest for ChatGPT integration

### Available ChatGPT Tools

1. **recommend**: Generate product recommendations
2. **submit_feedback**: Submit like/dislike feedback
3. **get_user_profile**: Retrieve user profile
4. **predictive_suggest**: Get contextual suggestions

See [chatgpt_app/README.md](chatgpt_app/README.md) for setup instructions.

## Project Structure

```bash
pinecone-scout/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models.py            # Pydantic models
│   ├── mcp_server.py        # MCP server for ChatGPT
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoints
│   └── services/
│       ├── __init__.py
│       ├── pinecone_service.py      # Pinecone operations
│       ├── embedding_service.py     # OpenAI embeddings
│       ├── user_profile_manager.py   # User profile management
│       ├── recommendation_engine.py # Core recommendation logic
│       ├── collaborative_filtering.py # Collaborative filtering (P1)
│       └── predictive_module.py      # Predictive suggestions (P2)
├── chatgpt_app/
│   ├── index.html           # Web component UI
│   ├── mcp_config.json      # MCP server configuration
│   ├── app_manifest.json    # App manifest
│   └── README.md            # ChatGPT integration guide
├── requirements.txt
├── .env.example
├── .gitignore
├── run.py
└── README.md
```

## Development

### Code Style

This project follows PEP 8 style guidelines. Consider using:

- `black` for code formatting
- `flake8` or `pylint` for linting
- `mypy` for type checking

### Testing

(To be implemented)

Run tests with:

```bash
pytest
```

## References

- [OpenAI Apps SDK Documentation](https://developers.openai.com/apps-sdk)
- [Pinecone Python SDK](https://docs.pinecone.io/reference/python-sdk)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## License

MIT License
