#!/bin/bash

# 🚀 Скрипт автоматического развертывания Extremist Checker
# Использование: ./DEPLOYMENT_SCRIPT.sh

set -e  # Остановка при ошибке

echo "🚀 Начинаем развертывание Extremist Checker..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав администратора
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Не запускайте скрипт от root пользователя!"
        exit 1
    fi
}

# Обновление системы
update_system() {
    log_info "Обновление системы..."
    sudo apt update && sudo apt upgrade -y
    log_success "Система обновлена"
}

# Установка базовых пакетов
install_basic_packages() {
    log_info "Установка базовых пакетов..."
    sudo apt install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        build-essential \
        git \
        curl \
        wget \
        nginx \
        certbot \
        python3-certbot-nginx \
        fail2ban \
        ufw \
        htop \
        unzip \
        redis-server
    log_success "Базовые пакеты установлены"
}

# Настройка Redis
setup_redis() {
    log_info "Настройка Redis..."
    
    # Останавливаем Redis для настройки
    sudo systemctl stop redis-server
    
    # Настраиваем Redis для кэширования
    sudo tee /etc/redis/redis.conf << EOF
# Основные настройки
bind 127.0.0.1
port 6379
timeout 300
tcp-keepalive 60

# Настройки памяти
maxmemory 2gb
maxmemory-policy allkeys-lru

# Настройки производительности
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes

# Настройки логирования
loglevel notice
logfile /var/log/redis/redis-server.log

# Настройки безопасности
protected-mode yes
EOF
    
    # Запускаем Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Проверяем статус
    if systemctl is-active --quiet redis-server; then
        log_success "Redis настроен и запущен"
    else
        log_error "Ошибка запуска Redis!"
        sudo systemctl status redis-server
    fi
}

# Настройка безопасности
setup_security() {
    log_info "Настройка безопасности..."
    
    # Настройка UFW
    sudo ufw --force enable
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80
    sudo ufw allow 443
    sudo ufw allow 22
    
    # Настройка Fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    
    log_success "Безопасность настроена"
}

# Настройка swap
setup_swap() {
    log_info "Настройка swap файла..."
    
    # Проверяем, есть ли уже swap
    if ! swapon --show | grep -q "/swapfile"; then
        sudo fallocate -l 8G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        
        # Добавляем в fstab
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    
    log_success "Swap настроен"
}

# Оптимизация системы
optimize_system() {
    log_info "Оптимизация системы..."
    
    # Оптимизация ядра
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
    echo 'net.core.somaxconn=65535' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv4.tcp_max_syn_backlog=65535' | sudo tee -a /etc/sysctl.conf
    
    # Применяем изменения
    sudo sysctl -p
    
    log_success "Система оптимизирована"
}

# Создание пользователя для приложения
create_app_user() {
    log_info "Создание пользователя для приложения..."
    
    if ! id "extremist_checker" &>/dev/null; then
        sudo useradd -m -s /bin/bash extremist_checker
        sudo usermod -aG sudo extremist_checker
        log_success "Пользователь extremist_checker создан"
    else
        log_warning "Пользователь extremist_checker уже существует"
    fi
}

# Клонирование репозитория
clone_repository() {
    log_info "Клонирование репозитория..."
    
    cd /home/extremist_checker
    sudo -u extremist_checker git clone https://github.com/your-username/rag_chrome_ext.git
    sudo chown -R extremist_checker:extremist_checker /home/extremist_checker/rag_chrome_ext
    
    log_success "Репозиторий склонирован"
}

# Настройка Python окружения
setup_python_env() {
    log_info "Настройка Python окружения..."
    
    cd /home/extremist_checker/rag_chrome_ext/backend
    
    # Создание виртуального окружения
    sudo -u extremist_checker python3.11 -m venv venv
    sudo -u extremist_checker ./venv/bin/pip install --upgrade pip
    
    # Установка зависимостей
    sudo -u extremist_checker ./venv/bin/pip install -r requirements.txt
    
    log_success "Python окружение настроено"
}

# Создание .env файла
create_env_file() {
    log_info "Создание .env файла..."
    
    cd /home/extremist_checker/rag_chrome_ext/backend
    
    # Копируем пример
    sudo -u extremist_checker cp env.example .env
    
    # Редактируем основные параметры
    sudo -u extremist_checker sed -i 's/LOG_LEVEL: str = "INFO"/LOG_LEVEL: str = "WARNING"/' .env
    sudo -u extremist_checker sed -i 's/RATE_LIMIT_PER_MINUTE: int = 60/RATE_LIMIT_PER_MINUTE: int = 120/' .env
    sudo -u extremist_checker sed -i 's/USE_HTTPS: bool = False/USE_HTTPS: bool = True/' .env
    
    log_success ".env файл создан"
}

# Настройка Nginx
setup_nginx() {
    log_info "Настройка Nginx..."
    
    # Создание конфигурации
    sudo tee /etc/nginx/sites-available/extremist-checker << EOF
server {
    listen 80;
    server_name api.extremist-checker.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Увеличиваем таймауты для долгих запросов
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Ограничение размера запроса
    client_max_body_size 1M;
    
    # Gzip сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
EOF
    
    # Активация сайта
    sudo ln -sf /etc/nginx/sites-available/extremist-checker /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Проверка конфигурации
    sudo nginx -t
    
    # Перезапуск Nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    log_success "Nginx настроен"
}

# Создание systemd сервиса
create_systemd_service() {
    log_info "Создание systemd сервиса..."
    
    sudo tee /etc/systemd/system/extremist-checker.service << EOF
[Unit]
Description=Extremist Checker API (Optimized)
After=network.target redis.service

[Service]
Type=simple
User=extremist_checker
Group=extremist_checker
WorkingDirectory=/home/extremist_checker/rag_chrome_ext/backend
Environment=PATH=/home/extremist_checker/rag_chrome_ext/backend/venv/bin
ExecStart=/home/extremist_checker/rag_chrome_ext/backend/venv/bin/uvicorn app_optimized:app --host 0.0.0.0 --port 8000 --workers 8 --loop uvloop --http httptools
Restart=always
RestartSec=10

# Ограничения ресурсов
LimitNOFILE=65535
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагрузка systemd и запуск сервиса
    sudo systemctl daemon-reload
    sudo systemctl enable extremist-checker
    sudo systemctl start extremist-checker
    
    log_success "Systemd сервис создан"
}

# Настройка SSL сертификата
setup_ssl() {
    log_info "Настройка SSL сертификата..."
    
    # Получение сертификата
    sudo certbot --nginx -d api.extremist-checker.com --non-interactive --agree-tos --email your-email@example.com
    
    # Настройка автообновления
    sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -
    
    log_success "SSL сертификат настроен"
}

# Создание скрипта мониторинга
create_monitoring_script() {
    log_info "Создание скрипта мониторинга..."
    
    sudo tee /home/extremist_checker/monitor.sh << 'EOF'
#!/bin/bash

# Скрипт мониторинга системы

echo "=== Мониторинг системы $(date) ==="

# CPU
echo "CPU использование:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1

# RAM
echo "RAM использование:"
free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}'

# Диск
echo "Диск использование:"
df -h / | awk 'NR==2{print $5}'

# Сетевые соединения
echo "Активные соединения:"
netstat -an | grep :8000 | wc -l

# Статус сервиса
echo "Статус сервиса:"
systemctl is-active extremist-checker

echo "========================"
EOF
    
    sudo chmod +x /home/extremist_checker/monitor.sh
    sudo chown extremist_checker:extremist_checker /home/extremist_checker/monitor.sh
    
    log_success "Скрипт мониторинга создан"
}

# Создание скрипта резервного копирования
create_backup_script() {
    log_info "Создание скрипта резервного копирования..."
    
    sudo tee /home/extremist_checker/backup.sh << 'EOF'
#!/bin/bash

# Скрипт резервного копирования

BACKUP_DIR="/home/extremist_checker/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="extremist_checker_backup_$DATE.tar.gz"

mkdir -p $BACKUP_DIR

# Создание резервной копии
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    /home/extremist_checker/rag_chrome_ext/backend/data \
    /home/extremist_checker/rag_chrome_ext/backend/models \
    /home/extremist_checker/rag_chrome_ext/backend/.env

# Удаление старых резервных копий (оставляем последние 7)
find $BACKUP_DIR -name "extremist_checker_backup_*.tar.gz" -mtime +7 -delete

echo "Резервная копия создана: $BACKUP_FILE"
EOF
    
    sudo chmod +x /home/extremist_checker/backup.sh
    sudo chown extremist_checker:extremist_checker /home/extremist_checker/backup.sh
    
    # Добавляем в cron (ежедневно в 2:00)
    sudo crontab -l 2>/dev/null | { cat; echo "0 2 * * * /home/extremist_checker/backup.sh"; } | sudo crontab -
    
    log_success "Скрипт резервного копирования создан"
}

# Финальная проверка
final_check() {
    log_info "Выполнение финальной проверки..."
    
    # Проверка статуса сервиса
    if systemctl is-active --quiet extremist-checker; then
        log_success "Сервис запущен"
    else
        log_error "Сервис не запущен!"
        sudo systemctl status extremist-checker
    fi
    
    # Проверка Nginx
    if systemctl is-active --quiet nginx; then
        log_success "Nginx запущен"
    else
        log_error "Nginx не запущен!"
    fi
    
    # Проверка портов
    if netstat -tlnp | grep -q :8000; then
        log_success "API слушает на порту 8000"
    else
        log_error "API не слушает на порту 8000!"
    fi
    
    if netstat -tlnp | grep -q :80; then
        log_success "Nginx слушает на порту 80"
    else
        log_error "Nginx не слушает на порту 80!"
    fi
    
    log_success "Финальная проверка завершена"
}

# Главная функция
main() {
    log_info "Начинаем развертывание Extremist Checker..."
    
    check_root
    update_system
    install_basic_packages
    setup_security
    setup_swap
    optimize_system
    create_app_user
    clone_repository
    setup_python_env
    create_env_file
    setup_redis
    setup_nginx
    create_systemd_service
    create_monitoring_script
    create_backup_script
    
    log_warning "ВНИМАНИЕ: Необходимо вручную:"
    log_warning "1. Загрузить модели в /home/extremist_checker/rag_chrome_ext/backend/models/"
    log_warning "2. Создать FAISS индекс"
    log_warning "3. Настроить домен api.extremist-checker.com"
    log_warning "4. Запустить setup_ssl() после настройки домена"
    log_warning "5. Обновить API URL в Chrome Extension"
    
    final_check
    
    log_success "Развертывание завершено!"
    log_info "Следующие шаги:"
    log_info "1. Настройте домен и DNS"
    log_info "2. Загрузите модели"
    log_info "3. Запустите setup_ssl()"
    log_info "4. Обновите Chrome Extension"
}

# Запуск главной функции
main "$@" 