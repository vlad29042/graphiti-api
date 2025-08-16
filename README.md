# Graphiti API Service with FalkorDB

Production-ready HTTP API обёртка для [Graphiti](https://github.com/getzep/graphiti) - фреймворка для построения временных графов знаний для AI агентов.

## Автор

- **Telegram канал**: [FlowHubN8N](https://t.me/FlowHubN8N) - проекты и архитектуры на базе n8n
- **Специализация**: Production системы с микросервисной архитектурой, интеграция AI в бизнес-процессы
- **Применение Graphiti**: Замена векторных БД, динамическая альтернатива статическим промптам, основа для систем самообучения

## Почему FalkorDB вместо Neo4j?

Этот форк использует **FalkorDB** вместо Neo4j Community Edition по следующим причинам:

### 🚀 Нативная поддержка векторного поиска
- **FalkorDB v4.0+** имеет встроенную поддержку векторных операций через тип `vecf32`
- **Neo4j Community Edition** НЕ поддерживает `vector.similarity.cosine`, что критично для семантического поиска
- Не нужны дополнительные плагины или Enterprise лицензия

### 💯 Полная совместимость с Graphiti
- Graphiti уже имеет встроенную поддержку FalkorDB через `FalkorDriver`
- Все функции работают из коробки без модификаций
- Сохраняется полная функциональность временных графов знаний

### ⚡ Производительность и простота
- Меньший размер Docker образа
- Быстрее запускается
- Проще конфигурация
- Open source без ограничений

## Ключевые изменения в этой версии

### 1. Полный переход на FalkorDB
- Удалены все зависимости от Neo4j
- Конфигурация упрощена до трёх переменных: `FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_PASSWORD`
- Docker Compose использует официальный образ FalkorDB

### 2. Исправления и улучшения
- ✅ Исправлена ошибка `'score' not defined` при удалении эпизодов
- ✅ Правильная обработка свойств объектов FalkorDB через `.properties`
- ✅ Добавлены новые endpoints для работы с эпизодами
- ✅ Улучшена обработка векторного поиска с расчётом score

### 3. Новые возможности
- **CRUD операции для эпизодов**: создание, чтение, обновление, удаление
- **Поиск с оценкой релевантности**: фильтрация результатов по score
- **Управление узлами и фактами**: полный доступ к графу знаний
- **Тесты**: набор тестов для проверки всех функций

## Возможности

- ✅ **Векторный поиск из коробки** - Нативная поддержка в FalkorDB
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

#### Поиск с векторной релевантностью
```bash
POST /search
{
  "query": "Расскажи про Tesla",
  "group_ids": ["project_123"],
  "search_type": "hybrid",
  "limit": 10
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

Ответ включает оценки релевантности благодаря векторному поиску FalkorDB:
```json
{
  "facts": [
    {
      "fact": "Tesla была основана в 2003 году Илоном Маском",
      "uuid": "...",
      "created_at": "2024-01-01T00:00:00Z",
      "valid_at": "2003-01-01T00:00:00Z",
      "invalid_at": null,
      "relevance_score": 0.85
    }
  ]
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
                          Использует graphiti-core
                          с FalkorDriver
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
│   ├── graphiti_logic.py # Интеграция с Graphiti
│   ├── crud_routes.py    # CRUD операции
│   └── n8n_routes.py     # n8n-специфичные endpoints
├── tests/                # Тесты функциональности
├── docker-compose.yml    # Оркестрация с FalkorDB
├── Dockerfile           
├── requirements.txt      
└── README.md            
```

## Production советы

### 1. Группировка знаний

Используйте разные `group_id` для разделения контекстов:
- `company_knowledge` - знания о компании
- `product_catalog` - каталог продукции  
- `customer_interactions` - история взаимодействий
- `technical_docs` - техническая документация

### 2. Оптимизация векторного поиска

- Используйте `min_score` для фильтрации нерелевантных результатов
- Мониторьте распределение score для настройки порогов
- Экспериментируйте с разными embedding моделями

### 3. Мониторинг

- Отслеживайте размер графа
- Мониторьте время ответа векторного поиска
- Логируйте relevance_score для оптимизации

## Решение проблем

### Частые проблемы

1. **Ошибка подключения к FalkorDB**
   - Проверьте что FalkorDB запущен: `docker-compose ps`
   - Проверьте пароль в `.env`
   - Проверьте логи: `docker-compose logs falkordb`

2. **Низкие score при поиске**
   - Проверьте качество embedding модели
   - Убедитесь что контент достаточно семантически богат
   - Попробуйте другую модель эмбеддингов

3. **Ошибка 'score' not defined**
   - Убедитесь что используется правильная версия graphiti-core
   - Проверьте что не используются старые Neo4j запросы

## Благодарности

- Основано на [Graphiti](https://github.com/getzep/graphiti) от Zep
- Использует [FalkorDB](https://github.com/FalkorDB/FalkorDB) для графовых операций
- Вдохновлено необходимостью векторного поиска в Community версии

## Лицензия

Эта обёртка лицензирована под MIT License.
Graphiti лицензирован под Apache 2.0 License.
FalkorDB лицензирован под их соответствующими лицензиями.