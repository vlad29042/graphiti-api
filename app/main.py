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

@app.post("/add_episode")
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

# Import n8n routes
from .n8n_routes import add_messages_n8n, get_memory_n8n, N8nMessagesRequest, GetMemoryRequest

# n8n compatible endpoints
@app.post("/messages")
async def add_messages(request: Request, messages_data: dict):
    """n8n compatible endpoint for adding messages"""
    messages_request = N8nMessagesRequest(**messages_data)
    return await add_messages_n8n(request, messages_request)

@app.post("/get-memory")
async def get_memory(request: Request, memory_request: dict):
    """n8n compatible endpoint for retrieving memory"""
    memory_data = GetMemoryRequest(**memory_request)
    return await get_memory_n8n(request, memory_data)

# Alternative delete endpoint that works
@app.post("/api/remove-episode")
async def remove_episode_api(request: Request, data: dict):
    """Alternative endpoint to delete episode"""
    try:
        episode_uuid = data.get("episode_uuid")
        if not episode_uuid:
            raise HTTPException(status_code=400, detail="episode_uuid is required")
            
        client = request.app.state.graphiti_client
        await client.remove_episode(episode_uuid)
        
        return {"success": True, "message": f"Episode {episode_uuid} deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete episode: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/episodes/{group_id}")
async def get_episodes_by_group(request: Request, group_id: str, last_n: int = Query(20)):
    """Get episodes by group_id"""
    try:
        client = request.app.state.graphiti_client
        from datetime import datetime, timezone
        episodes = await client.retrieve_episodes(
            group_ids=[group_id],
            reference_time=datetime.now(timezone.utc),
            last_n=last_n
        )
        
        # Convert episodes to dict format
        result = []
        for episode in episodes:
            result.append({
                "uuid": episode.uuid,
                "name": episode.name,
                "group_id": episode.group_id,
                "labels": getattr(episode, 'labels', []),
                "created_at": str(episode.created_at),
                "source": episode.source.value if hasattr(episode.source, 'value') else str(episode.source),
                "source_description": episode.source_description,
                "content": episode.content,
                "valid_at": str(episode.valid_at),
                "entity_edges": episode.entity_edges
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to get episodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))