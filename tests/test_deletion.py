#!/usr/bin/env python3
"""Test deletion functionality with FalkorDB"""

import httpx
import asyncio
import json
from datetime import datetime

API_URL = "http://localhost:8001"

async def test_deletion():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== Testing Graphiti API with FalkorDB ===\n")
        
        # 1. Health check
        response = await client.get(f"{API_URL}/health")
        print(f"Health check: {response.json()}")
        
        # 2. Add episode
        print("\n1. Adding episode...")
        add_data = {
            "name": "Test Episode",
            "content": "John works at Acme Corp as a software engineer.",
            "source": "test",
            "source_description": "Test source",
            "group_id": "test-deletion"
        }
        response = await client.post(f"{API_URL}/add_episode", json=add_data)
        if response.status_code == 200:
            episode_data = response.json()
            print(f"Response data: {episode_data}")
            episode_uuid = episode_data.get("episode_id") or episode_data.get("episode_uuid") or episode_data.get("uuid")
            print(f"✅ Episode added: {episode_uuid}")
        else:
            print(f"❌ Failed to add episode: {response.text}")
            return
        
        # 3. Search to verify
        print("\n2. Searching for added data...")
        search_data = {
            "query": "John",
            "group_id": "test-deletion"
        }
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results.get('results', []))} results")
        else:
            print(f"❌ Search failed: {response.text}")
        
        # 4. Delete episode
        print(f"\n3. Deleting episode {episode_uuid}...")
        delete_data = {
            "episode_uuid": episode_uuid
        }
        response = await client.request(
            "DELETE", 
            f"{API_URL}/episodes",
            json=delete_data
        )
        if response.status_code == 200:
            print(f"✅ {response.json()}")
        else:
            print(f"❌ Delete failed: {response.text}")
            return
        
        # 5. Search again to verify deletion
        print("\n4. Searching again to verify deletion...")
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            count = len(results.get('results', []))
            if count == 0:
                print("✅ Data successfully deleted - no results found")
            else:
                print(f"⚠️ Found {count} results after deletion")
        else:
            print(f"❌ Search failed: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_deletion())