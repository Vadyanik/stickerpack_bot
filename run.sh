#!/usr/bin/env bash

# Скрипт для запуска бота

# Проверка наличия .env файла
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Запуск бота
python3 bot.py
