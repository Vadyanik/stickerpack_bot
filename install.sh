#!/usr/bin/env bash

# Скрипт быстрой установки бота на сервере

set -e

echo "================================"
echo "Telegram Sticker Pack Bot"
echo "Установка на сервер"
echo "================================"
echo ""

# Проверка наличия необходимых команд
echo "Проверка зависимостей..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен. Устанавливаю..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
else
    echo "✓ Python3 установлен"
fi

if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Устанавливаю..."
    sudo apt update
    sudo apt install -y git
else
    echo "✓ Git установлен"
fi

echo ""
echo "Установка зависимостей Python..."
./setup.sh

echo ""
echo "================================"
echo "Настройка конфигурации"
echo "================================"
echo ""

# Проверка наличия .env
if [ ! -f .env ]; then
    echo "Создаю файл .env..."
    cp .env.example .env

    echo ""
    echo "⚠️  ВАЖНО: Настройте токен бота!"
    echo ""
    echo "Откройте файл .env и вставьте ваш токен:"
    echo "  nano .env"
    echo ""
    echo "Или установите токен прямо сейчас:"
    read -p "Введите BOT_TOKEN (или Enter для ручной настройки): " bot_token

    if [ -n "$bot_token" ]; then
        echo "BOT_TOKEN=$bot_token" > .env
        echo "✓ Токен сохранен в .env"
    else
        echo "ℹ️  Настройте токен позже: nano .env"
    fi
else
    echo "✓ Файл .env уже существует"
fi

echo ""
echo "================================"
echo "Проверка конфигурации"
echo "================================"
echo ""

# Показать текущие настройки
echo "Разрешенные группы:"
grep -A 5 "ALLOWED_GROUPS" config.py || echo "Нет ограничений"

echo ""
echo "================================"
echo "Установка завершена!"
echo "================================"
echo ""
echo "Следующие шаги:"
echo ""
echo "1. Проверьте конфигурацию:"
echo "   nano .env          # Токен бота"
echo "   nano config.py     # ID разрешенных групп"
echo ""
echo "2. Запустите бота:"
echo "   ./start.py                    # Тестовый запуск"
echo "   nohup ./start.py > bot.log &  # Фоновый запуск"
echo ""
echo "3. Или настройте systemd сервис:"
echo "   Смотрите DEPLOYMENT.md для инструкций"
echo ""
echo "4. Добавьте бота в группу:"
echo "   - Откройте @BotFather"
echo "   - Найдите вашего бота"
echo "   - Добавьте в группу"
echo "   - Отправьте /start"
echo ""
echo "Документация:"
echo "  README.md       - Общая информация"
echo "  QUICKSTART.md   - Быстрый старт"
echo "  DEPLOYMENT.md   - Развертывание на сервере"
echo ""
