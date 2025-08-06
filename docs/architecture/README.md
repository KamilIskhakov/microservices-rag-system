# 🏗️ Архитектура RAG Chrome Extension

## 🎯 Обзор архитектуры

RAG Chrome Extension построен на принципах **Domain-Driven Design (DDD)** и **микросервисной архитектуры**. Система разделена на независимые сервисы, каждый из которых отвечает за конкретную бизнес-функциональность.

### 🏛️ Архитектурные слои

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │Chrome Ext.  │  │   Mobile    │  │    Web      │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Auth      │  │   Rate      │  │   Routing   │      │
│  │  Service    │  │  Limiting   │  │   Service   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Request   │  │   Payment   │  │   Scraper   │      │
│  │ Processor   │  │   Service   │  │   Service   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   AI Model  │  │   Vector    │  │   RAG       │      │
│  │   Service   │  │   Store     │  │   Service   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │    Redis    │  │   Docker    │  │ Kubernetes  │      │
│  │   Cache     │  │  Containers │  │  Cluster    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 🏢 Микросервисы

### 🌐 API Gateway (Порт: 8000)

**Назначение**: Единая точка входа для всех клиентских запросов

**Основные функции**:
- Маршрутизация запросов к соответствующим сервисам
- Аутентификация и авторизация
- Rate limiting и throttling
- Валидация входных данных
- Агрегация ответов от микросервисов
- CORS настройки
- Логирование и мониторинг

**Технологии**:
- FastAPI
- Uvicorn
- Redis для кэширования
- JWT для аутентификации

**API Endpoints**:
```python
POST /check              # Проверка текста на экстремизм
GET  /health            # Health check
GET  /docs              # Swagger документация
POST /payment/create    # Создание платежа
GET  /payment/status    # Статус платежа
```

### 🤖 AI Model Service (Порт: 8003)

**Назначение**: Управление AI моделями и генерация текста

**Основные функции**:
- Загрузка и управление AI моделями
- Генерация текста с помощью RAG
- Оптимизация использования памяти
- Многопоточная обработка запросов
- Адаптивная загрузка моделей (CPU/GPU)
- Мониторинг производительности

**Технологии**:
- Transformers (Hugging Face)
- PyTorch
- Qwen2.5-3B-Instruct модель
- ThreadPoolExecutor для многопоточности

**API Endpoints**:
```python
POST /generate          # Генерация текста
GET  /health           # Health check
GET  /models           # Список доступных моделей
POST /models/load      # Загрузка модели
```

### 🗄️ Vector Store Service (Порт: 8002)

**Назначение**: Поиск по векторной базе данных

**Основные функции**:
- Индексация документов в векторном пространстве
- Семантический поиск по запросам
- Управление релевантностью результатов
- Автоматическое обновление индекса
- Масштабируемость для больших объемов данных

**Технологии**:
- FAISS для векторного поиска
- Sentence Transformers для эмбеддингов
- Redis для кэширования
- NumPy для работы с векторами

**API Endpoints**:
```python
POST /search           # Поиск документов
POST /index            # Индексация документа
GET  /health          # Health check
GET  /stats           # Статистика индекса
```

### 📡 Scraper Service (Порт: 8001)

**Назначение**: Парсинг данных из внешних источников

**Основные функции**:
- Автоматический парсинг сайта Минюста
- Планировщик задач для регулярного обновления
- Интеграция с Vector Store для автоматической индексации
- Мониторинг статуса задач парсинга
- Обработка ошибок и retry логика

**Технологии**:
- BeautifulSoup для парсинга HTML
- Requests для HTTP запросов
- Celery для планировщика задач
- Redis для очередей

**API Endpoints**:
```python
POST /jobs/create      # Создание задачи парсинга
GET  /jobs            # Список задач
GET  /jobs/{id}       # Статус задачи
POST /rag/sync        # Синхронизация с RAG
```

### 💳 Payment Service (Порт: 8005)

**Назначение**: Обработка платежей и управление подписками

**Основные функции**:
- Интеграция с YooKassa
- Управление freemium моделью (20 проверок/день)
- Обработка платежей и подписок
- Валидация лимитов пользователей
- Аналитика платежей

**Технологии**:
- YooKassa API
- Redis для кэширования лимитов
- JWT для токенов доступа
- SQLAlchemy для работы с БД

**API Endpoints**:
```python
POST /payment/create   # Создание платежа
GET  /payment/status   # Статус платежа
GET  /limits/check     # Проверка лимитов
POST /subscription     # Управление подпиской
```

### ⚙️ Request Processor (Порт: 8004)

**Назначение**: Координация запросов между сервисами

**Основные функции**:
- Оркестрация запросов к микросервисам
- Агрегация результатов от разных сервисов
- Обработка ошибок и fallback логика
- Кэширование результатов
- Мониторинг производительности

**Технологии**:
- FastAPI
- httpx для HTTP клиента
- Redis для кэширования
- asyncio для асинхронности

**API Endpoints**:
```python
POST /process          # Обработка запроса
GET  /health          # Health check
GET  /metrics         # Метрики производительности
```

## 🏛️ Domain-Driven Design (DDD)

### 📦 Доменные сущности

#### Request (Запрос)
```python
@dataclass
class Request:
    query: str                    # Текст для проверки
    user_id: Optional[str]        # ID пользователя
    session_id: Optional[str]     # ID сессии
    status: RequestStatus         # Статус обработки
    created_at: datetime          # Время создания
    result: Optional[str]         # Результат проверки
    processing_time: float        # Время обработки
```

#### Payment (Платеж)
```python
@dataclass
class Payment:
    payment_id: str              # ID платежа
    user_id: str                 # ID пользователя
    amount: float                # Сумма
    currency: str                # Валюта
    status: PaymentStatus        # Статус платежа
    payment_method: str          # Метод оплаты
    created_at: datetime         # Время создания
```

#### ScrapedData (Данные парсинга)
```python
@dataclass
class ScrapedData:
    id: str                      # Уникальный ID
    source: str                  # Источник данных
    content: str                 # Содержание
    metadata: Dict[str, Any]     # Метаданные
    created_at: datetime         # Время создания
```

### 🏪 Репозитории

#### VectorRepository
```python
class VectorRepository(ABC):
    @abstractmethod
    def add_document(self, document: VectorDocument) -> str
    
    @abstractmethod
    def search_documents(self, query: str, top_k: int) -> List[SearchResult]
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool
```

#### ModelRepository
```python
class ModelRepository(ABC):
    @abstractmethod
    def load_model(self, model_id: str) -> bool
    
    @abstractmethod
    def generate_text(self, model_id: str, prompt: str) -> str
    
    @abstractmethod
    def is_model_available(self, model_id: str) -> bool
```

### 🎯 Доменные сервисы

#### RAGService
```python
class RAGService:
    def check(self, request: CheckRequest) -> CheckResponse:
        # 1. Поиск релевантных документов
        # 2. Генерация контекста
        # 3. Анализ с помощью AI
        # 4. Формирование ответа
```

#### PaymentService
```python
class PaymentService:
    def create_payment(self, command: CreatePaymentCommand) -> CreatePaymentResult:
        # 1. Валидация данных
        # 2. Создание платежа в YooKassa
        # 3. Сохранение в БД
        # 4. Возврат URL для оплаты
```

## 🔄 Паттерны проектирования

### 🏭 Factory Pattern
```python
class DeviceFactory:
    @staticmethod
    def create_device(device_type: str) -> Device:
        if device_type == "cpu":
            return CPUDevice()
        elif device_type == "gpu":
            return GPUDevice()
        else:
            return AutoDevice()
```

### 🎯 Strategy Pattern
```python
class ModelLoadingStrategy(ABC):
    @abstractmethod
    def load_model(self, model_path: str) -> Any

class CPUModelLoadingStrategy(ModelLoadingStrategy):
    def load_model(self, model_path: str) -> Any:
        # Загрузка модели на CPU

class GPUModelLoadingStrategy(ModelLoadingStrategy):
    def load_model(self, model_path: str) -> Any:
        # Загрузка модели на GPU
```

### 👁️ Observer Pattern
```python
class ModelObserver(ABC):
    @abstractmethod
    def on_model_loaded(self, model_id: str)
    
    @abstractmethod
    def on_model_error(self, model_id: str, error: str)

class LoggingModelObserver(ModelObserver):
    def on_model_loaded(self, model_id: str):
        logger.info(f"Model {model_id} loaded successfully")
```

### 📋 Command Pattern
```python
@dataclass
class ProcessRequestCommand:
    query: str
    user_id: str
    session_id: Optional[str] = None

class ProcessRequestCommandHandler:
    def handle(self, command: ProcessRequestCommand) -> ProcessRequestResult:
        # Обработка команды
```

## 🔄 Event Sourcing

### 📝 События
```python
@dataclass
class RequestProcessedEvent:
    request_id: str
    user_id: str
    processing_time: float
    result: str
    timestamp: datetime

@dataclass
class PaymentCreatedEvent:
    payment_id: str
    user_id: str
    amount: float
    timestamp: datetime
```

### 🎯 Event Handlers
```python
class RequestProcessedEventHandler:
    def handle(self, event: RequestProcessedEvent):
        # Обновление статистики
        # Отправка уведомлений
        # Логирование
```

## 🔧 CQRS (Command Query Responsibility Segregation)

### 📝 Команды (Commands)
```python
@dataclass
class CreatePaymentCommand:
    user_id: str
    amount: float
    currency: str
    payment_method: str

@dataclass
class ProcessRequestCommand:
    query: str
    user_id: str
    session_id: Optional[str]
```

### 🔍 Запросы (Queries)
```python
@dataclass
class GetPaymentStatusQuery:
    payment_id: str

@dataclass
class GetUserLimitsQuery:
    user_id: str
```

## 📊 Мониторинг и метрики

### 🔍 Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "redis": check_redis(),
            "services": check_services()
        }
    }
```

### 📈 Метрики
- **Время ответа API** (Response Time)
- **Количество запросов** (Request Count)
- **Ошибки** (Error Rate)
- **Использование памяти** (Memory Usage)
- **CPU нагрузка** (CPU Load)

## 🔒 Безопасность

### 🔐 Аутентификация
- JWT токены для API
- API ключи для межсервисного взаимодействия
- Rate limiting для предотвращения DDoS

### 🛡️ Валидация данных
- Pydantic модели для валидации
- SQL injection protection
- XSS protection
- Input sanitization

## 🚀 Масштабируемость

### 📈 Горизонтальное масштабирование
- Независимые микросервисы
- Stateless архитектура
- Load balancing
- Auto-scaling в Kubernetes

### 🔄 Вертикальное масштабирование
- Оптимизация использования памяти
- Многопоточная обработка
- Кэширование результатов
- Connection pooling

## 📋 Диаграммы

### 🔄 Sequence Diagram - Проверка текста
```
Client → API Gateway → Request Processor → Vector Store
                                    ↓
                              AI Model Service
                                    ↓
                              Response Aggregation
                                    ↓
                              Client
```

### 🏗️ Component Diagram
```
┌─────────────────┐    ┌─────────────────┐
│  Chrome Ext.    │    │   API Gateway   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                    │
         ┌─────────────────┐
         │Request Processor│
         └─────────────────┘
    │              │              │
┌─────────┐  ┌─────────┐  ┌─────────┐
│AI Model │  │ Vector  │  │Payment  │
│Service  │  │ Store   │  │Service  │
└─────────┘  └─────────┘  └─────────┘
```

---

**🎯 Архитектура обеспечивает высокую производительность, масштабируемость и поддерживаемость системы.** 