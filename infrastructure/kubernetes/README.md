# Kubernetes развертывание RAG системы

## 🎯 Преимущества Kubernetes

### 1. **Автоматическое масштабирование**
- Horizontal Pod Autoscaler (HPA) автоматически масштабирует поды
- Вертикальное масштабирование ресурсов
- Масштабирование до нуля (scale to zero)

### 2. **Высокая доступность**
- Репликация сервисов
- Автоматическое восстановление после сбоев
- Распределение нагрузки

### 3. **Управление ресурсами**
- Точное выделение CPU и памяти
- Persistent Volumes для данных
- Resource Quotas

### 4. **Безопасность**
- RBAC (Role-Based Access Control)
- Network Policies
- Secrets management

## 📁 Структура манифестов

```
infrastructure/kubernetes/
├── namespace.yaml          # Namespace для RAG системы
├── configmap.yaml          # Конфигурация приложения
├── redis.yaml             # Redis с PersistentVolume
├── ai-model.yaml          # AI Model Service
├── api-gateway.yaml       # API Gateway
├── ingress.yaml           # Ingress для внешнего доступа
├── hpa.yaml              # Horizontal Pod Autoscaler
└── deploy.sh             # Скрипт развертывания
```

## 🚀 Быстрый старт

### Предварительные требования

1. **Kubernetes кластер** (minikube, kind, или облачный)
2. **kubectl** установлен и настроен
3. **Docker images** собраны и доступны

### Развертывание

```bash
# Переходим в директорию Kubernetes
cd infrastructure/kubernetes

# Делаем скрипт исполняемым
chmod +x deploy.sh

# Запускаем развертывание
./deploy.sh
```

### Проверка статуса

```bash
# Проверяем поды
kubectl get pods -n rag-system

# Проверяем сервисы
kubectl get services -n rag-system

# Проверяем ingress
kubectl get ingress -n rag-system

# Просмотр логов
kubectl logs -f deployment/ai-model-deployment -n rag-system
```

## 📊 Мониторинг и масштабирование

### Автоматическое масштабирование

HPA автоматически масштабирует поды на основе:
- CPU utilization (70% для API Gateway, 80% для AI Model)
- Memory utilization (80% для API Gateway, 85% для AI Model)

### Ручное масштабирование

```bash
# Масштабирование API Gateway
kubectl scale deployment/api-gateway-deployment --replicas=5 -n rag-system

# Масштабирование AI Model
kubectl scale deployment/ai-model-deployment --replicas=2 -n rag-system
```

## 🔧 Конфигурация

### ConfigMap

Основные настройки в `configmap.yaml`:
- Redis URL
- Путь к модели
- Устройство (CPU/GPU)
- Настройки Uvicorn
- Уровень логирования

### Secrets

Для продакшена создайте Secret для платежных данных:

```bash
kubectl create secret generic rag-secrets \
  --from-literal=YOOKASSA_SHOP_ID=your_shop_id \
  --from-literal=YOOKASSA_SECRET_KEY=your_secret_key \
  -n rag-system
```

## 💾 Хранилище

### Persistent Volumes

- **Redis PVC**: 1Gi для данных Redis
- **Models PVC**: 10Gi для AI моделей
- **Logs PVC**: 5Gi для логов

### Backup стратегия

```bash
# Backup Redis
kubectl exec -it redis-deployment-xxx -n rag-system -- redis-cli BGSAVE

# Backup моделей
kubectl cp rag-system/ai-model-deployment-xxx:/app/models ./backup/models
```

## 🔒 Безопасность

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: rag-network-policy
  namespace: rag-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: rag-system
    ports:
    - protocol: TCP
      port: 8000
```

### RBAC

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: rag-system
  name: rag-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
```

## 📈 Производительность

### Resource Limits

- **AI Model Service**: 10Gi RAM, 6 CPU
- **API Gateway**: 1Gi RAM, 2 CPU
- **Redis**: 512Mi RAM, 500m CPU

### Оптимизация

1. **Node Affinity** для размещения AI Model на мощных узлах
2. **Pod Disruption Budget** для защиты от случайного удаления
3. **Resource Quotas** для ограничения потребления ресурсов

## 🧪 Тестирование

### Load Testing

```bash
# Тестирование API Gateway
kubectl run load-test --image=busybox --rm -it --restart=Never -- \
  wget -O- http://api-gateway-service:8000/health
```

### Health Checks

Все сервисы имеют health checks:
- Liveness Probe: проверка работоспособности
- Readiness Probe: проверка готовности к трафику

## 🔄 Обновления

### Rolling Update

```bash
# Обновление образа
kubectl set image deployment/api-gateway-deployment \
  api-gateway=rag-api-gateway:v2.0.0 -n rag-system
```

### Blue-Green Deployment

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: api-gateway-rollout
spec:
  replicas: 3
  strategy:
    blueGreen:
      activeService: api-gateway-active
      previewService: api-gateway-preview
```

## 🗑️ Удаление

```bash
# Удаление всего namespace
kubectl delete namespace rag-system

# Или удаление отдельных компонентов
kubectl delete -f ai-model.yaml
kubectl delete -f api-gateway.yaml
kubectl delete -f redis.yaml
```

## 📋 Чеклист продакшена

- [ ] Настроены Secrets для платежей
- [ ] Настроен SSL/TLS сертификат
- [ ] Настроен мониторинг (Prometheus/Grafana)
- [ ] Настроено логирование (ELK stack)
- [ ] Настроены backup стратегии
- [ ] Настроены Network Policies
- [ ] Настроен RBAC
- [ ] Настроены Resource Quotas
- [ ] Настроен Horizontal Pod Autoscaler
- [ ] Настроен Pod Disruption Budget 