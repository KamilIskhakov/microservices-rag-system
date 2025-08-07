class ExtremistContentChecker {
  constructor() {
    this.apiUrl = 'http://localhost:8000/check';
    this.isChecking = false;
    this.lastQuery = '';
    this.resultContainer = null;
    this.checkButton = null;
    
    this.init();
  }

  init() {
    console.log('Инициализация ExtremistContentChecker');
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setupInterface());
    } else {
      this.setupInterface();
    }
  }

  setupInterface() {
    console.log('Настройка интерфейса');
    this.detectSearchEngine();
    this.createCheckButton();
    this.createPreSearchButton();
    this.createPremiumButton();
    this.createResultContainer();
    this.attachEventListeners();
  }

  detectSearchEngine() {
    const hostname = window.location.hostname;
    console.log('Определение поисковика для:', hostname);
    
    if (hostname.includes('google.com')) {
      this.searchEngine = 'google';
      this.searchInputSelector = 'input[name="q"]';
      this.searchFormSelector = 'form[role="search"]';
      this.insertionPoint = '#search';
      console.log('Определен Google');
    } else if (hostname.includes('yandex.ru')) {
      this.searchEngine = 'yandex';
      this.searchInputSelector = 'input[name="text"]';
      this.searchFormSelector = '.search2__form';
      this.insertionPoint = '.content__left';
      console.log('Определен Yandex');
    } else if (hostname.includes('bing.com')) {
      this.searchEngine = 'bing';
      this.searchInputSelector = 'input[name="q"]';
      this.searchFormSelector = '#sb_form';
      this.insertionPoint = '#b_results';
      console.log('Определен Bing');
    } else if (hostname.includes('duckduckgo.com')) {
      this.searchEngine = 'duckduckgo';
      this.searchInputSelector = 'input[name="q"]';
      this.searchFormSelector = '#search_form';
      this.insertionPoint = '#links';
      console.log('Определен DuckDuckGo');
    } else {
      console.log('Поисковик не определен, используем общие селекторы');
      this.searchEngine = 'unknown';
      this.searchInputSelector = 'input[type="search"], input[name="q"], input[name="text"]';
      this.insertionPoint = 'body';
    }
  }

  getSearchQuery() {
    const input = document.querySelector(this.searchInputSelector);
    return input ? input.value.trim() : '';
  }

  createCheckButton() {
    this.checkButton = document.createElement('button');
    this.checkButton.className = 'extremist-check-button';
    this.checkButton.innerHTML = `
      <svg class="shield-icon" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M12,7C13.4,7 14.8,8.6 14.8,10V11.5C15.4,11.5 16,12.1 16,12.7V16.2C16,16.8 15.4,17.3 14.8,17.3H9.2C8.6,17.3 8,16.8 8,16.2V12.8C8,12.2 8.6,11.7 9.2,11.7V10C9.2,8.6 10.6,7 12,7M12,8.2C11.2,8.2 10.5,8.7 10.5,9.5V11.5H13.5V9.5C13.5,8.7 12.8,8.2 12,8.2Z"/>
      </svg>
      Проверить на экстремизм
    `;
    
    this.checkButton.addEventListener('click', () => this.checkContent());
  }

  createPreSearchButton() {
    this.preSearchButton = document.createElement('button');
    this.preSearchButton.className = 'extremist-pre-search-button';
    this.preSearchButton.innerHTML = `
      <svg class="shield-icon" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M12,7C13.4,7 14.8,8.6 14.8,10V11.5C15.4,11.5 16,12.1 16,12.7V16.2C16,16.8 15.4,17.3 14.8,17.3H9.2C8.6,17.3 8,16.8 8,16.2V12.8C8,12.2 8.6,11.7 9.2,11.7V10C9.2,8.6 10.6,7 12,7M12,8.2C11.2,8.2 10.5,8.7 10.5,9.5V11.5H13.5V9.5C13.5,8.7 12.8,8.2 12,8.2Z"/>
      </svg>
      Проверить ДО поиска
    `;
    
    this.preSearchButton.addEventListener('click', () => this.checkPreSearch());
  }

  createPremiumButton() {
    this.premiumButton = document.createElement('button');
    this.premiumButton.className = 'extremist-premium-button';
    this.premiumButton.innerHTML = `
      💎 Премиум
    `;
    
    this.premiumButton.addEventListener('click', () => this.showPremiumModal());
  }

  createResultContainer() {
    this.resultContainer = document.createElement('div');
    this.resultContainer.className = 'extremist-check-result';
    this.resultContainer.style.display = 'none';
  }

  insertElements() {
    console.log('Попытка вставки элементов для поисковика:', this.searchEngine);

    if (document.querySelector('.extremist-check-button')) {
      console.log('Кнопки уже существуют, пропускаем вставку');
      return;
    }
    
    this.insertPreSearchButton();
    this.insertPremiumButton();
    this.insertMainButton();
  }

  insertPreSearchButton() {
    const searchInput = document.querySelector(this.searchInputSelector);
    if (searchInput) {
      const searchForm = searchInput.closest('form');
      if (searchForm) {
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'extremist-pre-search-container';
        buttonContainer.appendChild(this.preSearchButton);
        buttonContainer.appendChild(this.premiumButton);
        
        // Вставляем после поисковой строки
        searchForm.appendChild(buttonContainer);
        console.log('Кнопки ДО поиска вставлены');
      }
    }
  }

  insertPremiumButton() {
  }

  insertMainButton() {
    const insertionElement = document.querySelector(this.insertionPoint);
    console.log('Найден элемент вставки:', insertionElement);
    
    if (insertionElement) {
      const container = document.createElement('div');
      container.className = `extremist-check-container-${this.searchEngine}`;
      
      container.appendChild(this.checkButton);
      container.appendChild(this.resultContainer);
      if (this.searchEngine === 'google') {
        const searchDiv = document.querySelector('#search');
        console.log('Google search div:', searchDiv);
        if (searchDiv) {
          searchDiv.insertBefore(container, searchDiv.firstChild);
          console.log('Основная кнопка вставлена в Google');
        }
      } else if (this.searchEngine === 'yandex') {
        const contentLeft = document.querySelector('.content__left');
        console.log('Yandex content left:', contentLeft);
        if (contentLeft) {
          contentLeft.insertBefore(container, contentLeft.firstChild);
          console.log('Основная кнопка вставлена в Yandex');
        }
      } else if (this.searchEngine === 'bing') {
        const bingResults = document.querySelector('#b_results');
        console.log('Bing results:', bingResults);
        if (bingResults) {
          bingResults.insertBefore(container, bingResults.firstChild);
          console.log('Основная кнопка вставлена в Bing');
        }
      } else if (this.searchEngine === 'duckduckgo') {
        const ddgResults = document.querySelector('#links');
        console.log('DuckDuckGo results:', ddgResults);
        if (ddgResults) {
          ddgResults.insertBefore(container, ddgResults.firstChild);
          console.log('Основная кнопка вставлена в DuckDuckGo');
        }
      } else {
        insertionElement.insertBefore(container, insertionElement.firstChild);
        console.log('Основная кнопка вставлена в общий элемент');
      }
    } else {
      console.log('Элемент вставки не найден для:', this.insertionPoint);
    }
  }

  attachEventListeners() {
    const searchInput = document.querySelector(this.searchInputSelector);
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        this.hideResult();
      });
    }

    const observer = new MutationObserver(() => {
      if (!document.querySelector('.extremist-check-button')) {
        this.insertElements();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    setTimeout(() => this.insertElements(), 500);
    setTimeout(() => this.insertElements(), 1500);
    setTimeout(() => this.insertElements(), 3000);
  }

  async checkContent() {
    const query = this.getSearchQuery();
    
    if (!query) {
      this.showResult('Введите поисковый запрос для проверки', 'warning');
      return;
    }

    if (this.isChecking) {
      return;
    }

    // Проверяем лимиты 
    // const canMakeRequest = await this.limitsService.canMakeRequest();
    // if (!canMakeRequest) {
    //   this.showUpgradePrompt();
    //   return;
    // }

    this.isChecking = true;
    this.lastQuery = query;
    
    this.checkButton.disabled = true;
    this.checkButton.innerHTML = `
      <div class="loading-spinner"></div>
      Проверяем...
    `;

    this.showResult('Проверяем материал в реестре экстремистских материалов...', 'loading');

    try {
      console.log('Отправляем запрос к API:', this.apiUrl);
      console.log('Данные запроса:', { query: query });
      
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query })
      });
      
      console.log('Получен ответ:', response.status, response.statusText);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.displayResult(data);

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
      this.checkButton.innerHTML = `
        <svg class="shield-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M12,7C13.4,7 14.8,8.6 14.8,10V11.5C15.4,11.5 16,12.1 16,12.7V16.2C16,16.8 15.4,17.3 14.8,17.3H9.2C8.6,17.3 8,16.8 8,16.2V12.8C8,12.2 8.6,11.7 9.2,11.7V10C9.2,8.6 10.6,7 12,7M12,8.2C11.2,8.2 10.5,8.7 10.5,9.5V11.5H13.5V9.5C13.5,8.7 12.8,8.2 12,8.2Z"/>
        </svg>
        Проверить на экстремизм
      `;
    }
  }

  displayResult(data) {
    const result = data.result;
    let resultClass = 'safe';
    if (result.toLowerCase().includes('запрещен') || 
        result.toLowerCase().includes('экстремист') ||
        result.toLowerCase().includes('внесен в реестр')) {
      resultClass = 'danger';
    } else if (result.toLowerCase().includes('не найден') || 
               result.toLowerCase().includes('разрешен')) {
      resultClass = 'safe';
    } else {
      resultClass = 'warning';
    }

    const processingTime = data.processing_time ? 
      `<div style="font-size: 12px; color: #666; margin-top: 8px;">
        Время обработки: ${data.processing_time.toFixed(2)}с
      </div>` : '';

    this.showResult(result + processingTime, resultClass);
  }

  showResult(message, type) {
    this.resultContainer.innerHTML = message;
    this.resultContainer.className = `extremist-check-result ${type}`;
    this.resultContainer.style.display = 'block';
  }

  hideResult() {
    this.resultContainer.style.display = 'none';
  }

  showUpgradePrompt() {
    this.showResult(
      'Достигнут дневной лимит бесплатных проверок (20).\n\n' +
      '💎 Откройте расширение для перехода на Премиум с неограниченными проверками!',
      'warning'
    );
  }

  checkPreSearch() {
    const searchInput = document.querySelector(this.searchInputSelector);
    if (searchInput) {
      const query = searchInput.value.trim();
      if (query) {
        this.checkContent();
      } else {
        this.showResult('Введите текст в поисковую строку для проверки', 'warning');
      }
    } else {
      this.showResult('Поисковая строка не найдена', 'warning');
    }
  }

  showPremiumModal() {
    const modal = document.createElement('div');
    modal.className = 'extremist-premium-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h2>💎 Премиум подписка</h2>
          <button class="close-btn" onclick="this.parentElement.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="modal-body">
          <div class="pricing-card">
            <h3>299 ₽/месяц</h3>
            <ul>
              <li>✅ Неограниченное количество проверок</li>
              <li>✅ Приоритетная поддержка</li>
              <li>✅ Без рекламы</li>
            </ul>
            <button class="upgrade-btn-large" onclick="this.parentElement.parentElement.parentElement.remove(); window.open('https://extremist-checker.com/premium', '_blank')">
              💳 Купить премиум
            </button>
          </div>
        </div>
      </div>
    `;

    const style = document.createElement('style');
    style.textContent = `
      .extremist-premium-modal {
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
}

new ExtremistContentChecker();

new ExtremistContentChecker();