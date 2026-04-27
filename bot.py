#!/usr/bin/env python3
"""
Телеграм бот для автоматического сохранения стикеров из группы в общий стикерпак
"""

import logging
import json
import os
import asyncio
from telegram import Update, InputSticker
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class StickerPackManager:
    """Менеджер для управления стикерпаками"""

    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self) -> dict:
        """Загрузить состояние из файла"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки состояния: {e}")
                return {}
        return {}

    def save_state(self):
        """Сохранить состояние в файл"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения состояния: {e}")

    def get_chat_pack_info(self, chat_id: str) -> dict:
        """Получить информацию о паке для чата"""
        if chat_id not in self.state:
            self.state[chat_id] = {
                'packs': {},  # {'static': {...}, 'animated': {...}, 'video': {...}}
                'chat_title': None
            }
            self.save_state()
        return self.state[chat_id]

    def update_chat_pack_info(self, chat_id: str, **kwargs):
        """Обновить информацию о паке для чата"""
        if chat_id not in self.state:
            self.state[chat_id] = {}
        self.state[chat_id].update(kwargs)
        self.save_state()

    def get_pack_info_for_type(self, chat_id: str, sticker_format: str) -> dict:
        """Получить информацию о паке для конкретного типа стикеров"""
        chat_info = self.get_chat_pack_info(chat_id)
        if sticker_format not in chat_info['packs']:
            chat_info['packs'][sticker_format] = {
                'pack_number': 0,
                'current_pack_name': None,
                'sticker_count': 0
            }
            self.save_state()
        return chat_info['packs'][sticker_format]

    def increment_sticker_count(self, chat_id: str, sticker_format: str) -> int:
        """Увеличить счетчик стикеров и вернуть новое значение"""
        pack_info = self.get_pack_info_for_type(chat_id, sticker_format)
        pack_info['sticker_count'] += 1
        self.save_state()
        return pack_info['sticker_count']

    def get_max_stickers(self, sticker_format: str) -> int:
        """Получить максимальное количество стикеров для типа"""
        if sticker_format == "static":
            return config.MAX_STICKERS_STATIC
        elif sticker_format == "animated":
            return config.MAX_STICKERS_ANIMATED
        else:  # video
            return config.MAX_STICKERS_VIDEO

    def needs_new_pack(self, chat_id: str, sticker_format: str) -> bool:
        """Проверить, нужен ли новый пак"""
        pack_info = self.get_pack_info_for_type(chat_id, sticker_format)
        max_stickers = self.get_max_stickers(sticker_format)
        return pack_info['sticker_count'] >= max_stickers

    def create_pack_name(self, chat_title: str, sticker_format: str, pack_number: int, bot_username: str) -> str:
        """Создать имя пака"""
        # Убираем недопустимые символы и заменяем пробелы на подчеркивания
        safe_title = ''.join(c if c.isalnum() or c == '_' else '_' for c in chat_title)
        safe_title = safe_title[:25]  # ограничение длины

        # Добавляем тип стикера к имени
        type_suffix = {"static": "s", "animated": "a", "video": "v"}[sticker_format]

        if pack_number == 0:
            return f"{safe_title}_{type_suffix}_by_{bot_username}"
        else:
            return f"{safe_title}_{type_suffix}{pack_number}_by_{bot_username}"


# Глобальный менеджер паков
pack_manager = StickerPackManager(config.STATE_FILE)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    chat_type = update.message.chat.type

    if chat_type in ['group', 'supergroup']:
        # В группе - проверяем авторизацию
        is_allowed = not config.ALLOWED_GROUPS or update.message.chat_id in config.ALLOWED_GROUPS

        me = await context.bot.get_me()

        if is_allowed:
            await update.message.reply_text(
                "👋 Привет! Я бот для автоматического сохранения стикеров.\n\n"
                "Все стикеры, отправленные в эту группу, будут автоматически "
                "добавлены в общий стикерпак.\n\n"
                "📦 Поддерживаемые типы:\n"
                "• Обычные стикеры (макс. 120)\n"
                "• Анимированные (макс. 50)\n"
                "• Видео (макс. 50)\n\n"
                "Просто отправьте стикер, и я создам пак!\n\n"
                f"ℹ️ Мой username: @{me.username}"
            )
        else:
            await update.message.reply_text(
                "⛔ Эта группа не авторизована для использования бота.\n\n"
                f"ID группы: {update.message.chat_id}\n\n"
                "Свяжитесь с администратором бота для получения доступа."
            )
    else:
        # В личке
        await update.message.reply_text(
            "👋 Привет! Я бот для автоматического сохранения стикеров в группах.\n\n"
            "⚠️ Внимание: я работаю только в группах!\n\n"
            "📝 Как использовать:\n"
            "1. Добавьте меня в вашу группу\n"
            "2. Отправьте любой стикер в группу\n"
            "3. Я создам стикерпак и пришлю ссылку\n\n"
            "Все стикеры из группы будут автоматически сохраняться!"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "ℹ️ Помощь - Бот для сохранения стикеров\n\n"
        "Команды:\n"
        "/start - Информация о боте\n"
        "/help - Эта справка\n\n"
        "Как работает:\n"
        "1. Добавьте бота в группу\n"
        "2. Отправьте стикер в группу\n"
        "3. Бот создаст пак и даст ссылку\n\n"
        "⚠️ Важно:\n"
        "• Бот работает только в группах\n"
        "• Для каждого типа стикеров создается отдельный пак\n"
        "• При переполнении пака создается новый автоматически"
    )


async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик входящих стикеров"""

    # Проверка наличия сообщения
    if not update.message:
        logger.warning("Получено обновление без сообщения")
        return

    sticker = update.message.sticker
    if not sticker:
        logger.warning("Сообщение не содержит стикер")
        return

    # Логируем информацию о чате
    chat_type = update.message.chat.type
    chat_id = str(update.message.chat_id)
    chat_title = update.message.chat.title or "Unknown_Group"

    logger.info(f"Получен стикер | Тип чата: {chat_type} | Название: {chat_title} | ID: {chat_id}")

    # Проверяем, что это сообщение из группы
    if chat_type not in ['group', 'supergroup']:
        logger.info("Стикер отправлен не в группу, отправляем предупреждение")
        await update.message.reply_text(
            "⚠️ Я работаю только в группах!\n\n"
            "Добавьте меня в группу и отправьте стикер там."
        )
        return

    # Проверяем, что группа в списке разрешенных
    if config.ALLOWED_GROUPS and update.message.chat_id not in config.ALLOWED_GROUPS:
        logger.warning(f"Попытка использования бота в неразрешенной группе: {chat_title} (ID: {chat_id})")
        await update.message.reply_text(
            "⛔ Эта группа не авторизована для использования бота."
        )
        return

    logger.info(f"Начинаем обработку стикера в группе {chat_title}")

    try:
        # Получаем информацию о чате
        chat_info = pack_manager.get_chat_pack_info(chat_id)

        # Обновляем название чата, если оно изменилось
        if chat_info['chat_title'] != chat_title:
            pack_manager.update_chat_pack_info(chat_id, chat_title=chat_title)

        # Определяем формат стикера
        if sticker.is_video:
            sticker_format = "video"
        elif sticker.is_animated:
            sticker_format = "animated"
        else:
            sticker_format = "static"

        logger.info(f"Формат стикера: {sticker_format}")

        # Получаем информацию о паке для этого типа стикеров
        pack_info = pack_manager.get_pack_info_for_type(chat_id, sticker_format)

        # Проверяем, нужно ли создать новый пак
        bot_username = (await context.bot.get_me()).username

        if pack_info['current_pack_name'] is None or pack_manager.needs_new_pack(chat_id, sticker_format):
            # Создаем новый пак
            if pack_manager.needs_new_pack(chat_id, sticker_format):
                pack_info['pack_number'] += 1
                logger.info(f"Пак {sticker_format} переполнен, создаем новый пак #{pack_info['pack_number']}")

            pack_name = pack_manager.create_pack_name(
                chat_title,
                sticker_format,
                pack_info['pack_number'],
                bot_username
            )

            logger.info(f"Создание нового стикерпака ({sticker_format}): {pack_name}")

            # Получаем файл стикера
            file = await context.bot.get_file(sticker.file_id)
            sticker_file = await file.download_as_bytearray()

            # Создаем InputSticker (без параметра format)
            input_sticker = InputSticker(
                sticker=bytes(sticker_file),
                emoji_list=[sticker.emoji or "😊"]
            )

            # Создаем новый стикерпак
            format_names = {"static": "Обычные", "animated": "Анимированные", "video": "Видео"}
            pack_title = f"{chat_title} - {format_names[sticker_format]}"
            if pack_info['pack_number'] > 0:
                pack_title += f" #{pack_info['pack_number']}"

            await context.bot.create_new_sticker_set(
                user_id=config.OWNER_USER_ID,
                name=pack_name,
                title=pack_title,
                stickers=[input_sticker],
                sticker_format=sticker_format,  # Формат передается здесь!
                sticker_type="regular"
            )

            # Обновляем информацию о паке для этого типа
            pack_info['current_pack_name'] = pack_name
            pack_info['sticker_count'] = 1
            pack_manager.save_state()

            # Отправляем ссылку на пак в чат
            pack_link = f"https://t.me/addstickers/{pack_name}"
            await update.message.reply_text(
                f"Создан новый стикерпак ({format_names[sticker_format]})!\n{pack_link}"
            )

            logger.info(f"Пак создан успешно: {pack_link}")

        else:
            # Добавляем стикер в существующий пак
            pack_name = pack_info['current_pack_name']
            logger.info(f"Добавление стикера в существующий пак: {pack_name}")

            # Получаем файл стикера
            file = await context.bot.get_file(sticker.file_id)
            sticker_file = await file.download_as_bytearray()

            # Создаем InputSticker (без параметра format)
            input_sticker = InputSticker(
                sticker=bytes(sticker_file),
                emoji_list=[sticker.emoji or "😊"]
            )

            # Добавляем стикер в пак
            await context.bot.add_sticker_to_set(
                user_id=config.OWNER_USER_ID,
                name=pack_name,
                sticker=input_sticker
            )

            # Увеличиваем счетчик стикеров для этого типа
            new_count = pack_manager.increment_sticker_count(chat_id, sticker_format)

            logger.info(f"Стикер ({sticker_format}) добавлен. Всего стикеров в паке: {new_count}")

    except TelegramError as e:
        logger.error(f"Ошибка Telegram API: {e}")
        await update.message.reply_text(
            f"Ошибка при добавлении стикера: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
        await update.message.reply_text(
            f"Произошла ошибка: {str(e)}"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления: {context.error}", exc_info=context.error)


def main():
    """Запуск бота"""

    if config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Не установлен токен бота! Установите переменную окружения BOT_TOKEN")
        return

    # Создаем приложение
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Добавляем обработчик стикеров
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))

    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)

    logger.info("Бот запущен и готов к работе")

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
