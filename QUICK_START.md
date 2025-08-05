# 🚀 Быстрый старт: Развертывание сервера

## 📋 Что нужно сделать

### 1. Купить сервер
- **Провайдер:** [Hetzner](https://hetzner.com)
- **Тариф:** AX51 (16 CPU, 64GB RAM, 1TB NVMe)
- **Стоимость:** $120/мес
- **ОС:** Ubuntu 22.04 LTS

### 2. Запустить автоматическое развертывание
```bash
# Подключитесь к серверу по SSH
ssh root@your-server-ip

# Скачайте скрипт развертывания
wget https://raw.githubusercontent.com/your-repo/DEPLOYMENT_SCRIPT.sh

# Сделайте исполняемым и запустите
chmod +x DEPLOYMENT_SCRIPT.sh
./DEPLOYMENT_SCRIPT.sh
```

### 3. Загрузить модели
```bash
# Перейдите в директорию моделей
cd /home/extremist_checker/rag_chrome_ext/backend/models/

# Загрузите Qwen модель (замените на вашу ссылку)
wget https://your-model-url/qwen-model.tar.gz
tar -xzf qwen-model.tar.gz

# Создайте FAISS индекс
python3 create_faiss_index.py
```

### 4. Настроить домен и SSL
```bash
# Запустите настройку SSL (замените на ваш домен)
sudo certbot --nginx -d api.extremist-checker.com --non-interactive --agree-tos --email your-email@example.com
```

### 5. Обновить Chrome Extension
- Откройте `chrome_ext/content.js` и `chrome_ext/popup.js`
- Замените `http://localhost:8000` на `https://api.extremist-checker.com`
- Загрузите обновленное расширение в Chrome

## ✅ Проверка готовности

```bash
# Проверьте статус сервисов
systemctl status extremist-checker
systemctl status nginx

# Проверьте порты
netstat -tlnp | grep :8000
netstat -tlnp | grep :80

# Проверьте API
curl https://api.extremist-checker.com/health
```

## 🎯 Готово!

Ваш сервер готов обрабатывать 10,000+ пользователей!

**Следующие шаги:**
1. Загрузите Chrome Extension в Chrome Web Store
2. Настройте мониторинг
3. Начните маркетинг

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `journalctl -u extremist-checker -f`
2. Запустите мониторинг: `/home/extremist_checker/monitor.sh`
3. Проверьте документацию в `SERVER_REQUIREMENTS.md` 