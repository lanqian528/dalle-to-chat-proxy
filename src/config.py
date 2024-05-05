import os

from dotenv import load_dotenv

from src.Logger import logger

load_dotenv(encoding="ascii")


openai_base_url = os.getenv('OPENAI_BASE_URL', '')

logger.info("-" * 100)
logger.info("Environment variables:")
logger.info("OPENAI_BASE_URL:            " + str(openai_base_url))
logger.info("-" * 100)
