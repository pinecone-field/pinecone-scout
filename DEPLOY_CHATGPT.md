# Deploying Pinecone Scout to ChatGPT

This guide covers how to actually load and use your Pinecone Scout app inside ChatGPT.

## Overview

There are two components that need to be accessible:

1. **Backend API** - Your FastAPI server (needs to be publicly accessible)
2. **MCP Server** - Runs locally as a subprocess (configured in ChatGPT)

## Option 1: Local Development with ngrok

### Step 1: Start Your Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Start the backend server
python run.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's running: `http://localhost:8000/docs`

### Step 2: Expose Backend with ngrok

1. **Install ngrok** (if needed):

   ```bash
   # macOS
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   # Sign up for a free account at https://ngrok.com
   ```

2. **Start ngrok tunnel**:

   ```bash
   ngrok http 8000
   ```

3. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok-free.app`)

4. **Update Backend URL in MCP Server**:
   Edit `app/mcp_server.py`:

   ```python
   # Change line 10 from:
   BACKEND_URL = f"http://localhost:{settings.port}/api"
   
   # To:
   BACKEND_URL = "https://your-ngrok-url.ngrok-free.app/api"
   ```

### Step 3: Configure MCP Server in ChatGPT

1. **Open ChatGPT** (web interface at chat.openai.com)

2. **Enable Developer Mode**:
   - Click your profile icon (bottom left or top right)
   - Go to **Settings** → **Apps & Connectors** → **Advanced Settings**
   - Toggle **Developer Mode** ON

3. **Create a Connector**:
   - In **Settings** → **Apps & Connectors**, click **Create**
   - Fill in the connector details:
     - **Connector Name**: `Pinecone Scout`
     - **Description**: `AI-powered product recommendation system`
     - **Connector URL**: This depends on how you're running the MCP server:

   **Option A: Local Subprocess (if supported)**:
   - Some ChatGPT implementations support local subprocess MCP servers
   - Look for a "Local MCP Server" or "Subprocess" option
   - If available, use this configuration:

     ```json
     {
       "command": "/full/path/to/your/venv/bin/python",
       "args": ["-m", "app.mcp_server"],
       "cwd": "/full/path/to/pinecone-scout",
       "env": {
         "PINECONE_API_KEY": "your_actual_pinecone_key",
         "OPENAI_API_KEY": "your_actual_openai_key"
       }
     }
     ```

   **Option B: HTTP Endpoint (Recommended)**:
   - If ChatGPT requires an HTTP endpoint, you'll need to expose your MCP server as HTTP
   - See "Alternative: Deploy MCP Server as HTTP Endpoint" section below
   - Use the HTTPS URL to your MCP HTTP endpoint (e.g., `https://your-mcp-server.vercel.app/mcp`)

4. **Save and Connect**:
   - Click **Create** or **Save**
   - If prompted, click **Connect** to activate the connector
   - You should see your tools listed (recommend, submit_feedback, get_user_profile, predictive_suggest)

### Step 4: Test in ChatGPT

1. **Start a new chat** in ChatGPT
2. **Activate your app**:
   - **Method 1**: Click the **+ (Tools)** button near the message box
   - Select **Developer Mode** (if shown)
   - Toggle your **Pinecone Scout** connector ON
   - **Method 2**: Start your message with the app name: "Pinecone Scout, what tools do you have?"
3. **Verify tools are available**: Ask "What tools do you have available?"
   - It should list: `recommend`, `submit_feedback`, `get_user_profile`, `predictive_suggest`
4. **Test with a query**: "I need a vacation"
   - ChatGPT should call `predictive_suggest` and return cruise recommendations
5. **Test other tools**:
   - "I'm looking for a 50-inch TV" → should call `recommend`
   - "What are my preferences?" → should call `get_user_profile`

## Option 2: Deploy Backend to Vercel

### Step 1: Prepare for Vercel Deployment

Vercel works best with serverless functions. We'll need to adapt the FastAPI app for Vercel.

1. **Install Vercel CLI**:

   ```bash
   npm i -g vercel
   ```

2. **Create `vercel.json`** in your project root:

   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "run.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "run.py"
       }
     ],
     "env": {
       "PINECONE_API_KEY": "@pinecone_api_key",
       "OPENAI_API_KEY": "@openai_api_key"
     }
   }
   ```

3. **Create `api/index.py`** (Vercel serverless function wrapper):

   ```python
   from app.main import app
   import sys
   import os

   # Add project root to path
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

   # Export the app for Vercel
   handler = app
   ```

### Step 2: Deploy to Vercel

1. **Login to Vercel**:

   ```bash
   vercel login
   ```

2. **Deploy**:

   ```bash
   vercel
   ```

3. **Set Environment Variables**:

   ```bash
   vercel env add PINECONE_API_KEY
   vercel env add OPENAI_API_KEY
   vercel env add USERS_INDEX_NAME  # optional
   vercel env add ITEMS_INDEX_NAME  # optional
   ```

4. **Get your deployment URL** (e.g., `https://pinecone-scout.vercel.app`)

### Step 3: Update MCP Server Configuration

Edit `app/mcp_server.py`:

```python
# Change line 10 to:
BACKEND_URL = "https://pinecone-scout.vercel.app/api"
```

### Step 4: Configure MCP Server in ChatGPT

Follow the same steps as Option 1, Step 3, but now your backend is publicly accessible via Vercel.

## Alternative: Deploy MCP Server as HTTP Endpoint

If ChatGPT requires the MCP server to be an HTTP endpoint (not a subprocess), you'll need to:

1. **Create an HTTP wrapper for the MCP server**:
   Create `app/mcp_http_server.py`:

   ```python
   """HTTP wrapper for MCP server."""
   from fastapi import FastAPI, Request
   from app.mcp_server import PineconeScoutMCPServer
   import json

   app = FastAPI()
   mcp_server = PineconeScoutMCPServer()

   @app.post("/mcp")
   async def handle_mcp(request: Request):
       """Handle MCP requests via HTTP."""
       body = await request.json()
       response = await mcp_server.handle_request(body)
       return response
   ```

2. **Deploy this to Vercel** as well, or run it alongside your backend

3. **Configure ChatGPT** to use the HTTP endpoint instead of subprocess

## Troubleshooting

### MCP Server Not Starting

**Error**: ChatGPT can't start the MCP server

**Solutions**:

- Use absolute paths for Python and project directory
- Ensure virtual environment is activated or use full path to venv Python
- Check that `app/mcp_server.py` exists and is importable
- Verify environment variables are set correctly

### Backend Connection Errors

**Error**: MCP server can't reach backend

**Solutions**:

- Verify backend is running and accessible
- Check `BACKEND_URL` in `app/mcp_server.py` matches your deployment URL
- Test backend directly: `curl https://your-backend-url.vercel.app/api/`
- Check CORS settings if needed

### Tools Not Appearing

**Error**: ChatGPT doesn't show your tools

**Solutions**:

- Restart ChatGPT after adding MCP server
- Check MCP server logs (if available in ChatGPT UI)
- Verify the MCP server responds to `initialize` and `tools/list` requests
- Test MCP server locally first using MCP Inspector

### Vercel Deployment Issues

**Error**: FastAPI app not working on Vercel

**Solutions**:

- Vercel works best with serverless functions
- Consider using `vercel-python` or deploying as a Docker container
- Alternative: Use Fly.io, Render, or Railway which support long-running processes better

## Quick Start Checklist

- [ ] Backend server running locally or deployed
- [ ] Backend accessible via HTTPS (ngrok or Vercel)
- [ ] `BACKEND_URL` updated in `app/mcp_server.py`
- [ ] MCP server configuration added to ChatGPT
- [ ] Environment variables set (API keys)
- [ ] Developer Mode enabled in ChatGPT
- [ ] Tested with "What tools do you have available?"
- [ ] Tested with actual query: "I need a vacation"

## Next Steps

Once working:

- Test all tools: `recommend`, `submit_feedback`, `get_user_profile`, `predictive_suggest`
- Populate your indexes with product data
- Customize the UI component (`chatgpt_app/index.html`)
- Prepare for production deployment
