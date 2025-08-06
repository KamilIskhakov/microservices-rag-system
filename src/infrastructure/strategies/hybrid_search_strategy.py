from typing import List
from src.domain.strategies.search_strategy import SearchStrategy, SearchResult
from src.domain.entities.vector_document import VectorDocument


class HybridSearchStrategy(SearchStrategy):
    """Гибридная стратегия поиска"""
    
    def __init__(self, exact_strategy: SearchStrategy, semantic_strategy: SearchStrategy):
        self.exact_strategy = exact_strategy
        self.semantic_strategy = semantic_strategy
    
    def search(self, query: str, documents: List[VectorDocument], top_k: int = 5) -> List[SearchResult]:
        """Гибридный поиск: сначала точный, потом семантический"""
        
        # 1. Точный поиск
        exact_results = self.exact_strategy.search(query, documents, top_k)
        
        # Если нашли хорошие точные совпадения (score > 0.5), возвращаем их
        good_exact_results = [r for r in exact_results if r.score > 0.5]
        if good_exact_results:
            return good_exact_results[:top_k]
        
        # 2. Если точных совпадений нет или они слабые, добавляем семантические
        semantic_results = self.semantic_strategy.search(query, documents, top_k)
        
        # 3. Объединяем результаты
        combined_results = exact_results + semantic_results
        
        # 4. Убираем дубликаты по document.id
        unique_results = {}
        for result in combined_results:
            if result.document.id not in unique_results:
                unique_results[result.document.id] = result
            else:
                # Если документ уже есть, берем лучший score
                existing = unique_results[result.document.id]
                if result.score > existing.score:
                    unique_results[result.document.id] = result
        
        # 5. Сортируем по score и возвращаем top_k
        final_results = list(unique_results.values())
        final_results.sort(key=lambda x: x.score, reverse=True)
        
        return final_results[:top_k]
    
    def get_strategy_name(self) -> str:
        return "hybrid" 