# Testing Pinecone Scout MCP Server

## Using the MCP Inspector

The MCP Inspector is a tool for testing and debugging your MCP server before integrating with ChatGPT.

### Installation

First, install the MCP Inspector:

```bash
npm install -g @modelcontextprotocol/inspector
```

### Running with Standard Python (venv)

Since you're using a standard Python virtual environment (`.venv`), use this command:

```bash
npx @modelcontextprotocol/inspector \
  python \
  -m app.mcp_server
```

**From your project directory** (`/Users/cory/dev/pinecone-field/pinecone-scout`):

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Run the inspector
npx @modelcontextprotocol/inspector python -m app.mcp_server
```

### Running with uv (Alternative)

If you want to use `uv` instead, first install it:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then run:

```bash
npx @modelcontextprotocol/inspector \
  uv \
  --directory /Users/cory/dev/pinecone-field/pinecone-scout \
  run \
  python \
  -m app.mcp_server
```

### Setting Environment Variables

Make sure your environment variables are set. You can either:

Option 1: Export in your shell

```bash
export PINECONE_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"
npx @modelcontextprotocol/inspector python -m app.mcp_server
```

Option 2: Use a .env file
The MCP server will automatically load from `.env` if it exists in the project root.

Option 3: Pass via inspector

```bash
PINECONE_API_KEY="your_key" \
OPENAI_API_KEY="your_key" \
npx @modelcontextprotocol/inspector python -m app.mcp_server
```

### What to Expect

1. The inspector will start and show a web interface URL (usually `http://localhost:5173`)
2. Open that URL in your browser
3. You'll see a UI where you can:
   - List available tools
   - Call tools with parameters
   - See responses
   - Debug issues

### Testing Your Tools

In the inspector UI, you can test each tool:

1. **recommend**:

   ```json
   {
     "user_id": "test_user_123",
     "query": "I'm looking for a 50-inch TV"
   }
   ```

2. **submit_feedback**:

   ```json
   {
     "user_id": "test_user_123",
     "item_id": "item_001",
     "feedback_type": "like"
   }
   ```

3. **get_user_profile**:

   ```json
   {
     "user_id": "test_user_123"
   }
   ```

4. **predictive_suggest**:

   ```json
   {
     "user_id": "test_user_123",
     "conversation_context": "I'm planning a trip to Europe"
   }
   ```

### Troubleshooting

> **Error: Cannot find module 'app.mcp_server'**

- Make sure you're in the project root directory
- Ensure your virtual environment is activated
- Try using absolute path: `python -m /full/path/to/app/mcp_server`

> **Error: Backend connection failed**

- Make sure your FastAPI backend is running on port 8000
- Or update `BACKEND_URL` in `app/mcp_server.py` to point to your backend

> **Error: Environment variables not found**

- Export them in your shell before running
- Or ensure `.env` file exists with correct values

### Quick Test Script

You can also create a simple test script:

```bash
#!/bin/bash
# test-mcp.sh

source .venv/bin/activate
export PINECONE_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"

npx @modelcontextprotocol/inspector python -m app.mcp_server
```

Make it executable and run:

```bash
chmod +x test-mcp.sh
./test-mcp.sh
```
