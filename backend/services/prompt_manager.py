from typing import List, Dict, Any
from dataclasses import dataclass
import json
import re
from .logger import logger

@dataclass
class SearchResult:
    """Результат поиска"""
    text: str
    relevance_score: float
    metadata: Dict[str, Any] = None

@dataclass
class StructuredResponse:
    """Структурированный ответ"""
    result: str  # "Да" или "Нет"
    court_decision_date: str = ""
    explanation: str = ""
    confidence: float = 0.0

class PromptManager:
    """Менеджер промптов с structured output"""
    
    def __init__(self):
        self.system_prompt = """Ты эксперт по проверке экстремистских материалов. Отвечай ТОЛЬКО в формате JSON:

{
    "result": "Да" или "Нет",
    "court_decision_date": "дата" (если result="Да"),
    "explanation": "краткое объяснение",
    "confidence": 0.95
}

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. В базе данных содержатся материалы, которые уже признаны экстремистскими по решению суда
2. Твоя задача - определить, связан ли запрос пользователя с этими конкретными материалами
3. Анализируй СМЫСЛОВУЮ связь, а не только совпадение отдельных слов
4. Если запрос содержит общие слова (россия, пони, rag, llm), но НЕ связан с экстремистскими материалами - result="Нет"
5. Если запрос относится к конкретному экстремистскому материалу из базы - result="Да"
6. Будь ОЧЕНЬ строгим - лучше пропустить, чем ошибиться
7. Если сомневаешься - result="Нет"
8. Указывай реальные даты судебных решений из материалов
9. Отвечай только JSON без лишнего текста"""
        
        logger.info("PromptManager initialized")
    
    def create_prompt(self, query: str, search_results: List[SearchResult]) -> str:
        """Создает промпт для модели"""
        user_prompt = f"""Запрос пользователя: "{query}"

Найденные релевантные материалы (отсортированы по релевантности):
"""
        
        if search_results:
            for i, result in enumerate(search_results, 1):
                user_prompt += f"{i}. {result.text}\n   Релевантность: {result.relevance_score:.3f}\n\n"
            logger.info(f"Created prompt with {len(search_results)} search results")
        else:
            user_prompt += "Релевантные материалы не найдены.\n"
            logger.info("Created prompt with no search results")

        user_prompt += f"""
ВНИМАНИЕ: Определи, относится ли запрос "{query}" к одному из найденных экстремистских материалов.

КРИТИЧЕСКИ ВАЖНО:
- Анализируй СМЫСЛОВУЮ связь, а не только совпадение отдельных слов
- Если запрос содержит общие слова, но НЕ связан с экстремистскими материалами - result="Нет"
- Будь ОЧЕНЬ строгим - лучше пропустить, чем ошибиться
- Если сомневаешься - result="Нет"

Ответ в формате JSON:"""

        full_prompt = f"{self.system_prompt}\n\n{user_prompt}"
        return full_prompt
    
    def parse_response(self, response_text: str) -> StructuredResponse:
        """Парсит ответ модели в структурированный формат"""
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                structured_response = StructuredResponse(
                    result=data.get("result", "Нет"),
                    court_decision_date=data.get("court_decision_date", ""),
                    explanation=data.get("explanation", ""),
                    confidence=data.get("confidence", 0.0)
                )
                
                logger.info(f"Successfully parsed JSON response: {structured_response.result}")
                return structured_response
            else:
                # Fallback: анализируем текст
                logger.warning("No JSON found in response, using fallback parsing")
                return self._fallback_parse(response_text)
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON parsing error: {e}")
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, response_text: str) -> StructuredResponse:
        """Fallback парсинг текста"""
        response_lower = response_text.lower()
        
        # Ищем дату в тексте
        date_pattern = r'\d{1,2}\.\d{1,2}\.\d{4}'
        date_match = re.search(date_pattern, response_text)
        court_date = date_match.group() if date_match else ""
        
        # Определяем результат
        if "да" in response_lower or "yes" in response_lower:
            logger.info("Fallback parsing: Found positive result")
            return StructuredResponse(
                result="Да",
                court_decision_date=court_date,
                explanation="Найдены экстремистские материалы",
                confidence=0.7
            )
        else:
            logger.info("Fallback parsing: Found negative result")
            return StructuredResponse(
                result="Нет",
                court_decision_date="",
                explanation="Экстремистские материалы не найдены",
                confidence=0.8
            )
    
    def format_final_response(self, structured_response: StructuredResponse) -> str:
        """Форматирует финальный ответ"""
        if structured_response.result == "Да":
            if structured_response.court_decision_date:
                final_response = f"Да, решение суда от {structured_response.court_decision_date}. {structured_response.explanation}"
            else:
                final_response = f"Да, решение суда от [дата]. {structured_response.explanation}"
        else:
            final_response = "Нет"
        
        logger.info(f"Formatted final response: {final_response}")
        return final_response 