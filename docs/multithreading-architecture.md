# Архитектура многопоточности в RAG Chrome Extension

## Обзор

Проект использует комплексный подход к многопоточности, включающий корутины, ThreadPoolExecutor, ProcessPoolExecutor и асинхронные операции. Архитектура построена на принципах SOLID с использованием паттернов Factory и Strategy для изоляции низкоуровневых оптимизаций от основного кода.

## Ключевые принципы

### 1. Разделение ответственности
- **Domain Layer**: Бизнес-логика без зависимости от конкретных реализаций многопоточности
- **Infrastructure Layer**: Конкретные реализации пулов потоков и процессов
- **Application Layer**: Координация между доменной логикой и инфраструктурой

### 2. Стратегии и фабрики
- **DeviceStrategy**: Выбор между CPU и GPU
- **ThreadingStrategy**: Выбор между потоками и процессами
- **ModelFactory**: Создание моделей с оптимизациями

## Архитектурные паттерны

### Strategy Pattern - Выбор устройства

```python
class DeviceStrategy(ABC):
    @abstractmethod
    def select_device(self, model_id: str, config: Dict[str, Any] = None) -> str:
        pass

class AutoDeviceStrategy(DeviceStrategy):
    def select_device(self, model_id: str, config: Dict[str, Any] = None) -> str:
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
```

**Преимущества:**
- Автоматический выбор оптимального устройства
- Легкое добавление новых стратегий
- Изоляция логики выбора устройства

### Factory Pattern - Создание моделей

```python
class ModelFactory(ABC):
    @abstractmethod
    def create_model(self, model_id: str, config: Dict[str, Any] = None) -> Tuple[Any, Any]:
        pass

class OptimizedModelFactory(ModelFactory):
    def create_model(self, model_id: str, config: Dict[str, Any] = None) -> Tuple[Any, Any]:
        # Оптимизированное создание модели
        device = self.device_strategy.select_device(model_id, config)
        # ... создание модели с оптимизациями
```

**Преимущества:**
- Инкапсуляция сложной логики создания моделей
- Возможность переключения между разными фабриками
- Централизованное управление конфигурацией

## Стратегии многопоточности

### 1. AsyncThreadingStrategy
**Назначение:** I/O-интенсивные операции
**Реализация:** ThreadPoolExecutor
**Использование:** HTTP запросы, чтение файлов, сетевые операции

```python
class AsyncThreadingStrategy(ThreadingStrategy):
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
```

### 2. ProcessThreadingStrategy
**Назначение:** CPU-интенсивные операции
**Реализация:** ProcessPoolExecutor
**Использование:** Генерация текста, эмбеддинги, математические вычисления

```python
class ProcessThreadingStrategy(ThreadingStrategy):
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(4, os.cpu_count() or 1)
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
```

### 3. HybridThreadingStrategy
**Назначение:** Автоматический выбор оптимальной стратегии
**Реализация:** Комбинация ThreadPoolExecutor и ProcessPoolExecutor
**Использование:** Умное распределение задач

```python
class HybridThreadingStrategy(ThreadingStrategy):
    def _select_executor(self, task: Callable) -> ThreadPoolExecutor | ProcessPoolExecutor:
        task_name = task.__name__.lower()
        
        # CPU-интенсивные задачи
        cpu_intensive_keywords = ['compute', 'calculate', 'process', 'generate', 'encode']
        if any(keyword in task_name for keyword in cpu_intensive_keywords):
            return self.process_executor
        
        # I/O-интенсивные задачи
        return self.thread_executor
```

## CPU vs I/O Bounded задачи

### CPU-Bounded задачи
- **Генерация текста:** Использует ProcessPoolExecutor
- **Создание эмбеддингов:** Использует ProcessPoolExecutor
- **Математические вычисления:** Использует ProcessPoolExecutor

### I/O-Bounded задачи
- **HTTP запросы:** Использует ThreadPoolExecutor
- **Чтение файлов:** Использует ThreadPoolExecutor
- **Сетевые операции:** Использует ThreadPoolExecutor

## Корутины и асинхронность

### Принципы использования корутин

1. **Неблокирующие операции:** Все I/O операции выполняются асинхронно
2. **Семафоры для ограничения конкурентности:** Предотвращение перегрузки ресурсов
3. **Graceful shutdown:** Корректное завершение всех корутин

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

## Изоляция низкоуровневых оптимизаций

### 1. Абстракции в Domain Layer

```python
class ModelService:
    def __init__(self, model_repository: ModelRepository):
        self.model_repository = model_repository
    
    def generate_text(self, model_id: str, prompt: str, max_length: int = 512, temperature: float = 0.7) -> str:
        # Доменная логика без зависимости от конкретных реализаций
        if not self.is_model_available(model_id):
            raise ValueError(f"Модель {model_id} недоступна")
        
        return self.model_repository.generate_text(model_id, prompt, max_length, temperature)
```

### 2. Конкретные реализации в Infrastructure Layer

```python
class OptimizedModelRepository(ModelRepository):
    def __init__(self, factory_name: str = "optimized", threading_strategy: str = "hybrid"):
        self.model_factory = ModelFactoryRegistry.get_factory(factory_name)
        self.threading_manager = ThreadingManager(threading_strategy)
```

## Конфигурация ресурсов

### Docker конфигурация

```yaml
ai-model:
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

### Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `DEVICE_TYPE` | Тип устройства для моделей | `auto` |
| `CPU_THREADS` | Количество CPU потоков | `4` |
| `GPU_MEMORY_FRACTION` | Доля GPU памяти | `0.8` |
| `MAX_WORKERS` | Максимум рабочих потоков | `8` |
| `MAX_PROCESSES` | Максимум процессов | `2` |

## Мониторинг и метрики

### Метрики производительности

1. **Время выполнения задач**
2. **Использование CPU/GPU**
3. **Количество активных потоков/процессов**
4. **Кэш-хиты/миссы**

### Логирование

```python
logger.info(f"Инициализирован HybridThreadingStrategy: {self.thread_workers} потоков, {self.process_workers} процессов")
logger.info(f"Модель {model_id} успешно создана на {device}")
```

## Лучшие практики

### 1. Использование семафоров
```python
semaphore = asyncio.Semaphore(max_concurrent)
async with semaphore:
    result = await self.process_request(request)
```

### 2. Graceful shutdown
```python
@app.on_event("shutdown")
async def shutdown_event():
    if thread_pool:
        thread_pool.shutdown(wait=True)
    if process_pool:
        process_pool.shutdown(wait=True)
```

### 3. Обработка исключений
```python
try:
    result = await self.threading_manager.execute_task(task, *args, **kwargs)
except Exception as e:
    logger.error(f"Ошибка выполнения задачи: {e}")
    # Fallback логика
```

### 4. Мониторинг ресурсов
```python
def get_memory_usage(self) -> Dict[str, Any]:
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "gpu_memory": torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
    }
```

## Заключение

Архитектура многопоточности в проекте обеспечивает:

1. **Масштабируемость:** Автоматическое распределение задач между потоками и процессами
2. **Производительность:** Оптимальное использование CPU и GPU ресурсов
3. **Надежность:** Graceful shutdown и обработка исключений
4. **Гибкость:** Легкое переключение между стратегиями через фабрики
5. **Изоляцию:** Низкоуровневые оптимизации не проникают в основной код

Все решения основаны на принципах SOLID и обеспечивают чистую архитектуру с четким разделением ответственности между слоями.
