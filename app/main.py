import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, Query
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver
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
    
    # Create FalkorDB driver
    driver = FalkorDriver(
        host=settings.FALKORDB_HOST,
        port=settings.FALKORDB_PORT,
        password=settings.FALKORDB_PASSWORD
    )
    
    graphiti_client = Graphiti(graph_driver=driver)
    
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

@app.post("/search_with_score")
async def search_with_score(request: Request, search_data: SearchRequest):
    """Search with score visibility - показывает внутренний score"""
    try:
        client = request.app.state.graphiti_client
        from .crud_routes import search_with_score_logic
        return await search_with_score_logic(client, search_data)
    except Exception as e:
        logger.error(f"Search with score failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search operation failed.")

@app.get("/")
def read_root():
    return {"message": "Graphiti API Service is running."}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "graphiti-api"}

# Import CRUD routes
from .crud_routes import (
    delete_episode, 
    delete_fact, 
    update_fact,
    get_nodes,
    get_facts,
    DeleteEpisodeRequest,
    DeleteFactRequest,
    UpdateFactRequest,
    DeleteResponse,
    UpdateResponse
)

# CRUD endpoints
@app.delete("/episodes", response_model=DeleteResponse)
async def delete_episode_endpoint(request: Request, data: DeleteEpisodeRequest):
    """Delete an episode by UUID"""
    return await delete_episode(request, data)

@app.delete("/facts", response_model=DeleteResponse)
async def delete_fact_endpoint(request: Request, data: DeleteFactRequest):
    """Delete a fact by UUID"""
    return await delete_fact(request, data)

@app.put("/facts", response_model=UpdateResponse)
async def update_fact_endpoint(request: Request, data: UpdateFactRequest):
    """Update a fact"""
    return await update_fact(request, data)

@app.get("/nodes")
async def get_nodes_endpoint(request: Request, group_id: Optional[str] = None, limit: int = 100):
    """Get all nodes (entities) from the knowledge graph"""
    return await get_nodes(request, group_id, limit)

@app.get("/facts")
async def get_facts_endpoint(request: Request, group_id: Optional[str] = None, limit: int = 100):
    """Get all facts (edges) from the knowledge graph"""
    return await get_facts(request, group_id, limit)

@app.get("/episodes/{episode_uuid}")
async def get_episode_endpoint(request: Request, episode_uuid: str):
    """Get a specific episode by UUID"""
    from .crud_routes import get_episode
    return await get_episode(request, episode_uuid)