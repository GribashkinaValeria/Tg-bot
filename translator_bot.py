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


async def deepl_translate(text: str, target_lang: str) -> str:
    """Перевод текста через DeepL API."""
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


def detect_language(text: str) -> str:
    """Определяет язык по используемым символам."""
    latin = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    cyrillic = sum(1 for c in text if ('а' <= c.lower() <= 'я') or c in 'ёЁ')
    return "EN" if latin > cyrillic else "RU"


@bot.message_handler(commands=['start'])
async def start_command(message):
    """Обработчик команды /start."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_help = types.InlineKeyboardButton('Help', callback_data='help')
    btn_lang = types.InlineKeyboardButton('Language', callback_data='language')
    markup.add(btn_help, btn_lang)

    start_text = (
        'Привет!👐🏻\nЭто переводчик между русским и английским.\n'
        'Просто отправьте текст для перевода.\n\n'
        'Hi!👐🏻\nThis is a translator between Russian and English.\n'
        'Just send text to translate.'
    )
    await bot.send_message(message.chat.id, start_text, reply_markup=markup)


@bot.message_handler(commands=['help'])
async def help_command(message):
    """Обработчик команды /help."""
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton('Back', callback_data='back')
    markup.add(btn_back)

    help_text = (
        "Как использовать бота:\n\n"
        "1. Отправьте текст на русском или английском\n"
        "2. Бот автоматически определит язык\n"
        "3. Получите перевод\n\n"
        "How to use the bot:\n\n"
        "1. Send text in Russian or English\n"
        "2. The bot will detect the language automatically\n"
        "3. Receive the translation"
    )
    await bot.send_message(message.chat.id, help_text, reply_markup=markup)


@bot.message_handler(commands=['language'])
async def language_command(message):
    """Обработчик команды /language."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ru = types.InlineKeyboardButton('Русский', callback_data='lang_ru')
    btn_en = types.InlineKeyboardButton('English', callback_data='lang_en')
    btn_back = types.InlineKeyboardButton('Back', callback_data='back')
    markup.add(btn_ru, btn_en, btn_back)

    lang_text = "Выберите язык / Choose language"
    await bot.send_message(message.chat.id, lang_text, reply_markup=markup)


@bot.message_handler(content_types=['text'])
async def handle_text(message):
    """Обработка текстовых сообщений."""
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


@bot.callback_query_handler(func=lambda call: True)
async def callback_handler(call):
    """Обработчик inline-кнопок."""
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


async def main():
    """Основная функция запуска бота."""
    logger.info("Starting bot...")
    await bot.polling(none_stop=True)


if __name__ == '__main__':
    asyncio.run(main())
