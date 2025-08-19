# Graphiti API Service with FalkorDB

Production-ready HTTP API обёртка для [Graphiti](https://github.com/getzep/graphiti) - фреймворка для построения временных графов знаний для AI агентов.

## Автор

- **Telegram канал**: [FlowHubN8N](https://t.me/FlowHubN8N) - проекты и архитектуры на базе n8n
- **Специализация**: Production системы с микросервисной архитектурой, интеграция AI в бизнес-процессы
- **Применение Graphiti**: Замена векторных БД, динамическая альтернатива статическим промптам, основа для систем самообучения

## Почему FalkorDB вместо Neo4j?

Этот сервис использует **FalkorDB** вместо Neo4j Community Edition по следующим причинам:

### 🚀 Нативная поддержка векторного поиска
- **FalkorDB v4.0+** имеет встроенную поддержку векторных операций через тип `vecf32`
- **Neo4j Community Edition** НЕ поддерживает `vector.similarity.cosine`, что критично для семантического поиска
- Не нужны дополнительные плагины или Enterprise лицензия

### 💯 Полная совместимость с Graphiti
- Используется [форк Graphiti](https://github.com/vlad29042/graphiti) с поддержкой FalkorDB
- Все функции работают из коробки без модификаций
- Сохраняется полная функциональность временных графов знаний

### ⚡ Производительность и простота
- Меньший размер Docker образа
- Быстрее запускается
- Проще конфигурация
- Open source без ограничений

## 🔍 Fulltext Search Implementation

### Проблема: Отсутствие db.idx.fulltext.queryRelationships

FalkorDB v4.2.2 не поддерживает процедуру `db.idx.fulltext.queryRelationships`, которая есть в Neo4j. Эта функциональность планируется, но еще не реализована (см. [GitHub Issue #1211](https://github.com/FalkorDB/FalkorDB/issues/1211)).

### Решение: FactIndex Pattern

Форк Graphiti реализует умное решение через FactIndex узлы:

#### 1. При добавлении данных
Для каждой связи с фактом создается соответствующий FactIndex узел:
```python
FactIndexNode(
    fact_id=edge.uuid,           # UUID оригинальной связи
    text=edge.fact,              # Полный текст факта
    text_lower=fact.lower(),     # Для регистронезависимого поиска
    keywords=keywords,           # Извлеченные ключевые слова
    group_id=edge.group_id       # Для фильтрации по контексту
)
```

#### 2. При поиске
```cypher
# Вместо несуществующего в FalkorDB:
CALL db.idx.fulltext.queryRelationships("RELATES_TO", "search query")

# Используется:
CALL db.idx.fulltext.queryNodes("FactIndex", "search query")
YIELD node AS fact_node, score
// Затем извлекается оригинальная связь
MATCH (n:Entity)-[e:RELATES_TO {uuid: fact_node.fact_id}]->(m:Entity)
RETURN e, n, m, score
```

### Поддерживаемые операторы поиска

FactIndex поддерживает все операторы RediSearch:

| Оператор | Пример | Описание |
|----------|---------|----------|
| Wildcards | `Tesla*` | Найдет "Tesla", "Teslas", "Tesla's" |
| Phrases | `"founded in 2003"` | Точное совпадение фразы |
| OR | `Tesla \| SpaceX` | Любой из терминов |
| NOT | `Musk -Twitter` | Исключает результаты с "Twitter" |
| Combined | `"Elon Musk" Tesla* -Twitter` | Сложные запросы |

### Пример работы поиска

```python
# Пользователь ищет "Tesla founded"
POST /search
{
  "query": "Tesla founded*",
  "group_ids": ["company_data"],
  "search_type": "hybrid"
}

# Внутренний процесс:
# 1. Векторный поиск по эмбеддингам сущностей
# 2. Fulltext поиск по FactIndex узлам
# 3. Объединение и ранжирование результатов по релевантности

# Результат включает score благодаря форку:
{
  "facts": [
    {
      "fact": "Tesla was founded by Elon Musk in 2003",
      "uuid": "...",
      "relevance_score": 0.92  # Высокая релевантность
    }
  ]
}
```

### Производительность

- **Storage overhead**: ~20% из-за FactIndex узлов
- **Search performance**: Сравнима с нативным fulltext поиском
- **Indexing**: Происходит автоматически при добавлении эпизодов
- **Migration path**: Легко перейти на нативную поддержку когда она появится

## Ключевые изменения в этой версии

### 1. Полный переход на FalkorDB
- Удалены все зависимости от Neo4j
- Конфигурация упрощена до трёх переменных: `FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_PASSWORD`
- Docker Compose использует официальный образ FalkorDB

### 2. Использование форка Graphiti
- Используется [форк](https://github.com/vlad29042/graphiti) с поддержкой FalkorDB
- Добавлена поддержка relevance score в результатах
- Реализован FactIndex для fulltext поиска по связям

### 3. Исправления и улучшения
- ✅ Исправлена ошибка `'score' not defined` при удалении эпизодов
- ✅ Правильная обработка свойств объектов FalkorDB через `.properties`
- ✅ Добавлены новые endpoints для работы с эпизодами
- ✅ Улучшена обработка векторного поиска с расчётом score
- ✅ **ВАЖНО**: Исправлена проблема с паролем FalkorDB - в docker-compose убран пароль из настроек graphiti сервиса
- ✅ Исправлен метод `retrieve_episodes` - добавлен обязательный параметр `reference_time`

### 4. Новые возможности
- **CRUD операции для эпизодов**: создание, чтение, обновление, удаление
- **Поиск с оценкой релевантности**: фильтрация результатов по score
- **Управление узлами и фактами**: полный доступ к графу знаний
- **Fulltext поиск**: поддержка всех операторов RediSearch
- **Тесты**: набор тестов для проверки всех функций

## Возможности

- ✅ **Векторный поиск из коробки** - Нативная поддержка в FalkorDB
- ✅ **Fulltext поиск по фактам** - Через FactIndex pattern
- ✅ **Изоляция Event Loop** - Нет конфликтов с другими async системами
- ✅ **RESTful API** - HTTP интерфейс, не зависящий от языка
- ✅ **Интеграция с n8n** - Прямая совместимость с n8n workflows
- ✅ **Мониторинг здоровья** - Встроенные health checks
- ✅ **Docker Ready** - Production развёртывание через docker-compose
- ✅ **OpenAPI документация** - Автогенерируемая документация API на `/docs`
- ✅ **Оценка релевантности** - Фильтрация результатов по score

## Зачем эта обёртка?

Graphiti мощный инструмент, но имеет конфликты event loop при прямой интеграции с асинхронными системами. Эта FastAPI обёртка решает проблему через:
- Запуск Graphiti в изолированном процессе со своим event loop
- Предоставление RESTful HTTP endpoints для универсального доступа
- Добавление n8n-совместимых endpoints для автоматизации
- Включение health checks и мониторинга

## Быстрый старт

### Требования

- Docker и Docker Compose
- FalkorDB (включён в docker-compose)
- OpenAI API ключ

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/vlad29042/graphiti-api.git
cd graphiti-api
```

2. Создайте файл `.env`:
```env
# Настройки FalkorDB
FALKORDB_HOST=falkordb
FALKORDB_PORT=6379
FALKORDB_PASSWORD=ваш_надёжный_пароль

# Настройки OpenAI
OPENAI_API_KEY=ваш_openai_api_ключ

# Настройки моделей
DEFAULT_LLM_MODEL=gpt-4o-mini
DEFAULT_EMBEDDING_MODEL=text-embedding-3-small
```

3. Запустите сервисы:
```bash
docker-compose up -d
```

API будет доступен по адресу `http://localhost:8000`

## API Endpoints

Полная документация доступна на `/docs` (Swagger UI) после запуска сервиса.

### Основные endpoints

#### Добавление сообщений
```bash
POST /messages
{
  "group_id": "project_123",
  "messages": [
    {
      "role": "user",
      "content": "Tesla была основана в 2003 году Илоном Маском"
    }
  ]
}
```

#### Поиск с векторной и fulltext релевантностью
```bash
POST /search
{
  "query": "Tesla основана*",  # Поддержка wildcards
  "group_ids": ["project_123"],
  "search_type": "hybrid",     # vector + fulltext
  "limit": 10,
  "min_score": 0.7            # Фильтр по релевантности
}
```

### Управление эпизодами

#### Создание эпизода
```bash
POST /episodes
{
  "group_id": "project_123",
  "name": "История Tesla",
  "content": "Tesla была основана в 2003 году"
}
```

#### Получение эпизода
```bash
GET /episodes/{episode_id}
```

#### Удаление эпизода
```bash
DELETE /episodes/{episode_id}
```

### n8n Endpoints

#### Получение памяти (n8n совместимый)
```bash
POST /get-memory
{
  "group_id": "project_123",
  "messages": [
    {
      "role": "user",
      "content": "Что ты знаешь про Tesla?"
    }
  ],
  "max_facts": 10,
  "min_score": 0.7  // Опционально: фильтр по релевантности
}
```

Ответ включает оценки релевантности благодаря векторному и fulltext поиску:
```json
{
  "facts": [
    {
      "fact": "Tesla была основана в 2003 году Илоном Маском",
      "uuid": "...",
      "created_at": "2024-01-01T00:00:00Z",
      "valid_at": "2003-01-01T00:00:00Z",
      "invalid_at": null,
      "relevance_score": 0.92  // Комбинированный score
    }
  ]
}
```

### CRUD операции

#### Удаление эпизода (DELETE)
```bash
DELETE /episodes
{
  "episode_uuid": "uuid-эпизода-для-удаления"
}
```

#### Альтернативное удаление эпизода (POST)
```bash
POST /api/remove-episode
{
  "episode_uuid": "uuid-эпизода-для-удаления"
}
```

#### Получение эпизодов по группе
```bash
GET /episodes/{group_id}?last_n=20
```

#### Получение всех узлов (entities)
```bash
GET /nodes?group_id=project_123&limit=100
```

#### Получение всех фактов (edges)
```bash
GET /facts?group_id=project_123&limit=100
```

#### Удаление факта
```bash
DELETE /facts
{
  "fact_uuid": "uuid-факта-для-удаления"
}
```

#### Обновление факта
```bash
PUT /facts
{
  "fact_uuid": "uuid-факта",
  "new_fact": "Обновленная информация"
}
```

### Проверка здоровья
```bash
GET /health
```

## Векторный поиск в FalkorDB

FalkorDB вычисляет релевантность через косинусное расстояние:
```cypher
// Формула расчёта score в FalkorDB
score = (2 - vec.cosineDistance(embedding1, embedding2)) / 2
```

Где:
- `score = 1.0` - идеальное совпадение
- `score = 0.5` - средняя релевантность
- `score = 0.0` - полное несовпадение

## Архитектура

```
┌─────────┐     HTTP      ┌─────────────┐     Redis      ┌──────────┐
│  Клиент │ ─────────────▶│ Graphiti API│ ─────────────▶│ FalkorDB │
└─────────┘               │   (FastAPI) │   Protocol     └──────────┘
                          └─────────────┘
                                 │
                                 ▼
                          Использует форк graphiti
                          с FalkorDriver и FactIndex
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `FALKORDB_HOST` | Хост FalkorDB | `falkordb` |
| `FALKORDB_PORT` | Порт FalkorDB | `6379` |
| `FALKORDB_PASSWORD` | Пароль FalkorDB | Обязательно |
| `OPENAI_API_KEY` | API ключ OpenAI | Обязательно |
| `DEFAULT_LLM_MODEL` | LLM модель для обработки | `gpt-4o-mini` |
| `DEFAULT_EMBEDDING_MODEL` | Модель для эмбеддингов | `text-embedding-3-small` |

## Тестирование

В папке `tests/` находятся тесты для проверки всех функций:

- `test_deletion.py` - Тест удаления эпизодов
- `test_vector_search.py` - Тест векторного поиска
- `test_full_cycle.py` - Полный цикл: создание, поиск, удаление
- `test_detailed_score.py` - Детальная демонстрация расчёта score
- `test_score_demonstration.py` - Демонстрация работы score
- `test_final_score.py` - Финальный тест с явным отображением score

Запуск тестов:
```bash
python tests/test_full_cycle.py
```

## Разработка

### Структура проекта

```
graphiti-api/
├── app/
│   ├── __init__.py
│   ├── config.py         # Конфигурация FalkorDB
│   ├── main.py           # FastAPI приложение
│   ├── graphiti_logic.py # Интеграция с форком Graphiti
│   ├── crud_routes.py    # CRUD операции
│   └── n8n_routes.py     # n8n-специфичные endpoints
├── tests/                # Тесты функциональности
├── docker-compose.yml    # Оркестрация с FalkorDB
├── Dockerfile           
├── requirements.txt      # Включает форк graphiti
└── README.md            
```

## Production советы

### 1. Группировка знаний

Используйте разные `group_id` для разделения контекстов:
- `company_knowledge` - знания о компании
- `product_catalog` - каталог продукции  
- `customer_interactions` - история взаимодействий
- `technical_docs` - техническая документация

### 2. Оптимизация поиска

#### Векторный поиск
- Используйте `min_score` для фильтрации нерелевантных результатов
- Мониторьте распределение score для настройки порогов
- Экспериментируйте с разными embedding моделями

#### Fulltext поиск
- Используйте операторы RediSearch для точного поиска
- Wildcards полезны для поиска вариаций слов
- Фразы в кавычках для точных совпадений
- OR для расширения поиска, NOT для фильтрации

### 3. Мониторинг

- Отслеживайте размер графа и количество FactIndex узлов
- Мониторьте время ответа векторного и fulltext поиска
- Логируйте relevance_score для оптимизации порогов
- Следите за GitHub Issue #1211 для обновлений FalkorDB

## Решение проблем

### Частые проблемы

1. **Ошибка подключения к FalkorDB**
   - Проверьте что FalkorDB запущен: `docker-compose ps`
   - **ВАЖНО**: В настройках graphiti в docker-compose уберите пароль: `FALKORDB_PASSWORD=` (пустое значение)
   - Проверьте логи: `docker-compose logs falkordb`

2. **Ошибка `retrieve_episodes() missing 1 required positional argument: 'reference_time'`**
   - Метод `retrieve_episodes` требует обязательный параметр `reference_time`
   - Исправлено в последней версии - автоматически используется текущее время

3. **Низкие score при поиске**
   - Проверьте качество embedding модели
   - Убедитесь что контент достаточно семантически богат
   - Попробуйте другую модель эмбеддингов
   - Используйте операторы fulltext поиска для улучшения результатов

4. **Ошибка 'score' not defined**
   - Убедитесь что используется правильный форк graphiti
   - Проверьте что не используются старые Neo4j запросы

5. **Fulltext поиск не находит результаты**
   - Проверьте что FactIndex узлы создаются при добавлении данных
   - Используйте правильные операторы RediSearch
   - Помните что поиск регистрозависимый для точных фраз

## Благодарности

- Основано на [Graphiti](https://github.com/getzep/graphiti) от Zep
- Использует [форк Graphiti](https://github.com/vlad29042/graphiti) с поддержкой FalkorDB
- Работает с [FalkorDB](https://github.com/FalkorDB/FalkorDB) для графовых операций
- Вдохновлено необходимостью векторного и fulltext поиска в Community версии

## Лицензия

Эта обёртка лицензирована под MIT License.
Graphiti лицензирован под Apache 2.0 License.
FalkorDB лицензирован под их соответствующими лицензиями.