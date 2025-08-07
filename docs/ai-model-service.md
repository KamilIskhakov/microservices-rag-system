# AI Model Service - Техническая документация

## Обзор сервиса

AI Model Service отвечает за управление и выполнение языковых моделей для генерации текста. Сервис реализует паттерн Repository для управления моделями и предоставляет REST API для взаимодействия с другими сервисами системы.

## Архитектура

### Слои архитектуры

#### Domain Layer
- **Entities**: `Model` - доменная сущность модели
- **Repositories**: `ModelRepository` - абстрактный интерфейс для работы с моделями
- **Services**: `ModelService` - доменный сервис для бизнес-логики

#### Application Layer
- **Use Cases**: `GenerateTextUseCase` - сценарий генерации текста
- **Commands**: Обработка команд для управления моделями

#### Infrastructure Layer
- **Persistence**: `OptimizedModelRepository` - реализация репозитория
- **API**: FastAPI endpoints для внешнего взаимодействия

### Ключевые компоненты

#### Model Entity
```python
@dataclass
class Model:
    id: str
    name: str
    type: str
    device: str
    is_loaded: bool
    path: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
```

#### ModelRepository Interface
```python
class ModelRepository(ABC):
    @abstractmethod
    def load_model(self, model_id: str, device: str = "auto") -> Model:
        pass
    
    @abstractmethod
    def generate_text(self, model_id: str, prompt: str, 
                     max_length: int = 512, temperature: float = 0.7) -> str:
        pass
```

## API Endpoints

### Health Check
```
GET /health
```
Возвращает статус сервиса и информацию о загруженных моделях.

### System Information
```
GET /system-info
```
Предоставляет детальную информацию о системе:
- Количество CPU ядер
- Использование памяти
- Количество рабочих потоков и процессов
- Количество загруженных моделей

### Model Management

#### Load Model
```
POST /load-model
Parameters:
- model_id: str (default: "qwen-model_full")
- device: str (default: "auto")
```
Загружает модель в память на указанное устройство.

#### Unload Model
```
POST /unload-model
Parameters:
- model_id: str
```
Выгружает модель из памяти и освобождает ресурсы.

### Text Generation

#### Generate Text
```
POST /generate
Request Body:
{
    "query": "текст для анализа",
    "context": ["дополнительный контекст"],
    "max_length": 512,
    "temperature": 0.7,
    "model_id": "qwen-model_full",
    "use_async": true
}
```
Генерирует текст на основе входного запроса и контекста.

### Memory Management

#### Optimize Memory
```
POST /optimize-memory
```
Выполняет оптимизацию памяти:
- Принудительная сборка мусора
- Очистка GPU кэша (если доступен)
- Освобождение неиспользуемых ресурсов

#### Memory Usage
```
GET /memory-usage
```
Возвращает информацию об использовании памяти:
- RSS (Resident Set Size)
- VMS (Virtual Memory Size)
- Процент использования памяти
- Количество загруженных моделей

## Конфигурация

### Environment Variables

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `DEVICE_TYPE` | Тип устройства для моделей | `auto` |
| `CPU_THREADS` | Количество CPU потоков | `4` |
| `GPU_MEMORY_FRACTION` | Доля GPU памяти | `0.8` |
| `MAX_WORKERS` | Максимум рабочих потоков | `8` |
| `MAX_PROCESSES` | Максимум процессов | `2` |
| `MAX_GENERATION_TIME` | Максимальное время генерации | `30` |
| `MAX_NEW_TOKENS` | Максимум новых токенов | `10` |
| `GENERATION_TEMPERATURE` | Температура генерации | `0.1` |
| `MAX_MEMORY_USAGE` | Максимальное использование памяти | `0.9` |
| `MIN_MEMORY_GB` | Минимальная память в GB | `2` |

### Docker Configuration

```yaml
ai-model:
  build:
    context: ../../services/ai-model
    dockerfile: Dockerfile
  environment:
    - DEVICE_TYPE=auto
    - CPU_THREADS=4
    - GPU_MEMORY_FRACTION=0.8
    - MAX_WORKERS=8
    - MAX_PROCESSES=2
  deploy:
    resources:
      limits:
        memory: 14G
        cpus: '4.0'
      reservations:
        memory: 12G
        cpus: '2.0'
```

## Стратегии оптимизации

### Device Selection Strategy

Сервис реализует автоматический выбор устройства:

```python
def load_model(self, model_id: str, device: str = "auto") -> Model:
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
```

### Memory Management Strategy

1. **Мониторинг памяти**: Постоянное отслеживание использования памяти
2. **Автоматическая очистка**: Принудительная сборка мусора при превышении лимитов
3. **GPU кэш очистка**: Очистка CUDA кэша для освобождения GPU памяти
4. **Модель выгрузка**: Автоматическая выгрузка неиспользуемых моделей

### Threading Strategy

- **ThreadPoolExecutor**: Для I/O операций (8 рабочих потоков)
- **ProcessPoolExecutor**: Для CPU-интенсивных задач (2 процесса)
- **Async/Await**: Для неблокирующих операций

## Модели

### Поддерживаемые модели

#### Qwen2.5-3B-Instruct
- **Тип**: Causal Language Model
- **Размер**: ~3B параметров
- **Назначение**: Генерация текста для анализа экстремистского содержания
- **Путь**: `/app/models/qwen-model_full`

### Загрузка моделей

```python
def load_model(self, model_id: str, device: str = "auto") -> Model:
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, 
        torch_dtype=torch.float32,
        device_map=device
    )
```

## Обработка ошибок

### Типы ошибок

1. **ModelNotFoundError**: Модель не найдена в конфигурации
2. **ModelNotLoadedError**: Модель не загружена в память
3. **DeviceNotAvailableError**: Устройство недоступно
4. **MemoryError**: Недостаточно памяти для загрузки модели
5. **GenerationError**: Ошибка при генерации текста

### Обработка исключений

```python
try:
    result = model_service.generate_text(model_id, prompt)
except ModelNotLoadedError:
    # Попытка загрузить модель
    model_service.load_model(model_id)
    result = model_service.generate_text(model_id, prompt)
except MemoryError:
    # Очистка памяти и повторная попытка
    model_service.optimize_memory()
    result = model_service.generate_text(model_id, prompt)
```

## Мониторинг и метрики

### Health Check

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-model",
        "loaded_models_count": len(model_service.get_loaded_models()),
        "memory_usage": model_service.get_memory_usage()
    }
```

### Метрики производительности

- Время загрузки модели
- Время генерации текста
- Использование памяти (RSS, VMS)
- Количество активных запросов
- Ошибки генерации

## Безопасность

### Валидация входных данных

```python
class ModelRequest(BaseModel):
    query: str
    context: List[str] = []
    max_length: int = Field(ge=1, le=2048)
    temperature: float = Field(ge=0.0, le=2.0)
    model_id: str
    use_async: bool = True
```

### Rate Limiting

- Ограничение количества одновременных запросов
- Таймауты для длительных операций
- Защита от перегрузки системы

## Разработка и тестирование

### Локальная разработка

```bash
# Запуск сервиса
cd services/ai-model
python api/main.py

# Тестирование API
curl -X POST http://localhost:8003/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "тест", "model_id": "qwen-model_full"}'
```

### Unit тесты

```python
def test_model_loading():
    repository = OptimizedModelRepository()
    model = repository.load_model("test-model", "cpu")
    assert model.is_loaded == True
    assert model.device == "cpu"
```

### Integration тесты

```python
def test_text_generation():
    response = client.post("/generate", json={
        "query": "test query",
        "model_id": "qwen-model_full"
    })
    assert response.status_code == 200
    assert "result" in response.json()
```

## Масштабирование

### Горизонтальное масштабирование

- Множественные инстансы сервиса
- Балансировка нагрузки через API Gateway
- Общий Redis для кэширования

### Вертикальное масштабирование

- Увеличение CPU и памяти
- Добавление GPU ресурсов
- Оптимизация конфигурации моделей

## Интеграция с другими сервисами

### API Gateway
- Маршрутизация запросов к AI Model Service
- Агрегация ответов от нескольких сервисов

### Request Processor
- Координация запросов к AI Model Service
- Обработка результатов генерации

### Vector Store
- Получение контекста для генерации
- Интеграция результатов поиска в промпт

## Планы развития

### Краткосрочные цели
- Добавление поддержки новых моделей
- Улучшение стратегий управления памятью
- Оптимизация производительности генерации

### Долгосрочные цели
- Реализация батчинга запросов
- Добавление квантизации моделей
- Интеграция с внешними AI провайдерами