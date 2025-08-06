# 🌐 API Документация RAG Chrome Extension

## 📋 Обзор API

RAG Chrome Extension предоставляет RESTful API для проверки текстов на экстремизм. API построен на принципах REST и поддерживает JSON формат для всех запросов и ответов.

### 🏗️ Архитектура API

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chrome Ext.   │───▶│   API Gateway   │───▶│  Microservices  │
│   Mobile App    │    │   (Port 8000)   │    │                 │
│   Web Client    │    │                 │    │  • AI Model     │
└─────────────────┘    └─────────────────┘    │  • Vector Store │
                                              │  • Payment      │
                                              │  • Scraper      │
                                              └─────────────────┘
```

### 🔐 Аутентификация

API использует несколько уровней аутентификации:

#### API Gateway (Публичный API)
```bash
# Базовый уровень - API ключ
Authorization: Bearer YOUR_API_KEY

# Для Chrome Extension
X-Extension-Version: 1.0.0
X-User-ID: user123
```

#### Межсервисное взаимодействие
```bash
# Внутренние сервисы
X-Service-Token: INTERNAL_SERVICE_TOKEN
X-Service-Name: ai-model
```

### 📊 Rate Limiting

```bash
# Freemium пользователи
- 20 запросов в день
- 1 запрос в минуту

# Платные пользователи
- 1000 запросов в день
- 10 запросов в минуту
```

## 🚀 API Endpoints

### 🌐 API Gateway (Порт: 8000)

#### Проверка текста на экстремизм
```http
POST /check
Content-Type: application/json

{
  "query": "текст для проверки",
  "user_id": "user123",
  "session_id": "session456",
  "context": ["дополнительный контекст"]
}
```

**Ответ:**
```json
{
  "success": true,
  "result": "НЕ ЭКСТРЕМИСТСКИЙ",
  "processing_time": 2.45,
  "timestamp": "2025-08-06T17:30:00.000Z",
  "confidence": 0.85,
  "extremist_reason": "Текст не содержит признаков экстремизма",
  "court_date": "2023-01-15",
  "court_name": "Верховный Суд РФ",
  "material_name": "Постановление №123",
  "error": null
}
```

#### Health Check
```http
GET /health
```

**Ответ:**
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "timestamp": "2025-08-06T17:30:00.000Z",
  "dependencies": {
    "redis": "healthy",
    "services": "healthy"
  }
}
```

#### Создание платежа
```http
POST /payment/create
Content-Type: application/json

{
  "user_id": "user123",
  "amount": 299.00,
  "currency": "RUB",
  "payment_method": "yookassa",
  "description": "Подписка на месяц"
}
```

**Ответ:**
```json
{
  "success": true,
  "payment_id": "payment_123456",
  "payment_url": "https://yoomoney.ru/checkout/payments/v2/contract",
  "status": "pending",
  "amount": 299.00,
  "currency": "RUB"
}
```

#### Статус платежа
```http
GET /payment/status/{payment_id}
```

**Ответ:**
```json
{
  "success": true,
  "payment_id": "payment_123456",
  "status": "completed",
  "amount": 299.00,
  "currency": "RUB",
  "completed_at": "2025-08-06T17:30:00.000Z"
}
```

#### Проверка лимитов пользователя
```http
GET /limits/check/{user_id}
```

**Ответ:**
```json
{
  "success": true,
  "user_id": "user123",
  "daily_checks_used": 15,
  "daily_checks_limit": 20,
  "monthly_checks_used": 150,
  "monthly_checks_limit": 1000,
  "subscription_status": "free",
  "can_make_request": true
}
```

### 🤖 AI Model Service (Порт: 8003)

#### Генерация текста
```http
POST /generate
Content-Type: application/json

{
  "model_id": "qwen-model_full",
  "query": "Проверь этот текст на экстремизм: {текст}",
  "max_length": 100,
  "temperature": 0.1,
  "use_async": true
}
```

**Ответ:**
```json
{
  "success": true,
  "result": "Текст не содержит признаков экстремизма",
  "processing_time": 5.23,
  "timestamp": "2025-08-06T17:30:00.000Z",
  "model_id": "qwen-model_full",
  "memory_usage": {
    "total": 16748867584,
    "available": 2592301056,
    "used": 13909848064,
    "percent": 84.5
  }
}
```

#### Список доступных моделей
```http
GET /models
```

**Ответ:**
```json
{
  "success": true,
  "models": [
    {
      "model_id": "qwen-model_full",
      "name": "Qwen2.5-3B-Instruct",
      "status": "loaded",
      "device": "cpu",
      "memory_usage_mb": 8192
    }
  ]
}
```

#### Загрузка модели
```http
POST /models/load
Content-Type: application/json

{
  "model_id": "qwen-model_full",
  "device": "cpu"
}
```

**Ответ:**
```json
{
  "success": true,
  "model_id": "qwen-model_full",
  "status": "loaded",
  "load_time": 52.3,
  "device": "cpu"
}
```

### 🗄️ Vector Store Service (Порт: 8002)

#### Поиск документов
```http
POST /search
Content-Type: application/json

{
  "query": "экстремистская организация",
  "top_k": 5,
  "threshold": 0.3
}
```

**Ответ:**
```json
{
  "success": true,
  "results": [
    {
      "text": "материал исключен из списка",
      "relevance_score": 0.85,
      "metadata": {
        "source": "minjust",
        "number": "262",
        "date": "2025-08-06T10:34:21.441830",
        "content": "материал исключен из списка"
      }
    }
  ],
  "total_found": 1,
  "processing_time": 0.15,
  "timestamp": "2025-08-06T17:30:00.000Z"
}
```

#### Индексация документа
```http
POST /index
Content-Type: application/json

{
  "document_id": "doc_123",
  "text": "Текст документа для индексации",
  "metadata": {
    "source": "minjust",
    "date": "2025-08-06",
    "number": "123"
  }
}
```

**Ответ:**
```json
{
  "success": true,
  "document_id": "doc_123",
  "indexed": true,
  "processing_time": 0.05,
  "timestamp": "2025-08-06T17:30:00.000Z"
}
```

#### Статистика индекса
```http
GET /stats
```

**Ответ:**
```json
{
  "success": true,
  "documents_count": 5244,
  "faiss_index_size": 5244,
  "encoder_loaded": true,
  "model_name": "sentence-transformers/all-MiniLM-L6-v2",
  "index_size_mb": 45.2,
  "last_update": "2025-08-06T17:30:00.000Z"
}
```

### 📡 Scraper Service (Порт: 8001)

#### Создание задачи парсинга
```http
POST /jobs/create
Content-Type: application/json

{
  "source": "minjust",
  "priority": "normal",
  "max_pages": 10
}
```

**Ответ:**
```json
{
  "success": true,
  "job_id": "job_123456",
  "status": "pending",
  "source": "minjust",
  "created_at": "2025-08-06T17:30:00.000Z"
}
```

#### Список задач
```http
GET /jobs
```

**Ответ:**
```json
{
  "success": true,
  "jobs": [
    {
      "job_id": "job_123456",
      "status": "running",
      "source": "minjust",
      "created_at": "2025-08-06T17:30:00.000Z",
      "started_at": "2025-08-06T17:30:05.000Z",
      "progress": 0.75,
      "items_processed": 750,
      "items_total": 1000
    }
  ],
  "timestamp": "2025-08-06T17:30:00.000Z"
}
```

#### Статус задачи
```http
GET /jobs/{job_id}
```

**Ответ:**
```json
{
  "success": true,
  "job": {
    "job_id": "job_123456",
    "status": "completed",
    "source": "minjust",
    "created_at": "2025-08-06T17:30:00.000Z",
    "started_at": "2025-08-06T17:30:05.000Z",
    "completed_at": "2025-08-06T17:35:00.000Z",
    "items_processed": 1000,
    "items_total": 1000,
    "error": null
  }
}
```

#### Синхронизация с RAG
```http
POST /rag/sync
Content-Type: application/json

{
  "job_id": "job_123456",
  "force": false
}
```

**Ответ:**
```json
{
  "success": true,
  "job_id": "job_123456",
  "documents_synced": 1000,
  "processing_time": 15.2,
  "timestamp": "2025-08-06T17:30:00.000Z"
}
```

### 💳 Payment Service (Порт: 8005)

#### Создание платежа
```http
POST /payment/create
Content-Type: application/json

{
  "user_id": "user123",
  "amount": 299.00,
  "currency": "RUB",
  "payment_method": "yookassa",
  "description": "Подписка на месяц"
}
```

**Ответ:**
```json
{
  "success": true,
  "payment_id": "payment_123456",
  "payment_url": "https://yoomoney.ru/checkout/payments/v2/contract",
  "status": "pending",
  "amount": 299.00,
  "currency": "RUB",
  "created_at": "2025-08-06T17:30:00.000Z"
}
```

#### Статус платежа
```http
GET /payment/status/{payment_id}
```

**Ответ:**
```json
{
  "success": true,
  "payment_id": "payment_123456",
  "status": "completed",
  "amount": 299.00,
  "currency": "RUB",
  "payment_method": "yookassa",
  "created_at": "2025-08-06T17:30:00.000Z",
  "completed_at": "2025-08-06T17:32:00.000Z"
}
```

#### Проверка лимитов
```http
GET /limits/check/{user_id}
```

**Ответ:**
```json
{
  "success": true,
  "user_id": "user123",
  "subscription_type": "free",
  "daily_checks_used": 15,
  "daily_checks_limit": 20,
  "monthly_checks_used": 150,
  "monthly_checks_limit": 1000,
  "can_make_request": true,
  "next_reset": "2025-08-07T00:00:00.000Z"
}
```

### ⚙️ Request Processor (Порт: 8004)

#### Обработка запроса
```http
POST /process
Content-Type: application/json

{
  "query": "текст для проверки",
  "user_id": "user123",
  "session_id": "session456"
}
```

**Ответ:**
```json
{
  "success": true,
  "request_id": "req_123456",
  "results": {
    "ai-model": {
      "status": "processed",
      "result": "НЕ ЭКСТРЕМИСТСКИЙ"
    },
    "vectorstore": {
      "status": "processed",
      "results_count": 3
    }
  },
  "processing_time": 3.45,
  "timestamp": "2025-08-06T17:30:00.000Z"
}
```

#### Метрики производительности
```http
GET /metrics
```

**Ответ:**
```json
{
  "success": true,
  "metrics": {
    "requests_total": 1500,
    "requests_per_minute": 25,
    "average_response_time": 2.3,
    "error_rate": 0.02,
    "active_connections": 5
  },
  "timestamp": "2025-08-06T17:30:00.000Z"
}
```

## 🔄 WebSocket API

### Подключение к WebSocket

```javascript
// Подключение к WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    console.log('WebSocket соединение установлено');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Получено сообщение:', data);
};

ws.onclose = function() {
    console.log('WebSocket соединение закрыто');
};
```

### WebSocket события

#### Отправка запроса
```json
{
  "type": "check_request",
  "data": {
    "query": "текст для проверки",
    "user_id": "user123"
  }
}
```

#### Получение результата
```json
{
  "type": "check_response",
  "data": {
    "success": true,
    "result": "НЕ ЭКСТРЕМИСТСКИЙ",
    "processing_time": 2.45,
    "confidence": 0.85
  }
}
```

#### Статус обработки
```json
{
  "type": "processing_status",
  "data": {
    "status": "processing",
    "progress": 0.75,
    "stage": "ai_analysis"
  }
}
```

## 📊 Коды ошибок

### HTTP Status Codes

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 201 | Ресурс создан |
| 400 | Неверный запрос |
| 401 | Не авторизован |
| 403 | Доступ запрещен |
| 404 | Ресурс не найден |
| 429 | Превышен лимит запросов |
| 500 | Внутренняя ошибка сервера |
| 503 | Сервис недоступен |

### Коды ошибок API

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Превышен лимит запросов",
    "details": {
      "daily_limit": 20,
      "used": 20,
      "reset_time": "2025-08-07T00:00:00.000Z"
    }
  }
}
```

#### Распространенные коды ошибок

| Код | Описание |
|-----|----------|
| `INVALID_REQUEST` | Неверный формат запроса |
| `RATE_LIMIT_EXCEEDED` | Превышен лимит запросов |
| `MODEL_NOT_AVAILABLE` | Модель недоступна |
| `VECTOR_STORE_ERROR` | Ошибка векторного хранилища |
| `PAYMENT_REQUIRED` | Требуется оплата |
| `SERVICE_UNAVAILABLE` | Сервис недоступен |
| `INTERNAL_ERROR` | Внутренняя ошибка |

## 🔒 Безопасность

### Аутентификация

#### API Key аутентификация
```bash
# Заголовок для API ключа
Authorization: Bearer YOUR_API_KEY

# Для Chrome Extension
X-Extension-Version: 1.0.0
X-User-ID: user123
```

#### JWT токены (для внутренних сервисов)
```bash
# JWT токен
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Валидация данных

#### Схема валидации запроса
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 10000
    },
    "user_id": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9_-]+$"
    },
    "session_id": {
      "type": "string",
      "optional": true
    }
  },
  "required": ["query", "user_id"]
}
```

### Rate Limiting

#### Лимиты по типам пользователей

| Тип пользователя | Дневной лимит | Минутный лимит |
|------------------|----------------|----------------|
| Free | 20 | 1 |
| Basic | 100 | 5 |
| Premium | 1000 | 10 |
| Enterprise | Безлимитно | 50 |

#### Headers для rate limiting
```http
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1628198400
```

## 📈 Мониторинг и метрики

### Prometheus метрики

```python
# Метрики запросов
requests_total = Counter('requests_total', 'Total requests', ['endpoint', 'method'])
request_duration = Histogram('request_duration_seconds', 'Request duration')

# Метрики ошибок
errors_total = Counter('errors_total', 'Total errors', ['endpoint', 'error_type'])

# Метрики производительности
response_time = Histogram('response_time_seconds', 'Response time')
memory_usage = Gauge('memory_usage_bytes', 'Memory usage')
```

### Health Check endpoints

```http
GET /health
GET /ready
GET /live
```

### Логирование

#### Структура логов
```json
{
  "timestamp": "2025-08-06T17:30:00.000Z",
  "level": "INFO",
  "service": "api-gateway",
  "request_id": "req_123456",
  "user_id": "user123",
  "endpoint": "/check",
  "method": "POST",
  "status_code": 200,
  "response_time": 2.45,
  "message": "Request processed successfully"
}
```

## 🧪 Тестирование API

### Примеры запросов с curl

#### Проверка текста
```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "query": "тестовая проверка текста",
    "user_id": "user123"
  }'
```

#### Создание платежа
```bash
curl -X POST http://localhost:8000/payment/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "user_id": "user123",
    "amount": 299.00,
    "currency": "RUB",
    "payment_method": "yookassa"
  }'
```

#### Проверка лимитов
```bash
curl -X GET http://localhost:8000/limits/check/user123 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Тестирование с Python

```python
import requests
import json

# Базовый URL
BASE_URL = "http://localhost:8000"

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}

# Проверка текста
def check_text(text, user_id):
    response = requests.post(
        f"{BASE_URL}/check",
        headers=headers,
        json={
            "query": text,
            "user_id": user_id
        }
    )
    return response.json()

# Создание платежа
def create_payment(user_id, amount):
    response = requests.post(
        f"{BASE_URL}/payment/create",
        headers=headers,
        json={
            "user_id": user_id,
            "amount": amount,
            "currency": "RUB",
            "payment_method": "yookassa"
        }
    )
    return response.json()

# Тестирование
if __name__ == "__main__":
    # Проверка текста
    result = check_text("тестовая проверка", "user123")
    print("Результат проверки:", result)
    
    # Создание платежа
    payment = create_payment("user123", 299.00)
    print("Платеж создан:", payment)
```

## 📚 Дополнительные ресурсы

### Swagger документация
- **API Gateway**: http://localhost:8000/docs
- **AI Model Service**: http://localhost:8003/docs
- **Vector Store Service**: http://localhost:8002/docs
- **Scraper Service**: http://localhost:8001/docs
- **Payment Service**: http://localhost:8005/docs
- **Request Processor**: http://localhost:8004/docs

### Postman коллекции
```json
{
  "info": {
    "name": "RAG Chrome Extension API",
    "description": "API для проверки текстов на экстремизм"
  },
  "item": [
    {
      "name": "Check Text",
      "request": {
        "method": "POST",
        "url": "http://localhost:8000/check",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"query\": \"тестовая проверка\",\n  \"user_id\": \"user123\"\n}"
        }
      }
    }
  ]
}
```

---

**🎯 API готов к использованию! Все endpoints документированы и протестированы.** 