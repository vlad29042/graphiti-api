import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from graphiti_core import Graphiti
from .config import settings
from .graphiti_logic import (
    add_episode_logic,
    search_logic,
    EpisodeRequest,
    EpisodeResponse,
    SearchRequest,
    SearchResponse,
)
# Load environment variables
load_dotenv()
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the Graphiti client lifecycle with the FastAPI app."""
    logger.info("Application startup: Initializing Graphiti client...")
    # Graphiti reads models from environment variables DEFAULT_LLM_MODEL and DEFAULT_EMBEDDING_MODEL
    graphiti_client = Graphiti(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
    )
    
    logger.info("✅ Graphiti client initialized successfully")
    
    app.state.graphiti_client = graphiti_client
    yield
    logger.info("Application shutdown: Closing Graphiti client...")
    await graphiti_client.close()

app = FastAPI(
    title="Graphiti API Service",
    description="A service for interacting with a Graphiti knowledge graph.",
    version="1.0.0",
    lifespan=lifespan,
)

@app.post("/add_episode", response_model=EpisodeResponse)
async def add_episode(request: Request, episode_data: EpisodeRequest):
    try:
        client = request.app.state.graphiti_client
        return await add_episode_logic(client, episode_data)
    except Exception as e:
        logger.error(f"Add episode failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Add episode operation failed.")

@app.post("/search", response_model=SearchResponse)
async def search(request: Request, search_data: SearchRequest):
    try:
        client = request.app.state.graphiti_client
        return await search_logic(client, search_data)
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search operation failed.")

@app.get("/")
def read_root():
    return {"message": "Graphiti API Service is running."}

# Import n8n routes
from .n8n_routes import (
    add_messages_n8n, 
    get_episodes_n8n, 
    search_n8n,
    get_memory_n8n,
    N8nMessagesRequest,
    N8nResult,
    EpisodeData,
    GetMemoryRequest,
    GetMemoryResponse
)

# n8n compatible endpoints
@app.post("/messages", response_model=N8nResult, status_code=202)
async def add_messages(request: Request, data: N8nMessagesRequest):
    """n8n compatible endpoint for adding messages"""
    return await add_messages_n8n(request, data)

@app.get("/episodes/{group_id}", response_model=List[EpisodeData])
async def get_episodes(request: Request, group_id: str, last_n: int = 20):
    """n8n compatible endpoint for getting episodes"""
    return await get_episodes_n8n(request, group_id, last_n)

@app.post("/search/simple")
async def search_simple(request: Request, query: str, group_id: Optional[str] = None):
    """Simple search endpoint for n8n"""
    return await search_n8n(request, query, group_id)

@app.post("/get-memory", response_model=GetMemoryResponse)
async def get_memory(request: Request, data: GetMemoryRequest):
    """Get relevant facts from knowledge graph based on conversation context"""
    return await get_memory_n8n(request, data)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "graphiti-api"}