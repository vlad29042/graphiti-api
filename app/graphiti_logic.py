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

class SearchResultEpisode(BaseModel):
    content: str
    created_at: datetime | None = None

class SearchResponse(BaseModel):
    edges: List[SearchResultEdge]
    episodes: List[SearchResultEpisode]

# --- Core Logic Functions ---

async def add_episode_logic(client: Graphiti, episode_data: EpisodeRequest) -> EpisodeResponse:
    """Logic to add an episode to the knowledge graph."""
    episode = await client.add_episode(
        name=episode_data.name,
        episode_body=episode_data.content,
        source_description=episode_data.source_description,
        source=EpisodeType.text,
        reference_time=datetime.now(timezone.utc),
        group_id=episode_data.group_id,
    )
    # episode is AddEpisodeResults which contains: episode, nodes, edges
    episode_uuid = episode.episode.uuid if hasattr(episode, 'episode') else None
    return EpisodeResponse(status="success", episode_id=episode_uuid)

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