class LimitsService {
  constructor() {
    this.dailyLimit = 20;
    this.storageKey = 'extremist_checker_limits';
    this.premiumKey = 'extremist_checker_premium';
  }

  async getLimits() {
    return new Promise((resolve) => {
      chrome.storage.local.get([this.storageKey, this.premiumKey], (result) => {
        const limits = result[this.storageKey] || this.getDefaultLimits();
        const isPremium = result[this.premiumKey] || false;
        
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

  async canMakeRequest() {
    const limits = await this.getLimits();
    return limits.isPremium || limits.remaining > 0;
  }

  async incrementUsage() {
    const limits = await this.getLimits();
    if (!limits.isPremium) {
      limits.usedToday += 1;
      await this.saveLimits(limits);
    }
  }

  async setPremiumStatus(isPremium) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [this.premiumKey]: isPremium }, () => {
        resolve();
      });
    });
  }

  getDefaultLimits() {
    return {
      usedToday: 0,
      lastReset: new Date().toDateString()
    };
  }

  isNewDay(lastReset) {
    if (!lastReset) return true;
    const today = new Date().toDateString();
    return lastReset !== today;
  }

  async saveLimits(limits) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [this.storageKey]: limits }, () => {
        resolve();
      });
    });
  }

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

  async resetLimits() {
    const defaultLimits = this.getDefaultLimits();
    await this.saveLimits(defaultLimits);
  }
}

window.LimitsService = LimitsService; 