# Payment Service - Техническая документация

## Обзор сервиса

Payment Service отвечает за управление платежами, подписками и лимитами пользователей. Сервис реализует freemium модель с ограничением в 20 проверок в день для бесплатных пользователей и предоставляет REST API для интеграции с платежными системами, в частности с YooKassa.

## Архитектура

### Слои архитектуры

#### Domain Layer
- **Entities**: `Payment`, `Subscription` - доменные сущности
- **Repositories**: `PaymentRepository` - абстрактный интерфейс для работы с платежами
- **Services**: `PaymentService` - доменный сервис для бизнес-логики платежей

#### Application Layer
- **Use Cases**: Создание платежей, управление подписками
- **Commands**: Команды для обработки платежных операций

#### Infrastructure Layer
- **Persistence**: `InMemoryRepository` - реализация репозитория
- **API**: FastAPI endpoints для внешнего взаимодействия

### Ключевые компоненты

#### Payment Entity
```python
@dataclass
class Payment:
    id: str
    user_id: str
    amount: float
    currency: str = "RUB"
    status: str = "pending"  # pending, completed, failed, cancelled
    payment_method: str = "yookassa"
    created_at: datetime
    completed_at: Optional[datetime] = None
    external_payment_id: Optional[str] = None
    metadata: Dict[str, Any] = None
```

#### Subscription Entity
```python
@dataclass
class Subscription:
    id: str
    user_id: str
    plan_type: str  # free, basic, premium
    daily_limit: int
    used_today: int = 0
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = None
```

#### PaymentRepository Interface
```python
class PaymentRepository(ABC):
    @abstractmethod
    def save_payment(self, payment: Payment) -> str:
        pass
    
    @abstractmethod
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        pass
    
    @abstractmethod
    def save_subscription(self, subscription: Subscription) -> str:
        pass
    
    @abstractmethod
    def get_subscription(self, user_id: str) -> Optional[Subscription]:
        pass
    
    @abstractmethod
    def update_usage(self, user_id: str, usage_count: int = 1) -> bool:
        pass
```

## API Endpoints

### Health Check
```
GET /health
```
Возвращает статус сервиса и статистику платежей.

### Payment Management

#### Create Payment
```
POST /payment
Request Body:
{
    "user_id": "user123",
    "amount": 299.00,
    "currency": "RUB",
    "payment_method": "yookassa",
    "metadata": {
        "plan": "basic",
        "duration_days": 30
    }
}
```
Создает новый платеж.

#### Get Payment Status
```
GET /payment/{payment_id}
```
Возвращает статус и детали платежа.

#### Confirm Payment
```
POST /payment/{payment_id}/confirm
Request Body:
{
    "external_payment_id": "yk_123456789",
    "status": "completed"
}
```
Подтверждает успешный платеж.

### Subscription Management

#### Get User Subscription
```
GET /subscription/{user_id}
```
Возвращает информацию о подписке пользователя.

#### Create Subscription
```
POST /subscription
Request Body:
{
    "user_id": "user123",
    "plan_type": "basic",
    "daily_limit": 100,
    "duration_days": 30
}
```
Создает новую подписку.

#### Update Usage
```
POST /subscription/{user_id}/usage
Request Body:
{
    "usage_count": 1
}
```
Обновляет счетчик использованных запросов.

### Usage Limits

#### Check Usage Limit
```
GET /subscription/{user_id}/limit
```
Проверяет лимиты пользователя и возвращает информацию о доступности.

#### Reset Daily Usage
```
POST /subscription/{user_id}/reset
```
Сбрасывает дневной счетчик использованных запросов.

### Statistics

#### Payment Statistics
```
GET /statistics/payments
```
Возвращает статистику по платежам:
- Общее количество платежей
- Сумма всех платежей
- Количество успешных/неуспешных платежей
- Средний чек

#### Subscription Statistics
```
GET /statistics/subscriptions
```
Возвращает статистику по подпискам:
- Количество активных подписок
- Распределение по типам планов
- Среднее использование лимитов

## Конфигурация

### Environment Variables

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `PAYMENT_SERVICE_HOST` | Хост для привязки | `0.0.0.0` |
| `PAYMENT_SERVICE_PORT` | Порт для привязки | `8005` |
| `YOOKASSA_SHOP_ID` | ID магазина YooKassa | - |
| `YOOKASSA_SECRET_KEY` | Секретный ключ YooKassa | - |
| `FREE_DAILY_LIMIT` | Лимит для бесплатных пользователей | `20` |
| `BASIC_DAILY_LIMIT` | Лимит для базового плана | `100` |
| `PREMIUM_DAILY_LIMIT` | Лимит для премиум плана | `1000` |

### Docker Configuration

```yaml
payment:
  build:
    context: ../../services/payment
    dockerfile: Dockerfile
  environment:
    - PAYMENT_SERVICE_HOST=0.0.0.0
    - PAYMENT_SERVICE_PORT=8005
    - FREE_DAILY_LIMIT=20
    - BASIC_DAILY_LIMIT=100
    - PREMIUM_DAILY_LIMIT=1000
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
```

## Бизнес-логика

### Freemium Model

Сервис реализует freemium модель с тремя уровнями подписок:

#### Free Plan
- **Лимит**: 20 проверок в день
- **Стоимость**: Бесплатно
- **Ограничения**: Базовые функции

#### Basic Plan
- **Лимит**: 100 проверок в день
- **Стоимость**: 299 руб/месяц
- **Возможности**: Расширенная аналитика

#### Premium Plan
- **Лимит**: 1000 проверок в день
- **Стоимость**: 999 руб/месяц
- **Возможности**: Приоритетная поддержка, API доступ

### Usage Tracking

```python
class UsageTracker:
    def __init__(self):
        self.daily_usage = {}  # user_id -> usage_count
        self.last_reset = {}   # user_id -> last_reset_date
    
    def check_usage_limit(self, user_id: str) -> Dict[str, Any]:
        subscription = self.repository.get_subscription(user_id)
        if not subscription:
            # Создаем бесплатную подписку
            subscription = self._create_free_subscription(user_id)
        
        # Проверяем, нужно ли сбросить счетчик
        self._reset_daily_usage_if_needed(user_id)
        
        current_usage = subscription.used_today
        daily_limit = subscription.daily_limit
        
        return {
            "can_use": current_usage < daily_limit,
            "used_today": current_usage,
            "daily_limit": daily_limit,
            "remaining": daily_limit - current_usage,
            "plan_type": subscription.plan_type
        }
    
    def increment_usage(self, user_id: str) -> bool:
        subscription = self.repository.get_subscription(user_id)
        if not subscription:
            return False
        
        if subscription.used_today >= subscription.daily_limit:
            return False
        
        subscription.used_today += 1
        self.repository.save_subscription(subscription)
        return True
```

### Payment Processing

```python
class PaymentProcessor:
    def __init__(self, yookassa_client):
        self.yookassa_client = yookassa_client
    
    async def create_payment(self, user_id: str, amount: float, 
                           plan_type: str) -> Dict[str, Any]:
        # Создание платежа в YooKassa
        payment_data = {
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://app.example.com/payment/success"
            },
            "capture": True,
            "description": f"Подписка {plan_type}",
            "metadata": {
                "user_id": user_id,
                "plan_type": plan_type
            }
        }
        
        response = await self.yookassa_client.create_payment(payment_data)
        
        # Сохранение платежа в базе данных
        payment = Payment(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount=amount,
            status="pending",
            payment_method="yookassa",
            created_at=datetime.now(),
            external_payment_id=response["id"],
            metadata={"plan_type": plan_type}
        )
        
        payment_id = self.repository.save_payment(payment)
        
        return {
            "payment_id": payment_id,
            "external_payment_id": response["id"],
            "confirmation_url": response["confirmation"]["confirmation_url"]
        }
```

## Обработка ошибок

### Типы ошибок

1. **PaymentNotFoundError**: Платеж не найден
2. **SubscriptionNotFoundError**: Подписка не найдена
3. **UsageLimitExceededError**: Превышен дневной лимит
4. **PaymentFailedError**: Ошибка обработки платежа
5. **InvalidPlanError**: Неверный тип плана

### Обработка исключений

```python
async def process_payment(self, payment_id: str, external_payment_id: str) -> bool:
    try:
        payment = self.repository.get_payment(payment_id)
        if not payment:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")
        
        # Обновление статуса платежа
        payment.status = "completed"
        payment.completed_at = datetime.now()
        payment.external_payment_id = external_payment_id
        self.repository.save_payment(payment)
        
        # Создание или обновление подписки
        plan_type = payment.metadata.get("plan_type", "basic")
        subscription = self._create_or_update_subscription(
            payment.user_id, plan_type
        )
        
        return True
        
    except Exception as e:
        payment.status = "failed"
        self.repository.save_payment(payment)
        raise PaymentFailedError(f"Failed to process payment: {str(e)}")
```

## Мониторинг и метрики

### Health Check

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "payment",
        "total_payments": len(payment_service.get_all_payments()),
        "active_subscriptions": len(payment_service.get_active_subscriptions()),
        "total_revenue": payment_service.get_total_revenue()
    }
```

### Метрики бизнеса

- Общая выручка
- Конверсия в платные планы
- Средний чек
- Churn rate (отток пользователей)
- ARPU (Average Revenue Per User)

## Безопасность

### Валидация входных данных

```python
class PaymentRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0, le=10000)
    currency: str = Field(default="RUB", regex=r"^[A-Z]{3}$")
    payment_method: str = Field(default="yookassa")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SubscriptionRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    plan_type: str = Field(regex=r"^(free|basic|premium)$")
    daily_limit: int = Field(ge=1, le=10000)
    duration_days: int = Field(ge=1, le=365)
```

### Аутентификация и авторизация

```python
def verify_user_access(self, user_id: str, resource_user_id: str) -> bool:
    # Проверка доступа пользователя к ресурсу
    return user_id == resource_user_id or self.is_admin(user_id)
```

## Разработка и тестирование

### Локальная разработка

```bash
# Запуск сервиса
cd services/payment
python api/main.py

# Тестирование API
curl -X POST http://localhost:8005/payment \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "amount": 299.00, "plan_type": "basic"}'
```

### Unit тесты

```python
def test_payment_creation():
    repository = InMemoryRepository()
    payment = Payment(
        id="test-1",
        user_id="test_user",
        amount=299.00,
        status="pending",
        created_at=datetime.now()
    )
    payment_id = repository.save_payment(payment)
    assert payment_id == "test-1"

def test_usage_limit_check():
    tracker = UsageTracker()
    result = tracker.check_usage_limit("test_user")
    assert result["can_use"] == True
    assert result["daily_limit"] == 20
```

### Integration тесты

```python
def test_payment_flow():
    # Создание платежа
    response = client.post("/payment", json={
        "user_id": "test_user",
        "amount": 299.00,
        "plan_type": "basic"
    })
    assert response.status_code == 200
    payment_id = response.json()["payment_id"]
    
    # Подтверждение платежа
    response = client.post(f"/payment/{payment_id}/confirm", json={
        "external_payment_id": "test_external_id",
        "status": "completed"
    })
    assert response.status_code == 200
    
    # Проверка подписки
    response = client.get("/subscription/test_user")
    assert response.status_code == 200
    assert response.json()["plan_type"] == "basic"
```

## Масштабирование

### Горизонтальное масштабирование

- Множественные инстансы Payment Service
- Общая база данных для платежей
- Синхронизация состояния подписок

### Вертикальное масштабирование

- Увеличение производительности обработки платежей
- Оптимизация запросов к базе данных
- Кэширование часто используемых данных

## Интеграция с другими сервисами

### API Gateway
- Проверка лимитов пользователей
- Валидация подписок перед обработкой запросов

### Request Processor
- Обновление счетчиков использования
- Проверка доступности сервисов

### External Payment Systems
- YooKassa для обработки платежей
- Webhook обработка уведомлений

## Планы развития

### Краткосрочные цели
- Интеграция с дополнительными платежными системами
- Реализация промокодов и скидок
- Улучшение аналитики платежей

### Долгосрочные цели
- Реализация рекуррентных платежей
- Интеграция с системами аналитики
- Добавление поддержки корпоративных планов
