"""
Тесты для фабрик и стратегий в AI Model Service
"""
import pytest
import asyncio
import torch
from unittest.mock import Mock, patch
from typing import Dict, Any

# Импорты из доменного слоя
from domain.factories.model_factory import ModelFactoryRegistry, OptimizedModelFactory
from domain.strategies.device_strategy import DeviceStrategyFactory, AutoDeviceStrategy, GPUFirstStrategy, CPUOnlyStrategy
from domain.strategies.threading_strategy import ThreadingStrategyFactory, HybridThreadingStrategy


class TestDeviceStrategies:
    """Тесты для стратегий выбора устройства"""
    
    def test_auto_device_strategy_cuda_available(self):
        """Тест автоматической стратегии с доступным CUDA"""
        with patch('torch.cuda.is_available', return_value=True):
            strategy = AutoDeviceStrategy()
            device = strategy.select_device("test_model")
            assert device == "cuda"
    
    def test_auto_device_strategy_cuda_unavailable(self):
        """Тест автоматической стратегии без CUDA"""
        with patch('torch.cuda.is_available', return_value=False):
            strategy = AutoDeviceStrategy()
            device = strategy.select_device("test_model")
            assert device == "cpu"
    
    def test_gpu_first_strategy_sufficient_memory(self):
        """Тест GPU-первой стратегии с достаточной памятью"""
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.get_device_properties') as mock_props:
            
            mock_props.return_value.total_memory = 16 * 1024**3  # 16GB
            
            strategy = GPUFirstStrategy()
            device = strategy.select_device("test_model", {"required_memory": 8 * 1024**3})
            assert device == "cuda"
    
    def test_gpu_first_strategy_insufficient_memory(self):
        """Тест GPU-первой стратегии с недостаточной памятью"""
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.get_device_properties') as mock_props:
            
            mock_props.return_value.total_memory = 4 * 1024**3  # 4GB
            
            strategy = GPUFirstStrategy()
            device = strategy.select_device("test_model", {"required_memory": 8 * 1024**3})
            assert device == "cpu"
    
    def test_cpu_only_strategy(self):
        """Тест CPU-только стратегии"""
        strategy = CPUOnlyStrategy()
        device = strategy.select_device("test_model")
        assert device == "cpu"
    
    def test_device_strategy_factory(self):
        """Тест фабрики стратегий устройств"""
        # Тест создания стратегий
        auto_strategy = DeviceStrategyFactory.create_strategy("auto")
        gpu_strategy = DeviceStrategyFactory.create_strategy("gpu_first")
        cpu_strategy = DeviceStrategyFactory.create_strategy("cpu_only")
        
        assert isinstance(auto_strategy, AutoDeviceStrategy)
        assert isinstance(gpu_strategy, GPUFirstStrategy)
        assert isinstance(cpu_strategy, CPUOnlyStrategy)
        
        # Тест получения доступных стратегий
        available_strategies = DeviceStrategyFactory.get_available_strategies()
        assert "auto" in available_strategies
        assert "gpu_first" in available_strategies
        assert "cpu_only" in available_strategies


class TestThreadingStrategies:
    """Тесты для стратегий многопоточности"""
    
    @pytest.mark.asyncio
    async def test_hybrid_threading_strategy(self):
        """Тест гибридной стратегии многопоточности"""
        strategy = HybridThreadingStrategy(thread_workers=2, process_workers=1)
        
        # Тест выполнения задачи
        def cpu_task():
            return "cpu_result"
        
        def io_task():
            return "io_result"
        
        # CPU-интенсивная задача должна использовать ProcessPoolExecutor
        result = await strategy.execute_task(cpu_task)
        assert result == "cpu_result"
        
        # I/O-интенсивная задача должна использовать ThreadPoolExecutor
        result = await strategy.execute_task(io_task)
        assert result == "io_result"
        
        # Очистка ресурсов
        strategy.cleanup()
    
    def test_threading_strategy_factory(self):
        """Тест фабрики стратегий многопоточности"""
        # Тест создания стратегий
        async_strategy = ThreadingStrategyFactory.create_strategy("async")
        process_strategy = ThreadingStrategyFactory.create_strategy("process")
        hybrid_strategy = ThreadingStrategyFactory.create_strategy("hybrid")
        
        assert hasattr(async_strategy, 'execute_task')
        assert hasattr(process_strategy, 'execute_task')
        assert hasattr(hybrid_strategy, 'execute_task')
        
        # Тест получения доступных стратегий
        available_strategies = ThreadingStrategyFactory.get_available_strategies()
        assert "async" in available_strategies
        assert "process" in available_strategies
        assert "hybrid" in available_strategies


class TestModelFactories:
    """Тесты для фабрик моделей"""
    
    def test_optimized_model_factory_validation(self):
        """Тест валидации модели в оптимизированной фабрике"""
        factory = OptimizedModelFactory()
        
        # Тест с несуществующей моделью
        assert not factory.validate_model("non_existent_model")
        
        # Тест с существующей моделью (если путь существует)
        with patch('os.path.exists', return_value=True):
            assert factory.validate_model("qwen-model_full")
    
    def test_model_factory_registry(self):
        """Тест реестра фабрик моделей"""
        # Регистрация новой фабрики
        custom_factory = Mock()
        ModelFactoryRegistry.register_factory("custom", custom_factory)
        
        # Получение фабрики
        factory = ModelFactoryRegistry.get_factory("custom")
        assert factory == custom_factory
        
        # Получение несуществующей фабрики (должна вернуть optimized)
        factory = ModelFactoryRegistry.get_factory("non_existent")
        assert isinstance(factory, OptimizedModelFactory)
        
        # Получение доступных фабрик
        available_factories = ModelFactoryRegistry.get_available_factories()
        assert "optimized" in available_factories
        assert "custom" in available_factories


class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_repository_with_factories_and_strategies(self):
        """Тест репозитория с фабриками и стратегиями"""
        from infrastructure.persistence.optimized_model_repository import OptimizedModelRepository
        
        # Создание репозитория с кастомными стратегиями
        repository = OptimizedModelRepository(
            factory_name="optimized",
            threading_strategy="hybrid"
        )
        
        # Проверка инициализации
        assert hasattr(repository, 'model_factory')
        assert hasattr(repository, 'threading_manager')
        assert isinstance(repository.model_factory, OptimizedModelFactory)
        assert isinstance(repository.threading_manager.strategy, HybridThreadingStrategy)
    
    def test_device_selection_integration(self):
        """Тест интеграции выбора устройства"""
        # Создание фабрики с GPU-первой стратегией
        device_strategy = GPUFirstStrategy()
        factory = OptimizedModelFactory(device_strategy=device_strategy)
        
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.get_device_properties') as mock_props:
            
            mock_props.return_value.total_memory = 16 * 1024**3
            
            # Проверка конфигурации модели
            config = factory.get_model_config("qwen-model_full")
            assert "required_memory" in config
            assert config["required_memory"] == 8 * 1024**3


class TestPerformance:
    """Тесты производительности"""
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        """Тест параллельного выполнения задач"""
        strategy = HybridThreadingStrategy(thread_workers=2, process_workers=1)
        
        def cpu_intensive_task():
            # Симуляция CPU-интенсивной задачи
            result = 0
            for i in range(100000):
                result += i
            return result
        
        def io_intensive_task():
            # Симуляция I/O-интенсивной задачи
            import time
            time.sleep(0.01)
            return "io_done"
        
        # Параллельное выполнение задач
        tasks = [cpu_intensive_task, io_intensive_task, cpu_intensive_task]
        results = await strategy.execute_tasks_concurrently(tasks)
        
        assert len(results) == 3
        assert all(isinstance(result, (int, str)) for result in results)
        
        strategy.cleanup()


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])
