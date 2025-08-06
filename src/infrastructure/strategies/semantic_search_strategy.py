from typing import List
from src.domain.strategies.search_strategy import SearchStrategy, SearchResult
from src.domain.entities.vector_document import VectorDocument
import faiss
import numpy as np


class SemanticSearchStrategy(SearchStrategy):
    """Стратегия семантического поиска через FAISS"""
    
    def __init__(self, encoder, index, document_ids: List[str]):
        self.encoder = encoder
        self.index = index
        self.document_ids = document_ids
    
    def search(self, query: str, documents: List[VectorDocument], top_k: int = 5) -> List[SearchResult]:
        """Семантический поиск через FAISS"""
        if not self.encoder or not self.index:
            return []
        
        try:
            # Создаем эмбеддинг для запроса
            query_embedding = self.encoder.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Выполняем поиск
            scores, indices = self.index.search(
                query_embedding.astype('float32'), 
                min(top_k, len(self.document_ids))
            )
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.document_ids):
                    doc_id = self.document_ids[idx]
                    # Находим документ по ID
                    document = next((doc for doc in documents if doc.id == doc_id), None)
                    if document:
                        # Используем score как есть (больше = лучше для FAISS)
                        normalized_score = score
                        results.append(SearchResult(
                            document=document,
                            score=normalized_score,
                            search_type="semantic"
                        ))
            
            return results
            
        except Exception as e:
            print(f"Ошибка семантического поиска: {e}")
            return []
    
    def get_strategy_name(self) -> str:
        return "semantic" 