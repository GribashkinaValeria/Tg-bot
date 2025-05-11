import aiohttp
import logging
from config import DEEPL_API_KEY


logger = logging.getLogger(__name__)


# Перевод текста через DeepL API
async def deepl_translate(text: str, target_lang: str) -> str:
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error("DeepL error: %s - %s",
                                 response.status, error)
                    return f"Ошибка перевода (статус {response.status})"

                data = await response.json()
                return data['translations'][0]['text']
    except Exception as e:
        logger.error("Translation error: %s", e)
        return "Ошибка при переводе"


# Определение языка текста
def detect_language(text: str) -> str:
    try:
        latin = sum(1 for c in text if 'a' <= c.lower() <= 'z')
        cyrillic = sum(1 for c in text if 'а' <= c.lower() <= 'я')
        return "EN" if latin > cyrillic else "RU"
    except Exception as e:
        logger.error("Language detection error: %s", e)
        return "EN"
