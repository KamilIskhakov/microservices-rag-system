# Request Processor Service - Техническая документация

## Обзор сервиса

Request Processor Service выполняет роль координатора между различными микросервисами системы. Сервис обрабатывает входящие запросы, координирует взаимодействие между AI Model Service, Vector Store Service и другими сервисами, а также обеспечивает агрегацию результатов для формирования единого ответа клиенту.

## Архитектура

### Слои архитектуры

#### Domain Layer
- **Entities**: `Request` - доменная сущность запроса
- **Repositories**: `RequestRepository` - абстрактный интерфейс для работы с запросами
- **Services**: `RequestService` - доменный сервис для координации запросов

#### Application Layer
- **Use Cases**: Обработка и координация запросов
- **Commands**: Команды для управления процессом обработки

#### Infrastructure Layer
- **Persistence**: `InMemoryRepository` - реализация репозитория
- **API**: FastAPI endpoints для внешнего взаимодействия
- **HTTP Client**: aiohttp для межсервисного взаимодействия

### Ключевые компоненты

#### Request Entity
```python
@dataclass
class Request:
    id: str
    user_id: str
    query: str
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
```

#### RequestRepository Interface
```python
class RequestRepository(ABC):
    @abstractmethod
    def save_request(self, request: Request) -> str:
        pass
    
    @abstractmethod
    def get_request(self, request_id: str) -> Optional[Request]:
        pass
    
    @abstractmethod
    def update_request(self, request: Request) -> bool:
        pass
    
    @abstractmethod
    def get_requests_by_user(self, user_id: str) -> List[Request]:
        pass
```

## API Endpoints

### Health Check
```
GET /health
```
Возвращает статус сервиса и статистику обработки запросов.

### Request Processing

#### Process Request
```
POST /process
Request Body:
{
    "user_id": "user123",
    "query": "текст для анализа",
    "context": ["дополнительный контекст"],
    "options": {
        "max_results": 5,
        "threshold": 0.3,
        "include_metadata": true
    }
}
```
Обрабатывает запрос пользователя и возвращает результат анализа.

#### Get Request Status
```
GET /request/{request_id}
```
Возвращает статус и результат обработки запроса.

#### List User Requests
```
GET /requests/{user_id}
Parameters:
- limit: int (optional, default: 10)
- offset: int (optional, default: 0)
- status: str (optional)
```
Возвращает список запросов пользователя с возможностью фильтрации.

### Batch Processing

#### Process Batch Requests
```
POST /process/batch
Request Body:
{
    "requests": [
        {
            "user_id": "user123",
            "query": "запрос 1"
        },
        {
            "user_id": "user123",
            "query": "запрос 2"
        }
    ],
    "options": {
        "parallel": true,
        "max_concurrent": 3
    }
}
```
Обрабатывает несколько запросов одновременно.

### Statistics

#### Request Statistics
```
GET /statistics/requests
```
Возвращает статистику по запросам:
- Общее количество запросов
- Количество запросов по статусам
- Среднее время обработки
- Количество ошибок

#### User Statistics
```
GET /statistics/users/{user_id}
```
Возвращает статистику по конкретному пользователю:
- Количество запросов
- Среднее время обработки
- Частота использования

## Конфигурация

### Environment Variables

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `REQUEST_PROCESSOR_HOST` | Хост для привязки | `0.0.0.0` |
| `REQUEST_PROCESSOR_PORT` | Порт для привязки | `8004` |
| `AI_MODEL_URL` | URL AI Model Service | `http://ai-model:8003` |
| `VECTOR_STORE_URL` | URL Vector Store Service | `http://vectorstore:8002` |
| `PAYMENT_URL` | URL Payment Service | `http://payment:8005` |
| `REQUEST_TIMEOUT` | Таймаут запросов (сек) | `30` |
| `MAX_CONCURRENT_REQUESTS` | Максимум одновременных запросов | `10` |

### Docker Configuration

```yaml
request-processor:
  build:
    context: ../../services/request-processor
    dockerfile: Dockerfile
  environment:
    - REQUEST_PROCESSOR_HOST=0.0.0.0
    - REQUEST_PROCESSOR_PORT=8004
    - AI_MODEL_URL=http://ai-model:8003
    - VECTOR_STORE_URL=http://vectorstore:8002
    - PAYMENT_URL=http://payment:8005
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
```

## Алгоритмы и стратегии

### Request Processing Pipeline

Сервис реализует многоэтапный pipeline для обработки запросов:

#### 1. Validation Stage
```python
def validate_request(self, request_data: Dict[str, Any]) -> bool:
    # Проверка обязательных полей
    required_fields = ["user_id", "query"]
    for field in required_fields:
        if field not in request_data:
            return False
    
    # Валидация длины запроса
    if len(request_data["query"].strip()) < 1:
        return False
    
    # Проверка лимитов пользователя
    user_id = request_data["user_id"]
    usage_info = self.payment_service.check_usage_limit(user_id)
    if not usage_info["can_use"]:
        return False
    
    return True
```

#### 2. Payment Check Stage
```python
async def check_user_limits(self, user_id: str) -> Dict[str, Any]:
    try:
        response = await self.http_client.get(
            f"{self.payment_url}/subscription/{user_id}/limit"
        )
        return response.json()
    except Exception as e:
        # В случае недоступности Payment Service, разрешаем запрос
        return {"can_use": True, "plan_type": "free"}
```

#### 3. Vector Search Stage
```python
async def search_similar_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    try:
        response = await self.http_client.post(
            f"{self.vector_store_url}/search",
            json={
                "query": query,
                "top_k": top_k,
                "threshold": 0.3
            }
        )
        return response.json()["results"]
    except Exception as e:
        # Возвращаем пустой результат при ошибке
        return []
```

#### 4. AI Generation Stage
```python
async def generate_analysis(self, query: str, context: List[str]) -> str:
    try:
        response = await self.http_client.post(
            f"{self.ai_model_url}/generate",
            json={
                "query": query,
                "context": context,
                "max_length": 512,
                "temperature": 0.7
            }
        )
        return response.json()["result"]
    except Exception as e:
        raise Exception(f"AI generation failed: {str(e)}")
```

#### 5. Usage Update Stage
```python
async def update_user_usage(self, user_id: str) -> bool:
    try:
        response = await self.http_client.post(
            f"{self.payment_url}/subscription/{user_id}/usage",
            json={"usage_count": 1}
        )
        return response.status_code == 200
    except Exception as e:
        # Логируем ошибку, но не прерываем обработку
        return False
```

### Concurrent Processing Strategy

```python
async def process_requests_concurrently(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def process_single_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            return await self.process_request(request_data)
    
    tasks = [process_single_request(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [
        result if not isinstance(result, Exception) 
        else {"error": str(result)} 
        for result in results
    ]
```

### Error Handling Strategy

```python
async def process_request_with_retry(self, request_data: Dict[str, Any], 
                                   max_retries: int = 3) -> Dict[str, Any]:
    for attempt in range(max_retries):
        try:
            return await self.process_request(request_data)
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "error": f"Request processing failed after {max_retries} attempts: {str(e)}",
                    "status": "failed"
                }
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Обработка ошибок

### Типы ошибок

1. **RequestValidationError**: Ошибка валидации запроса
2. **UserLimitExceededError**: Превышен лимит пользователя
3. **ServiceUnavailableError**: Сервис недоступен
4. **ProcessingError**: Ошибка обработки запроса
5. **TimeoutError**: Таймаут обработки

### Обработка исключений

```python
async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    request = Request(
        id=str(uuid.uuid4()),
        user_id=request_data["user_id"],
        query=request_data["query"],
        created_at=datetime.now(),
        metadata=request_data.get("options", {})
    )
    
    try:
        # Сохранение запроса
        request_id = self.repository.save_request(request)
        
        # Обновление статуса
        request.status = "processing"
        request.started_at = datetime.now()
        self.repository.update_request(request)
        
        # Проверка лимитов пользователя
        usage_info = await self.check_user_limits(request.user_id)
        if not usage_info["can_use"]:
            raise UserLimitExceededError("Daily limit exceeded")
        
        # Поиск похожих документов
        similar_docs = await self.search_similar_documents(request.query)
        
        # Генерация анализа
        analysis = await self.generate_analysis(request.query, similar_docs)
        
        # Обновление использования
        await self.update_user_usage(request.user_id)
        
        # Формирование результата
        result = {
            "analysis": analysis,
            "similar_documents": similar_docs,
            "usage_info": usage_info
        }
        
        request.status = "completed"
        request.completed_at = datetime.now()
        request.result = result
        self.repository.update_request(request)
        
        return {
            "request_id": request_id,
            "status": "completed",
            "result": result
        }
        
    except Exception as e:
        request.status = "failed"
        request.completed_at = datetime.now()
        request.error_message = str(e)
        self.repository.update_request(request)
        
        raise ProcessingError(f"Failed to process request: {str(e)}")
```

## Мониторинг и метрики

### Health Check

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "request-processor",
        "total_requests": len(request_service.get_all_requests()),
        "active_requests": len(request_service.get_active_requests()),
        "average_processing_time": request_service.get_average_processing_time()
    }
```

### Метрики производительности

- Время обработки запросов
- Количество успешных/неуспешных запросов
- Задержка между сервисами
- Использование ресурсов

## Безопасность

### Валидация входных данных

```python
class ProcessRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=10000)
    context: List[str] = Field(default_factory=list)
    options: Dict[str, Any] = Field(default_factory=dict)

class BatchProcessRequest(BaseModel):
    requests: List[ProcessRequest] = Field(min_items=1, max_items=100)
    options: Dict[str, Any] = Field(default_factory=dict)
```

### Rate Limiting

```python
class RequestRateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests = {}
    
    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Очистка старых запросов (старше 1 минуты)
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] 
            if now - req_time < 60
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
```

## Разработка и тестирование

### Локальная разработка

```bash
# Запуск сервиса
cd services/request-processor
python api/main.py

# Тестирование API
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "query": "тестовый запрос"}'
```

### Unit тесты

```python
def test_request_validation():
    processor = RequestProcessor()
    valid_request = {
        "user_id": "test_user",
        "query": "test query"
    }
    assert processor.validate_request(valid_request) == True

def test_request_creation():
    repository = InMemoryRepository()
    request = Request(
        id="test-1",
        user_id="test_user",
        query="test query",
        created_at=datetime.now()
    )
    request_id = repository.save_request(request)
    assert request_id == "test-1"
```

### Integration тесты

```python
def test_request_processing():
    response = client.post("/process", json={
        "user_id": "test_user",
        "query": "test query"
    })
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["status"] == "completed"

def test_batch_processing():
    response = client.post("/process/batch", json={
        "requests": [
            {"user_id": "test_user", "query": "query 1"},
            {"user_id": "test_user", "query": "query 2"}
        ]
    })
    assert response.status_code == 200
    assert len(response.json()["results"]) == 2
```

## Масштабирование

### Горизонтальное масштабирование

- Множественные инстансы Request Processor Service
- Балансировка нагрузки через API Gateway
- Общее хранилище для состояния запросов

### Вертикальное масштабирование

- Увеличение количества одновременных запросов
- Оптимизация алгоритмов обработки
- Улучшение стратегий кэширования

## Интеграция с другими сервисами

### AI Model Service
- Генерация анализа на основе запроса и контекста
- Получение результатов обработки текста

### Vector Store Service
- Поиск похожих документов
- Получение релевантного контекста

### Payment Service
- Проверка лимитов пользователей
- Обновление счетчиков использования

### API Gateway
- Получение запросов от клиентов
- Возврат результатов обработки

## Планы развития

### Краткосрочные цели
- Добавление кэширования результатов
- Улучшение обработки ошибок
- Реализация приоритизации запросов

### Долгосрочные цели
- Реализация асинхронной обработки
- Добавление поддержки WebSocket
- Интеграция с системами мониторинга
