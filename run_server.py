#!/usr/bin/env python3

import os
import sys
import subprocess

def main():
    # Определяем пути
    project_root = os.path.dirname(os.path.abspath(__file__))
    backend_path = os.path.join(project_root, 'backend')
    venv_path = os.path.join(backend_path, 'venv')
    
    # Проверяем, существует ли виртуальное окружение
    if not os.path.exists(venv_path):
        print("❌ Виртуальное окружение не найдено в backend/venv")
        print("Создайте виртуальное окружение командой:")
        print("cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
        sys.exit(1)
    
    # Определяем путь к python в виртуальном окружении
    venv_python = os.path.join(venv_path, 'bin', 'python')
    
    if not os.path.exists(venv_python):
        print("❌ Python не найден в виртуальном окружении")
        sys.exit(1)
    
    print("🚀 Запускаем сервер проверки экстремистских материалов...")
    print("🌐 Сервер будет доступен на: http://localhost:8000")
    print("📋 API документация: http://localhost:8000/docs")
    print("🛑 Для остановки нажмите Ctrl+C")
    print()
    
    # Запускаем сервер через виртуальное окружение
    app_path = os.path.join(backend_path, 'app.py')
    
    cmd = [
        venv_python, '-m', 'uvicorn', 
        'app:app', 
        '--host', '0.0.0.0', 
        '--port', '8000', 
        '--reload'
    ]
    
    try:
        # Меняем рабочую директорию на backend
        os.chdir(backend_path)
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")

if __name__ == '__main__':
    main()
