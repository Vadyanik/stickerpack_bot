# Развертывание бота на сервере

## Быстрая установка на Ubuntu/Debian сервере

### 1. Подключитесь к серверу
```bash
ssh user@your-server.com
```

### 2. Установите необходимые пакеты
```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv
```

### 3. Клонируйте репозиторий
```bash
cd ~
git clone git@github.com:Vadyanik/stickerpack_bot.git
# Или через HTTPS:
# git clone https://github.com/Vadyanik/stickerpack_bot.git

cd stickerpack_bot
```

### 4. Установите зависимости
```bash
./setup.sh
```

### 5. Настройте токен бота
```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте файл и вставьте ваш токен
nano .env
# или
vim .env
```

В файле `.env` замените токен:
```
BOT_TOKEN=ваш_токен_от_BotFather
```

Сохраните файл (Ctrl+O, Enter, Ctrl+X в nano)

### 6. Настройте разрешенные группы (опционально)
```bash
nano config.py
```

Убедитесь, что список `ALLOWED_GROUPS` содержит нужные группы:
```python
ALLOWED_GROUPS = [
    -5255145507,
    -1003463889030,
    -1002772620324
]
```

### 7. Запустите бота
```bash
./start.py
```

Бот должен вывести:
```
Загружаем переменные из .env
INFO - Бот запущен и готов к работе
```

## Запуск в фоновом режиме

### Вариант 1: Screen (простой)
```bash
# Установите screen
sudo apt install screen

# Создайте сессию
screen -S stickerbot

# Запустите бота
./start.py

# Отключитесь от сессии: Ctrl+A, затем D
# Подключитесь обратно: screen -r stickerbot
```

### Вариант 2: tmux
```bash
# Установите tmux
sudo apt install tmux

# Создайте сессию
tmux new -s stickerbot

# Запустите бота
./start.py

# Отключитесь: Ctrl+B, затем D
# Подключитесь: tmux attach -t stickerbot
```

### Вариант 3: nohup (самый простой)
```bash
nohup ./start.py > bot.log 2>&1 &

# Просмотр логов
tail -f bot.log

# Остановка бота
ps aux | grep start.py
kill <PID>
```

### Вариант 4: systemd (рекомендуется для production)

Создайте systemd service:
```bash
sudo nano /etc/systemd/system/stickerbot.service
```

Вставьте:
```ini
[Unit]
Description=Telegram Sticker Pack Bot
After=network.target

[Service]
Type=simple
User=ваш_пользователь
WorkingDirectory=/home/ваш_пользователь/stickerpack_bot
Environment="PATH=/home/ваш_пользователь/stickerpack_bot/venv/bin"
ExecStart=/home/ваш_пользователь/stickerpack_bot/venv/bin/python /home/ваш_пользователь/stickerpack_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Замените `ваш_пользователь` на ваше имя пользователя!**

Активируйте сервис:
```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Запустите бота
sudo systemctl start stickerbot

# Проверьте статус
sudo systemctl status stickerbot

# Включите автозапуск при загрузке
sudo systemctl enable stickerbot

# Просмотр логов
sudo journalctl -u stickerbot -f
```

Управление сервисом:
```bash
sudo systemctl start stickerbot    # Запустить
sudo systemctl stop stickerbot     # Остановить
sudo systemctl restart stickerbot  # Перезапустить
sudo systemctl status stickerbot   # Статус
```

## Обновление бота

```bash
cd ~/stickerpack_bot

# Остановите бота (если запущен через systemd)
sudo systemctl stop stickerbot

# Обновите код
git pull origin main

# Обновите зависимости (если изменились)
source venv/bin/activate
pip install -r requirements.txt

# Запустите бота
sudo systemctl start stickerbot
```

## Проверка работы

1. Откройте Telegram
2. Добавьте бота в группу
3. Отправьте `/start`
4. Отправьте стикер
5. Бот должен создать пак и отправить ссылку

## Устранение неполадок

### Бот не запускается
```bash
# Проверьте логи
sudo journalctl -u stickerbot -n 50

# Проверьте токен
cat .env

# Проверьте зависимости
source venv/bin/activate
python -c "import telegram; print('OK')"
```

### Бот не отвечает
```bash
# Проверьте, что Privacy Mode выключен в @BotFather
# /mybots -> выберите бота -> Bot Settings -> Group Privacy -> Turn off

# Проверьте логи
tail -f bot.log
# или
sudo journalctl -u stickerbot -f
```

### Ошибка "Module not found"
```bash
# Переустановите зависимости
rm -rf venv
./setup.sh
```

## Мониторинг

Просмотр логов в реальном времени:
```bash
# Если запущен через systemd
sudo journalctl -u stickerbot -f

# Если запущен через nohup
tail -f bot.log

# Если запущен через screen
screen -r stickerbot
```

## Безопасность

1. **Не коммитьте .env файл в git** (уже в .gitignore)
2. **Ограничьте доступ к файлу с токеном:**
   ```bash
   chmod 600 .env
   ```
3. **Настройте firewall** (разрешите только SSH)
4. **Регулярно обновляйте систему:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## Резервное копирование

Важные файлы для бэкапа:
- `.env` - токен бота
- `config.py` - конфигурация (ID групп)
- `packs_state.json` - состояние паков (создается автоматически)

```bash
# Создать бэкап
tar -czf stickerbot-backup-$(date +%Y%m%d).tar.gz .env config.py packs_state.json

# Восстановить
tar -xzf stickerbot-backup-YYYYMMDD.tar.gz
```
