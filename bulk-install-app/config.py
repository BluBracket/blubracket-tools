import os

from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.environ.get('BLU_DOMAIN') or 'github.com'
GITHUB_APP_NAME = os.environ.get('BLU_GITHUB_APP_NAME')  # or 'blubracket-checks-app'
USERNAME = os.environ.get('BLU_USERNAME')
PASSWORD = os.environ.get('BLU_PASSWORD')
DEBUG = bool(int(os.environ.get('BLU_DEBUG'))) if os.environ.get('BLU_DEBUG') else False
