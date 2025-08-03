class ExtremistCheckerPopup {
  constructor() {
    this.apiUrl = 'http://localhost:8000/check';
    this.isChecking = false;
    
    this.queryInput = document.getElementById('query');
    this.checkButton = document.getElementById('checkBtn');
    this.resultDiv = document.getElementById('result');
    
    this.init();
  }

  init() {
    // Загружаем сохранённый запрос из поисковой строки
    this.loadSavedQuery();
    
    // Добавляем обработчики событий
    this.checkButton.addEventListener('click', () => this.checkContent());
    
    // Проверяем при нажатии Enter в текстовом поле
    this.queryInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) {
        this.checkContent();
      }
    });

    // Автофокус на поле ввода
    this.queryInput.focus();
  }

  loadSavedQuery() {
    // Пытаемся получить текущий запрос с активной вкладки
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      chrome.scripting.executeScript({
        target: {tabId: tabs[0].id},
        function: () => {
          // Попытка извлечь поисковый запрос с текущей страницы
          const searchInputs = [
            'input[name="q"]',  // Google, Bing, DuckDuckGo
            'input[name="text"]', // Yandex
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

    // Также проверяем сохранённый запрос в хранилище
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

    this.isChecking = true;
    
    // Сохраняем запрос
    chrome.storage.session.set({ query: query });
    
    // Обновляем UI
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

    } catch (error) {
      console.error('Ошибка при проверке:', error);
      
      let errorMessage = 'Ошибка подключения к сервису проверки.\n\n';
      
      if (error.message.includes('Failed to fetch')) {
        errorMessage += 'Убедитесь, что:\n';
        errorMessage += '• Сервер запущен на localhost:8000\n';
        errorMessage += '• Нет блокировки CORS\n';
        errorMessage += '• Интернет соединение работает';
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
    
    // Определяем тип результата на основе ответа
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
}

// Инициализируем popup при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  new ExtremistCheckerPopup();
});