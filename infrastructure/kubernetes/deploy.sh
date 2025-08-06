#!/bin/bash

# Скрипт для развертывания RAG системы в Kubernetes

set -e

echo "🚀 Развертывание RAG системы в Kubernetes..."

# Проверяем наличие kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl не установлен"
    exit 1
fi

# Проверяем подключение к кластеру
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Не удается подключиться к Kubernetes кластеру"
    exit 1
fi

# Создаем namespace
echo "📁 Создаем namespace..."
kubectl apply -f namespace.yaml

# Создаем ConfigMap
echo "⚙️ Создаем ConfigMap..."
kubectl apply -f configmap.yaml

# Создаем PersistentVolumeClaims
echo "💾 Создаем PersistentVolumeClaims..."
kubectl apply -f redis.yaml

# Ждем создания PVC
echo "⏳ Ждем создания PersistentVolumeClaims..."
kubectl wait --for=condition=Bound pvc/redis-pvc -n rag-system --timeout=60s
kubectl wait --for=condition=Bound pvc/models-pvc -n rag-system --timeout=60s
kubectl wait --for=condition=Bound pvc/logs-pvc -n rag-system --timeout=60s

# Развертываем Redis
echo "📊 Развертываем Redis..."
kubectl apply -f redis.yaml

# Ждем готовности Redis
echo "⏳ Ждем готовности Redis..."
kubectl wait --for=condition=available deployment/redis-deployment -n rag-system --timeout=120s

# Развертываем AI Model Service
echo "🤖 Развертываем AI Model Service..."
kubectl apply -f ai-model.yaml

# Развертываем API Gateway
echo "🌐 Развертываем API Gateway..."
kubectl apply -f api-gateway.yaml

# Развертываем Ingress
echo "🔗 Развертываем Ingress..."
kubectl apply -f ingress.yaml

# Развертываем HPA
echo "📈 Развертываем Horizontal Pod Autoscaler..."
kubectl apply -f hpa.yaml

# Ждем готовности всех сервисов
echo "⏳ Ждем готовности всех сервисов..."
kubectl wait --for=condition=available deployment/ai-model-deployment -n rag-system --timeout=300s
kubectl wait --for=condition=available deployment/api-gateway-deployment -n rag-system --timeout=120s

# Показываем статус
echo "📊 Статус развертывания:"
kubectl get pods -n rag-system
kubectl get services -n rag-system
kubectl get ingress -n rag-system

echo ""
echo "🎉 Развертывание завершено!"
echo ""
echo "📋 Полезные команды:"
echo "  - Просмотр логов: kubectl logs -f deployment/ai-model-deployment -n rag-system"
echo "  - Масштабирование: kubectl scale deployment/api-gateway-deployment --replicas=5 -n rag-system"
echo "  - Удаление: kubectl delete namespace rag-system"
echo ""
echo "🌐 Доступ к API:"
echo "  - Внутренний: api-gateway-service.rag-system.svc.cluster.local:8000"
echo "  - Внешний: через LoadBalancer или Ingress" 