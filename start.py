#!/usr/bin/env python3
"""
Альтернативный запуск бота с загрузкой .env файла
Работает на любой системе (NixOS, Ubuntu, и т.д.)
"""

import os
import sys
from pathlib import Path

# Проверяем наличие venv и активируем его
script_dir = Path(__file__).parent
venv_activate = script_dir / 'venv' / 'bin' / 'activate_this.py'

# Загружаем .env файл, если он есть
env_file = script_dir / '.env'
if env_file.exists():
    print(f"Загружаем переменные из {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, _, value = line.partition('=')
                os.environ[key.strip()] = value.strip()

# Импортируем и запускаем основной модуль
if __name__ == '__main__':
    try:
        import bot
        bot.main()
    except ModuleNotFoundError as e:
        print(f"\n❌ Ошибка: {e}")
        print("\nЗависимости не установлены!")
        print("Запустите сначала: ./setup.sh")
        print("Или вручную:")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate")
        print("  pip install -r requirements.txt")
        sys.exit(1)
