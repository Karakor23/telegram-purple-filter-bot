import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.TOKEN = self.get_token()

    def get_token(self):
        """Get token with detailed logging."""
        token = os.environ.get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")
        return token

def load_config():
    return Config()
