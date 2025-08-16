# Graphiti API Endpoints

База: `http://localhost:8000`

## Основные операции

### 1. POST /add_episode
Добавить новый эпизод (документ, событие)
```json
{
  "name": "Meeting notes",
  "content": "Discussed project timeline",
  "source_description": "Team meeting",
  "group_id": "project-123"
}
```

### 2. POST /search
Расширенный поиск
```json
{
  "query": "project timeline",
  "group_ids": ["project-123"],
  "num_results": 10,
  "focal_node_uuid": "optional-uuid"
}
```

## n8n-специфичные endpoints

### 3. POST /messages
Добавить сообщения чата
```json
{
  "group_id": "session-123",
  "messages": [
    {
      "content": "Hello AI",
      "role_type": "user",
      "timestamp": "2025-01-16T10:00:00Z"
    }
  ]
}
```

### 4. POST /get-memory
Получить релевантные факты для контекста
```json
{
  "group_id": "session-123",
  "messages": [{"content": "What about the project?", "role": "user"}],
  "max_facts": 20,
  "min_score": 0.7
}
```

### 5. GET /episodes/{group_id}
Получить эпизоды по группе
```
GET /episodes/session-123?last_n=20
```

### 6. POST /search/simple
Простой поиск
```
POST /search/simple?query=timeline&group_id=project-123
```

## CRUD операции

### 7. GET /nodes
Получить все узлы (сущности)
```
GET /nodes?group_id=project-123&limit=100
```

### 8. GET /facts  
Получить все факты (связи)
```
GET /facts?group_id=project-123&limit=100
```

### 9. DELETE /episodes ✅
Удалить эпизод (использует graphiti-core remove_episode)
```json
{
  "episode_uuid": "uuid-123",
  "group_id": "project-123"
}
```
Удаляет эпизод и все связанные с ним узлы/рёбра, которые больше нигде не используются.

### 10. DELETE /facts ✅
Удалить факт (инвалидация или физическое удаление)
```json
{
  "fact_uuid": "uuid-456",
  "group_id": "project-123"
}
```
По умолчанию выполняет временную инвалидацию (устанавливает invalid_at). Если не удаётся - физически удаляет.

### 11. PUT /facts ✅
Обновить факт (создаёт новую версию, инвалидирует старую)
```json
{
  "fact_uuid": "uuid-456",
  "new_fact": "Updated fact text",
  "group_id": "project-123"
}
```
Сохраняет историю изменений: старый факт помечается как недействительный, создаётся новый.

## Служебные

### 12. GET /
Главная страница

### 13. GET /health
Проверка состояния

## Итого: 13 endpoints

### Все endpoints реализованы! ✅

#### Основные операции:
- Чтение и добавление данных
- Поиск по knowledge graph
- n8n интеграция

#### CRUD операции:
- **DELETE /episodes** - использует `remove_episode` из graphiti-core
- **DELETE /facts** - временная инвалидация (preferred) или физическое удаление
- **PUT /facts** - обновление с сохранением истории (temporal versioning)
- Получение узлов и фактов через прямые запросы к Neo4j

### Особенности реализации:
1. **Temporal Knowledge Graph** - данные имеют временные метки (valid_at, invalid_at)
2. **Версионирование** - при обновлении фактов старые версии сохраняются с пометкой invalid_at
3. **Каскадное удаление** - при удалении эпизода удаляются только уникальные для него узлы/рёбра