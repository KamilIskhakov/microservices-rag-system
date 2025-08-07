# Vector Store Service - Техническая документация

## Обзор сервиса

Vector Store Service обеспечивает семантический поиск документов с использованием векторных эмбеддингов. Сервис использует FAISS для индексации и поиска векторов, а также Sentence Transformers для генерации эмбеддингов. Реализует паттерн Repository для работы с векторными документами.

## Архитектура

### Слои архитектуры

#### Domain Layer
- **Entities**: `VectorDocument`, `SearchResult` - доменные сущности
- **Repositories**: `VectorRepository` - абстрактный интерфейс для работы с векторами
- **Services**: `VectorService` - доменный сервис для векторных операций

#### Application Layer
- **Use Cases**: Обработка запросов на поиск и индексацию
- **Commands**: Команды для управления векторным хранилищем

#### Infrastructure Layer
- **Persistence**: `FAISSRepository` - реализация репозитория с FAISS
- **API**: FastAPI endpoints для внешнего взаимодействия

### Ключевые компоненты

#### VectorDocument Entity
```python
@dataclass
class VectorDocument:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

#### SearchResult Entity
```python
@dataclass
class SearchResult:
    document_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    rank: int
```

#### VectorRepository Interface
```python
class VectorRepository(ABC):
    @abstractmethod
    def save_document(self, document: VectorDocument) -> str:
        pass
    
    @abstractmethod
    def search_similar(self, query_embedding: List[float], 
                      top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
        pass
```

## API Endpoints

### Health Check
```
GET /health
```
Возвращает статус сервиса и статистику документов.

### Document Management

#### Add Document
```
POST /document
Request Body:
{
    "content": "текст документа",
    "metadata": {
        "source": "источник",
        "category": "категория",
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```
Добавляет новый документ в векторное хранилище.

#### Get Document
```
GET /document/{document_id}
```
Возвращает документ по его идентификатору.

#### Update Document
```
PUT /document/{document_id}
Request Body:
{
    "content": "обновленный текст",
    "metadata": {
        "updated": true
    }
}
```
Обновляет существующий документ.

#### Delete Document
```
DELETE /document/{document_id}
```
Удаляет документ из хранилища.

### Search Operations

#### Search Documents
```
POST /search
Request Body:
{
    "query": "поисковый запрос",
    "top_k": 5,
    "threshold": 0.3,
    "filters": {
        "category": "категория",
        "date_from": "2024-01-01",
        "date_to": "2024-12-31"
    }
}
```
Выполняет семантический поиск документов.

#### Batch Search
```
POST /search/batch
Request Body:
{
    "queries": ["запрос 1", "запрос 2", "запрос 3"],
    "top_k": 5,
    "threshold": 0.3
}
```
Выполняет поиск для нескольких запросов одновременно.

### Index Management

#### Rebuild Index
```
POST /index/rebuild
```
Перестраивает индекс для всех документов.

#### Index Statistics
```
GET /index/stats
```
Возвращает статистику индекса:
- Общее количество документов
- Размер индекса
- Время последнего обновления

## Конфигурация

### Environment Variables

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `VECTOR_STORE_MODEL` | Модель для эмбеддингов | `sentence-transformers/all-MiniLM-L6-v2` |
| `RELEVANCE_THRESHOLD` | Порог релевантности | `0.3` |
| `TOP_K_RESULTS` | Количество результатов поиска | `5` |
| `INDEX_TYPE` | Тип FAISS индекса | `IndexFlatIP` |
| `EMBEDDING_DIMENSION` | Размерность эмбеддингов | `384` |

### Docker Configuration

```yaml
vectorstore:
  build:
    context: ../../services/vectorstore
    dockerfile: Dockerfile
  environment:
    - VECTOR_STORE_MODEL=sentence-transformers/all-MiniLM-L6-v2
    - RELEVANCE_THRESHOLD=0.3
    - TOP_K_RESULTS=5
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.0'
```

## Алгоритмы и стратегии

### Embedding Generation

Сервис использует Sentence Transformers для генерации эмбеддингов:

```python
from sentence_transformers import SentenceTransformer

class VectorService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def generate_embedding(self, text: str) -> List[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()
```

### Similarity Search

Используется косинусное сходство для поиска похожих документов:

```python
def search_similar(self, query_embedding: List[float], 
                  top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
    # Нормализация вектора запроса
    query_vector = np.array(query_embedding, dtype=np.float32)
    query_vector = query_vector / np.linalg.norm(query_vector)
    
    # Поиск в FAISS индексе
    similarities, indices = self.index.search(query_vector.reshape(1, -1), top_k)
    
    # Фильтрация по порогу релевантности
    results = []
    for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
        if similarity >= threshold:
            document = self.documents[idx]
            results.append(SearchResult(
                document_id=document.id,
                content=document.content,
                metadata=document.metadata,
                similarity_score=float(similarity),
                rank=i + 1
            ))
    
    return results
```

### Index Management

#### Index Types

1. **IndexFlatIP**: Точный поиск, быстрое построение
2. **IndexIVFFlat**: Приближенный поиск, быстрый поиск
3. **IndexHNSW**: Иерархический поиск, высокое качество

#### Index Building

```python
def build_index(self):
    if len(self.documents) == 0:
        return
    
    # Сбор всех эмбеддингов
    embeddings = []
    for doc in self.documents:
        if doc.embedding is not None:
            embeddings.append(doc.embedding)
    
    if not embeddings:
        return
    
    # Создание индекса
    embeddings_array = np.array(embeddings, dtype=np.float32)
    dimension = embeddings_array.shape[1]
    
    self.index = faiss.IndexFlatIP(dimension)
    self.index.add(embeddings_array)
```

## Производительность

### Оптимизации

1. **Кэширование эмбеддингов**: Сохранение предвычисленных эмбеддингов
2. **Батчинг**: Обработка документов пакетами
3. **Индексация**: Использование FAISS для быстрого поиска
4. **Фильтрация**: Предварительная фильтрация по метаданным

### Метрики производительности

- Время генерации эмбеддинга
- Время поиска в индексе
- Точность поиска (precision/recall)
- Пропускная способность (documents/second)

## Обработка ошибок

### Типы ошибок

1. **DocumentNotFoundError**: Документ не найден
2. **IndexNotBuiltError**: Индекс не построен
3. **EmbeddingError**: Ошибка генерации эмбеддинга
4. **SearchError**: Ошибка поиска
5. **ValidationError**: Ошибка валидации входных данных

### Обработка исключений

```python
try:
    results = vector_service.search_similar(query_embedding)
except IndexNotBuiltError:
    # Перестроение индекса
    vector_service.rebuild_index()
    results = vector_service.search_similar(query_embedding)
except EmbeddingError:
    # Повторная попытка генерации эмбеддинга
    query_embedding = vector_service.generate_embedding(query_text)
    results = vector_service.search_similar(query_embedding)
```

## Мониторинг и метрики

### Health Check

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "vectorstore",
        "total_documents": len(vector_service.get_all_documents()),
        "indexed_documents": vector_service.get_indexed_count(),
        "index_size_mb": vector_service.get_index_size_mb()
    }
```

### Метрики качества

- **Precision@k**: Точность поиска для топ-k результатов
- **Recall@k**: Полнота поиска для топ-k результатов
- **NDCG@k**: Нормализованный дисконтированный кумулятивный выигрыш
- **Query Response Time**: Время ответа на запрос

## Безопасность

### Валидация входных данных

```python
class DocumentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(ge=1, le=100)
    threshold: float = Field(ge=0.0, le=1.0)
```

### Санитизация данных

- Очистка HTML тегов из контента
- Валидация метаданных
- Ограничение размера документов

## Разработка и тестирование

### Локальная разработка

```bash
# Запуск сервиса
cd services/vectorstore
python api/main.py

# Тестирование API
curl -X POST http://localhost:8002/document \
  -H "Content-Type: application/json" \
  -d '{"content": "тестовый документ", "metadata": {"test": true}}'
```

### Unit тесты

```python
def test_document_creation():
    repository = FAISSRepository()
    document = VectorDocument(
        id="test-1",
        content="test content",
        metadata={"test": True}
    )
    doc_id = repository.save_document(document)
    assert doc_id == "test-1"
```

### Integration тесты

```python
def test_search_functionality():
    # Добавление тестовых документов
    client.post("/document", json={
        "content": "документ о машинном обучении",
        "metadata": {"category": "ai"}
    })
    
    # Поиск документов
    response = client.post("/search", json={
        "query": "машинное обучение",
        "top_k": 5
    })
    
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0
```

## Масштабирование

### Горизонтальное масштабирование

- Репликация индекса на несколько узлов
- Шардинг документов по категориям
- Балансировка нагрузки через API Gateway

### Вертикальное масштабирование

- Увеличение памяти для больших индексов
- Использование более мощных CPU для генерации эмбеддингов
- Оптимизация размера индекса

## Интеграция с другими сервисами

### Scraper Service
- Получение новых документов для индексации
- Автоматическое обновление индекса

### AI Model Service
- Предоставление контекста для генерации
- Интеграция результатов поиска в промпт

### Request Processor
- Координация поисковых запросов
- Агрегация результатов от нескольких источников

## Планы развития

### Краткосрочные цели
- Добавление поддержки различных типов FAISS индексов
- Реализация фильтрации по метаданным
- Оптимизация производительности поиска

### Долгосрочные цели
- Интеграция с внешними векторными базами данных
- Поддержка мультиязычных эмбеддингов
- Реализация семантического кластеринга документов
