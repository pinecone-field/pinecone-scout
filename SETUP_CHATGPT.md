# Setting Up Pinecone Scout in ChatGPT

This guide will walk you through adding Pinecone Scout to your ChatGPT account for testing.

## Prerequisites

1. **ChatGPT Account with Developer Mode Access**
   - The Apps SDK is currently in preview
   - You need access to ChatGPT's Developer Mode
   - If you don't have access, you may need to wait for broader availability

2. **Backend Server Running**
   - Your FastAPI backend must be running and accessible
   - For local testing, you'll need to expose it (see below)

3. **Environment Variables Set**
   - Your `.env` file should have `PINECONE_API_KEY` and `OPENAI_API_KEY` configured

## Step-by-Step Setup

### Step 1: Start Your Backend Server

First, make sure your backend is running:

```bash
# Activate your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the server
python run.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's working by visiting: `http://localhost:8000/docs`

### Step 2: Expose Your Backend for ChatGPT (Local Testing)

Since ChatGPT needs to access your backend, you have two options:

#### Option A: Use ngrok (Recommended for Local Testing)

1. **Install ngrok** (if not already installed):

   ```bash
   # macOS
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   ```

2. **Start ngrok tunnel**:

   ```bash
   ngrok http 8000
   ```

3. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

4. **Update MCP Server Backend URL**:
   Edit `app/mcp_server.py` and update the `BACKEND_URL`:

   ```python
   # Change this line (around line 11)
   BACKEND_URL = "https://your-ngrok-url.ngrok.io/api"
   ```

#### Option B: Deploy to a Public Server

Deploy your backend to a service like:

- Fly.io
- Render
- Railway
- Google Cloud Run
- Azure Container Apps

Then update `BACKEND_URL` in `app/mcp_server.py` to point to your deployed URL.

### Step 3: Configure ChatGPT to Use Your MCP Server

The MCP server configuration needs to be added to ChatGPT. The exact method depends on how ChatGPT exposes MCP server configuration:

#### Method 1: ChatGPT Desktop App (if supported)

1. Open ChatGPT desktop app
2. Go to Settings → Developer Settings (or similar)
3. Add MCP server configuration
4. Use the configuration from `chatgpt_app/mcp_config.json`:

```json
{
  "mcpServers": {
    "pinecone-scout": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "env": {
        "PINECONE_API_KEY": "your_actual_key_here",
        "OPENAI_API_KEY": "your_actual_key_here"
      }
    }
  }
}
```

**Important**: Replace the environment variable placeholders with your actual API keys, or ensure they're available in your shell environment.

#### Method 2: Environment-Based Configuration

If ChatGPT reads from environment variables or a config file:

1. **Set environment variables**:

   ```bash
   export PINECONE_API_KEY="your_key_here"
   export OPENAI_API_KEY="your_key_here"
   ```

2. **Update mcp_config.json** to use actual values or environment variable references (depending on ChatGPT's implementation)

#### Method 3: ChatGPT Web Interface

1. Go to ChatGPT web interface
2. Look for Developer Mode or Settings
3. Find "MCP Servers" or "Custom Tools" section
4. Add a new MCP server with:
   - **Name**: `pinecone-scout`
   - **Command**: `python`
   - **Args**: `["-m", "app.mcp_server"]`
   - **Working Directory**: Path to your `pinecone-scout` directory
   - **Environment Variables**: Your API keys

### Step 4: Test the MCP Server Locally

Before adding to ChatGPT, test that your MCP server works:

```bash
# From your project directory
python -m app.mcp_server
```

You should see it waiting for input (it reads from stdin). You can test it by sending a JSON-RPC request, but for now, just verify it starts without errors.

### Step 5: Load Your App in ChatGPT

Once the MCP server is configured:

1. **Open ChatGPT** (web or desktop app)
2. **Enable Developer Mode** (if not already enabled)
3. **Start a new conversation**
4. **Test the tools** by asking ChatGPT:
   - "I'm looking for a 50-inch TV for my apartment"
   - ChatGPT should call the `recommend` tool
   - You should see recommendations displayed

### Step 6: Verify Tools Are Available

Ask ChatGPT:

```text
What tools do you have available?
```

It should list:

- `recommend`
- `submit_feedback`
- `get_user_profile`
- `predictive_suggest`

## Troubleshooting

### MCP Server Not Found

**Error**: ChatGPT can't find or start the MCP server

**Solutions**:

1. Ensure Python is in your PATH
2. Use absolute paths in the MCP config:

   ```json
   "command": "/full/path/to/python",
   "args": ["-m", "app.mcp_server"],
   "cwd": "/full/path/to/pinecone-scout"
   ```

3. Verify the virtual environment is activated or use the full Python path

### Backend Connection Errors

**Error**: MCP server can't connect to backend

**Solutions**:

1. Verify backend is running: `curl http://localhost:8000/health`
2. If using ngrok, ensure the tunnel is active
3. Update `BACKEND_URL` in `app/mcp_server.py` to match your backend URL
4. Check firewall settings

### Environment Variables Not Set

**Error**: API keys not found

**Solutions**:

1. Ensure `.env` file exists and has correct values
2. Or set environment variables explicitly in MCP config
3. Or export them in your shell before starting ChatGPT

### Tools Not Appearing

**Error**: ChatGPT doesn't show your tools

**Solutions**:

1. Restart ChatGPT after adding MCP server
2. Check MCP server logs for errors
3. Verify the MCP server is responding correctly
4. Check ChatGPT's developer console for errors

## Testing Your Integration

Once set up, test with these prompts:

1. **Get Recommendations**:

   ```text
   I'm looking for a 50-inch TV for my apartment
   ```

2. **Submit Feedback**:

   ```text
   I like the Samsung Frame TV recommendation
   ```

   (ChatGPT should call submit_feedback)

3. **Check Profile**:

   ```text
   What are my preferences?
   ```

4. **Predictive Suggestion**:

   ```text
   I'm planning a trip to Europe this spring
   ```

## Next Steps

- **Add Sample Data**: Populate your Pinecone indexes with product data
- **Customize UI**: Modify `chatgpt_app/index.html` to match your brand
- **Deploy**: When ready, deploy to production and submit through OpenAI's app directory

## Additional Resources

- [OpenAI Apps SDK Documentation](https://developers.openai.com/apps-sdk)
- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [Apps SDK Examples](https://github.com/openai/apps-sdk-examples)

## Notes

- The Apps SDK is currently in **preview** - features may change
- You can only test your own app in Developer Mode currently
- Public sharing will be available when OpenAI opens app submissions
