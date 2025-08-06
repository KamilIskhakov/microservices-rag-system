# 📚 RAG Chrome Extension - Документация для разработчиков

## 🎯 Обзор проекта

RAG Chrome Extension - это система проверки текстов на экстремизм с использованием Retrieval-Augmented Generation (RAG) и микросервисной архитектуры. Проект построен на принципах SOLID и Domain-Driven Design (DDD).

### 🏗️ Архитектурные принципы

- **SOLID принципы** - все компоненты следуют принципам SOLID
- **DDD (Domain-Driven Design)** - четкое разделение доменной логики
- **Микросервисная архитектура** - независимые сервисы
- **CQRS** - разделение команд и запросов
- **Event Sourcing** - отслеживание изменений через события

## 📋 Содержание документации

### 🏗️ [Архитектура](architecture/README.md)
- Обзор архитектуры системы
- Диаграммы компонентов
- Паттерны проектирования
- Принципы DDD

### 🚀 [Развертывание](deployment/README.md)
- Docker Compose развертывание
- Kubernetes развертывание
- Конфигурация окружения
- Мониторинг и логирование

### 🌐 [API Документация](api/README.md)
- REST API endpoints
- WebSocket API
- Аутентификация и авторизация
- Rate limiting

### 🧪 [Тестирование](testing/README.md)
- Unit тесты
- Integration тесты
- E2E тесты
- Performance тесты

### 🔧 [Разработка](development/README.md)
- Настройка окружения разработки
- Структура кода
- Стандарты кодирования
- Git workflow

### 📊 [Мониторинг](monitoring/README.md)
- Метрики и алерты
- Логирование
- Трейсинг
- Health checks

## 🚀 Быстрый старт

### Предварительные требования

```bash
# Системные требования
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM (минимум)
- 20GB свободного места
- Python 3.11+ (для разработки)
```

### Запуск системы

```bash
# Клонирование репозитория
git clone https://github.com/your-repo/rag_chrome_ext.git
cd rag_chrome_ext

# Запуск всех сервисов
./run_optimized.sh

# Проверка статуса
docker ps
```

### Доступные сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| API Gateway | 8000 | Единая точка входа |
| AI Model | 8003 | Генерация текста |
| Vector Store | 8002 | Поиск по векторам |
| Scraper | 8001 | Парсинг данных |
| Payment | 8005 | Обработка платежей |
| Request Processor | 8004 | Координация запросов |
| Redis | 6379 | Кэширование |

## 🏗️ Структура проекта

```
rag_chrome_ext/
├── 📁 src/                    # Исходный код (DDD архитектура)
│   ├── 📁 domain/             # Доменный слой
│   │   ├── 📁 entities/       # Доменные сущности
│   │   ├── 📁 repositories/   # Интерфейсы репозиториев
│   │   ├── 📁 services/       # Доменные сервисы
│   │   ├── 📁 strategies/     # Стратегии
│   │   └── 📁 observers/      # Наблюдатели
│   ├── 📁 application/        # Слой приложения
│   │   └── 📁 commands/       # Команды (CQRS)
│   ├── 📁 infrastructure/     # Инфраструктурный слой
│   │   ├── 📁 api/           # API endpoints
│   │   ├── 📁 persistence/   # Реализации репозиториев
│   │   └── 📁 factories/     # Фабрики
│   └── 📁 shared/            # Общие компоненты
│       ├── 📁 config/        # Конфигурация
│       └── 📁 utils/         # Утилиты
├── 📁 services/              # Микросервисы
│   ├── 📁 ai-model/         # AI Model Service
│   ├── 📁 api-gateway/      # API Gateway
│   ├── 📁 vectorstore/      # Vector Store Service
│   ├── 📁 scraper/          # Scraper Service
│   ├── 📁 payment/          # Payment Service
│   └── 📁 request-processor/ # Request Processor
├── 📁 infrastructure/        # Инфраструктура
│   ├── 📁 docker/           # Docker конфигурации
│   └── 📁 kubernetes/       # Kubernetes манифесты
├── 📁 chrome_ext/           # Chrome Extension
├── 📁 docs/                 # Документация
└── 📁 models/               # AI модели
```

## 🎯 Ключевые особенности

### 🔍 RAG Система
- **Retrieval**: Поиск релевантных документов в векторной БД
- **Generation**: Генерация ответов с помощью AI модели
- **Augmentation**: Обогащение контекста найденными документами

### 🤖 AI Модель
- **Модель**: Qwen2.5-3B-Instruct
- **Оптимизация**: CPU/GPU адаптивная загрузка
- **Производительность**: Многопоточная обработка
- **Память**: Эффективное управление памятью

### 🗄️ Vector Store
- **Индексация**: FAISS для быстрого поиска
- **Эмбеддинги**: Sentence Transformers
- **Масштабируемость**: Поддержка больших объемов данных
- **Релевантность**: Настраиваемые пороги релевантности

### 📡 Scraper
- **Источник**: Минюст РФ
- **Автоматизация**: Планировщик задач
- **Интеграция**: Автоматическая синхронизация с RAG
- **Мониторинг**: Отслеживание статуса задач

### 💳 Payment
- **Провайдер**: YooKassa
- **Модель**: Freemium (20 проверок/день)
- **Безопасность**: Шифрование данных
- **Аналитика**: Отслеживание платежей

## 🔧 Технологический стек

### Backend
- **Python 3.11+** - основной язык
- **FastAPI** - веб-фреймворк
- **Uvicorn** - ASGI сервер
- **Redis** - кэширование и очереди
- **FAISS** - векторная БД
- **Transformers** - AI модели

### Frontend
- **Chrome Extension** - клиентское приложение
- **JavaScript ES6+** - язык программирования
- **Manifest V3** - современный API

### DevOps
- **Docker** - контейнеризация
- **Docker Compose** - оркестрация
- **Kubernetes** - продакшн развертывание
- **Prometheus** - мониторинг
- **Grafana** - визуализация

## 📊 Метрики и мониторинг

### Системные метрики
- CPU и RAM использование
- Время ответа API
- Количество запросов
- Ошибки и исключения

### Бизнес метрики
- Количество проверок
- Конверсия в платные пользователи
- Релевантность результатов
- Пользовательская активность

## 🔒 Безопасность

### Аутентификация
- API ключи для сервисов
- Rate limiting
- Input validation
- SQL injection protection

### Шифрование
- HTTPS/TLS
- Шифрование чувствительных данных
- Безопасное хранение секретов

## 🚀 Roadmap

### Версия 2.0
- [ ] Поддержка множественных языков
- [ ] Расширенная аналитика
- [ ] API для интеграций
- [ ] Мобильное приложение

### Версия 3.0
- [ ] Машинное обучение для улучшения точности
- [ ] Поддержка видео и аудио
- [ ] Интеграция с другими источниками данных
- [ ] Расширенная персонализация

## 🤝 Вклад в проект

### Стандарты кодирования
- PEP 8 для Python
- ESLint для JavaScript
- TypeScript для типизации
- Prettier для форматирования

### Git Workflow
- Feature branches
- Pull requests
- Code review
- Automated testing

### Тестирование
- Unit тесты (pytest)
- Integration тесты
- E2E тесты (Playwright)
- Performance тесты

## 📞 Поддержка

### Контакты
- **Email**: dev@rag-extension.com
- **Slack**: #rag-extension-dev
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

### Ресурсы
- [API Документация](api/README.md)
- [Архитектура](architecture/README.md)
- [Развертывание](deployment/README.md)
- [Разработка](development/README.md)

---

**🎉 Спасибо за использование RAG Chrome Extension!** 