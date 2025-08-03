// Background script для Extremist Content Checker

chrome.runtime.onInstalled.addListener(() => {
  console.log('Extremist Content Checker установлен');
});

// Обработка сообщений от content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'saveQuery') {
    chrome.storage.session.set({ query: request.query });
  }
  
  if (request.action === 'getQuery') {
    chrome.storage.session.get('query', (data) => {
      sendResponse({ query: data.query || '' });
    });
    return true; // Указывает, что ответ будет асинхронным
  }
});

// Обновление значка расширения при навигации
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete') {
    // Проверяем, является ли текущая страница поисковиком
    const searchEngines = ['google.com', 'yandex.ru', 'bing.com', 'duckduckgo.com'];
    const isSearchEngine = searchEngines.some(engine => 
      tab.url && tab.url.includes(engine)
    );
    
    if (isSearchEngine) {
      // Можно установить специальный значок для поисковых систем
      chrome.action.setBadgeText({
        tabId: tabId,
        text: '!'
      });
      chrome.action.setBadgeBackgroundColor({
        tabId: tabId,
        color: '#ff6b6b'
      });
    } else {
      chrome.action.setBadgeText({
        tabId: tabId,
        text: ''
      });
    }
  }
});