import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import TELEGRAM_TOKEN
from api import deepl_translate, detect_language


# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)
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


# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
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
        'с коммунальным переводом в сфере медицины🩺🧪\n'
        'Выбери нужную команду📝\n\n'
        'Hi!👐🏻\n'
        'This is a telegram bot that will help you\n'
        'with community translation in the medical field🩺🧪\n'
        'Choose the necessary function📝'
    )
    await message.answer(start_text, reply_markup=markup)


# Обработчик команды /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⬅ Back', callback_data='back')]
        ]
    )
    help_text = (
        "Как работает телеграм-бот?💡\n\n"
        "📌После запуска бота выбери язык;\n"
        "📌Введи слово/словосочетание/предложение, "
        "которое требует перевода;\n"
        "📌Далее бот взаимодействует с API-сервисом "
        "Deep Translate и выводит результат, "
        "т.е. перевод введённого ранее текста;\n"
        "📌После выполнения перевода ты можешь ввести новый запрос.\n\n"
        "How does the telegram bot work?💡\n\n"
        "📌Select a language after launching the bot;\n"
        "📌Enter the word/phrase/sentence that needs translation;\n"
        "📌Next, the bot interacts with the Deep Translate API "
        "service and outputs the result, i.e. "
        "the translation of the previously entered text;\n"
        "📌After completing the translation "
        "you can enter a new request."
    )
    await message.answer(help_text, reply_markup=markup)


# Обработчик команды /language
@dp.message(Command("language"))
async def language_command(message: types.Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='🇷🇺 Русский',
                                     callback_data='lang_ru'),
                InlineKeyboardButton(text='🇬🇧 English',
                                     callback_data='lang_en')
            ],
            [InlineKeyboardButton(text='⬅ Back', callback_data='back')]
        ]
    )
    await message.answer(
        "Выберите язык / Choose language:", reply_markup=markup
    )


# Обработчик текстовых сообщений для перевода
@dp.message()
async def handle_text(message: types.Message):
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


# Обработчик callback-запросов
@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
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


# Запуск бота
async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)
    await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
