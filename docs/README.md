# RAG Chrome Extension - Техническая документация

## Обзор проекта

RAG Chrome Extension представляет собой микросервисную систему для анализа текстов на предмет экстремистского содержания с использованием технологий Retrieval-Augmented Generation (RAG). Система построена на принципах Clean Architecture и Domain-Driven Design.

## Архитектура системы

Система состоит из семи независимых микросервисов:

1. **API Gateway** - Единая точка входа для всех запросов
2. **AI Model Service** - Управление и выполнение AI моделей
3. **Vector Store Service** - Векторное хранилище для семантического поиска
4. **Scraper Service** - Сбор и обработка данных из внешних источников
5. **Request Processor Service** - Координация и обработка запросов
6. **Payment Service** - Управление платежами и подписками
7. **Redis** - Кэширование и очереди сообщений

## Структура документации

### Архитектурная документация
- [Обзор архитектуры](architecture/README.md)
- [Диаграммы компонентов](architecture/README.md#диаграммы-компонентов)
- [Принципы проектирования](architecture/README.md#принципы-проектирования)

### API документация
- [AI Model Service](ai-model-service.md)
- [Vector Store Service](vector-store-service.md)
- [API Gateway Service](api-gateway-service.md)
- [Scraper Service](scraper-service.md)
- [Payment Service](payment-service.md)
- [Request Processor Service](request-processor-service.md)

### Документация по развертыванию
- [Локальное развертывание](deployment/README.md#локальное-развертывание)
- [Docker Compose](deployment/README.md#docker-compose)
- [Kubernetes](deployment/README.md#kubernetes)
- [Мониторинг и логирование](deployment/README.md#мониторинг-и-логирование)

## Технологический стек

### Backend
- **Python 3.11+** - Основной язык разработки
- **FastAPI** - Веб-фреймворк для API
- **Pydantic** - Валидация данных
- **Redis** - Кэширование и очереди
- **FAISS** - Векторное хранилище
- **Transformers** - Работа с AI моделями

### Инфраструктура
- **Docker** - Контейнеризация
- **Docker Compose** - Оркестрация контейнеров
- **Kubernetes** - Продакшн развертывание
- **Nginx** - Обратный прокси

### AI/ML
- **Qwen2.5-3B-Instruct** - Основная языковая модель
- **Sentence Transformers** - Эмбеддинги для векторного поиска
- **PyTorch** - Машинное обучение

## Принципы разработки

### Clean Architecture
Каждый микросервис следует принципам Clean Architecture с четким разделением на слои:
- **Domain Layer** - Бизнес-логика и сущности
- **Application Layer** - Use cases и координация
- **Infrastructure Layer** - Внешние зависимости и persistence

### SOLID принципы
- **Single Responsibility** - Каждый класс имеет одну ответственность
- **Open/Closed** - Расширение без изменения существующего кода
- **Liskov Substitution** - Подтипы заменяют базовые типы
- **Interface Segregation** - Интерфейсы содержат только необходимые методы
- **Dependency Inversion** - Зависимости от абстракций

### Микросервисные принципы
- **Независимость** - Каждый сервис может быть развернут отдельно
- **Слабая связанность** - Минимальные зависимости между сервисами
- **Высокая когезия** - Связанная функциональность в одном сервисе
- **API-first** - Все взаимодействия через четко определенные API

## Структура проекта

```
rag_chrome_ext/
├── services/                    # Микросервисы
│   ├── ai-model/              # AI Model Service
│   ├── api-gateway/           # API Gateway Service
│   ├── vectorstore/           # Vector Store Service
│   ├── scraper/               # Scraper Service
│   ├── request-processor/     # Request Processor Service
│   └── payment/               # Payment Service
├── infrastructure/             # Инфраструктура
│   ├── docker/                # Docker конфигурации
│   └── kubernetes/            # Kubernetes манифесты
├── docs/                      # Документация
├── models/                    # AI модели
└── chrome_ext/                # Chrome Extension
```

## Разработка и тестирование

### Локальная разработка
```bash
# Запуск всех сервисов
docker-compose -f infrastructure/docker/docker-compose.optimized.yml up -d

# Проверка здоровья сервисов
curl http://localhost:8000/health
```

### Тестирование API
```bash
# Тест генерации текста
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "текст для анализа", "user_id": "user123"}'
```

## Мониторинг и логирование

### Health Checks
Все сервисы предоставляют health endpoints:
- `GET /health` - Статус сервиса
- `GET /system-info` - Информация о системе (AI Model Service)

### Логирование
- Структурированные логи в формате JSON
- Уровни логирования: DEBUG, INFO, WARNING, ERROR
- Централизованный сбор логов через Docker

### Метрики
- Использование CPU и памяти
- Время ответа API
- Количество загруженных моделей
- Статистика запросов

## Безопасность

### Аутентификация
- JWT токены для API доступа
- Валидация пользователей через Payment Service

### Валидация данных
- Pydantic модели для валидации входных данных
- Санитизация пользовательского ввода

### Rate Limiting
- Ограничение количества запросов на пользователя
- Защита от DDoS атак

## Производительность

### Оптимизации
- Кэширование результатов в Redis
- Асинхронная обработка запросов
- Пул соединений для HTTP клиентов
- Оптимизация памяти GPU

### Масштабирование
- Горизонтальное масштабирование через Kubernetes
- Автоматическое масштабирование на основе нагрузки
- Балансировка нагрузки между инстансами

## Поддержка и развитие

### Добавление новых сервисов
1. Создать структуру папки в `services/`
2. Реализовать слои Domain, Application, Infrastructure
3. Добавить Dockerfile и docker-compose конфигурацию
4. Обновить API Gateway для маршрутизации

### Расширение функциональности
- Следование принципам Clean Architecture
- Добавление unit и integration тестов
- Обновление документации API
- Мониторинг производительности
