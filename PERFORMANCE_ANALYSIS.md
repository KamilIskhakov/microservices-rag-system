# ⚡ Анализ производительности и оптимизация

## 🔍 Текущая архитектура

### Bottlenecks в системе:

1. **GIL (Global Interpreter Lock)** - ограничивает параллелизм в Python
2. **CPU-bound задачи** - инференс модели и векторный поиск
3. **Последовательная обработка** - каждый запрос обрабатывается по очереди
4. **Блокирующие операции** - загрузка модели в память

## 📊 Анализ производительности

### Текущие ограничения:

#### При 16 CPU ядрах (Hetzner AX51):
- **GIL ограничение:** Только 1 поток может выполнять Python код одновременно
- **Эффективное использование CPU:** ~6-8% от доступных ресурсов
- **Параллелизм:** Только I/O операции (сеть, диск)

#### Ожидаемая производительность:
- **Без оптимизации:** 50-100 запросов/минуту
- **С базовой оптимизацией:** 200-500 запросов/минуту
- **С полной оптимизацией:** 1000-2000 запросов/минуту

## 🚀 Решения для оптимизации

### 1. Многопроцессная архитектура

```python
# backend/app.py - обновленная конфигурация
import multiprocessing

# Определяем количество воркеров
workers = multiprocessing.cpu_count() * 2 + 1

# Запуск с множественными процессами
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 8
```

### 2. Асинхронная обработка

```python
# backend/services/async_rag_service.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

class AsyncRAGService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()
    
    async def check_async(self, request: CheckRequest) -> CheckResponse:
        """Асинхронная проверка"""
        loop = asyncio.get_event_loop()
        
        # Выполняем тяжелые операции в отдельном потоке
        result = await loop.run_in_executor(
            self.executor, 
            self._check_sync, 
            request
        )
        
        return result
    
    def _check_sync(self, request: CheckRequest) -> CheckResponse:
        """Синхронная проверка в отдельном потоке"""
        # Существующая логика RAGService.check()
        pass
```

### 3. Кэширование результатов

```python
# backend/services/cache_service.py
import redis
import hashlib
import json

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600  # 1 час
    
    def get_cache_key(self, query: str) -> str:
        """Генерирует ключ кэша"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get_cached_result(self, query: str) -> Optional[CheckResponse]:
        """Получает результат из кэша"""
        key = self.get_cache_key(query)
        cached = self.redis_client.get(key)
        
        if cached:
            data = json.loads(cached)
            return CheckResponse(**data)
        
        return None
    
    def cache_result(self, query: str, result: CheckResponse):
        """Кэширует результат"""
        key = self.get_cache_key(query)
        data = json.dumps(result.__dict__)
        self.redis_client.setex(key, self.cache_ttl, data)
```

### 4. Оптимизация модели

```python
# backend/services/optimized_model_manager.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch.jit

class OptimizedModelManager:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model = None
        self._tokenizer = None
        self._compiled_model = None
    
    def load_and_optimize(self):
        """Загружает и оптимизирует модель"""
        # Загружаем модель
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        
        # Компилируем модель для ускорения
        self._compiled_model = torch.jit.script(self._model)
        
        # Оптимизации для инференса
        self._compiled_model.eval()
        with torch.no_grad():
            # Предварительный прогрев
            dummy_input = torch.randint(0, 1000, (1, 10))
            _ = self._compiled_model(dummy_input)
    
    def generate_optimized(self, prompt: str) -> str:
        """Оптимизированная генерация"""
        with torch.no_grad():
            # Используем скомпилированную модель
            result = self._compiled_model.generate(
                input_ids=self._tokenizer.encode(prompt, return_tensors="pt"),
                max_length=50,
                temperature=0.1,
                do_sample=True
            )
            
            return self._tokenizer.decode(result[0], skip_special_tokens=True)
```

### 5. Векторный поиск оптимизация

```python
# backend/vectorstore/optimized_faiss_store.py
import faiss
import numpy as np
from typing import List, Tuple

class OptimizedFaissStore:
    def __init__(self):
        self.index = None
        self.texts = []
        self.embeddings = []
        self._lock = threading.Lock()
    
    def build_index(self, texts: List[str], embeddings: List[np.ndarray]):
        """Строит оптимизированный индекс"""
        self.texts = texts
        self.embeddings = np.array(embeddings, dtype=np.float32)
        
        # Создаем индекс с оптимизациями
        dimension = embeddings[0].shape[0]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product для косинусного сходства
        
        # Нормализуем векторы
        faiss.normalize_L2(self.embeddings)
        
        # Добавляем в индекс
        self.index.add(self.embeddings)
        
        # Оптимизируем для поиска
        self.index.make_direct_map()
    
    def query_optimized(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Оптимизированный поиск"""
        with self._lock:
            # Нормализуем запрос
            query_norm = query_embedding.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(query_norm)
            
            # Выполняем поиск
            scores, indices = self.index.search(query_norm, top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.texts):
                    results.append((self.texts[idx], float(score)))
            
            return results
```

## 🏗️ Обновленная архитектура

### Многопроцессная система:

```python
# backend/app_optimized.py
from fastapi import FastAPI
import uvicorn
from multiprocessing import cpu_count

app = FastAPI()

# Конфигурация для высоких нагрузок
if __name__ == "__main__":
    workers = cpu_count() * 2 + 1
    uvicorn.run(
        "app_optimized:app",
        host="0.0.0.0",
        port=8000,
        workers=workers,
        loop="uvloop",
        http="httptools"
    )
```

### Load Balancer конфигурация:

```nginx
# /etc/nginx/sites-available/extremist-checker-optimized
upstream api_backend {
    least_conn;  # Распределение по наименьшей нагрузке
    
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
    server 127.0.0.1:8005;
    server 127.0.0.1:8006;
    server 127.0.0.1:8007;
}

server {
    listen 80;
    server_name api.extremist-checker.com;
    
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Увеличиваем таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Буферизация
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}
```

## 📈 Ожидаемые улучшения

### После оптимизации:

#### Производительность:
- **Запросов в минуту:** 1000-2000 (вместо 50-100)
- **Время ответа:** <1 секунда (вместо 2-5 секунд)
- **Использование CPU:** 60-80% (вместо 6-8%)
- **Параллелизм:** 8 процессов + асинхронность

#### Масштабируемость:
- **10,000 пользователей:** Легко обрабатывается
- **100,000 пользователей:** Требует дополнительных серверов
- **1,000,000 пользователей:** Кластер из нескольких серверов

## 🔧 Рекомендации по серверу

### Обновленные требования:

#### Hetzner AX51 (рекомендуется):
- **CPU:** 16 ядер (используем 8-12 процессов)
- **RAM:** 64 GB (32 GB для моделей + 32 GB для кэша)
- **SSD:** 1 TB NVMe (быстрый доступ к данным)
- **Дополнительно:** Redis для кэширования

#### Мониторинг производительности:
```bash
# Установка Redis
sudo apt install redis-server

# Мониторинг процессов
htop

# Мониторинг сети
iftop

# Мониторинг диска
iotop
```

## 🎯 Итоговые рекомендации

### Для максимальной производительности:

1. **Используйте многопроцессную архитектуру** (8-12 воркеров)
2. **Добавьте Redis кэширование** для повторяющихся запросов
3. **Оптимизируйте модель** (компиляция, float16)
4. **Настройте Load Balancer** для распределения нагрузки
5. **Мониторьте производительность** в реальном времени

### Ожидаемый результат:
**1000-2000 запросов/минуту** вместо 50-100!

Это позволит обрабатывать **10,000+ пользователей** без проблем! 🚀 