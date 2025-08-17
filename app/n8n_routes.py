"""
Additional routes specifically for n8n integration
Compatible with the original Graphiti API format
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from pydantic import BaseModel

from graphiti_core.nodes import EpisodeType
from .graphiti_logic import SearchResponse, SearchResultEdge, SearchResultEpisode

logger = logging.getLogger(__name__)

# n8n compatible models
class N8nMessage(BaseModel):
    content: str
    role_type: str = "user"
    role: str = "promt"
    uuid: Optional[str] = None
    name: Optional[str] = None
    timestamp: Optional[datetime] = None
    source_description: Optional[str] = None

class N8nMessagesRequest(BaseModel):
    group_id: str
    messages: List[N8nMessage]

class N8nResult(BaseModel):
    message: str
    success: bool

# Get memory models
class GetMemoryRequest(BaseModel):
    group_id: str
    messages: List[N8nMessage]
    max_facts: int = 20
    min_score: Optional[float] = None

class FactResult(BaseModel):
    fact: str
    uuid: str
    created_at: datetime
    valid_at: datetime
    invalid_at: Optional[datetime] = None
    relevance_score: Optional[float] = None
    
class GetMemoryResponse(BaseModel):
    facts: List[FactResult]

# Episode response model (n8n format)
class EpisodeData(BaseModel):
    uuid: str
    name: str
    group_id: str
    labels: List[str] = []
    created_at: datetime
    source: str
    source_description: str
    content: str
    valid_at: datetime
    entity_edges: List[dict] = []

async def add_messages_n8n(request: Request, data: N8nMessagesRequest) -> N8nResult:
    """
    n8n compatible endpoint for adding messages
    Accepts the format used by the original Graphiti server
    """
    try:
        client = request.app.state.graphiti_client
        
        for msg in data.messages:
            # Format the episode body like the original implementation
            episode_body = f'{msg.role or ""}({msg.role_type}): {msg.content}'
            
            await client.add_episode(
                uuid=msg.uuid,
                name=msg.name or f"Message from {data.group_id}",
                episode_body=episode_body,
                source_description=msg.source_description or "n8n message",
                source=EpisodeType.message,
                reference_time=msg.timestamp or datetime.now(timezone.utc),
                group_id=data.group_id,
            )
        
        return N8nResult(message="Messages added to processing queue", success=True)
    except Exception as e:
        logger.error(f"Failed to add messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def get_episodes_n8n(
    request: Request, 
    group_id: str, 
    last_n: int = 20
) -> List[EpisodeData]:
    """
    n8n compatible endpoint for retrieving episodes
    Returns episodes in the format expected by n8n
    """
    try:
        client = request.app.state.graphiti_client
        
        # Try different parameter names for retrieve_episodes
        try:
            # Try with reference_time parameter (required)
            episodes = await client.retrieve_episodes(
                group_ids=[group_id],
                reference_time=datetime.now(timezone.utc),
                last_n=last_n
            )
        except Exception as e:
            logger.warning(f"retrieve_episodes failed: {e}")
            # Try alternative approach - direct query
            from neo4j import AsyncGraphDatabase
            driver = AsyncGraphDatabase.driver(
                "bolt://neo4j:7687", 
                auth=("neo4j", "graphiti_password_2025")
            )
            
            async with driver.session() as session:
                result = await session.run("""
                    MATCH (e:Episodic)
                    WHERE e.group_id = $group_id
                    RETURN e
                    ORDER BY e.created_at DESC
                    LIMIT $limit
                """, group_id=group_id, limit=last_n)
                
                episodes = []
                async for record in result:
                    ep = record["e"]
                    episodes.append(type('Episode', (), {
                        'uuid': ep.get('uuid'),
                        'name': ep.get('name', ''),
                        'group_id': ep.get('group_id'),
                        'created_at': ep.get('created_at'),
                        'source': ep.get('source', 'text'),
                        'source_description': ep.get('source_description', ''),
                        'content': ep.get('content', ''),
                        'valid_at': ep.get('valid_at', ep.get('created_at'))
                    })())
            
            await driver.close()
        
        # Convert to n8n format
        result = []
        for episode in episodes:
            episode_data = EpisodeData(
                uuid=str(episode.uuid),
                name=episode.name or "",
                group_id=episode.group_id if hasattr(episode, 'group_id') else group_id,
                labels=[],
                created_at=episode.created_at,
                source=episode.source.value if hasattr(episode.source, 'value') else str(episode.source),
                source_description=episode.source_description or "",
                content=episode.content if hasattr(episode, 'content') else "",
                valid_at=episode.valid_at if hasattr(episode, 'valid_at') else episode.created_at,
                entity_edges=[]
            )
            result.append(episode_data)
        
        return result
    except Exception as e:
        logger.error(f"Failed to get episodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def search_n8n(request: Request, query: str, group_id: Optional[str] = None) -> SearchResponse:
    """
    Simple search endpoint for n8n
    """
    try:
        client = request.app.state.graphiti_client
        
        search_kwargs = {"num_results": 20}
        if group_id:
            search_kwargs["group_ids"] = [group_id]
        
        results = await client.search(query, **search_kwargs)
        
        edges = []
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
        
        return SearchResponse(episodes=[], edges=edges)
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def get_memory_n8n(request: Request, data: GetMemoryRequest) -> GetMemoryResponse:
    """
    Get memory endpoint for n8n - returns relevant facts from the knowledge graph
    based on the conversation context
    """
    try:
        client = request.app.state.graphiti_client
        
        # Compose query from messages
        combined_query = ""
        for message in data.messages:
            role_type = message.role_type or ""
            role = message.role or ""
            combined_query += f"{role_type}({role}): {message.content}\n"
        
        # Search the knowledge graph
        results = await client.search(
            query=combined_query,
            group_ids=[data.group_id],
            num_results=data.max_facts
        )
        
        # Convert edges to facts
        facts = []
        for edge in results:
            if hasattr(edge, "fact"):
                score = getattr(edge, 'score', None)
                # Filter by min_score if specified
                if data.min_score is not None and score is not None and score < data.min_score:
                    continue
                    
                fact = FactResult(
                    fact=edge.fact,
                    uuid=str(edge.uuid),
                    created_at=edge.created_at,
                    valid_at=edge.valid_at,
                    invalid_at=edge.invalid_at,
                    relevance_score=score,
                )
                facts.append(fact)
        
        return GetMemoryResponse(facts=facts)
    except Exception as e:
        logger.error(f"Get memory failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))