"""
Use case для генерации текста в AI Model Service
"""
from dataclasses import dataclass
from typing import Optional, List
from domain.services.model_service import ModelService


@dataclass
class GenerateTextRequest:
    """Запрос на генерацию текста"""
    query: str
    context: List[str] = None
    max_length: int = 512
    temperature: float = 0.7
    model_id: str = "qwen-model_full"


@dataclass
class GenerateTextResponse:
    """Ответ на генерацию текста"""
    success: bool
    result: str
    processing_time: float
    model_id: str
    error: Optional[str] = None


class GenerateTextUseCase:
    """Use case для генерации текста"""
    
    def __init__(self, model_service: ModelService):
        self.model_service = model_service
    
    async def execute(self, request: GenerateTextRequest) -> GenerateTextResponse:
        """Выполнить генерацию текста"""
        import time
        start_time = time.time()
        
        try:
            if not self.model_service.is_model_available(request.model_id):
                await self.model_service.load_model(request.model_id)
            
            prompt = self._build_prompt(request.query, request.context or [])
            
            result = await self.model_service.generate_text(
                model_id=request.model_id,
                prompt=prompt,
                max_length=request.max_length,
                temperature=request.temperature
            )
            
            processing_time = time.time() - start_time
            
            return GenerateTextResponse(
                success=True,
                result=result,
                processing_time=processing_time,
                model_id=request.model_id
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return GenerateTextResponse(
                success=False,
                result="",
                processing_time=processing_time,
                model_id=request.model_id,
                error=str(e)
            )
    
    def _build_prompt(self, query: str, context: List[str]) -> str:
        """Построить промпт с контекстом"""
        if not context:
            return query
        
        context_text = "\n".join(context)
        return f"Контекст:\n{context_text}\n\nЗапрос: {query}\n\nОтвет:"
