import logging
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from .config import settings
# Setup logging
logger = logging.getLogger(__name__)

# --- Pydantic Models for API Data Validation ---

class EpisodeRequest(BaseModel):
    name: str
    content: str
    source_description: str
    group_id: Optional[str] = None

class EpisodeResponse(BaseModel):
    status: str
    episode_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    group_ids: Optional[List[str]] = None
    num_results: int = 10
    focal_node_uuid: Optional[str] = None

class SearchResultEdge(BaseModel):
    fact: str
    uuid: str
    created_at: datetime | None = None
    valid_at: datetime | None = None
    invalid_at: datetime | None = None
    relevance_score: float | None = None

class SearchResultEpisode(BaseModel):
    content: str
    created_at: datetime | None = None

class SearchResponse(BaseModel):
    edges: List[SearchResultEdge]
    episodes: List[SearchResultEpisode]

# --- Core Logic Functions ---

async def add_episode_logic(client: Graphiti, episode_data: EpisodeRequest) -> dict:
    """Logic to add an episode to the knowledge graph."""
    result = await client.add_episode(
        name=episode_data.name,
        episode_body=episode_data.content,
        source_description=episode_data.source_description,
        source=EpisodeType.text,
        reference_time=datetime.now(timezone.utc),
        group_id=episode_data.group_id,
    )
    # result is AddEpisodeResults which contains: episode, nodes, edges
    episode_uuid = result.episode.uuid if hasattr(result, 'episode') else None
    nodes_count = len(result.nodes) if hasattr(result, 'nodes') else 0
    edges_count = len(result.edges) if hasattr(result, 'edges') else 0
    
    logger.info(f"Episode added: {nodes_count} nodes, {edges_count} edges")
    
    return {
        "status": "success", 
        "episode_id": episode_uuid,
        "nodes_count": nodes_count,
        "edges_count": edges_count
    }

async def search_logic(client: Graphiti, search_data: SearchRequest) -> SearchResponse:
    """Logic to search the knowledge graph."""
    logger.info(
        f"Searching with query='{search_data.query}' for groups={search_data.group_ids}"
    )
    try:
        # Prepare search parameters
        search_kwargs = {"num_results": search_data.num_results}
        if search_data.group_ids:
            search_kwargs["group_ids"] = search_data.group_ids
        if search_data.focal_node_uuid:
            search_kwargs["focal_node_uuid"] = search_data.focal_node_uuid
        results = await client.search(search_data.query, **search_kwargs)
        logger.info(f"Search returned {len(results)} results.")
        episodes = []
        edges = []
        if not results:
            return SearchResponse(episodes=[], edges=[])
        # The search result from graphiti-core is a list of EntityEdge objects,
        # not a complex object with .episodes
        for edge in results:
            if hasattr(edge, "fact"):
                search_edge = SearchResultEdge(
                    fact=edge.fact,
                    uuid=str(edge.uuid),
                    created_at=edge.created_at,
                    valid_at=edge.valid_at,
                    invalid_at=edge.invalid_at,
                    relevance_score=getattr(edge, 'score', None),
                )
                edges.append(search_edge)
            else:
                logger.warning(
                    f"Result object is missing 'fact' attribute: {type(edge)}"
                )
        logger.info(f"Returning {len(edges)} edges from search.")
        return SearchResponse(episodes=episodes, edges=edges)
    except Exception as e:
        logger.error(f"Search logic error: {e}", exc_info=True)
        # Re-raise the exception to be handled by the main app
        raise