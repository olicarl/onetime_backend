import os
import logging

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db/onetime")
    # RabbitMQ keys removed

settings = Settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("onetime_backend")
