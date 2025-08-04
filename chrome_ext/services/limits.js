class LimitsService {
  constructor() {
    this.dailyLimit = 20;
    this.storageKey = 'extremist_checker_limits';
    this.premiumKey = 'extremist_checker_premium';
  }

  // Получить текущие лимиты
  async getLimits() {
    return new Promise((resolve) => {
      chrome.storage.local.get([this.storageKey, this.premiumKey], (result) => {
        const limits = result[this.storageKey] || this.getDefaultLimits();
        const isPremium = result[this.premiumKey] || false;
        
        // Проверяем, нужно ли сбросить счетчик (новый день)
        if (this.isNewDay(limits.lastReset)) {
          limits.usedToday = 0;
          limits.lastReset = new Date().toDateString();
          this.saveLimits(limits);
        }
        
        resolve({
          usedToday: limits.usedToday,
          dailyLimit: this.dailyLimit,
          isPremium: isPremium,
          remaining: this.dailyLimit - limits.usedToday
        });
      });
    });
  }

  // Проверить, можно ли сделать запрос
  async canMakeRequest() {
    const limits = await this.getLimits();
    return limits.isPremium || limits.remaining > 0;
  }

  // Увеличить счетчик использованных запросов
  async incrementUsage() {
    const limits = await this.getLimits();
    if (!limits.isPremium) {
      limits.usedToday += 1;
      await this.saveLimits(limits);
    }
  }

  // Установить премиум статус
  async setPremiumStatus(isPremium) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [this.premiumKey]: isPremium }, () => {
        resolve();
      });
    });
  }

  // Получить дефолтные лимиты
  getDefaultLimits() {
    return {
      usedToday: 0,
      lastReset: new Date().toDateString()
    };
  }

  // Проверить, новый ли это день
  isNewDay(lastReset) {
    if (!lastReset) return true;
    const today = new Date().toDateString();
    return lastReset !== today;
  }

  // Сохранить лимиты
  async saveLimits(limits) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [this.storageKey]: limits }, () => {
        resolve();
      });
    });
  }

  // Получить статистику использования
  async getUsageStats() {
    const limits = await this.getLimits();
    return {
      usedToday: limits.usedToday,
      dailyLimit: this.dailyLimit,
      remaining: limits.remaining,
      isPremium: limits.isPremium,
      percentageUsed: Math.round((limits.usedToday / this.dailyLimit) * 100)
    };
  }

  // Сбросить лимиты (для тестирования)
  async resetLimits() {
    const defaultLimits = this.getDefaultLimits();
    await this.saveLimits(defaultLimits);
  }
}

// Экспортируем для использования в других файлах
window.LimitsService = LimitsService; 