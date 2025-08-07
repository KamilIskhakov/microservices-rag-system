# Scraper Service - Техническая документация

## Обзор сервиса

Scraper Service отвечает за сбор и обработку данных из внешних источников, в частности с сайта Минюста РФ. Сервис реализует паттерн Repository для управления задачами скрапинга и предоставляет REST API для создания, мониторинга и управления задачами сбора данных.

## Архитектура

### Слои архитектуры

#### Domain Layer
- **Entities**: `ScrapedData`, `ScrapingJob` - доменные сущности
- **Repositories**: `ScraperRepository` - абстрактный интерфейс для работы с данными
- **Services**: `ScraperService` - доменный сервис для бизнес-логики скрапинга

#### Application Layer
- **Use Cases**: Создание и управление задачами скрапинга
- **Commands**: Команды для управления процессом сбора данных

#### Infrastructure Layer
- **Persistence**: `InMemoryRepository` - реализация репозитория
- **API**: FastAPI endpoints для внешнего взаимодействия

### Ключевые компоненты

#### ScrapedData Entity
```python
@dataclass
class ScrapedData:
    id: str
    content: str
    source_url: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str = "pending"
    job_id: Optional[str] = None
```

#### ScrapingJob Entity
```python
@dataclass
class ScrapingJob:
    id: str
    url: str
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
```

#### ScraperRepository Interface
```python
class ScraperRepository(ABC):
    @abstractmethod
    def save_job(self, job: ScrapingJob) -> str:
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[ScrapingJob]:
        pass
    
    @abstractmethod
    def save_data(self, data: ScrapedData) -> str:
        pass
    
    @abstractmethod
    def get_data_by_job(self, job_id: str) -> List[ScrapedData]:
        pass
```

## API Endpoints

### Health Check
```
GET /health
```
Возвращает статус сервиса и информацию о текущих задачах.

### Job Management

#### Create Job
```
POST /job
Request Body:
{
    "url": "https://minjust.gov.ru/ru/extremist-materials/",
    "metadata": {
        "source": "minjust",
        "category": "extremist_materials"
    }
}
```
Создает новую задачу скрапинга.

#### Get Job Status
```
GET /job/{job_id}
```
Возвращает статус и детали задачи скрапинга.

#### List Jobs
```
GET /jobs
Parameters:
- status: str (optional)
- limit: int (optional, default: 10)
- offset: int (optional, default: 0)
```
Возвращает список задач с возможностью фильтрации.

#### Cancel Job
```
DELETE /job/{job_id}
```
Отменяет выполнение задачи.

### Data Management

#### Get Scraped Data
```
GET /data/{data_id}
```
Возвращает собранные данные по идентификатору.

#### Get Data by Job
```
GET /job/{job_id}/data
```
Возвращает все данные, собранные для конкретной задачи.

#### Export Data
```
GET /job/{job_id}/export
Parameters:
- format: str (json, csv, xml)
```
Экспортирует собранные данные в указанном формате.

### Statistics

#### Job Statistics
```
GET /statistics/jobs
```
Возвращает статистику по задачам:
- Общее количество задач
- Количество задач по статусам
- Среднее время выполнения
- Количество ошибок

#### Data Statistics
```
GET /statistics/data
```
Возвращает статистику по собранным данным:
- Общее количество записей
- Количество записей по источникам
- Размер данных в байтах

## Конфигурация

### Environment Variables

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `SCRAPER_TIMEOUT` | Таймаут запросов (сек) | `30` |
| `SCRAPER_DELAY` | Задержка между запросами (сек) | `1` |
| `SCRAPER_MAX_RETRIES` | Максимум попыток | `3` |
| `SCRAPER_USER_AGENT` | User-Agent для запросов | `Mozilla/5.0` |
| `SCRAPER_MAX_CONCURRENT` | Максимум одновременных задач | `5` |
| `SCRAPER_DATA_DIR` | Директория для сохранения данных | `/app/data` |

### Docker Configuration

```yaml
scraper:
  build:
    context: ../../services/scraper
    dockerfile: Dockerfile
  environment:
    - SCRAPER_TIMEOUT=30
    - SCRAPER_DELAY=1
    - SCRAPER_MAX_RETRIES=3
  volumes:
    - scraper_data:/app/data
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
```

## Алгоритмы и стратегии

### Web Scraping Strategy

Сервис использует несколько стратегий для эффективного сбора данных:

#### 1. Polite Scraping
```python
class PoliteScraper:
    def __init__(self, delay: float = 1.0, timeout: int = 30):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ScraperBot/1.0)'
        })
    
    def scrape(self, url: str) -> str:
        # Добавление задержки между запросами
        time.sleep(self.delay)
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        return response.text
```

#### 2. Retry Strategy
```python
def scrape_with_retry(self, url: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            return self.scraper.scrape(url)
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
```

#### 3. Concurrent Processing
```python
async def process_jobs_concurrently(self, jobs: List[ScrapingJob]) -> List[ScrapedData]:
    semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def process_job(job: ScrapingJob) -> Optional[ScrapedData]:
        async with semaphore:
            return await self._process_single_job(job)
    
    tasks = [process_job(job) for job in jobs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [result for result in results if result is not None]
```

### Data Processing Strategy

#### 1. HTML Parsing
```python
from bs4 import BeautifulSoup

def parse_html_content(self, html_content: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Извлечение данных из таблиц
    tables = soup.find_all('table')
    data = []
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if cells:
                row_data = {
                    'text': ' '.join(cell.get_text(strip=True) for cell in cells),
                    'cells': [cell.get_text(strip=True) for cell in cells]
                }
                data.append(row_data)
    
    return data
```

#### 2. Data Validation
```python
def validate_scraped_data(self, data: ScrapedData) -> bool:
    # Проверка минимальной длины контента
    if len(data.content.strip()) < 10:
        return False
    
    # Проверка наличия ключевых элементов
    required_elements = ['text', 'metadata']
    for element in required_elements:
        if not hasattr(data, element):
            return False
    
    return True
```

## Обработка ошибок

### Типы ошибок

1. **JobNotFoundError**: Задача не найдена
2. **ScrapingError**: Ошибка при скрапинге
3. **ValidationError**: Ошибка валидации данных
4. **TimeoutError**: Таймаут запроса
5. **RateLimitError**: Превышение лимита запросов

### Обработка исключений

```python
async def process_job(self, job: ScrapingJob) -> ScrapedData:
    try:
        # Обновление статуса на "running"
        job.status = "running"
        job.started_at = datetime.now()
        self.repository.update_job(job)
        
        # Выполнение скрапинга
        content = await self.scraper.scrape_with_retry(job.url)
        
        # Создание записи данных
        data = ScrapedData(
            id=str(uuid.uuid4()),
            content=content,
            source_url=job.url,
            metadata=job.metadata or {},
            created_at=datetime.now(),
            job_id=job.id
        )
        
        # Валидация и сохранение
        if self.validate_scraped_data(data):
            self.repository.save_data(data)
            job.status = "completed"
        else:
            job.status = "failed"
            job.error_message = "Data validation failed"
        
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        raise ScrapingError(f"Failed to process job {job.id}: {str(e)}")
    
    finally:
        job.completed_at = datetime.now()
        self.repository.update_job(job)
    
    return data
```

## Мониторинг и метрики

### Health Check

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "scraper",
        "active_jobs": len(scraper_service.get_active_jobs()),
        "total_jobs": len(scraper_service.get_all_jobs()),
        "total_data_records": len(scraper_service.get_all_data())
    }
```

### Метрики производительности

- Время выполнения задач
- Количество успешных/неуспешных запросов
- Размер собранных данных
- Скорость сбора данных (records/second)

## Безопасность

### Валидация входных данных

```python
class JobRequest(BaseModel):
    url: str = Field(regex=r'^https?://.*')
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
```

### Rate Limiting

```python
class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def is_allowed(self) -> bool:
        now = time.time()
        # Очистка старых запросов
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.window_seconds]
        
        if len(self.requests) >= self.max_requests:
            return False
        
        self.requests.append(now)
        return True
```

## Разработка и тестирование

### Локальная разработка

```bash
# Запуск сервиса
cd services/scraper
python api/main.py

# Тестирование API
curl -X POST http://localhost:8001/job \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "metadata": {"test": true}}'
```

### Unit тесты

```python
def test_job_creation():
    repository = InMemoryRepository()
    job = ScrapingJob(
        id="test-1",
        url="https://example.com",
        status="pending",
        created_at=datetime.now()
    )
    job_id = repository.save_job(job)
    assert job_id == "test-1"

def test_data_validation():
    data = ScrapedData(
        id="test-1",
        content="test content",
        source_url="https://example.com",
        metadata={},
        created_at=datetime.now()
    )
    assert validate_scraped_data(data) == True
```

### Integration тесты

```python
def test_job_processing():
    # Создание задачи
    response = client.post("/job", json={
        "url": "https://httpbin.org/html",
        "metadata": {"test": True}
    })
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Проверка статуса
    response = client.get(f"/job/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["pending", "running", "completed"]
```

## Масштабирование

### Горизонтальное масштабирование

- Множественные инстансы Scraper Service
- Распределение задач между инстансами
- Общее хранилище данных

### Вертикальное масштабирование

- Увеличение количества одновременных задач
- Оптимизация алгоритмов парсинга
- Улучшение стратегий кэширования

## Интеграция с другими сервисами

### Vector Store Service
- Автоматическая индексация собранных данных
- Обновление векторного индекса при новых данных

### Request Processor Service
- Координация задач скрапинга
- Обработка результатов сбора данных

### AI Model Service
- Анализ собранных данных
- Классификация и обработка контента

## Планы развития

### Краткосрочные цели
- Добавление поддержки новых источников данных
- Улучшение алгоритмов парсинга
- Реализация планировщика задач

### Долгосрочные цели
- Интеграция с внешними API для сбора данных
- Реализация распределенного скрапинга
- Добавление поддержки JavaScript-рендеринга
