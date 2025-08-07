class ExtremistCheckerPopup {
  constructor() {
    this.apiUrl = 'http://localhost:8000/check';
    this.isChecking = false;
    
    this.queryInput = document.getElementById('query');
    this.checkButton = document.getElementById('checkBtn');
    this.resultDiv = document.getElementById('result');
    this.usageText = document.getElementById('usageText');
    this.usageFill = document.getElementById('usageFill');
    this.upgradeBtn = document.getElementById('upgradeBtn');
    this.premiumBtn = document.getElementById('premiumBtn');

    this.limitsService = new LimitsService();
    this.paymentService = new PaymentService();
    
    this.init();
  }

  init() {
    this.loadSavedQuery();
    this.loadLimitsInfo();
    this.checkButton.addEventListener('click', () => this.checkContent());
    this.upgradeBtn.addEventListener('click', () => this.showUpgradeModal());
    this.premiumBtn.addEventListener('click', () => this.showUpgradeModal());
    this.queryInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) {
        this.checkContent();
      }
    });
    this.queryInput.focus();
  }

  loadSavedQuery() {
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      chrome.scripting.executeScript({
        target: {tabId: tabs[0].id},
        function: () => {
          const searchInputs = [
            'input[name="q"]', 
            'input[name="text"]', 
            'input[type="search"]'
          ];
          
          for (const selector of searchInputs) {
            const input = document.querySelector(selector);
            if (input && input.value.trim()) {
              return input.value.trim();
            }
          }
          
          return '';
        }
      }, (results) => {
        if (results && results[0] && results[0].result) {
          this.queryInput.value = results[0].result;
        }
      });
    });
    chrome.storage.session.get('query', (data) => {
      if (data.query && !this.queryInput.value) {
        this.queryInput.value = data.query;
      }
    });
  }

  async checkContent() {
    const query = this.queryInput.value.trim();
    
    if (!query) {
      this.showResult('Введите текст для проверки', 'warning');
      return;
    }

    if (this.isChecking) {
      return;
    }
    const canMakeRequest = await this.limitsService.canMakeRequest();
    if (!canMakeRequest) {
      this.showUpgradePrompt();
      return;
    }

    this.isChecking = true;
    chrome.storage.session.set({ query: query });
    this.checkButton.disabled = true;
    this.checkButton.innerHTML = '<div class="loading-spinner"></div>Проверяем...';
    
    this.showResult('Проверяем материал в реестре экстремистских материалов Минюста РФ...', 'loading');

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.displayResult(data);

      await this.limitsService.incrementUsage();
      await this.loadLimitsInfo();

    } catch (error) {
      console.error('Ошибка при проверке:', error);
      
      let errorMessage = 'Ошибка подключения к сервису проверки.\n\n';
      
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMessage += 'Возможные причины:\n';
        errorMessage += '• Проблемы с интернет-соединением\n';
        errorMessage += '• Сервис временно недоступен\n';
        errorMessage += '• Блокировка со стороны провайдера\n\n';
        errorMessage += 'Попробуйте позже или обратитесь в поддержку.';
      } else if (error.message.includes('429')) {
        errorMessage += 'Превышен лимит запросов. Попробуйте через несколько минут.';
      } else if (error.message.includes('500')) {
        errorMessage += 'Внутренняя ошибка сервера. Попробуйте позже.';
      } else {
        errorMessage += `Детали ошибки: ${error.message}`;
      }
      
      this.showResult(errorMessage, 'danger');
    } finally {
      this.isChecking = false;
      this.checkButton.disabled = false;
      this.checkButton.innerHTML = '🔍 Проверить';
    }
  }

  displayResult(data) {
    const result = data.result;
    let resultClass = 'safe';
    let icon = '✅';
    if (result.toLowerCase().includes('запрещен') || 
        result.toLowerCase().includes('экстремист') ||
        result.toLowerCase().includes('внесен в реестр') ||
        result.toLowerCase().includes('признан экстремистским')) {
      resultClass = 'danger';
      icon = '🚫';
    } else if (result.toLowerCase().includes('не найден') || 
               result.toLowerCase().includes('разрешен') ||
               result.toLowerCase().includes('не является экстремистским')) {
      resultClass = 'safe';
      icon = '✅';
    } else {
      resultClass = 'warning';
      icon = '⚠️';
    }

    let message = `${icon} ${result}`;
    
    if (resultClass === 'danger' && data.material_name) {
      message += `\n\n📄 Материал: ${data.material_name}`;
    }
    
    if (data.court_date) {
      message += `\n📅 Дата: ${data.court_date}`;
    }
    
    if (data.court_name) {
      message += `\n⚖️ Суд: ${data.court_name}`;
    }
    
    if (data.extremist_reason) {
      message += `\n🔍 Причина: ${data.extremist_reason}`;
    }
    
    if (data.processing_time) {
      message += `\n\n⏱️ Время обработки: ${data.processing_time.toFixed(2)} сек.`;
    }

    if (data.confidence) {
      message += `\n🎯 Уверенность: ${(data.confidence * 100).toFixed(1)}%`;
    }

    this.showResult(message, resultClass);
  }

  showResult(message, type) {
    this.resultDiv.textContent = message;
    this.resultDiv.className = type;
  }

  async loadLimitsInfo() {
    try {
      const stats = await this.limitsService.getUsageStats();
      const subscription = await this.paymentService.checkSubscriptionStatus();
      
      if (stats.isPremium || subscription.active) {
        this.usageText.innerHTML = `
          <span class="premium-badge">💎 Премиум</span>
          ${subscription.active ? `(${subscription.daysLeft} дн.)` : ''}
        `;
        this.upgradeBtn.style.display = 'none';
        this.usageFill.style.width = '100%';
        this.usageFill.className = 'usage-fill';
      } else {
        const percentage = stats.percentageUsed;
        this.usageText.textContent = `${stats.usedToday}/${stats.dailyLimit} проверок`;
        this.usageFill.style.width = `${percentage}%`;
        this.usageFill.className = 'usage-fill';
        if (percentage > 80) {
          this.usageFill.classList.add('danger');
        } else if (percentage > 60) {
          this.usageFill.classList.add('warning');
        }
        if (percentage > 50) {
          this.upgradeBtn.style.display = 'inline-block';
        } else {
          this.upgradeBtn.style.display = 'none';
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки лимитов:', error);
      this.usageText.textContent = 'Ошибка загрузки';
    }
  }
  showUpgradePrompt() {
    this.showResult(
      'Достигнут дневной лимит бесплатных проверок (20).\n\n' +
      '💎 Перейдите на Премиум для неограниченного количества проверок и приоритетной поддержки!',
      'warning'
    );
    this.upgradeBtn.style.display = 'inline-block';
  }
  showUpgradeModal() {
    const pricing = this.paymentService.getPricingInfo();
    const modal = document.createElement('div');
    modal.className = 'upgrade-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h2>💎 Премиум подписка</h2>
          <button class="close-btn" onclick="this.parentElement.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="modal-body">
          <div class="pricing-card">
            <h3>${pricing.monthly.price} ₽/месяц</h3>
            <ul>
              ${pricing.monthly.features.map(feature => `<li>✅ ${feature}</li>`).join('')}
            </ul>
            <button class="upgrade-btn-large" onclick="this.parentElement.parentElement.parentElement.remove(); window.extremistChecker.startPayment()">
              💳 Оплатить ${pricing.monthly.price} ₽
            </button>
          </div>
        </div>
      </div>
    `;
    const style = document.createElement('style');
    style.textContent = `
      .upgrade-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
      }
      .modal-content {
        background: white;
        border-radius: 12px;
        padding: 20px;
        max-width: 400px;
        width: 90%;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      }
      .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
      }
      .close-btn {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #666;
      }
      .pricing-card {
        text-align: center;
      }
      .pricing-card h3 {
        color: #333;
        margin-bottom: 15px;
      }
      .pricing-card ul {
        text-align: left;
        margin: 15px 0;
        padding-left: 20px;
      }
      .upgrade-btn-large {
        background: linear-gradient(135deg, #ffd700, #ffed4e);
        color: #333;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
      }
      .upgrade-btn-large:hover {
        background: linear-gradient(135deg, #ffed4e, #ffd700);
        transform: translateY(-1px);
      }
    `;
    document.head.appendChild(style);
    document.body.appendChild(modal);
  }
  async startPayment() {
    try {
      this.showResult('Создание платежа...', 'loading');
      
      const payment = await this.paymentService.createPayment();
      
      window.open(payment.confirmation.confirmation_url, '_blank');
      
      this.showResult(
        'Платеж создан! Откройте вкладку с оплатой и завершите платеж.\n\n' +
        'После успешной оплаты премиум статус будет активирован автоматически.',
        'safe'
      );
      
    } catch (error) {
      console.error('Ошибка создания платежа:', error);
      this.showResult(
        'Ошибка создания платежа. Попробуйте позже или обратитесь в поддержку.',
        'danger'
      );
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.extremistChecker = new ExtremistCheckerPopup();
});

document.addEventListener('DOMContentLoaded', () => {
  new ExtremistCheckerPopup();
});