import os


from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
