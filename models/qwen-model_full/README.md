# Qwen2.5-3B-Instruct Model

Эта папка предназначена для модели `Qwen2.5-3B-Instruct`.

## 📥 Автоматическая загрузка

Для автоматической загрузки модели используйте скрипт:

```bash
./setup_model.sh
```

Этот скрипт:
- ✅ Проверит требования (Python 3.8+, 8GB места)
- ✅ Создаст виртуальное окружение
- ✅ Установит зависимости
- ✅ Загрузит модель Qwen2.5-3B-Instruct
- ✅ Сохранит в эту папку

## 📥 Ручная загрузка

### Вариант 1: Hugging Face Hub

```bash
# Установка transformers
pip install transformers torch accelerate

# Загрузка модели
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = 'Qwen/Qwen2.5-3B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map='auto',
    trust_remote_code=True
)
tokenizer.save_pretrained('./models/qwen-model_full/')
model.save_pretrained('./models/qwen-model_full/')
"
```

### Вариант 2: Ручная загрузка

1. Скачайте модель с [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
2. Распакуйте файлы в эту папку
3. Убедитесь, что структура выглядит так:
   ```
   models/qwen-model_full/
   ├── config.json
   ├── pytorch_model.bin
   ├── tokenizer.json
   ├── tokenizer_config.json
   └── README.md
   ```

## 🔧 Конфигурация

Модель автоматически загружается при запуске AI Model Service.

### Характеристики модели

- **Название**: Qwen2.5-3B-Instruct
- **Размер**: ~3B параметров
- **Тип**: Инструкционная модель
- **Язык**: Многоязычная (включая русский)
- **Размер файлов**: ~6-8GB
- **Память**: ~4-6GB RAM

## 📝 Примечание

Для тестирования можно использовать пустую папку, но функциональность AI Model Service будет ограничена.

## 🚀 После загрузки

После успешной загрузки модели:

```bash
# Запуск проекта
./run_local.sh

# Тестирование с моделью
./test_api.sh
``` 