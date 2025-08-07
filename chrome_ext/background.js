chrome.runtime.onInstalled.addListener(() => {
  console.log('Extremist Content Checker установлен');
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'saveQuery') {
    chrome.storage.session.set({ query: request.query });
  }
  
  if (request.action === 'getQuery') {
    chrome.storage.session.get('query', (data) => {
      sendResponse({ query: data.query || '' });
    });
    return true; 
  }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete') {
    const searchEngines = ['google.com', 'yandex.ru', 'bing.com', 'duckduckgo.com'];
    const isSearchEngine = searchEngines.some(engine => 
      tab.url && tab.url.includes(engine)
    );
    
    if (isSearchEngine) {
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