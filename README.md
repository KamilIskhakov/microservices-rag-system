# Microservices-rag-system

Микросервисная система для анализа текстов на экстремизм с использованием RAG (Retrieval-Augmented Generation) и Chrome Extension.

## Архитектура

### Микросервисы
- **API Gateway** (FastAPI) - Единая точка входа, маршрутизация запросов
- **AI Model Service** (Python) - Управление Qwen2.5-3B-Instruct моделью
- **Vector Store Service** (FAISS) - Семантический поиск документов
- **Scraper Service** (Python) - Сбор данных с сайта Минюста
- **Payment Service** (Python) - Freemium модель (20 проверок/день)
- **Request Processor** (Python) - Координация между сервисами

### Технологический стек
- **Backend**: Python 3.11, FastAPI, aiohttp
- **AI/ML**: Transformers, PyTorch, Sentence Transformers
- **Vector DB**: FAISS
- **Cache**: Redis
- **Containerization**: Docker, Docker Compose
- **Frontend**: Chrome Extension (JavaScript)

## Принципы проектирования

### Clean Architecture
Каждый микросервис структурирован по слоям:
```
services/service-name/
├── domain/          # Бизнес-логика, сущности, репозитории
├── application/     # Use cases, координация
└── infrastructure/  # API, persistence, внешние зависимости
```

### SOLID принципы
- **SRP**: Каждый класс имеет одну ответственность
- **OCP**: Расширение через наследование/композицию
- **LSP**: Подтипы заменяют базовые типы
- **ISP**: Интерфейсы содержат только необходимые методы
- **DIP**: Зависимости от абстракций

### Паттерны проектирования
- **Repository Pattern** - Абстракция доступа к данным
- **Strategy Pattern** - Алгоритмы загрузки моделей (CPU/GPU)
- **Factory Pattern** - Создание объектов
- **Observer Pattern** - События и уведомления

## Ключевые технические решения

### Оптимизация AI модели
```python
# Автоматический выбор устройства
device = "cuda" if torch.cuda.is_available() else "cpu"

# Управление памятью
def optimize_memory(self):
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
```

### Векторный поиск
```python
# FAISS индекс для быстрого поиска
self.index = faiss.IndexFlatIP(dimension)
self.index.add(embeddings_array)

# Косинусное сходство
similarities, indices = self.index.search(query_vector, top_k)
```

### Асинхронная обработка
```python
# Concurrent processing с semaphore
semaphore = asyncio.Semaphore(max_concurrent)
async with semaphore:
    result = await self.process_request(request)
```

## API Endpoints

| Сервис | Порт | Основные endpoints |
|--------|------|-------------------|
| API Gateway | 8000 | `/health`, `/generate`, `/search` |
| AI Model | 8003 | `/health`, `/generate`, `/system-info` |
| Vector Store | 8002 | `/health`, `/search`, `/document` |
| Scraper | 8001 | `/health`, `/job`, `/data` |
| Payment | 8005 | `/health`, `/payment`, `/subscription` |
| Request Processor | 8004 | `/health`, `/process` |

## Развертывание

### Docker Compose
```bash
# Запуск всех сервисов
docker-compose -f infrastructure/docker/docker-compose.optimized.yml up -d

# Проверка статуса
curl http://localhost:8000/health
```

### Kubernetes
```bash
# Развертывание в кластере
kubectl apply -f infrastructure/kubernetes/
```

## Мониторинг и метрики

### Health Checks
Все сервисы предоставляют `/health` endpoints с информацией о:
- Статусе сервиса
- Использовании ресурсов
- Количестве активных запросов

### Метрики производительности
- Время ответа API (target: < 2s)
- Использование памяти (target: < 80%)
- Количество одновременных запросов
- Точность поиска (precision@5 > 0.8)

## Безопасность

### Валидация данных
```python
class RequestModel(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    user_id: str = Field(min_length=1, max_length=100)
```

### Rate Limiting
- 20 запросов/день для бесплатных пользователей
- 100 запросов/день для базового плана
- 1000 запросов/день для премиум плана

## Тестирование

### Unit тесты
```bash
cd services/ai-model
python -m pytest tests/
```

### Integration тесты
```bash
# Тест полного pipeline
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "user_id": "test_user"}'
```

## Производительность

### Оптимизации
- **Кэширование**: Redis для результатов поиска
- **Асинхронность**: aiohttp для межсервисного взаимодействия
- **Пул соединений**: Переиспользование HTTP соединений
- **Батчинг**: Группировка запросов к AI модели

### Масштабирование
- **Горизонтальное**: Множественные инстансы сервисов
- **Вертикальное**: Увеличение CPU/GPU ресурсов
- **Автоматическое**: Kubernetes HPA на основе метрик

## Документация

Подробная техническая документация в папке `docs/`:
- [AI Model Service](docs/ai-model-service.md)
- [Vector Store Service](docs/vector-store-service.md)
- [API Gateway Service](docs/api-gateway-service.md)
- [Scraper Service](docs/scraper-service.md)
- [Payment Service](docs/payment-service.md)
- [Request Processor Service](docs/request-processor-service.md)

## Развитие проекта

### Краткосрочные цели
- Добавление unit и integration тестов
- Реализация CI/CD pipeline
- Оптимизация производительности AI модели

### Долгосрочные цели
- Интеграция с внешними AI провайдерами
- Реализация распределенного скрапинга
- Добавление поддержки мультиязычности
