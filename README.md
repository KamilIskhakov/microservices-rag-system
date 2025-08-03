# RAG Chrome Extension Backend

Backend для Chrome расширения, использующий RAG (Retrieval-Augmented Generation) для проверки экстремистских материалов.

## Особенности

- **Qwen модель**: Локальная модель Qwen для анализа экстремистских материалов
- **FAISS векторное хранилище**: Эффективный поиск по векторным эмбеддингам
- **Structured Output**: Структурированные ответы в формате JSON
- **Умный поиск**: Комбинация семантического и точного поиска
- **Chrome Extension**: Готовое расширение для браузера

## Установка

### Требования

- Python 3.10+
- Docker (опционально)
- Модель Qwen (должна быть в папке `backend/models/`)

### Локальная установка (для Mac с Apple Silicon)

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd rag_chrome_ext
```

2. Создайте виртуальное окружение:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Убедитесь, что модели находятся в папке `backend/models/`:
```bash
ls models/
# Должны быть файлы: config.json, tokenizer.json, model.safetensors и др.
```

5. Запустите сервер:
```bash
python run_server.py
```

Сервер будет доступен по адресу: http://localhost:8000

### Docker установка

1. Сборка и запуск:
```bash
docker-compose up --build
```

2. Или в фоновом режиме:
```bash
docker-compose up -d --build
```

3. Просмотр логов:
```bash
docker-compose logs -f
```

4. Остановка:
```bash
docker-compose down
```

## Использование

### API Endpoints

- `POST /check` - Проверка текста на экстремистские материалы

### Пример использования

```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"query": "навальный патриот"}'
```

Ответ:
```json
{
  "result": "Да. «алексей навальный. патриот. – издательство one book publishing, литва, 2024» - 09.06.2025",
  "processing_time": 4.05,
  "confidence": 0.95
}
```

### Тестирование API

1. Проверка экстремистского материала:
```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"query": "навальный патриот"}'
```

2. Проверка обычного запроса:
```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"query": "спорт футбол"}'
```

3. Проверка здоровья сервера:
```bash
curl http://localhost:8000/health
```

## Структура проекта

```
backend/
├── api/                    # API endpoints
├── models/                 # Модели Qwen
├── services/              # Бизнес-логика
│   ├── rag_service.py     # Основной RAG сервис
│   ├── model_manager.py   # Управление моделями
│   └── prompt_manager.py  # Управление промптами
├── vectorstore/           # Векторное хранилище
├── middleware/            # Middleware (безопасность)
└── scraper/              # Скраперы данных

chrome_ext/
├── manifest.json          # Манифест расширения
├── content.js             # Скрипт для страниц
├── popup.html             # Интерфейс расширения
└── styles.css             # Стили
```

## Конфигурация

Основные настройки в `config.py`:

- `QWEN_MODEL_PATH` - путь к модели Qwen
- `FAISS_INDEX_PATH` - путь к FAISS индексу
- `VECTOR_DIM` - размерность векторов
- `RELEVANCE_THRESHOLD` - порог релевантности для определения экстремистских материалов

### Переменные окружения

Создайте файл `.env` в корне проекта:

```bash
# Пути к моделям и данным
QWEN_MODEL_PATH=models/qwen-model
FAISS_INDEX_PATH=data/index.faiss
FAISS_META_PATH=data/index.faiss.meta

# Настройки сервера
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Настройки безопасности
LOG_SENSITIVE_DATA=false
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Настройки модели
VECTOR_DIM=384
RELEVANCE_THRESHOLD=0.3
CONFIDENCE_THRESHOLD=0.7

# Настройки логирования
LOG_LEVEL=INFO
LOG_FILE=logs/rag_service.log
ERROR_LOG_FILE=logs/errors.log

# CORS настройки
ALLOW_ORIGINS=["*"]
ALLOW_METHODS=["GET", "POST", "OPTIONS"]
ALLOW_HEADERS=["*"]
```

## Производительность

- **Время ответа**: ~3-5 секунд на запрос
- **Точность**: Высокая точность определения экстремистских материалов
- **Память**: ~8-16GB RAM для работы с моделью

## Возможности

- ✅ Проверка экстремистских материалов по РЕГ базе данных
- ✅ Извлечение полного названия материала и даты решения
- ✅ Умная фильтрация ложных срабатываний
- ✅ Chrome расширение с красивым интерфейсом
- ✅ CORS поддержка для работы с расширением
- ✅ Логирование и мониторинг

## Установка Chrome расширения

1. Откройте Chrome и перейдите в `chrome://extensions/`
2. Включите "Режим разработчика" (Developer mode)
3. Нажмите "Загрузить распакованное расширение" (Load unpacked)
4. Выберите папку `chrome_ext/`
5. Расширение будет установлено и появится в списке

### Использование расширения

1. Перейдите на любую веб-страницу
2. Нажмите на иконку расширения в панели инструментов
3. Введите текст для проверки
4. Получите результат: красный фон для экстремистских материалов, желтый для обычных

## Лицензия

MIT