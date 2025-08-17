#!/usr/bin/env python3
"""Test vector search functionality with FalkorDB"""

import httpx
import asyncio
import json
from datetime import datetime

API_URL = "http://localhost:8001"

async def test_vector_search():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== Testing Vector Search with FalkorDB ===\n")
        
        # 1. Health check
        response = await client.get(f"{API_URL}/health")
        print(f"Health check: {response.json()}")
        
        # 2. Add multiple episodes with different content
        print("\n1. Adding episodes...")
        episodes = [
            {
                "name": "Episode 1",
                "content": "Alice works at Microsoft as a software engineer specializing in artificial intelligence.",
                "source": "test",
                "source_description": "Test source",
                "group_id": "test-vector"
            },
            {
                "name": "Episode 2", 
                "content": "Bob is a data scientist at Google working on machine learning algorithms.",
                "source": "test",
                "source_description": "Test source",
                "group_id": "test-vector"
            },
            {
                "name": "Episode 3",
                "content": "Charlie is a chef at a French restaurant specializing in pastries and desserts.",
                "source": "test",
                "source_description": "Test source",
                "group_id": "test-vector"
            }
        ]
        
        episode_ids = []
        for episode in episodes:
            response = await client.post(f"{API_URL}/add_episode", json=episode)
            if response.status_code == 200:
                episode_data = response.json()
                episode_id = episode_data.get("episode_id")
                episode_ids.append(episode_id)
                print(f"✅ Added: {episode['name']} (ID: {episode_id})")
            else:
                print(f"❌ Failed to add {episode['name']}: {response.text}")
                return
        
        # Wait for processing
        print("\n2. Waiting for processing...")
        await asyncio.sleep(5)
        
        # 3. Test semantic search - should find tech-related results
        print("\n3. Testing semantic search for 'artificial intelligence'...")
        search_data = {
            "query": "artificial intelligence",
            "group_ids": ["test-vector"],
            "num_results": 10
        }
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            edges = results.get('edges', [])
            print(f"✅ Found {len(edges)} results")
            for edge in edges[:3]:  # Show first 3 results
                print(f"   - {edge.get('fact', 'No fact')}")
        else:
            print(f"❌ Search failed: {response.text}")
        
        # 4. Test another semantic search - should find food-related results  
        print("\n4. Testing semantic search for 'cooking and cuisine'...")
        search_data = {
            "query": "cooking and cuisine",
            "group_ids": ["test-vector"],
            "num_results": 10
        }
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            edges = results.get('edges', [])
            print(f"✅ Found {len(edges)} results")
            for edge in edges[:3]:  # Show first 3 results
                print(f"   - {edge.get('fact', 'No fact')}")
        else:
            print(f"❌ Search failed: {response.text}")
        
        # 5. Clean up - delete all episodes
        print("\n5. Cleaning up...")
        for episode_id in episode_ids:
            delete_data = {"episode_uuid": episode_id}
            response = await client.request("DELETE", f"{API_URL}/episodes", json=delete_data)
            if response.status_code == 200:
                print(f"✅ Deleted episode {episode_id}")
            else:
                print(f"❌ Failed to delete {episode_id}: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_vector_search())