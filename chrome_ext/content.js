class ExtremistContentChecker {
  constructor() {
    this.apiUrl = 'https://api.extremist-checker.com/check';
    this.isChecking = false;
    this.lastQuery = '';
    this.resultContainer = null;
    this.checkButton = null;
    
    this.init();
  }

  init() {
    console.log('Инициализация ExtremistContentChecker');
    // Ждем, пока страница полностью загрузится
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

  createResultContainer() {
    this.resultContainer = document.createElement('div');
    this.resultContainer.className = 'extremist-check-result';
    this.resultContainer.style.display = 'none';
  }

  insertElements() {
    console.log('Попытка вставки элементов для поисковика:', this.searchEngine);
    
    const insertionElement = document.querySelector(this.insertionPoint);
    console.log('Найден элемент вставки:', insertionElement);
    
    if (insertionElement) {
      const container = document.createElement('div');
      container.className = `extremist-check-container-${this.searchEngine}`;
      
      container.appendChild(this.checkButton);
      container.appendChild(this.resultContainer);
      
      // Вставляем перед результатами поиска
      if (this.searchEngine === 'google') {
        const searchDiv = document.querySelector('#search');
        console.log('Google search div:', searchDiv);
        if (searchDiv) {
          searchDiv.insertBefore(container, searchDiv.firstChild);
          console.log('Кнопка вставлена в Google');
        }
      } else if (this.searchEngine === 'yandex') {
        const contentLeft = document.querySelector('.content__left');
        console.log('Yandex content left:', contentLeft);
        if (contentLeft) {
          contentLeft.insertBefore(container, contentLeft.firstChild);
          console.log('Кнопка вставлена в Yandex');
        }
      } else if (this.searchEngine === 'bing') {
        const bingResults = document.querySelector('#b_results');
        console.log('Bing results:', bingResults);
        if (bingResults) {
          bingResults.insertBefore(container, bingResults.firstChild);
          console.log('Кнопка вставлена в Bing');
        }
      } else if (this.searchEngine === 'duckduckgo') {
        const ddgResults = document.querySelector('#links');
        console.log('DuckDuckGo results:', ddgResults);
        if (ddgResults) {
          ddgResults.insertBefore(container, ddgResults.firstChild);
          console.log('Кнопка вставлена в DuckDuckGo');
        }
      } else {
        insertionElement.insertBefore(container, insertionElement.firstChild);
        console.log('Кнопка вставлена в общий элемент');
      }
    } else {
      console.log('Элемент вставки не найден для:', this.insertionPoint);
    }
  }

  attachEventListeners() {
    // Отслеживаем изменения в поисковой строке
    const searchInput = document.querySelector(this.searchInputSelector);
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        this.hideResult();
      });
    }

    // Отслеживаем изменения в DOM для динамически загружаемого контента
    const observer = new MutationObserver(() => {
      if (!document.querySelector('.extremist-check-button')) {
        this.insertElements();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Вставляем элементы при первом запуске с несколькими попытками
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

    // Проверяем лимиты (временно отключено для тестирования)
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
      
      // Увеличиваем счетчик использованных запросов (временно отключено)
      // await this.limitsService.incrementUsage();

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
    
    // Определяем тип результата на основе ответа
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

  // Показать промпт для апгрейда
  showUpgradePrompt() {
    this.showResult(
      'Достигнут дневной лимит бесплатных проверок (20).\n\n' +
      '💎 Откройте расширение для перехода на Премиум с неограниченными проверками!',
      'warning'
    );
  }
}

// Инициализируем расширение
new ExtremistContentChecker();

// Инициализируем расширение
new ExtremistContentChecker();