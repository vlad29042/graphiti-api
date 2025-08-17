# Graphiti API with FalkorDB Support

This API wrapper provides HTTP endpoints for Graphiti knowledge graph with full FalkorDB support.

## Features

- Full FalkorDB support with FactIndex pattern for relationship search
- RediSearch operators (wildcards, phrases, OR, NOT)
- Vector search with proper scoring
- Hybrid search capabilities
- Complete CRUD operations

## Installation

```bash
# Clone repository
git clone https://github.com/vlad29042/graphiti-api.git
cd graphiti-api

# Install dependencies
pip install -r requirements.txt

# Copy environment example
cp .env.example .env

# Edit .env and set your OpenAI API key
```

## Running with Docker

```bash
# Start FalkorDB and API
docker-compose up -d

# API will be available at http://localhost:8000
```

## Quick Start

```python
import requests

# Add episode
response = requests.post("http://localhost:8000/add_episode", json={
    "name": "Company Info",
    "content": "DonKrovlyaStroy sells metal tiles for 550 rubles per square meter.",
    "source_description": "Business data"
})

# Search with RediSearch operators
response = requests.post("http://localhost:8000/search", json={
    "query": "metal* | tiles",  # OR search
    "group_ids": ["default"],
    "limit": 10
})
```

## API Endpoints

- `POST /add_episode` - Add new episode
- `POST /search` - Search with fulltext and vector
- `GET /nodes` - Get nodes
- `GET /facts` - Get relationships
- `DELETE /episodes` - Delete episode
- `PUT /facts` - Update fact

## Configuration

Environment variables in `.env`:

```env
# OpenAI API Key (required)
OPENAI_API_KEY=your_key_here

# FalkorDB connection
FALKORDB_HOST=localhost
FALKORDB_PORT=6379
FALKORDB_PASSWORD=

# API settings
API_PORT=8000
LOG_LEVEL=INFO
```

## Testing

Run comprehensive test:

```bash
python test_http_factindex.py
```

## License

Same as original Graphiti project.