"""
CRUD routes for managing episodes and facts
"""
import logging
from typing import Optional
from fastapi import Request, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Models for CRUD operations
class DeleteEpisodeRequest(BaseModel):
    episode_uuid: str
    group_id: Optional[str] = None

class DeleteFactRequest(BaseModel):
    fact_uuid: str
    group_id: Optional[str] = None

class UpdateFactRequest(BaseModel):
    fact_uuid: str
    new_fact: str
    group_id: Optional[str] = None

class DeleteResponse(BaseModel):
    success: bool
    message: str

class UpdateResponse(BaseModel):
    success: bool
    message: str
    updated_fact: Optional[dict] = None

async def delete_episode(request: Request, data: DeleteEpisodeRequest) -> DeleteResponse:
    """
    Delete an episode by UUID using graphiti-core's remove_episode method
    """
    try:
        client = request.app.state.graphiti_client
        
        logger.info(f"Deleting episode with UUID: {data.episode_uuid}")
        
        # Use graphiti-core's remove_episode method
        await client.remove_episode(data.episode_uuid)
        
        logger.info(f"Successfully deleted episode: {data.episode_uuid}")
        
        return DeleteResponse(
            success=True, 
            message=f"Episode {data.episode_uuid} successfully deleted"
        )
        
    except Exception as e:
        logger.error(f"Failed to delete episode: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def delete_fact(request: Request, data: DeleteFactRequest) -> DeleteResponse:
    """
    Delete a fact (edge) by UUID
    For temporal knowledge graphs, we prefer to invalidate facts rather than delete them
    """
    try:
        client = request.app.state.graphiti_client
        
        logger.info(f"Processing fact deletion for UUID: {data.fact_uuid}")
        
        # Option 1: Temporal invalidation (preferred for audit trail)
        # Set invalid_at timestamp to mark the fact as no longer valid
        from datetime import datetime, timezone
        
        # Direct query to invalidate the fact
        query = """
        MATCH ()-[r:RELATES_TO {uuid: $uuid}]-()
        SET r.invalid_at = $invalid_at
        RETURN r
        """
        
        result = await client.driver.execute_query(
            query,
            uuid=data.fact_uuid,
            invalid_at=datetime.now(timezone.utc).isoformat()
        )
        
        if result[0]:  # If we found and updated the edge
            logger.info(f"Successfully invalidated fact: {data.fact_uuid}")
            return DeleteResponse(
                success=True,
                message=f"Fact {data.fact_uuid} has been invalidated (temporal deletion)"
            )
        else:
            # Option 2: Physical deletion (if invalidation failed or not found)
            # Use the Edge.delete_by_uuids method from graphiti-core
            from graphiti_core.edges import Edge
            await Edge.delete_by_uuids(client.driver, [data.fact_uuid])
            
            logger.info(f"Successfully deleted fact: {data.fact_uuid}")
            return DeleteResponse(
                success=True,
                message=f"Fact {data.fact_uuid} has been permanently deleted"
            )
        
    except Exception as e:
        logger.error(f"Failed to delete fact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def update_fact(request: Request, data: UpdateFactRequest) -> UpdateResponse:
    """
    Update a fact - this typically means invalidating the old one and creating a new one
    In temporal knowledge graphs, we preserve history by invalidating old facts
    """
    try:
        client = request.app.state.graphiti_client
        
        logger.info(f"Updating fact UUID: {data.fact_uuid}")
        
        from datetime import datetime, timezone
        
        # Step 1: Get the existing fact details
        get_fact_query = """
        MATCH (n1:Entity)-[r:RELATES_TO {uuid: $uuid}]->(n2:Entity)
        RETURN r, n1.uuid as source_uuid, n2.uuid as target_uuid, 
               n1.name as source_name, n2.name as target_name,
               r.group_id as group_id, r.episodes as episodes
        """
        
        result = await client.driver.execute_query(
            get_fact_query,
            uuid=data.fact_uuid
        )
        
        if not result[0]:
            return UpdateResponse(
                success=False,
                message=f"Fact {data.fact_uuid} not found"
            )
        
        fact_data = result[0][0]
        
        # Step 2: Invalidate the old fact
        invalidate_query = """
        MATCH ()-[r:RELATES_TO {uuid: $uuid}]-()
        SET r.invalid_at = $invalid_at
        RETURN r
        """
        
        current_time = datetime.now(timezone.utc)
        await client.driver.execute_query(
            invalidate_query,
            uuid=data.fact_uuid,
            invalid_at=current_time.isoformat()
        )
        
        # Step 3: Create a new fact with updated content
        from graphiti_core.edges import EntityEdge
        import uuid
        
        new_edge = EntityEdge(
            uuid=str(uuid.uuid4()),
            source_node_uuid=fact_data['source_uuid'],
            target_node_uuid=fact_data['target_uuid'],
            fact=data.new_fact,
            episodes=fact_data['episodes'],
            created_at=current_time,
            valid_at=current_time,
            invalid_at=None,
            group_id=data.group_id or fact_data['group_id']
        )
        
        await new_edge.save(client.driver)
        
        logger.info(f"Successfully updated fact: old UUID {data.fact_uuid}, new UUID {new_edge.uuid}")
        
        return UpdateResponse(
            success=True,
            message=f"Fact updated successfully. Old fact invalidated, new fact created.",
            updated_fact={
                "old_uuid": data.fact_uuid,
                "new_uuid": new_edge.uuid,
                "fact": data.new_fact,
                "source": fact_data['source_name'],
                "target": fact_data['target_name'],
                "invalidated_at": current_time.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to update fact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def get_nodes(request: Request, group_id: Optional[str] = Query(None), limit: int = Query(100)):
    """
    Get all nodes (entities) from the knowledge graph
    """
    try:
        client = request.app.state.graphiti_client
        
        # Direct query to get nodes using graphiti driver
        if group_id:
            query = """
                MATCH (n:Entity)
                WHERE n.group_id = $group_id
                RETURN n
                LIMIT $limit
            """
            records, _, _ = await client.driver.execute_query(
                query, 
                group_id=group_id, 
                limit=limit
            )
        else:
            query = """
                MATCH (n:Entity)
                RETURN n
                LIMIT $limit
            """
            records, _, _ = await client.driver.execute_query(
                query, 
                limit=limit
            )
        
        nodes = []
        for record in records:
            node = record["n"]
            # FalkorDB возвращает объекты с атрибутом properties
            props = node.properties if hasattr(node, 'properties') else node
            
            nodes.append({
                "uuid": props.get("uuid") if isinstance(props, dict) else None,
                "name": props.get("name") if isinstance(props, dict) else None,
                "type": props.get("type", "Entity") if isinstance(props, dict) else "Entity",
                "group_id": props.get("group_id") if isinstance(props, dict) else None,
                "created_at": str(props.get("created_at")) if isinstance(props, dict) and props.get("created_at") else None
            })
        
        return {"nodes": nodes, "count": len(nodes)}
        
    except Exception as e:
        logger.error(f"Failed to get nodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def get_facts(request: Request, group_id: Optional[str] = Query(None), limit: int = Query(100)):
    """
    Get all facts (edges) from the knowledge graph
    """
    try:
        client = request.app.state.graphiti_client
        
        # Direct query to get facts using graphiti driver
        if group_id:
            query = """
                MATCH (n1:Entity)-[r:RELATES_TO]->(n2:Entity)
                WHERE r.group_id = $group_id
                RETURN n1, r, n2
                LIMIT $limit
            """
            records, _, _ = await client.driver.execute_query(
                query, 
                group_id=group_id, 
                limit=limit
            )
        else:
            query = """
                MATCH (n1:Entity)-[r:RELATES_TO]->(n2:Entity)
                RETURN n1, r, n2
                LIMIT $limit
            """
            records, _, _ = await client.driver.execute_query(
                query, 
                limit=limit
            )
        
        facts = []
        for record in records:
            n1 = record["n1"]
            r = record["r"]
            n2 = record["n2"]
            
            # FalkorDB возвращает объекты с атрибутом properties
            r_props = r.properties if hasattr(r, 'properties') else r
            n1_props = n1.properties if hasattr(n1, 'properties') else n1
            n2_props = n2.properties if hasattr(n2, 'properties') else n2
            
            facts.append({
                "uuid": r_props.get("uuid") if isinstance(r_props, dict) else None,
                "fact": r_props.get("fact") if isinstance(r_props, dict) else None,
                "source_entity": n1_props.get("name") if isinstance(n1_props, dict) else None,
                "target_entity": n2_props.get("name") if isinstance(n2_props, dict) else None,
                "group_id": r_props.get("group_id") if isinstance(r_props, dict) else None,
                "created_at": str(r_props.get("created_at")) if isinstance(r_props, dict) and r_props.get("created_at") else None,
                "valid_at": str(r_props.get("valid_at")) if isinstance(r_props, dict) and r_props.get("valid_at") else None,
                "invalid_at": str(r_props.get("invalid_at")) if isinstance(r_props, dict) and r_props.get("invalid_at") else None
            })
        
        return {"facts": facts, "count": len(facts)}
        
    except Exception as e:
        logger.error(f"Failed to get facts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def get_episode(request: Request, episode_uuid: str):
    """
    Get a specific episode by UUID with all its relationships
    """
    try:
        client = request.app.state.graphiti_client
        
        logger.info(f"Getting episode with UUID: {episode_uuid}")
        
        # Query to get episode node and its edges
        query = """
            MATCH (e:Episodic {uuid: $uuid})
            OPTIONAL MATCH (e)-[r:MENTIONS]->(n:Entity)
            RETURN e, collect({edge: r, entity: n}) as mentions
        """
        
        records, _, _ = await client.driver.execute_query(
            query,
            uuid=episode_uuid
        )
        
        if not records:
            raise HTTPException(status_code=404, detail=f"Episode {episode_uuid} not found")
        
        record = records[0]
        episode_node = record["e"]
        mentions = record["mentions"]
        
        # Extract episode properties
        episode_props = episode_node.properties if hasattr(episode_node, 'properties') else episode_node
        
        # Extract mentioned entities
        entities = []
        for mention in mentions:
            if mention and mention.get("entity"):
                entity = mention["entity"]
                entity_props = entity.properties if hasattr(entity, 'properties') else entity
                entities.append({
                    "uuid": entity_props.get("uuid") if isinstance(entity_props, dict) else None,
                    "name": entity_props.get("name") if isinstance(entity_props, dict) else None,
                    "type": entity_props.get("type", "Entity") if isinstance(entity_props, dict) else "Entity"
                })
        
        episode_data = {
            "uuid": episode_props.get("uuid") if isinstance(episode_props, dict) else None,
            "name": episode_props.get("name") if isinstance(episode_props, dict) else None,
            "content": episode_props.get("content") if isinstance(episode_props, dict) else None,
            "source": episode_props.get("source") if isinstance(episode_props, dict) else None,
            "source_description": episode_props.get("source_description") if isinstance(episode_props, dict) else None,
            "group_id": episode_props.get("group_id") if isinstance(episode_props, dict) else None,
            "created_at": str(episode_props.get("created_at")) if isinstance(episode_props, dict) and episode_props.get("created_at") else None,
            "entities_mentioned": entities,
            "entity_count": len(entities)
        }
        
        return {"episode": episode_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get episode: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def search_with_score_logic(client, search_data):
    """
    Search with direct score visibility using raw Cypher query
    """
    from graphiti_core.embedder import OpenAIEmbedder
    import os
    
    logger.info(f"Searching with score for query: '{search_data.query}'")
    
    # Create embedder to generate query embedding
    # OpenAIEmbedder берёт API key из переменной окружения автоматически
    embedder = OpenAIEmbedder()
    query_embedding = await embedder.create(input_data=[search_data.query])
    
    # Build group filter
    group_filter = ""
    if search_data.group_ids:
        group_filter = "AND e.group_id IN $group_ids"
    
    # Direct Cypher query that returns score
    query = f"""
        MATCH (n:Entity)-[e:RELATES_TO]->(m:Entity)
        WHERE e.fact_embedding IS NOT NULL
        {group_filter}
        WITH e, n, m, (2 - vec.cosineDistance(e.fact_embedding, vecf32($search_vector)))/2 AS score
        WHERE score > 0.5
        RETURN 
            e.uuid AS uuid,
            e.fact AS fact,
            n.name AS source_entity,
            m.name AS target_entity,
            e.created_at AS created_at,
            score
        ORDER BY score DESC
        LIMIT $limit
    """
    
    params = {
        "search_vector": query_embedding,
        "limit": search_data.num_results
    }
    if search_data.group_ids:
        params["group_ids"] = search_data.group_ids
    
    records, _, _ = await client.driver.execute_query(query, **params)
    
    results = []
    for record in records:
        results.append({
            "uuid": record["uuid"],
            "fact": record["fact"],
            "source_entity": record["source_entity"],
            "target_entity": record["target_entity"],
            "created_at": str(record["created_at"]) if record["created_at"] else None,
            "score": float(record["score"]),  # Вот он - SCORE!
            "score_percent": f"{float(record['score']) * 100:.1f}%"
        })
    
    return {
        "query": search_data.query,
        "results_count": len(results),
        "results": results
    }