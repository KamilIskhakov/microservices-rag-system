from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
from typing import Dict, List
import time
import hashlib
from config import settings
import re

class SecurityMiddleware:
    """Middleware для обеспечения безопасности"""
    
    def __init__(self):
        self.rate_limit_store: Dict[str, List[float]] = {}
        self.sensitive_patterns = [
            r'password\s*[:=]',
            r'secret\s*[:=]',
            r'key\s*[:=]',
            r'token\s*[:=]',
            r'api_key\s*[:=]',
            r'database\s*[:=]',
            r'admin\s*[:=]',
            r'root\s*[:=]'
        ]
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Проверяет ограничение скорости запросов"""
        current_time = time.time()
        window_start = current_time - 60  # 1 минута
        
        # Очищаем старые записи
        if client_ip in self.rate_limit_store:
            self.rate_limit_store[client_ip] = [
                timestamp for timestamp in self.rate_limit_store[client_ip]
                if timestamp > window_start
            ]
        else:
            self.rate_limit_store[client_ip] = []
        
        # Проверяем лимит
        if len(self.rate_limit_store[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
            return False
        
        # Добавляем текущий запрос
        self.rate_limit_store[client_ip].append(current_time)
        return True
    
    def sanitize_log_data(self, data: str) -> str:
        """Очищает чувствительные данные из логов"""
        if not settings.LOG_SENSITIVE_DATA:
            for pattern in self.sensitive_patterns:
                data = re.sub(pattern, r'[REDACTED]', data, flags=re.IGNORECASE)
        return data
    
    def add_security_headers(self, response: Response):
        """Добавляет заголовки безопасности"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        if settings.USE_HTTPS:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        response.headers["Content-Security-Policy"] = csp
    
    def validate_input(self, data: dict) -> bool:
        """Валидирует входные данные"""
        if not data or "query" not in data:
            return False
        
        query = data["query"]
        
        # Проверяем длину
        if len(query) > 1000:
            return False
        
        # Проверяем на XSS
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'data:text/html',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False
        
        # Проверяем на SQL Injection
        sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter)\b)',
            r'(\b(or|and)\b\s+\d+\s*=\s*\d+)',
            r'(\b(union|select)\b.*\bfrom\b)',
            r'(\b(union|select)\b.*\bwhere\b)'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False
        
        return True

# Глобальный экземпляр middleware
security_middleware = SecurityMiddleware() 