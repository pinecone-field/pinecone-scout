"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.services.pinecone_service import pinecone_service
from app.mcp_server import PineconeScoutMCPServer
from app.config import settings

# Configure logging
logging.basicConfig(
    #level=logging.INFO,  # Set to DEBUG to see debug logs
    level=logging.DEBUG,  # Set to DEBUG to see debug logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Initialize Pinecone
    await pinecone_service.initialize()
    yield
    # Shutdown: Close Pinecone connections
    await pinecone_service.close()


app = FastAPI(
    title="Pinecone Scout API",
    description="Backend service for ChatGPT-based product recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["recommendations"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Pinecone Scout API",
        "version": "1.0.0",
        "endpoints": {
            "recommend": "POST /api/recommend",
            "feedback": "POST /api/feedback",
            "profile": "GET /api/profile",
            "predictive_suggest": "POST /api/predictive_suggest"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# MCP Server HTTP endpoint for ChatGPT
mcp_server_instance = PineconeScoutMCPServer()


@app.post("/mcp")
async def handle_mcp(request: Request):
    """
    Handle MCP (Model Context Protocol) requests via HTTP.
    This endpoint allows ChatGPT to communicate with the MCP server over HTTP.
    """
    try:
        body = await request.json()
        response = await mcp_server_instance.handle_request(body)
        return response
    except Exception as e:
        logging.error(f"Error handling MCP request: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if isinstance(body, dict) else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


@app.get("/mcp")
async def mcp_info():
    """
    Return MCP server information and available tools.
    ChatGPT may call this to discover available tools.
    """
    from app.mcp_server import TOOLS
    return {
        "name": "Pinecone Scout MCP Server",
        "version": "1.0.0",
        "tools": [
            {
                "name": tool["name"],
                "description": tool.get("description", "")
            }
            for tool in TOOLS
        ]
    }

