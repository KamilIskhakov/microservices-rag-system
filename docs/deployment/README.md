# 🚀 Развертывание RAG Chrome Extension

## 📋 Обзор развертывания

RAG Chrome Extension поддерживает несколько вариантов развертывания в зависимости от требований и ресурсов:

- **🐳 Docker Compose** - для разработки и MVP
- **☸️ Kubernetes** - для продакшена
- **☁️ Облачные провайдеры** - для масштабирования

## 🐳 Docker Compose развертывание

### Предварительные требования

```bash
# Системные требования
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM (минимум)
- 20GB свободного места
- Linux/macOS/Windows с Docker Desktop
```

### Быстрый старт

```bash
# 1. Клонирование репозитория
git clone https://github.com/your-repo/rag_chrome_ext.git
cd rag_chrome_ext

# 2. Настройка переменных окружения
cp env.example .env
# Отредактируйте .env файл

# 3. Запуск системы
./run_optimized.sh

# 4. Проверка статуса
docker ps
```

### Конфигурация окружения

Создайте файл `.env` в корне проекта:

```bash
# Redis конфигурация
REDIS_URL=redis://localhost:6379

# AI Model конфигурация
MODEL_PATH=/app/models/qwen-model_full
DEVICE=cpu
MAX_GENERATION_TIME=30
MAX_WORKERS=8

# Vector Store конфигурация
VECTOR_STORE_MODEL=sentence-transformers/all-MiniLM-L6-v2
RELEVANCE_THRESHOLD=0.3
TOP_K_RESULTS=5

# Payment конфигурация (заполнить реальными значениями)
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# Логирование
LOG_LEVEL=INFO

# Мониторинг
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Структура Docker Compose

```yaml
version: '3.8'

services:
  # Redis для кэширования
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # AI Model Service
  ai-model-optimized:
    build:
      context: .
      dockerfile: infrastructure/docker/services/Dockerfile.ai-model-optimized
    ports:
      - "8003:8003"
    environment:
      - MODEL_PATH=/app/models/qwen-model_full
      - DEVICE=cpu
    volumes:
      - ./models:/app/models
      - ai_model_data:/app/data

  # Vector Store Service
  vectorstore:
    build:
      context: .
      dockerfile: services/vectorstore/Dockerfile
    ports:
      - "8002:8002"
    environment:
      - VECTOR_STORE_MODEL=sentence-transformers/all-MiniLM-L6-v2
    volumes:
      - vectorstore_data:/app/data

  # API Gateway
  api-gateway:
    build:
      context: .
      dockerfile: services/api-gateway/Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - ai-model-optimized
      - vectorstore

  # Остальные сервисы...
```

### Команды управления

```bash
# Запуск всех сервисов
docker-compose -f infrastructure/docker/docker-compose.optimized.yml up -d

# Остановка всех сервисов
docker-compose -f infrastructure/docker/docker-compose.optimized.yml down

# Пересборка и запуск
docker-compose -f infrastructure/docker/docker-compose.optimized.yml up --build -d

# Просмотр логов
docker-compose -f infrastructure/docker/docker-compose.optimized.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f infrastructure/docker/docker-compose.optimized.yml logs -f api-gateway
```

### Проверка развертывания

```bash
# Проверка статуса контейнеров
docker ps

# Проверка health checks
curl http://localhost:8000/health
curl http://localhost:8003/health
curl http://localhost:8002/health

# Тестирование API
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"query": "тестовая проверка", "user_id": "user123"}'
```

## ☸️ Kubernetes развертывание

### Предварительные требования

```bash
# Системные требования
- Kubernetes 1.24+
- kubectl настроен
- Helm 3.0+ (опционально)
- 16GB RAM (минимум)
- 50GB свободного места
- Ingress контроллер
```

### Структура Kubernetes манифестов

```
infrastructure/kubernetes/
├── namespace.yaml           # Namespace
├── configmap.yaml          # Конфигурация
├── secrets.yaml            # Секреты
├── redis.yaml             # Redis StatefulSet
├── ai-model.yaml          # AI Model Deployment
├── vectorstore.yaml       # Vector Store Deployment
├── api-gateway.yaml       # API Gateway Deployment
├── scraper.yaml           # Scraper Deployment
├── payment.yaml           # Payment Deployment
├── request-processor.yaml # Request Processor Deployment
├── ingress.yaml           # Ingress
├── hpa.yaml              # Horizontal Pod Autoscaler
└── deploy.sh             # Скрипт развертывания
```

### Развертывание в Kubernetes

```bash
# 1. Создание namespace
kubectl apply -f infrastructure/kubernetes/namespace.yaml

# 2. Настройка конфигурации
kubectl apply -f infrastructure/kubernetes/configmap.yaml
kubectl apply -f infrastructure/kubernetes/secrets.yaml

# 3. Развертывание Redis
kubectl apply -f infrastructure/kubernetes/redis.yaml

# 4. Развертывание сервисов
kubectl apply -f infrastructure/kubernetes/ai-model.yaml
kubectl apply -f infrastructure/kubernetes/vectorstore.yaml
kubectl apply -f infrastructure/kubernetes/api-gateway.yaml
kubectl apply -f infrastructure/kubernetes/scraper.yaml
kubectl apply -f infrastructure/kubernetes/payment.yaml
kubectl apply -f infrastructure/kubernetes/request-processor.yaml

# 5. Настройка Ingress
kubectl apply -f infrastructure/kubernetes/ingress.yaml

# 6. Настройка HPA
kubectl apply -f infrastructure/kubernetes/hpa.yaml
```

### Автоматическое развертывание

```bash
# Использование скрипта развертывания
cd infrastructure/kubernetes
./deploy.sh

# Или с помощью Helm (если доступен)
helm install rag-system ./helm-chart
```

### Конфигурация Kubernetes

#### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-config
  namespace: rag-system
data:
  REDIS_URL: "redis://redis-service:6379"
  MODEL_PATH: "/app/models/qwen-model_full"
  DEVICE: "cpu"
  LOG_LEVEL: "INFO"
  VECTOR_STORE_MODEL: "sentence-transformers/all-MiniLM-L6-v2"
```

#### Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: rag-secrets
  namespace: rag-system
type: Opaque
data:
  YOOKASSA_SHOP_ID: <base64-encoded>
  YOOKASSA_SECRET_KEY: <base64-encoded>
```

#### PersistentVolumes
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-storage
  namespace: rag-system
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### Мониторинг в Kubernetes

```bash
# Проверка статуса подов
kubectl get pods -n rag-system

# Просмотр логов
kubectl logs -f deployment/ai-model -n rag-system

# Проверка сервисов
kubectl get services -n rag-system

# Проверка ingress
kubectl get ingress -n rag-system
```

## ☁️ Облачные провайдеры

### AWS EKS

```bash
# Создание кластера EKS
eksctl create cluster \
  --name rag-cluster \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 5

# Развертывание приложения
kubectl apply -f infrastructure/kubernetes/
```

### Google GKE

```bash
# Создание кластера GKE
gcloud container clusters create rag-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-standard-4

# Развертывание приложения
kubectl apply -f infrastructure/kubernetes/
```

### Azure AKS

```bash
# Создание кластера AKS
az aks create \
  --resource-group rag-rg \
  --name rag-cluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3

# Развертывание приложения
kubectl apply -f infrastructure/kubernetes/
```

## 🔧 Конфигурация и настройка

### Переменные окружения

#### Общие переменные
```bash
# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=json

# Мониторинг
ENABLE_METRICS=true
METRICS_PORT=9090

# Безопасность
JWT_SECRET=your-jwt-secret
API_KEY=your-api-key
```

#### AI Model Service
```bash
# Модель
MODEL_PATH=/app/models/qwen-model_full
MODEL_NAME=qwen-model_full
MODEL_TYPE=causal_lm

# Устройство
DEVICE_TYPE=auto
CPU_THREADS=4
GPU_MEMORY_FRACTION=0.8

# Производительность
MAX_GENERATION_TIME=30
MAX_WORKERS=8
MAX_PROCESSES=2
MAX_NEW_TOKENS=10
GENERATION_TEMPERATURE=0.1

# Память
MAX_MEMORY_USAGE=0.9
MIN_MEMORY_GB=2
```

#### Vector Store Service
```bash
# Модель эмбеддингов
VECTOR_STORE_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Поиск
RELEVANCE_THRESHOLD=0.3
TOP_K_RESULTS=5
MAX_SEARCH_TIME=10

# Индексация
INDEX_TYPE=faiss
INDEX_PATH=/app/data/faiss_index
```

#### Payment Service
```bash
# YooKassa
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
YOOKASSA_RETURN_URL=https://your-domain.com/payment/return

# Лимиты
FREE_DAILY_LIMIT=20
PAID_DAILY_LIMIT=1000
```

### Health Checks

```yaml
# Kubernetes health check
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Resource Limits

```yaml
# Kubernetes resource limits
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2"
```

## 📊 Мониторинг и логирование

### Prometheus метрики

```python
# Пример метрик
from prometheus_client import Counter, Histogram, Gauge

# Метрики запросов
REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

# Метрики модели
MODEL_MEMORY_USAGE = Gauge('model_memory_bytes', 'Model memory usage')
MODEL_LOAD_TIME = Histogram('model_load_duration_seconds', 'Model load time')
```

### Grafana дашборды

```json
{
  "dashboard": {
    "title": "RAG System Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, request_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

### Логирование

```python
# Structured logging
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "rag-system",
            "module": record.module
        }
        return json.dumps(log_entry)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🔒 Безопасность

### SSL/TLS настройка

```yaml
# Kubernetes Ingress с SSL
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rag-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - rag.example.com
    secretName: rag-tls
  rules:
  - host: rag.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway-service
            port:
              number: 8000
```

### Network Policies

```yaml
# Kubernetes Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: rag-network-policy
spec:
  podSelector:
    matchLabels:
      app: rag-system
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

## 🧪 Тестирование развертывания

### Smoke тесты

```bash
#!/bin/bash
# smoke_tests.sh

echo "🧪 Запуск smoke тестов..."

# Проверка доступности сервисов
services=("api-gateway:8000" "ai-model:8003" "vectorstore:8002")

for service in "${services[@]}"; do
    host=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    echo "Проверка $host:$port..."
    if curl -f http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $host доступен"
    else
        echo "❌ $host недоступен"
        exit 1
    fi
done

# Тестирование API
echo "Тестирование API..."
response=$(curl -s -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"query": "тест", "user_id": "test"}')

if echo "$response" | grep -q "success"; then
    echo "✅ API работает"
else
    echo "❌ API не работает"
    exit 1
fi

echo "🎉 Все тесты пройдены!"
```

### Load тесты

```python
# load_test.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def make_request(session, url, data):
    async with session.post(url, json=data) as response:
        return await response.json()

async def load_test():
    url = "http://localhost:8000/check"
    data = {"query": "тестовая проверка", "user_id": "user123"}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = make_request(session, url, data)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        print(f"Время выполнения: {end_time - start_time:.2f} секунд")
        print(f"Количество запросов: {len(results)}")
        print(f"RPS: {len(results) / (end_time - start_time):.2f}")

if __name__ == "__main__":
    asyncio.run(load_test())
```

## 🔄 Обновления и миграции

### Rolling Update

```bash
# Kubernetes rolling update
kubectl set image deployment/api-gateway-deployment \
  api-gateway=rag-api-gateway:v2.0.0 -n rag-system

# Проверка статуса
kubectl rollout status deployment/api-gateway-deployment -n rag-system
```

### Blue-Green Deployment

```yaml
# Blue-Green deployment strategy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway-blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
      version: blue
  template:
    metadata:
      labels:
        app: api-gateway
        version: blue
    spec:
      containers:
      - name: api-gateway
        image: rag-api-gateway:v1.0.0
```

### Database Migrations

```python
# Пример миграции
import redis
import json

def migrate_redis_data():
    r = redis.Redis(host='localhost', port=6379)
    
    # Миграция структуры данных
    old_keys = r.keys("user:*:limits")
    for key in old_keys:
        old_data = r.get(key)
        if old_data:
            new_data = {
                "daily_checks": int(old_data),
                "monthly_checks": 0,
                "last_reset": time.time()
            }
            r.set(key, json.dumps(new_data))
```

## 🗑️ Удаление

### Docker Compose

```bash
# Остановка и удаление контейнеров
docker-compose -f infrastructure/docker/docker-compose.optimized.yml down -v

# Удаление образов
docker rmi $(docker images -q rag-*)

# Очистка volumes
docker volume prune -f
```

### Kubernetes

```bash
# Удаление всех ресурсов
kubectl delete namespace rag-system

# Удаление PersistentVolumes
kubectl delete pv --all

# Очистка ConfigMaps и Secrets
kubectl delete configmap --all -n rag-system
kubectl delete secret --all -n rag-system
```

---

**🎯 Система готова к развертыванию в любом окружении!** 