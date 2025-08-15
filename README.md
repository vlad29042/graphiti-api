# Graphiti API Service

Production-ready HTTP API обёртка для [Graphiti](https://github.com/getzep/graphiti) - фреймворка для построения временных графов знаний для AI агентов.

## Зачем эта обёртка?

Graphiti мощный инструмент, но имеет конфликты event loop при прямой интеграции с асинхронными системами. Эта FastAPI обёртка решает проблему через:
- Запуск Graphiti в изолированном процессе со своим event loop
- Предоставление RESTful HTTP endpoints для универсального доступа
- Добавление n8n-совместимых endpoints для автоматизации
- Включение health checks и мониторинга

## Возможности

- ✅ **Изоляция Event Loop** - Нет конфликтов с другими async системами
- ✅ **RESTful API** - HTTP интерфейс, не зависящий от языка
- ✅ **Интеграция с n8n** - Прямая совместимость с n8n workflows
- ✅ **Мониторинг здоровья** - Встроенные health checks
- ✅ **Docker Ready** - Production развёртывание через docker-compose
- ✅ **OpenAPI документация** - Автогенерируемая документация API на `/docs`
- ✅ **Оценка релевантности** - Фильтрация результатов по score (требует форк Graphiti)

## Быстрый старт

### Требования

- Docker и Docker Compose
- Neo4j 5.26+ (включён в docker-compose)
- OpenAI API ключ

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/graphiti-api.git
cd graphiti-api
```

2. Создайте файл `.env`:
```env
# Настройки Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=ваш_надёжный_пароль

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

#### Поиск
```bash
POST /search
{
  "query": "Расскажи про Tesla",
  "group_ids": ["project_123"],
  "search_type": "hybrid",
  "limit": 10
}
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

Ответ включает оценки релевантности:
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

## Архитектура

```
┌─────────┐     HTTP      ┌─────────────┐     Bolt      ┌────────┐
│  Клиент │ ─────────────▶│ Graphiti API│ ─────────────▶│ Neo4j  │
└─────────┘               │   (FastAPI) │                └────────┘
                          └─────────────┘
                                 │
                                 ▼
                          Использует graphiti-core
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `NEO4J_URI` | URI подключения к Neo4j | `bolt://neo4j:7687` |
| `NEO4J_USER` | Имя пользователя Neo4j | `neo4j` |
| `NEO4J_PASSWORD` | Пароль Neo4j | Обязательно |
| `OPENAI_API_KEY` | API ключ OpenAI | Обязательно |
| `DEFAULT_LLM_MODEL` | LLM модель для обработки | `gpt-4o-mini` |
| `DEFAULT_EMBEDDING_MODEL` | Модель для эмбеддингов | `text-embedding-3-small` |

### Использование кастомного форка Graphiti

Для использования форка с поддержкой score:

1. Обновите `requirements.txt`:
```
git+https://github.com/yourusername/graphiti.git@main
```

2. Обновите Dockerfile для установки git:
```dockerfile
RUN apt-get update && apt-get install -y gcc g++ git && rm -rf /var/lib/apt/lists/*
```

## Разработка

### Локальная разработка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите локально:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Структура проекта

```
graphiti-api/
├── app/
│   ├── __init__.py
│   ├── config.py         # Управление конфигурацией
│   ├── main.py           # FastAPI приложение
│   ├── graphiti_logic.py # Интеграция с Graphiti
│   └── n8n_routes.py     # n8n-специфичные endpoints
├── docker-compose.yml    # Оркестрация контейнеров
├── Dockerfile            # Определение контейнера API
├── requirements.txt      # Python зависимости
├── .env.example         # Шаблон окружения
└── README.md            # Этот файл
```

## Развёртывание

### Production развёртывание

1. Используйте надёжные пароли для Neo4j
2. Настройте SSL/TLS терминацию (nginx/traefik)
3. Настройте логирование
4. Настройте мониторинг (Prometheus/Grafana)
5. Используйте менеджер секретов для API ключей

### Docker Compose

Включённый `docker-compose.yml` предоставляет:
- Neo4j база данных с постоянным хранилищем
- Health checks для обоих сервисов
- Политики автоматического перезапуска
- Изоляция сети

## Решение проблем

### Частые проблемы

1. **Ошибка подключения к Neo4j**
   - Проверьте что Neo4j запущен: `docker-compose ps`
   - Проверьте учётные данные в `.env`
   - Проверьте логи Neo4j: `docker-compose logs neo4j`

2. **Ошибки OpenAI API**
   - Проверьте валидность API ключа
   - Проверьте лимиты запросов
   - Мониторьте использование в OpenAI dashboard

3. **Пустые результаты поиска**
   - Убедитесь что данные успешно загружены
   - Проверьте что group_id совпадает
   - Проверьте существование Neo4j индексов

## Участие в разработке

1. Сделайте форк репозитория
2. Создайте ветку для фичи
3. Внесите изменения
4. Добавьте тесты
5. Отправьте pull request

## Лицензия

Эта обёртка лицензирована под MIT License.
Graphiti лицензирован под Apache 2.0 License.

## Благодарности

- Основано на [Graphiti](https://github.com/getzep/graphiti) от Zep
- Вдохновлено статьёй ["A Production-Ready API for Graphiti"](https://medium.com/@saeed.hajebi) от Saeed Hajebi