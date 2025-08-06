from typing import List
from src.domain.strategies.search_strategy import SearchStrategy, SearchResult
from src.domain.entities.vector_document import VectorDocument
import re


class ExactSearchStrategy(SearchStrategy):
    """Стратегия точного поиска по ключевым словам"""
    
    def search(self, query: str, documents: List[VectorDocument], top_k: int = 5) -> List[SearchResult]:
        """Точный поиск по ключевым словам"""
        query_words = self._extract_keywords(query.lower())
        results = []
        
        for document in documents:
            text_lower = document.text.lower()
            score = self._calculate_exact_score(query_words, text_lower)
            
            if score > 0:
                results.append(SearchResult(
                    document=document,
                    score=score,
                    search_type="exact"
                ))
        
        # Сортируем по убыванию score и берем top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def get_strategy_name(self) -> str:
        return "exact"
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Извлечение ключевых слов из запроса"""
        # Убираем стоп-слова и оставляем значимые
        stop_words = {"и", "в", "на", "с", "по", "для", "от", "до", "из", "за", "о", "об", "а", "но", "или", "что", "как", "где", "когда"}
        words = re.findall(r'\b\w+\b', query)
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _calculate_exact_score(self, query_words: List[str], text: str) -> float:
        """Расчет точности совпадения"""
        if not query_words:
            return 0.0
        
        matches = 0
        total_words = len(query_words)
        
        for word in query_words:
            if word in text:
                matches += 1
        
        # Возвращаем процент совпадений
        return matches / total_words if total_words > 0 else 0.0 