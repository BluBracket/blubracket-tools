import os

from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DOMAIN = os.environ.get('BLU_DOMAIN') or 'github.com'
GITHUB_APP_NAME = os.environ.get('BLU_GITHUB_APP_NAME') or 'blubracket-checks-app'
USERNAME = os.environ.get('BLU_USERNAME')
PASSWORD = os.environ.get('BLU_PASSWORD')
DEBUG = bool(int(os.environ.get('BLU_DEBUG'))) if os.environ.get('BLU_DEBUG') else False
MAX_ORGANIZATIONS = int(os.environ.get('BLU_MAX_ORGANIZATIONS')) if os.environ.get('BLU_MAX_ORGANIZATIONS') else None

DOMAIN = urlparse(DOMAIN if '//' in DOMAIN else f'//{DOMAIN}').netloc
APPS_LOCATION = 'apps' if DOMAIN == 'github.com' else 'github-apps'
