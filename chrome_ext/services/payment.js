class PaymentService {
  constructor() {
    this.yookassaShopId = 'your_shop_id'; // Замените на ваш Shop ID
    this.yookassaSecretKey = 'your_secret_key'; // Замените на ваш Secret Key
    this.paymentUrl = 'https://api.yookassa.ru/v3/payments';
    this.premiumPrice = 299; // 299 рублей в месяц
  }

  // Создать платеж в ЮKassa
  async createPayment() {
    try {
      const paymentData = {
        amount: {
          value: this.premiumPrice.toString(),
          currency: 'RUB'
        },
        capture: true,
        confirmation: {
          type: 'redirect',
          return_url: 'https://extremist-checker.com/success'
        },
        description: 'Премиум подписка "Глаз Закона" на 1 месяц',
        metadata: {
          extension_id: chrome.runtime.id,
          user_id: await this.getUserId()
        }
      };

      const response = await fetch(this.paymentUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotence-Key': this.generateIdempotenceKey(),
          'Authorization': `Basic ${btoa(this.yookassaShopId + ':' + this.yookassaSecretKey)}`
        },
        body: JSON.stringify(paymentData)
      });

      if (!response.ok) {
        throw new Error(`Payment creation failed: ${response.status}`);
      }

      const payment = await response.json();
      return payment;
    } catch (error) {
      console.error('Ошибка создания платежа:', error);
      throw error;
    }
  }

  // Проверить статус платежа
  async checkPaymentStatus(paymentId) {
    try {
      const response = await fetch(`${this.paymentUrl}/${paymentId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Basic ${btoa(this.yookassaShopId + ':' + this.yookassaSecretKey)}`
        }
      });

      if (!response.ok) {
        throw new Error(`Payment status check failed: ${response.status}`);
      }

      const payment = await response.json();
      return payment.status;
    } catch (error) {
      console.error('Ошибка проверки статуса платежа:', error);
      throw error;
    }
  }

  // Обработать успешный платеж
  async handleSuccessfulPayment(paymentId) {
    try {
      const status = await this.checkPaymentStatus(paymentId);
      
      if (status === 'succeeded') {
        // Устанавливаем премиум статус
        const limitsService = new LimitsService();
        await limitsService.setPremiumStatus(true);
        
        // Сохраняем информацию о подписке
        await this.saveSubscriptionInfo(paymentId);
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Ошибка обработки платежа:', error);
      return false;
    }
  }

  // Сохранить информацию о подписке
  async saveSubscriptionInfo(paymentId) {
    const subscriptionInfo = {
      paymentId: paymentId,
      startDate: new Date().toISOString(),
      endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // +30 дней
      status: 'active'
    };

    return new Promise((resolve) => {
      chrome.storage.local.set({ 
        'extremist_checker_subscription': subscriptionInfo 
      }, () => {
        resolve();
      });
    });
  }

  // Проверить активность подписки
  async checkSubscriptionStatus() {
    return new Promise((resolve) => {
      chrome.storage.local.get(['extremist_checker_subscription'], (result) => {
        const subscription = result.extremist_checker_subscription;
        
        if (!subscription) {
          resolve({ active: false, daysLeft: 0 });
          return;
        }

        const endDate = new Date(subscription.endDate);
        const now = new Date();
        const daysLeft = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
        
        resolve({
          active: daysLeft > 0,
          daysLeft: Math.max(0, daysLeft),
          subscription: subscription
        });
      });
    });
  }

  // Получить уникальный ID пользователя
  async getUserId() {
    return new Promise((resolve) => {
      chrome.storage.local.get(['extremist_checker_user_id'], (result) => {
        let userId = result.extremist_checker_user_id;
        
        if (!userId) {
          userId = this.generateUserId();
          chrome.storage.local.set({ 'extremist_checker_user_id': userId });
        }
        
        resolve(userId);
      });
    });
  }

  // Генерировать уникальный ID пользователя
  generateUserId() {
    return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Генерировать ключ идемпотентности
  generateIdempotenceKey() {
    return 'payment_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Получить информацию о ценах
  getPricingInfo() {
    return {
      monthly: {
        price: this.premiumPrice,
        currency: 'RUB',
        period: 'месяц',
        features: [
          'Неограниченное количество проверок',
          'Приоритетная поддержка',
          'Без рекламы'
        ]
      }
    };
  }
}

// Экспортируем для использования в других файлах
window.PaymentService = PaymentService; 