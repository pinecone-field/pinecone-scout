# ChatGPT App Integration

This directory contains the ChatGPT Apps SDK integration for the Pinecone Scout service.

## Structure

- `index.html` - Web component UI for displaying recommendations in ChatGPT
- `mcp_config.json` - MCP server configuration
- `app_manifest.json` - App manifest for ChatGPT Apps SDK

## Setup

### 1. Start the Backend Server

Make sure your FastAPI backend is running:

```bash
python run.py
# or
uvicorn app.main:app --reload
```

The backend should be accessible at `http://localhost:8000`

### 2. Configure MCP Server

The MCP server is configured to connect to the backend API. Update the `BACKEND_URL` in `app/mcp_server.py` if your backend is running on a different host/port.

### 3. Connect to ChatGPT

1. **Developer Mode**: Enable Developer Mode in ChatGPT
2. **Load MCP Server**: Configure ChatGPT to use the MCP server defined in `mcp_config.json`
3. **Load App**: Use the app manifest to register the app with ChatGPT

### 4. Test the Integration

Once connected, you can test the integration by:

1. Asking ChatGPT for recommendations: "I'm looking for a 50-inch TV"
2. ChatGPT will call the `recommend` tool
3. The recommendations will be displayed in the web component
4. Users can like/dislike items using the feedback buttons

## Tools Available

### recommend

Generate product recommendations based on user query.

**Example:**

```text
User: "I'm looking for a 50-inch TV for my apartment"
ChatGPT calls: recommend(user_id="user_123", query="50-inch TV for apartment")
```

### submit_feedback

Submit user feedback (like/dislike) for a product.

**Example:**

```text
User clicks "👍 Like" on a recommendation
ChatGPT calls: submit_feedback(user_id="user_123", item_id="item_001", feedback_type="like")
```

### get_user_profile

Retrieve user profile information.

**Example:**

```text
User: "What are my preferences?"
ChatGPT calls: get_user_profile(user_id="user_123")
```

### predictive_suggest

Generate contextual suggestions based on conversation.

**Example:**

```text
User: "I'm planning a trip to Europe"
ChatGPT calls: predictive_suggest(user_id="user_123", conversation_context="planning a trip to Europe")
```

## Development

### Local Testing

1. Serve the HTML file locally:

    ```bash
    cd chatgpt_app
    python -m http.server 8080
    ```

2. Update the MCP server to point to your local backend

3. Test the web component in isolation before integrating with ChatGPT

### Debugging

- Check browser console for JavaScript errors
- Check backend logs for API calls
- Use ChatGPT's developer tools to inspect tool calls

## Deployment

When ready for production:

1. Deploy the backend API to a public URL
2. Update `BACKEND_URL` in `mcp_server.py`
3. Deploy the HTML component to a CDN or static hosting
4. Update `app_manifest.json` with production URLs
5. Submit your app through OpenAI's app submission process

## References

- [OpenAI Apps SDK Documentation](https://developers.openai.com/apps-sdk)
- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [Apps SDK Examples](https://github.com/openai/apps-sdk-examples)
