import asyncio
import datetime
import logging

import aiohttp
import config
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# Проверка конфигурации
try:
    if not hasattr(config, 'TELEGRAM_TOKEN'):
        raise ValueError(
            "TELEGRAM_TOKEN не найден в config.py\n"
            "Добавьте: TELEGRAM_TOKEN = 'ваш_токен'"
        )
    if not config.TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN пустой в config.py")

    if not hasattr(config, 'DEEPL_API_KEY'):
        raise ValueError(
            "DEEPL_API_KEY не найден в config.py\n"
            "Добавьте: DEEPL_API_KEY = 'ваш_ключ'\n"
            "Получить ключ: https://www.deepl.com/pro-api"
        )
    if not config.DEEPL_API_KEY:
        raise ValueError("DEEPL_API_KEY пустой в config.py")

    bot = Bot(token=config.TELEGRAM_TOKEN)
except Exception as e:
    print(f"Ошибка конфигурации: {e}")
    exit(1)


dp = Dispatcher()
user_data = {}


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
current_datetime = datetime.datetime.now()
lang_names = {'ru': 'Русский', 'en': 'English'}
logger.info("Bot configuration started at: %s", current_datetime)


async def deepl_translate(text: str, target_lang: str) -> str:
    """Перевод текста через DeepL API."""
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": config.DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error(
                        "DeepL error: %s - %s", response.status, error
                    )
                    return f"Ошибка перевода (статус {response.status})"

                data = await response.json()
                return data['translations'][0]['text']
    except Exception as e:
        logger.error("Translation error: %s", e)
        return "Ошибка при переводе"


def detect_language(text: str) -> str:
    """Определение языка текста."""
    try:
        latin = sum(1 for c in text if 'a' <= c.lower() <= 'z')
        cyrillic = sum(1 for c in text if 'а' <= c.lower() <= 'я')
        return "EN" if latin > cyrillic else "RU"
    except Exception as e:
        logger.error("Language detection error: %s", e)
        return "EN"


@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start."""
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Help', callback_data='help'),
                InlineKeyboardButton(text='Language', callback_data='language')
            ]
        ]
    )
    start_text = (
                'Привет!👐🏻\n'
                'Это телеграм-бот, который поможет тебе\n'
                'с коммунальным переводом в сфере медицины🩺🧪'
                'Выбери нужную команду📝\n'

                'Hi!👐🏻\n'

                'This is a telegram bot that will help you'
                'with community translation in the medical field🩺🧪\n'
                'Choose the necessary function📝\n'
    )
    await message.answer(start_text, reply_markup=markup)


@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Обработчик команды /help."""
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Back', callback_data='back')
            ]
        ]
    )
    help_text = (
                "Как работает телеграм-бот?\n💡"

                "📌После запуска бота выбери язык;\n"
                "📌Введи слово/словосочетание/предложение,"
                "которое требует перевода;\n"
                "📌Далее бот взаимодействует с API-сервисом"
                "Deep Translate и выводит результат,"
                "т.е. перевод введённого ранее текста;\n"
                "📌После выполнения перевода ты можешь ввести новый запрос.\n"

                "How does the telegram bot work?💡\n"

                "📌Select a language, after launching the bot;\n"
                "📌Enter the word/phrase/sentence that needs translation;\n"
                "📌Next, the bot interacts with the Deep Translate API"
                "service and outputs the result, i.e."
                "the translation of the previously entered text;\n"
                "📌After completing the translation "
                "you can enter a new request.\n"
    )
    await message.answer(help_text, reply_markup=markup)


@dp.message(Command("language"))
async def language_command(message: types.Message):
    """Обработчик команды /language."""
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='🇷🇺 Русский',
                                     callback_data='lang_ru'),
                InlineKeyboardButton(text='🇬🇧 English',
                                     callback_data='lang_en')
            ],
            [
                InlineKeyboardButton(text='Back', callback_data='back')
            ]
        ]
    )
    await message.answer(
        "Выберите язык / Choose language:", reply_markup=markup
    )


@dp.message()
async def handle_text(message: types.Message):
    """Обработка текстовых сообщений."""
    if not message.text or not message.text.strip():
        return await message.answer("Пожалуйста, введите текст")

    text = message.text.strip()
    source_lang = detect_language(text)
    target_lang = "RU" if source_lang == "EN" else "EN"

    translated = await deepl_translate(text, target_lang)
    response = (
        f"🔹 Original ("
        f"{lang_names.get(source_lang.lower(), source_lang)}):\n"
        f"{text}\n\n"
        f"🔸 Translation ("
        f"{lang_names.get(target_lang.lower(), target_lang)}):\n"
        f"{translated}"
    )
    await message.answer(response)


@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
    """Обработчик callback-запросов."""
    if call.data == 'help':
        await help_command(call.message)
    elif call.data == 'language':
        await language_command(call.message)
    elif call.data == 'back':
        await start_command(call.message)
    elif call.data.startswith('lang_'):
        lang = call.data.split('_')[1]
        user_data[call.from_user.id] = {'lang': lang}
        await call.answer(f"Язык установлен: {lang_names.get(lang, lang)}")


async def main():
    """Основная функция запуска бота."""
    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Bot error: %s", e)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Fatal error: %s", e)
