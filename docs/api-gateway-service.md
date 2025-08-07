# API Gateway Service - Техническая документация

## Обзор сервиса

API Gateway Service служит единой точкой входа для всех клиентских запросов к микросервисной системе. Сервис реализует паттерн Gateway для маршрутизации запросов, агрегации ответов и обеспечения единообразного API интерфейса. Выполняет функции обратного прокси, балансировки нагрузки и централизованной обработки запросов.

## Архитектура

### Слои архитектуры

#### Domain Layer
- **Entities**: `GatewayRequest`, `ServiceEndpoint` - доменные сущности
- **Services**: `GatewayService` - доменный сервис для маршрутизации

#### Application Layer
- **Use Cases**: Обработка и маршрутизация запросов
- **Commands**: Команды для управления сервисами

#### Infrastructure Layer
- **API**: FastAPI endpoints для внешнего взаимодействия
- **HTTP Client**: aiohttp для межсервисного взаимодействия

### Ключевые компоненты

#### GatewayRequest Entity
```python
@dataclass
class GatewayRequest:
    id: str
    method: str
    path: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    status_code: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

#### ServiceEndpoint Entity
```python
@dataclass
class ServiceEndpoint:
    name: str
    url: str
    is_available: bool = True
    health_check_url: Optional[str] = None
    timeout: int = 30
```

#### GatewayService
```python
class GatewayService:
    def __init__(self):
        self.services = {
            "ai-model": ServiceEndpoint("ai-model", "http://ai-model:8003"),
            "vectorstore": ServiceEndpoint("vectorstore", "http://vectorstore:8002"),
            "scraper": ServiceEndpoint("scraper", "http://scraper:8001"),
            "request-processor": ServiceEndpoint("request-processor", "http://request-processor:8004"),
            "payment": ServiceEndpoint("payment", "http://payment:8005")
        }
```

## API Endpoints

### Health Check
```
GET /health
```
Возвращает агрегированную информацию о здоровье всех сервисов системы.

### Service Information
```
GET /services
```
Предоставляет информацию о всех доступных сервисах и их статусе.

### Service Health Check
```
GET /services/{service_name}/health
```
Проверяет здоровье конкретного сервиса.

### Request Routing
```
{method} /{path}
```
Маршрутизирует запросы к соответствующим микросервисам на основе пути.

### Statistics
```
GET /statistics
```
Возвращает статистику обработки запросов.

## Маршрутизация запросов

### Правила маршрутизации

Сервис определяет целевой микросервис на основе пути запроса:

```python
def _determine_target_service(self, path: str) -> Optional[str]:
    if path.startswith("/ai-model") or path.startswith("/generate") or path.startswith("/model"):
        return "ai-model"
    elif path.startswith("/vectorstore") or path.startswith("/search") or path.startswith("/document"):
        return "vectorstore"
    elif path.startswith("/scraper") or path.startswith("/job") or path.startswith("/data"):
        return "scraper"
    elif path.startswith("/request-processor") or path.startswith("/process"):
        return "request-processor"
    elif path.startswith("/payment") or path.startswith("/subscription"):
        return "payment"
    else:
        return None
```

### Примеры маршрутизации

| Путь | Целевой сервис | Описание |
|------|----------------|----------|
| `/generate` | AI Model Service | Генерация текста |
| `/search` | Vector Store Service | Поиск документов |
| `/job/create` | Scraper Service | Создание задачи скрапинга |
| `/process` | Request Processor Service | Обработка запросов |
| `/payment/create` | Payment Service | Создание платежа |

## Обработка запросов

### Request Flow

1. **Получение запроса**: Прием HTTP запроса от клиента
2. **Валидация**: Проверка корректности запроса
3. **Маршрутизация**: Определение целевого сервиса
4. **Проксирование**: Передача запроса к микросервису
5. **Агрегация**: Обработка ответа от микросервиса
6. **Возврат**: Отправка ответа клиенту

### Обработка ошибок

```python
async def route_request(self, method: str, path: str, headers: Dict[str, str] = None, 
                       body: Dict[str, Any] = None, user_id: str = None, 
                       session_id: str = None) -> Dict[str, Any]:
    try:
        # Определяем целевой сервис
        target_service = self._determine_target_service(path)
        if not target_service:
            raise ValueError(f"Неизвестный путь: {path}")
        
        # Проверяем доступность сервиса
        if not self.services[target_service].is_available:
            raise Exception(f"Сервис {target_service} недоступен")
        
        # Выполняем запрос
        response = await self._make_request(method, target_url, headers, body)
        
        return {
            "success": True,
            "target_service": target_service,
            "status_code": response["status_code"],
            "body": response["body"],
            "processing_time": processing_time
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processing_time": processing_time
        }
```

## Конфигурация

### Environment Variables

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `API_GATEWAY_HOST` | Хост для привязки | `0.0.0.0` |
| `API_GATEWAY_PORT` | Порт для привязки | `8000` |
| `REQUEST_TIMEOUT` | Таймаут запросов (сек) | `30` |
| `MAX_CONCURRENT_REQUESTS` | Максимум одновременных запросов | `100` |
| `ENABLE_CORS` | Включение CORS | `true` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

### Docker Configuration

```yaml
api-gateway:
  build:
    context: ../../services/api-gateway
    dockerfile: Dockerfile
  environment:
    - API_GATEWAY_HOST=0.0.0.0
    - API_GATEWAY_PORT=8000
    - REQUEST_TIMEOUT=30
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
```

## Стратегии обработки

### Load Balancing

Сервис поддерживает простую стратегию балансировки нагрузки:

```python
def _get_service_instance(self, service_name: str) -> ServiceEndpoint:
    # В будущем можно добавить более сложную логику
    # например, round-robin или least-connections
    return self.services[service_name]
```

### Circuit Breaker

Реализован простой circuit breaker для защиты от недоступных сервисов:

```python
def _check_service_health(self, service_name: str) -> bool:
    try:
        service = self.services[service_name]
        # Проверка здоровья сервиса
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{service.url}/health", timeout=5) as response:
                return response.status == 200
    except Exception:
        return False
```

### Retry Strategy

```python
async def _make_request_with_retry(self, method: str, url: str, 
                                  headers: Dict[str, str] = None, 
                                  body: Dict[str, Any] = None, 
                                  max_retries: int = 3) -> Dict[str, Any]:
    for attempt in range(max_retries):
        try:
            return await self._make_request(method, url, headers, body)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Мониторинг и метрики

### Health Check Aggregation

```python
async def check_all_services_health(self) -> Dict[str, Any]:
    results = {}
    for service_name, service in self.services.items():
        try:
            health_data = await self._check_service_health(service_name)
            results[service_name] = health_data
        except Exception as e:
            results[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    return results
```

### Request Statistics

- Общее количество запросов
- Количество успешных/неуспешных запросов
- Среднее время ответа
- Количество запросов по сервисам
- Ошибки маршрутизации

## Безопасность

### Аутентификация и авторизация

```python
def _extract_user_info(self, headers: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    user_id = headers.get("X-User-ID")
    session_id = headers.get("X-Session-ID")
    return user_id, session_id
```

### Rate Limiting

```python
class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Очистка старых запросов
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] 
            if now - req_time < self.window_seconds
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
```

### Валидация входных данных

```python
class GatewayRequestValidator:
    def validate_request(self, method: str, path: str, headers: Dict[str, str]) -> bool:
        # Проверка метода
        if method not in ["GET", "POST", "PUT", "DELETE"]:
            return False
        
        # Проверка пути
        if not path or len(path) > 1000:
            return False
        
        # Проверка заголовков
        if "Content-Length" in headers:
            try:
                content_length = int(headers["Content-Length"])
                if content_length > 10 * 1024 * 1024:  # 10MB
                    return False
            except ValueError:
                return False
        
        return True
```

## Обработка ошибок

### Типы ошибок

1. **ServiceUnavailableError**: Сервис недоступен
2. **RoutingError**: Ошибка маршрутизации
3. **TimeoutError**: Таймаут запроса
4. **ValidationError**: Ошибка валидации
5. **RateLimitError**: Превышение лимита запросов

### Error Response Format

```python
{
    "error": "описание ошибки",
    "error_code": "ERROR_CODE",
    "target_service": "service-name",
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## Производительность

### Оптимизации

1. **Connection Pooling**: Переиспользование HTTP соединений
2. **Request Batching**: Группировка запросов
3. **Response Caching**: Кэширование ответов
4. **Async Processing**: Асинхронная обработка запросов

### Метрики производительности

- Время обработки запроса
- Пропускная способность (requests/second)
- Задержка между сервисами
- Использование памяти и CPU

## Разработка и тестирование

### Локальная разработка

```bash
# Запуск сервиса
cd services/api-gateway
python api/main.py

# Тестирование API
curl -X GET http://localhost:8000/health
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "тест"}'
```

### Unit тесты

```python
def test_service_routing():
    gateway_service = GatewayService()
    target_service = gateway_service._determine_target_service("/generate")
    assert target_service == "ai-model"

def test_request_validation():
    validator = GatewayRequestValidator()
    is_valid = validator.validate_request("POST", "/generate", {})
    assert is_valid == True
```

### Integration тесты

```python
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "ai-model" in data["services"]

def test_request_routing():
    response = client.post("/generate", json={"query": "test"})
    assert response.status_code == 200
    assert "result" in response.json()
```

## Масштабирование

### Горизонтальное масштабирование

- Множественные инстансы API Gateway
- Балансировка нагрузки через внешний load balancer
- Общий Redis для кэширования и сессий

### Вертикальное масштабирование

- Увеличение CPU и памяти
- Оптимизация конфигурации
- Улучшение алгоритмов маршрутизации

## Интеграция с другими сервисами

### Все микросервисы
- Маршрутизация запросов к соответствующим сервисам
- Агрегация ответов от нескольких сервисов
- Централизованная обработка ошибок

### Monitoring и Logging
- Сбор метрик от всех сервисов
- Централизованное логирование
- Трейсинг запросов

## Планы развития

### Краткосрочные цели
- Добавление более сложных алгоритмов балансировки нагрузки
- Реализация кэширования ответов
- Улучшение мониторинга и метрик

### Долгосрочные цели
- Интеграция с внешними API провайдерами
- Реализация GraphQL API
- Добавление поддержки WebSocket соединений