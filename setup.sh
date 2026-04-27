#!/usr/bin/env bash

# Скрипт установки для NixOS и других систем

echo "Настройка окружения для бота..."

# Создаем виртуальное окружение, если его нет
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "Активация виртуального окружения..."
source venv/bin/activate

# Обновляем pip
echo "Обновление pip..."
pip install --upgrade pip

# Устанавливаем зависимости
echo "Установка зависимостей..."
pip install -r requirements.txt

echo ""
echo "✓ Установка завершена!"
echo ""
echo "Для запуска бота используйте:"
echo "  source venv/bin/activate"
echo "  python3 bot.py"
echo ""
echo "Или используйте готовый скрипт:"
echo "  ./start.py"
