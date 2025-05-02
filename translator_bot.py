import datetime
import asyncio
import logging
import requests
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv

load_dotenv()
bot = AsyncTeleBot('7683563071:AAFxJh5hbr7zSt0YVxjrLBT1MD5CzMoC744')
user_data = {}
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
current_datetime = datetime.datetime.now()
lang_names = {'ru': 'Русский', 'en': 'English'}
logger.info("Bot started at: %s", current_datetime)


# Использование DeepL API для перевода
async def deepl_translate(text: str, target_lang: str) -> str:
    api_key = "185b0fbe-7484-4d0b-8bf4-8bd28c5d4fcb:fx"
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": api_key,
        "text": text,
        "target_lang": target_lang
    }

    response = requests.post(url, data=params, timeout=10)
    if response.status_code != 200:
        logger.error(f"DeepL API error: {response.status_code}")
        return f"Ошибка перевода: статус {response.status_code}"

    data = response.json()
    if not data or "translations" not in data:
        logger.error("Invalid DeepL response format")
        return "Ошибка: неверный формат ответа"

    translations = data["translations"]
    if not translations or "text" not in translations[0]:
        logger.error("No translation in response")
        return "Ошибка: перевод отсутствует"

    return translations[0]["text"]


# Обработчик для определения языка
def detect_language(text: str) -> str:
    latin = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    cyrillic = sum(1 for c in text if ('а' <= c.lower() <= 'я') or c in 'ёЁ')
    return "EN" if latin > cyrillic else "RU"


# Обработчик команды /start
@bot.message_handler(commands=['start'])
async def start_command(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_help = types.InlineKeyboardButton('Help', callback_data='help')
    btn_lang = types.InlineKeyboardButton('Language', callback_data='language')
    markup.add(btn_help, btn_lang)

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
    await bot.send_message(message.chat.id, start_text, reply_markup=markup)


# Обработчик команды /help
@bot.message_handler(commands=['help'])
async def help_command(message):
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton('Back', callback_data='back')
    markup.add(btn_back)

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
    await bot.send_message(message.chat.id, help_text, reply_markup=markup)


# Обработчик команды /language
@bot.message_handler(commands=['language'])
async def language_command(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ru = types.InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru')
    btn_en = types.InlineKeyboardButton('🇬🇧 English', callback_data='lang_en')
    btn_back = types.InlineKeyboardButton('Back', callback_data='back')
    markup.add(btn_ru, btn_en, btn_back)

    lang_text = "Выберите язык / Choose language"
    await bot.send_message(message.chat.id, lang_text, reply_markup=markup)


# Перевод текста
@bot.message_handler(content_types=['text'])
async def handle_text(message):
    if not message.text or not message.text.strip():
        await bot.send_message(message.chat.id, "Пожалуйста, введите текст")
        return

    text = message.text.strip()
    source_lang = detect_language(text)
    target_lang = "RU" if source_lang == "EN" else "EN"

    translated = await deepl_translate(text, target_lang)
    response = (
        f"🔹 Исходный ({lang_names[source_lang.lower()]}): {text}\n\n"
        f"🔸 Перевод ({lang_names[target_lang.lower()]}): {translated}"
    )
    await bot.send_message(message.chat.id, response)


# Обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
async def callback_handler(call):
    if call.data == 'help':
        await help_command(call.message)
    elif call.data == 'language':
        await language_command(call.message)
    elif call.data == 'back':
        await start_command(call.message)
    elif call.data.startswith('lang_'):
        lang = call.data.split('_')[1]
        user_data[call.from_user.id] = {'lang': lang}
        await bot.answer_callback_query(call.id, f"Язык: {lang_names[lang]}")


# Запуск самого бота
async def main():
    logger.info("Starting bot...")
    await bot.polling(none_stop=True)


if __name__ == '__main__':
    asyncio.run(main())
