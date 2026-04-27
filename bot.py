#!/usr/bin/env python3
"""
Телеграм бот для автоматического сохранения стикеров из группы в общий стикерпак
"""

import logging
import json
import os
import asyncio
import io
from telegram import Update, InputSticker
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
from PIL import Image
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
        "/help - Эта справка\n"
        "/add - Добавить фото/картинку в пак (ответом на сообщение)\n\n"
        "Как работает:\n"
        "1. Добавьте бота в группу\n"
        "2. Отправьте стикер в группу\n"
        "3. Бот создаст пак и даст ссылку\n\n"
        "Создание стикеров из фото:\n"
        "• Ответьте на сообщение с фото командой /add\n"
        "• Можно указать эмодзи: /add 😊 или /add 😊🎉👍\n"
        "• Бот автоматически обрежет и подгонит изображение\n\n"
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


async def convert_image_to_sticker(image_bytes: bytes) -> bytes:
    """Конвертировать изображение в формат webp 512x512"""
    try:
        # Открываем изображение
        img = Image.open(io.BytesIO(image_bytes))

        # Конвертируем в RGBA если нужно
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Определяем размеры для квадратного обрезания
        width, height = img.size
        size = min(width, height)

        # Обрезаем по центру до квадрата
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size

        img = img.crop((left, top, right, bottom))

        # Масштабируем до 512x512
        img = img.resize((512, 512), Image.Resampling.LANCZOS)

        # Сохраняем в webp
        output = io.BytesIO()
        img.save(output, format='WEBP')
        output.seek(0)

        return output.read()
    except Exception as e:
        logger.error(f"Ошибка конвертации изображения: {e}")
        raise


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /add для добавления фото/видео/gif в стикерпак"""

    # Проверяем, что это ответ на сообщение
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "⚠️ Используйте эту команду ответом на сообщение с фото, GIF или видео.\n\n"
            "Примеры:\n"
            "/add - добавить с эмодзи по умолчанию\n"
            "/add 😊 - добавить с эмодзи 😊\n"
            "/add 😊🎉👍 - добавить с несколькими эмодзи"
        )
        return

    # Проверяем тип чата
    chat_type = update.message.chat.type
    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⚠️ Эта команда работает только в группах!"
        )
        return

    # Проверяем авторизацию группы
    if config.ALLOWED_GROUPS and update.message.chat_id not in config.ALLOWED_GROUPS:
        logger.warning(f"Попытка использования /add в неразрешенной группе: {update.message.chat_id}")
        await update.message.reply_text(
            "⛔ Эта группа не авторизована для использования бота."
        )
        return

    replied_msg = update.message.reply_to_message
    chat_id = str(update.message.chat_id)
    chat_title = update.message.chat.title or "Unknown_Group"

    # Извлекаем эмодзи из аргументов команды
    emoji_list = ["😊"]  # По умолчанию
    if context.args:
        # Объединяем все аргументы и разбиваем на эмодзи
        emoji_text = ''.join(context.args)
        # Простая проверка - если есть не-пробельные символы, используем их
        if emoji_text.strip():
            emoji_list = list(emoji_text.strip())

    logger.info(f"Команда /add в группе {chat_title}, эмодзи: {emoji_list}")

    # Определяем тип медиа и получаем файл
    media_file = None
    sticker_format = None

    try:
        # Проверяем наличие фото
        if replied_msg.photo:
            logger.info("Обнаружено фото")
            # Берем фото наибольшего размера
            photo = replied_msg.photo[-1]
            media_file = await context.bot.get_file(photo.file_id)
            sticker_format = "static"

        # Проверяем наличие документа (может быть GIF)
        elif replied_msg.document and replied_msg.document.mime_type:
            mime_type = replied_msg.document.mime_type
            logger.info(f"Обнаружен документ: {mime_type}")

            if mime_type.startswith('image/'):
                media_file = await context.bot.get_file(replied_msg.document.file_id)
                sticker_format = "static"
            elif mime_type == 'video/mp4' or mime_type.startswith('video/'):
                await update.message.reply_text(
                    "⚠️ Конвертация видео в стикеры пока не поддерживается.\n"
                    "Используйте фото или статические GIF."
                )
                return

        # Проверяем наличие видео
        elif replied_msg.video:
            logger.info("Обнаружено видео")
            await update.message.reply_text(
                "⚠️ Конвертация видео в стикеры пока не поддерживается.\n"
                "Используйте фото или статические изображения."
            )
            return

        # Проверяем наличие анимации (GIF)
        elif replied_msg.animation:
            logger.info("Обнаружена анимация (GIF)")
            await update.message.reply_text(
                "⚠️ Конвертация анимированных GIF в стикеры пока не поддерживается.\n"
                "Используйте статические изображения."
            )
            return

        else:
            await update.message.reply_text(
                "⚠️ Сообщение не содержит фото, GIF или видео."
            )
            return

        if not media_file or not sticker_format:
            await update.message.reply_text(
                "⚠️ Не удалось определить тип медиа."
            )
            return

        # Скачиваем файл
        logger.info("Скачивание файла...")
        media_bytes = await media_file.download_as_bytearray()

        # Конвертируем изображение в формат стикера
        logger.info("Конвертация в формат стикера...")
        sticker_bytes = await convert_image_to_sticker(bytes(media_bytes))

        # Теперь добавляем стикер в пак (используем ту же логику, что и для обычных стикеров)
        chat_info = pack_manager.get_chat_pack_info(chat_id)

        # Обновляем название чата, если оно изменилось
        if chat_info['chat_title'] != chat_title:
            pack_manager.update_chat_pack_info(chat_id, chat_title=chat_title)

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

            # Создаем InputSticker
            input_sticker = InputSticker(
                sticker=sticker_bytes,
                emoji_list=emoji_list
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
                sticker_format=sticker_format,
                sticker_type="regular"
            )

            # Обновляем информацию о паке для этого типа
            pack_info['current_pack_name'] = pack_name
            pack_info['sticker_count'] = 1
            pack_manager.save_state()

            # Отправляем ссылку на пак в чат
            pack_link = f"https://t.me/addstickers/{pack_name}"
            await update.message.reply_text(
                f"✅ Создан новый стикерпак ({format_names[sticker_format]})!\n{pack_link}\n\n"
                f"Стикер из фото добавлен с эмодзи: {' '.join(emoji_list)}"
            )

            logger.info(f"Пак создан успешно: {pack_link}")

        else:
            # Добавляем стикер в существующий пак
            pack_name = pack_info['current_pack_name']
            logger.info(f"Добавление стикера в существующий пак: {pack_name}")

            # Создаем InputSticker
            input_sticker = InputSticker(
                sticker=sticker_bytes,
                emoji_list=emoji_list
            )

            # Добавляем стикер в пак
            await context.bot.add_sticker_to_set(
                user_id=config.OWNER_USER_ID,
                name=pack_name,
                sticker=input_sticker
            )

            # Увеличиваем счетчик стикеров для этого типа
            new_count = pack_manager.increment_sticker_count(chat_id, sticker_format)

            await update.message.reply_text(
                f"✅ Стикер добавлен в пак!\n"
                f"Эмодзи: {' '.join(emoji_list)}\n"
                f"Всего стикеров: {new_count}"
            )

            logger.info(f"Стикер ({sticker_format}) из фото добавлен. Всего в паке: {new_count}")

    except TelegramError as e:
        logger.error(f"Ошибка Telegram API при добавлении: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при добавлении стикера: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Произошла ошибка: {str(e)}"
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
    application.add_handler(CommandHandler("add", add_command))

    # Добавляем обработчик стикеров
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))

    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)

    logger.info("Бот запущен и готов к работе")

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
