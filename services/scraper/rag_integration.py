"""
Интеграция между скраппером и RAG системой
"""
import logging
import httpx
from typing import List, Dict, Any
from datetime import datetime

from src.domain.entities.scraped_data import ScrapedData
from src.domain.entities.vector_document import VectorDocument

logger = logging.getLogger(__name__)

from config import scraper_settings

class RAGIntegration:
    """Интеграция с RAG системой"""
    
    def __init__(self, vectorstore_url: str = None):
        self.vectorstore_url = vectorstore_url or scraper_settings.VECTORSTORE_URL
    
    async def add_scraped_data_to_rag(self, scraped_data: List[ScrapedData]) -> bool:
        """Добавляет данные из скраппера в RAG систему"""
        try:
            logger.info(f"🔄 Добавление {len(scraped_data)} материалов в RAG систему...")
            
            # Подготавливаем документы для batch отправки
            documents = []
            for material in scraped_data:
                document = {
                    "text": material.content.lower(),
                    "metadata": {
                        "source": "minjust",
                        "number": material.number.lower(),
                        "date": material.date.isoformat() if material.date else "",
                        "content": material.content.lower()
                    }
                }
                documents.append(document)
            
            # Отправляем batch запрос
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.vectorstore_url}/add-documents-batch",
                    json=documents,
                    timeout=300.0  # Увеличиваем таймаут для batch операции
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Успешно добавлено {result.get('added_count', 0)} из {len(scraped_data)} материалов в RAG систему")
                    return True
                else:
                    logger.error(f"❌ Ошибка batch добавления: {response.status_code}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка интеграции с RAG системой: {e}")
            return False
    
    async def search_in_rag(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Поиск в RAG системе"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.vectorstore_url}/search",
                    json={
                        "query": query,
                        "top_k": top_k,
                        "threshold": 0.3
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                else:
                    logger.error(f"Ошибка поиска в RAG: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Ошибка поиска в RAG системе: {e}")
            return []
    
    async def get_rag_statistics(self) -> Dict[str, Any]:
        """Получение статистики RAG системы"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.vectorstore_url}/statistics")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Status code: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики RAG: {e}")
            return {"error": str(e)} 