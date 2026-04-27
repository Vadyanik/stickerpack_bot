#!/usr/bin/env bash

# Скрипт установки для NixOS и других систем

set -e  # Останавливаться при ошибках

echo "Настройка окружения для бота..."

# Проверяем наличие python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите python3:"
    echo "   sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# Создаем виртуальное окружение, если его нет
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Ошибка создания venv. Установите python3-venv:"
        echo "   sudo apt install python3-venv"
        exit 1
    fi
    echo "✓ Виртуальное окружение создано"
else
    echo "✓ Виртуальное окружение уже существует"
fi

# Обновляем pip (используем pip из venv)
echo "Обновление pip..."
venv/bin/pip install --upgrade pip

# Устанавливаем зависимости
echo "Установка зависимостей..."
venv/bin/pip install -r requirements.txt

echo ""
echo "✓ Установка завершена!"
echo ""
echo "Для запуска бота используйте:"
echo "  source venv/bin/activate"
echo "  python3 bot.py"
echo ""
echo "Или используйте готовый скрипт:"
echo "  ./start.py"
